"""指标计算单元测试

跑法:cd backend && ../.venv/bin/python ../scripts/test_metrics.py
"""
from __future__ import annotations
import sys
from pathlib import Path

# 把 backend 父目录加到 sys.path,以便用 backend.xxx 包形式导入
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import math
import numpy as np
from backend.parsers.schema import Activity, Sample
from backend.metrics import compute_metrics, power, hr, curve


def make_activity(powers, hrs=None, cads=None, duration_s=None):
    """构造测试 Activity(1Hz 样本)"""
    n = len(powers)
    if duration_s is None:
        duration_s = n
    if hrs is None:
        hrs = [150] * n
    if cads is None:
        cads = [90] * n
    samples = [
        Sample(
            t_offset=i,
            power=powers[i],
            hr=hrs[i],
            cadence=cads[i],
            speed=8.0,
            elevation=0.0,
        )
        for i in range(n)
    ]
    return Activity(
        source="test",
        start_time=__import__("datetime").datetime(2024, 1, 1),
        duration_s=duration_s,
        distance_m=8.0 * n,
        avg_power=int(np.mean(powers)),
        max_power=max(powers),
        avg_hr=int(np.mean(hrs)),
        max_hr=max(hrs) if hrs else None,
        avg_cadence=int(np.mean(cads)),
        samples=samples,
        laps=[],
    )


# ====== NP 测试 ======

def test_np_constant_power():
    """恒功率 200W,NP 应等于 200"""
    a = make_activity([200] * 60)
    np_val = power.normalized_power(a)
    assert np_val == 200, f"NP should be 200, got {np_val}"
    print("✓ test_np_constant_power")


def test_np_intervals_higher():
    """间歇(高低交替)NP 应高于均值"""
    # 30s 高 + 30s 低,共 60s;均值 = 200,但 NP 应 > 200
    powers = [300] * 30 + [100] * 30
    a = make_activity(powers)
    np_val = power.normalized_power(a)
    avg = np.mean(powers)
    assert np_val > avg, f"NP={np_val} should be > avg={avg}"
    print(f"✓ test_np_intervals_higher: avg={avg}, NP={np_val}")


# ====== IF / TSS 测试 ======

def test_if_tss_ftp_test():
    """FTP 测试(60 分钟全力):IF ≈ 1.0,TSS = 100"""
    powers = [250] * 3600  # 1 小时,250W 假设 FTP=250
    a = make_activity(powers)
    np_val = power.normalized_power(a)
    if_val = power.intensity_factor(np_val, ftp=250)
    tss = power.training_stress_score(np_val, if_val, a.duration_s, ftp=250)
    assert math.isclose(if_val, 1.0, abs_tol=0.01), f"IF should be 1.0, got {if_val}"
    assert math.isclose(tss, 100, abs_tol=0.5), f"TSS should be 100, got {tss}"
    print(f"✓ test_if_tss_ftp_test: IF={if_val:.2f}, TSS={tss}")


def test_if_recovery():
    """恢复训练(50% FTP,30 分钟):IF=0.5, TSS = duration_h * IF² * 100 ≈ 12.5"""
    # 经典公式: TSS = duration_h × IF² × 100
    # 0.5h × 0.25 × 100 = 12.5
    powers = [125] * 1800  # 30 分钟,50% FTP
    a = make_activity(powers)
    np_val = power.normalized_power(a)
    if_val = power.intensity_factor(np_val, ftp=250)
    tss = power.training_stress_score(np_val, if_val, a.duration_s, ftp=250)
    assert math.isclose(if_val, 0.5, abs_tol=0.01)
    assert math.isclose(tss, 12.5, abs_tol=0.5), f"TSS should be ~12.5, got {tss}"
    print(f"✓ test_if_recovery: IF={if_val:.2f}, TSS={tss}")


# ====== Power Zones 测试 ======

def test_power_zones_distribution():
    """功率区间累计时间应等于总时长"""
    # 50% (Z1) + 100% (Z4) + 130% (Z6) = 3min
    powers = [125] * 60 + [250] * 60 + [325] * 60  # 50%/100%/130% of 250
    a = make_activity(powers)
    pz = power.power_zones(a, ftp=250)
    assert pz, "power_zones should return non-empty dict"
    total = sum(pz.values())
    assert total == 180, f"total should be 180s, got {total}"
    # 验证:50% < 55% 边界 → Z1;100% 在 91-105% → Z4;130% 在 121-150% → Z6
    assert pz["Z1"] == 60, f"Z1 (50%) should be 60s, got {pz.get('Z1')}"
    assert pz["Z4"] == 60, f"Z4 (100%) should be 60s, got {pz.get('Z4')}"
    assert pz["Z6"] == 60, f"Z6 (130%) should be 60s, got {pz.get('Z6')}"
    print(f"✓ test_power_zones_distribution: {pz}")


def test_power_zones_coggan_7_zones():
    """Coggan 7 区边界"""
    pz = {"Z1": 100, "Z2": 100, "Z3": 100, "Z4": 100, "Z5": 100, "Z6": 100, "Z7": 100}
    a = make_activity([200] * 700)
    # mock:实际由 power_zones 自己算
    pz = power.power_zones(a, ftp=250)
    assert set(pz.keys()) == {"Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7"}, f"应该有 7 个区, got {set(pz.keys())}"
    print(f"✓ test_power_zones_coggan_7_zones: keys={list(pz.keys())}")


# ====== HR Zones 测试 ======

