"""/api/activities - 训练管理"""
from __future__ import annotations
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.config import settings
from ..db import get_db
from ..db.models import Activity
from ..parsers import FitParser
from ..parsers.schema import Activity as PydanticActivity
from ..metrics import compute_metrics
from ..profile import store as profile_store
from ..coach.tools import analyze_activity_tool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/activities", tags=["activities"])

# 上传白名单
_ALLOWED_EXTS = {".fit", ".FIT", ".tcx", ".TCX", ".csv", ".CSV"}


# ---------- Schema ----------

class ActivitySummary(BaseModel):
    id: int
    start_time: datetime
    duration_s: int
    distance_m: float | None
    avg_power: int | None
    normalized_power: int | None
    tss: int | None
    avg_hr: int | None
    avg_cadence: int | None
    total_elevation_gain: float | None
    device: str | None
    source: str
    has_report: bool

    class Config:
        from_attributes = True


class ActivityDetail(ActivitySummary):
    max_power: int | None
    max_hr: int | None
    max_speed: float | None
    calories: int | None
    metrics: dict | None
    samples: list | None
    laps: list | None
    report: str | None
    report_status: str


class AnalyzeRequest(BaseModel):
    focus: str | None = None


class AnalyzeResponse(BaseModel):
    ok: bool
    report: str | None
    reason: str | None


# ---------- API ----------

@router.post("/upload")
async def upload_activity(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """上传 FIT 文件 → 解析 + 入库 + 异步生成 AI 报告"""
    if not file.filename:
        raise HTTPException(400, "未提供文件名")
    ext = Path(file.filename).suffix
    if ext not in _ALLOWED_EXTS:
        raise HTTPException(400, f"不支持的文件类型: {ext}(仅 .fit/.tcx/.csv)")

    # 落盘
    workspace = Path(settings.workspace_dir).resolve()
    input_dir = workspace / "input" / datetime.now().strftime("%Y%m%d-%H%M%S")
    input_dir.mkdir(parents=True, exist_ok=True)
    file_path = input_dir / file.filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    logger.info(f"文件已保存: {file_path} ({file_path.stat().st_size} bytes)")

    # 解析(同步,避免 V0.1.0 还要做异步队列)
    try:
        if ext.lower() == ".fit":
            activity = FitParser().parse_file(file_path)
        else:
            raise HTTPException(400, f"V0.1.0 暂只支持 .fit,{ext} 留给 V1.0")
    except Exception as e:
        logger.exception(f"解析失败: {e}")
        raise HTTPException(400, f"解析失败: {e}")

    # 指标计算
    athlete = profile_store.get_or_create_athlete(db)
    metrics = compute_metrics(
        activity,
        ftp=athlete.ftp,
        max_hr=athlete.max_hr,
        lthr=athlete.lthr,
    )

    # 入库
    db_activity = Activity(
        athlete_id=athlete.id,
        source="fit",
        file_name=file.filename,
        file_path=str(file_path),
        start_time=activity.start_time.replace(tzinfo=None) if activity.start_time.tzinfo else activity.start_time,
        duration_s=activity.duration_s,
        distance_m=activity.distance_m,
        total_elevation_gain=activity.total_elevation_gain,
        avg_power=activity.avg_power,
        max_power=activity.max_power,
        avg_hr=activity.avg_hr,
        max_hr=activity.max_hr,
        avg_cadence=activity.avg_cadence,
        avg_speed=activity.avg_speed,
        max_speed=activity.max_speed,
        calories=activity.calories,
        device=activity.device,
        metrics=metrics,
        samples_json=[s.model_dump() for s in activity.samples[:7200]],  # 上限 2h
        laps_json=[lap.model_dump() for lap in activity.laps],
        report_status="pending",
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    logger.info(f"活动入库: id={db_activity.id}, NP={metrics.get('normalized_power')}")

    # 异步生成报告
    if background_tasks is not None:
        background_tasks.add_task(_run_analyze, db_activity.id, None)

    return {
        "ok": True,
        "id": db_activity.id,
        "metrics": metrics,
        "report_status": "pending",
    }


def _run_analyze(activity_id: int, focus: str | None) -> None:
    """后台任务:生成 AI 报告"""
    from ..db.database import SessionLocal
    db = SessionLocal()
    try:
        result = analyze_activity_tool(db, activity_id, focus=focus)
        a = db.query(Activity).get(activity_id)
        if a:
            if result["ok"]:
                report = result.get("report") or ""
                a.report = report
                a.report_status = "done" if report.strip() else "failed"
                logger.info(
                    f"活动 {activity_id} 报告生成: status={a.report_status}, "
                    f"len={len(report)}"
                )
            else:
                a.report_status = "failed"
                logger.warning(
                    f"活动 {activity_id} 报告生成失败: {result.get('reason')}"
                )
            db.commit()
            logger.info(f"活动 {activity_id} 报告状态: {a.report_status}")
    finally:
        db.close()


@router.get("", response_model=list[ActivitySummary])
def list_activities(limit: int = 50, db: Session = Depends(get_db)):
    """活动列表(按时间倒序)"""
    activities = (
        db.query(Activity)
        .order_by(Activity.start_time.desc())
        .limit(limit)
        .all()
    )
    return [_to_summary(a) for a in activities]


@router.get("/{activity_id}", response_model=ActivityDetail)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    """活动详情(含 1Hz 样本 + AI 报告)"""
    a = db.query(Activity).get(activity_id)
    if not a:
        raise HTTPException(404, f"活动 {activity_id} 不存在")
    return _to_detail(a)


@router.post("/{activity_id}/analyze", response_model=AnalyzeResponse)
def trigger_analyze(
    activity_id: int,
    req: AnalyzeRequest = AnalyzeRequest(),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """重新生成 AI 报告"""
    a = db.query(Activity).get(activity_id)
    if not a:
        raise HTTPException(404, f"活动 {activity_id} 不存在")
    a.report_status = "analyzing"
    db.commit()
    if background_tasks is not None:
        background_tasks.add_task(_run_analyze, activity_id, req.focus)
    return {"ok": True, "report": None, "reason": "已加入后台队列"}


@router.delete("/{activity_id}")
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    a = db.query(Activity).get(activity_id)
    if not a:
        raise HTTPException(404, f"活动 {activity_id} 不存在")
    db.delete(a)
    db.commit()
    return {"ok": True}


# ---------- helpers ----------

def _to_summary(a: Activity) -> ActivitySummary:
    m = a.metrics or {}
    return ActivitySummary(
        id=a.id,
        start_time=a.start_time,
        duration_s=a.duration_s,
        distance_m=a.distance_m,
        avg_power=a.avg_power,
        normalized_power=m.get("normalized_power") if isinstance(m, dict) else None,
        tss=m.get("tss") if isinstance(m, dict) else None,
        avg_hr=a.avg_hr,
        avg_cadence=a.avg_cadence,
        total_elevation_gain=a.total_elevation_gain,
        device=a.device,
        source=a.source,
        has_report=bool(a.report),
    )


def _to_detail(a: Activity) -> ActivityDetail:
    s = _to_summary(a)
    return ActivityDetail(
        **s.model_dump(),
        max_power=a.max_power,
        max_hr=a.max_hr,
        max_speed=a.max_speed,
        calories=a.calories,
        metrics=a.metrics,
        samples=a.samples_json or [],
        laps=a.laps_json or [],
        report=a.report,
        report_status=a.report_status,
    )
