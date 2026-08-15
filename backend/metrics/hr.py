"""心率相关指标"""
from __future__ import annotations
from typing import Optional

import numpy as np

from ..parsers.schema import Activity, Sample


def hr_zones(
    activity: Activity, max_hr: int, zones: int = 5
) -> dict[str, int]:
    """心率区间累计时间(秒)

    zones=5(默认,Coggan):
      Z1: <60%  max
      Z2: 60-70%
      Z3: 70-80%
      Z4: 80-90%
      Z5: >90%
    """
    if max_hr <= 0:
        return {}
    hrs = [s.hr for s in activity.samples if s.hr is not None]
    if not hrs:
        return {}
    arr = np.array(hrs)
    pct = arr / max_hr
    bins = [0, 0.6, 0.7, 0.8, 0.9, 1.01]
    labels = ["Z1", "Z2", "Z3", "Z4", "Z5"]
    result: dict[str, int] = {}
    for i, label in enumerate(labels):
        lo, hi = bins[i], bins[i + 1]
        mask = (pct >= lo) & (pct < hi)
        result[label] = int(mask.sum())
    return result


def hr_drift(activity: Activity) -> Optional[float]:
    """心率漂移:后半段平均 HR - 前半段平均 HR

    有氧基础好的人漂移小(控强度长时间输出)
    """
    hrs = [s.hr for s in activity.samples if s.hr is not None]
    if len(hrs) < 120:  # 至少 2 分钟
        return None
    half = len(hrs) // 2
    first = np.mean(hrs[:half])
    second = np.mean(hrs[half:])
    return round(float(second - first), 1)
