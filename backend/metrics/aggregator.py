"""指标聚合入口

对 Activity 算所有指标,返回结构化 dict,便于 DB 存 + API 返回
"""
from __future__ import annotations
import logging
from typing import Optional

from ..parsers.schema import Activity
from . import power, hr, curve

logger = logging.getLogger(__name__)


def compute_metrics(
    activity: Activity, ftp: Optional[int] = None, max_hr: Optional[int] = None
) -> dict:
    """聚合计算所有指标"""
    np_val = power.normalized_power(activity)
    if_val = power.intensity_factor(np_val, ftp)
    tss_val = power.training_stress_score(np_val, if_val, activity.duration_s, ftp)
    ef = power.efficiency_factor(np_val, activity.avg_hr)
    vi = power.variability_index(np_val, activity.avg_power)
    mmp = curve.mean_maximal_power(activity)
    hr_zones = hr.hr_zones(activity, max_hr) if max_hr else {}
    drift = hr.hr_drift(activity)
    cad_zones = curve.cadence_zones(activity)
    ftp_est = curve.estimate_ftp(activity) if not ftp else None

    metrics = {
        "normalized_power": np_val,
        "intensity_factor": if_val,
        "tss": tss_val,
        "efficiency_factor": ef,
        "variability_index": vi,
        "power_curve": mmp,
        "hr_zones": hr_zones,
        "hr_drift": drift,
        "cadence_zones": cad_zones,
        "ftp_estimated": ftp_est,
    }
    logger.info(
        f"指标聚合完成: NP={np_val}W IF={if_val} TSS={tss_val} VI={vi}"
    )
    return metrics
