"""功率相关指标

参考:
- NP (Normalized Power) — TrainingPeaks / Andrew Coggan 公式
- IF (Intensity Factor) — NP / FTP
- TSS (Training Stress Score) — 经典公式
- W'bal — Skiba 模型(简化版,MVP 可选)
"""
from __future__ import annotations
import math
from typing import Optional

import numpy as np

from ..parsers.schema import Activity, Sample


def normalized_power(activity: Activity, window_s: int = 30) -> Optional[int]:
    """归一化功率 NP

    步骤:
    1. 取每秒平均功率(用现有 avg_power 不够准,这里重算自 samples)
    2. 30s 滚动平均
    3. 升 4 次方 → 平均 → 开 4 次方
    """
    pwrs = [s.power for s in activity.samples if s.power is not None]
    if not pwrs:
        return None
    arr = np.array(pwrs, dtype=float)
    if len(arr) < window_s:
        return int(round(arr.mean()))
    # 滚动平均
    kernel = np.ones(window_s) / window_s
    smoothed = np.convolve(arr, kernel, mode="valid")
    np_val = (np.mean(smoothed ** 4)) ** 0.25
    return int(round(np_val))


def intensity_factor(np_val: Optional[int], ftp: Optional[int]) -> Optional[float]:
    """IF = NP / FTP"""
    if np_val is None or ftp is None or ftp <= 0:
        return None
    return round(np_val / ftp, 3)


def training_stress_score(
    np_val: Optional[int], if_val: Optional[float], duration_s: int, ftp: Optional[int]
) -> Optional[int]:
    """TSS = (duration_s × NP × IF) / (FTP × 3600) × 100

    当 IF = NP/FTP 时可化简为: duration_s × NP² / (FTP² × 3600) × 100
    """
    if np_val is None or ftp is None or ftp <= 0 or duration_s <= 0:
        return None
    return int(round(duration_s * (np_val ** 2) / (ftp ** 2 * 3600) * 100))


def efficiency_factor(
    np_val: Optional[int], avg_hr: Optional[int]
) -> Optional[float]:
    """EF = NP / avg_HR(简化版,无 LTHR 时用)

    衡量有氧效率:同样功率下心率越低越好
    """
    if np_val is None or avg_hr is None or avg_hr <= 0:
        return None
    return round(np_val / avg_hr, 2)


def variability_index(np_val: Optional[int], avg_power: Optional[int]) -> Optional[float]:
    """VI = NP / avg_power

    衡量输出的稳定性:VI 接近 1.0 越稳,间歇训练会高(>1.05)
    """
    if np_val is None or avg_power is None or avg_power <= 0:
        return None
    return round(np_val / avg_power, 2)


def w_prime_balance(
    samples: list[Sample], cp: int, w_prime: int = 20000
) -> list[float]:
    """W'bal 模型(Skiba 2012 简化)

    W'bal(t) = W' - Σ( (W(t) - CP) × Δt )_where W>CP
    恢复时:W'bal 指数恢复,τ=546s

    返回每秒 W'bal 数组
    返回 None if 数据不足
    """
    pwrs = [s.power for s in samples if s.power is not None]
    if not pwrs or cp <= 0:
        return []
    arr = np.array(pwrs, dtype=float)
    bal = np.zeros(len(arr))
    bal[0] = w_prime
    tau = 546.0
    for i in range(1, len(arr)):
        w = arr[i]
        if w > cp:
            # 消耗
            bal[i] = max(0, bal[i - 1] - (w - cp))
        else:
            # 恢复(指数)
            bal[i] = w_prime - (w_prime - bal[i - 1]) * math.exp(-1.0 / tau)
    return bal.tolist()
