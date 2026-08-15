"""ORM 模型

表:
- athletes: 运动员(单用户 MVP,只有 1 行)
- activities: 训练记录
- workouts: AI 生成的训练课程
- preferences: 用户偏好 / 配置
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Integer, String, Float, DateTime, Text, ForeignKey, JSON, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Athlete(Base):
    """运动员(单用户 MVP)"""
    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), default="Rider")
    ftp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ftp_estimated: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lthr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    activities: Mapped[list["Activity"]] = relationship(back_populates="athlete")


class Activity(Base):
    """单次训练"""
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"), index=True)

    # 基础
    source: Mapped[str] = mapped_column(String(16))  # fit/tcx/csv
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    duration_s: Mapped[int] = mapped_column(Integer)

    # 设备给出的统计
    distance_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_elevation_gain: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_power: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_power: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_cadence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    device: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # 我们算的指标(JSON,前端拿来直接渲染)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # 1Hz 样本(只存最近 1 小时的完整数据,大量数据走文件)
    samples_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    laps_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # AI 报告
    report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_status: Mapped[str] = mapped_column(String(16), default="pending")
    # pending → analyzing → done | failed

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    athlete: Mapped[Athlete] = relationship(back_populates="activities")


class Workout(Base):
    """AI 生成的训练课程"""
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"), index=True)
    activity_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("activities.id"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(128))
    goal: Mapped[str] = mapped_column(String(64))  # 爬坡/冲刺/恢复/...
    duration_min: Mapped[int] = mapped_column(Integer)
    structure: Mapped[list] = mapped_column(JSON)  # 课程结构(分段时间)
    erg_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    zwo_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Preference(Base):
    """用户偏好(KV)"""
    __tablename__ = "preferences"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)  # JSON 字符串
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
