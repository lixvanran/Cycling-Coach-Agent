"""心率相关指标"""
from __future__ import annotations
from typing import Optional

import numpy as np

from ..parsers.schema import Activity, Sample


def hr_zones(
    activity: Activity,
    max_hr: Optional[int] = None,
    lthr: Optional[int] = None,
) -> dict[str, int]:
    """心率区间累计时间(秒)

    V0.1.1 升级:有 LTHR 用 Karvonen 7 区(更准),否则用 max_hr 5 区(Coggan 兜底)

    Karvonen 7 区(基于 LTHR):
      Z1: <81%   Active Recovery
      Z2: 81-89% Endurance
      Z3: 90-93% Tempo
      Z4: 94-99% Threshold
      Z5: 100-102% Above Threshold
      Z6: 103-105% Anaerobic
      Z7: >106%  VO2 Max

    Coggan 5 区(基于 max_hr):
      Z1: <60%   Recovery
      Z2: 60-70% Endurance
      Z3: 70-80% Tempo
      Z4: 80-90% Threshold
      Z5: >90%   VO2

    返回 {"Z1": seconds, "Z2": seconds, ..., "Z5"/"Z7": seconds}
    """
    hrs = [s.hr for s in activity.samples if s.hr is not None]
    if not hrs:
        return {}
    arr = np.array(hrs)

    if lthr and lthr > 0:
        # Karvonen 7 区
        pct = arr / lthr
        bins = [-np.inf, 0.81, 0.89, 0.93, 0.99, 1.02, 1.05, np.inf]
        labels = ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7"]
    else:
        # 兜底:Coggan 5 区(max_hr)
        if not max_hr or max_hr <= 0:
            return {}
        pct = arr / max_hr
        bins = [-np.inf, 0.60, 0.70, 0.80, 0.90, np.inf]
        labels = ["Z1", "Z2", "Z3", "Z4", "Z5"]

    result: dict[str, int] = {label: 0 for label in labels}
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