def test_hr_zones_lthr_7_zones():
    """有 LTHR 用 Karvonen 7 区"""
    # LTHR=170,Z1<81%LTHR=137.7,Z2 81-89%=137.7-151.3
    # 130bpm 在 Z1, 145 在 Z2, 165 在 Z3, 170 在 Z4-5, 180 在 Z6-7
    hrs = [130] * 10 + [145] * 10 + [165] * 10 + [170] * 10 + [180] * 10
    a = make_activity([150] * 50, hrs=hrs)
    hz = hr.hr_zones(a, max_hr=190, lthr=170)
    assert set(hz.keys()) == {"Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7"}, f"应 7 区, got {set(hz.keys())}"
    assert hz["Z1"] == 10
    assert hz["Z2"] == 10
    print(f"✓ test_hr_zones_lthr_7_zones: {hz}")


def test_hr_zones_fallback_max_hr_5_zones():
    """无 LTHR 兜底 max_hr 5 区"""
    hrs = [120] * 30 + [150] * 30 + [180] * 30  # ~63%, ~79%, ~95% of 190
    a = make_activity([150] * 90, hrs=hrs)
    hz = hr.hr_zones(a, max_hr=190, lthr=None)
    assert set(hz.keys()) == {"Z1", "Z2", "Z3", "Z4", "Z5"}, f"应 5 区兜底, got {set(hz.keys())}"
    print(f"✓ test_hr_zones_fallback_max_hr_5_zones: {hz}")


# ====== 功率曲线测试 ======

def test_power_curve():
    """功率曲线(各时长 max avg)应该单调递减"""
    # 60s 全力 300W,前面 30s 150W
    powers = [150] * 30 + [300] * 30 + [200] * 240
    a = make_activity(powers, duration_s=300)
    mmp = curve.mean_maximal_power(a, durations_s=[5, 30, 60, 300])
    assert mmp["5s"] >= 290, f"5s max avg should be ~300, got {mmp['5s']}"
    assert mmp["30s"] >= 200, f"30s max avg should be high, got {mmp['30s']}"
    assert mmp["300s"] < mmp["30s"], "300s 应该 ≤ 30s"
    print(f"✓ test_power_curve: {mmp}")


# ====== HR Drift 测试 ======

def test_hr_drift():
    """后半段 HR - 前半段 HR(需要 ≥120s 数据)"""
    # 5min 数据:前 150s 平均 140,后 150s 平均 160
    hrs = [140] * 150 + [160] * 150
    a = make_activity([150] * 300, hrs=hrs, duration_s=300)
    drift = hr.hr_drift(a)
    assert drift == 20.0, f"drift should be 20, got {drift}"
    print(f"✓ test_hr_drift: {drift}")


def test_hr_drift_short_returns_none():
    """数据太短(<120s)drift 返回 None"""
    hrs = [140] * 30 + [160] * 30  # 只有 60s
    a = make_activity([150] * 60, hrs=hrs)
    drift = hr.hr_drift(a)
    assert drift is None, f"短数据应返回 None, got {drift}"
    print(f"✓ test_hr_drift_short_returns_none: {drift}")


# ====== Cadence Zones 测试 ======

def test_cadence_zones_4_zones():
    """4 区: <60, 60-79, 80-94, ≥95"""
    cads = [50] * 10 + [70] * 10 + [85] * 10 + [100] * 10
    a = make_activity([150] * 40, cads=cads)
    cz = curve.cadence_zones(a)
    assert set(cz.keys()) == {"<60", "60-79", "80-94", "≥95"}, f"应 4 区, got {set(cz.keys())}"
    assert cz["<60"] == 10
    assert cz["60-79"] == 10
    assert cz["80-94"] == 10
    assert cz["≥95"] == 10
    print(f"✓ test_cadence_zones_4_zones: {cz}")


# ====== 端到端 compute_metrics 测试 ======

def test_compute_metrics_full():
    """完整 compute_metrics 跑一次,确保所有字段都有"""
    a = make_activity([200] * 600, hrs=[150] * 600, cads=[88] * 600)
    m = compute_metrics(a, ftp=250, max_hr=190, lthr=170)
    expected_keys = [
        "normalized_power", "intensity_factor", "tss",
        "efficiency_factor", "variability_index",
        "power_curve", "power_zones", "hr_zones", "hr_drift",
        "cadence_zones", "ftp_estimated",
    ]
    for k in expected_keys:
        assert k in m, f"missing key: {k}"
    # 验证有值
    assert m["normalized_power"] is not None
    assert m["power_zones"]
    assert m["hr_zones"]
    assert m["cadence_zones"]
    print(f"✓ test_compute_metrics_full: NP={m['normalized_power']}, TSS={m['tss']}")


# ====== 主入口 ======

if __name__ == "__main__":
    tests = [
        test_np_constant_power,
        test_np_intervals_higher,
        test_if_tss_ftp_test,
        test_if_recovery,
        test_power_zones_distribution,
        test_power_zones_coggan_7_zones,
        test_hr_zones_lthr_7_zones,
        test_hr_zones_fallback_max_hr_5_zones,
        test_power_curve,
        test_hr_drift,
        test_hr_drift_short_returns_none,
        test_cadence_zones_4_zones,
        test_compute_metrics_full,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"✗ {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print()
    if failed == 0:
        print(f"✅ {len(tests)}/{len(tests)} passed")
    else:
        print(f"❌ {len(tests) - failed}/{len(tests)} passed ({failed} failed)")
        sys.exit(1)
