"""Cycling Coach 端到端冒烟测试

模拟用户使用流程:
1. 启动后,健康检查
2. 生成 5 个不同类型 mock 活动
3. 验证列表 / 详情 / 指标计算正确
4. 触发 AI 报告
5. 验证 dashboard 统计
"""
from __future__ import annotations
import json
import sys
import time
import urllib.request
from urllib.error import URLError

BASE = "http://127.0.0.1:8765"


def req(method: str, path: str, body=None) -> dict:
    url = BASE + path
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"} if data else {}
    r = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(r, timeout=10) as resp:
        return json.loads(resp.read())


def wait_for_server(timeout: int = 30) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            req("GET", "/api/health")
            return
        except URLError:
            time.sleep(1)
    raise SystemExit(f"Server not ready after {timeout}s")


def main() -> int:
    print("=" * 50)
    print("Cycling Coach v0.1.0 冒烟测试")
    print("=" * 50)

    print("\n[1] 健康检查")
    d = req("GET", "/api/diagnose")
    assert d["ok"], f"diagnose failed: {d}"
    print(f"  ✓ version={d['version']}, mock_mode={d['m3_mock_mode']}")

    print("\n[2] 生成 5 个 mock 活动")
    profiles = ["z2_long", "threshold", "vo2max", "recovery", "hills"]
    created_ids = []
    for p in profiles:
        r = req("POST", f"/api/dev/generate-mock?profile_key={p}")
        assert r["ok"], f"generate {p} failed: {r}"
        m = r["metrics"]
        assert m["normalized_power"] > 0, f"NP should be > 0, got {m}"
        created_ids.append(r["id"])
        print(f"  ✓ {p:12s} id={r['id']:2d} NP={m['normalized_power']:3d}W "
              f"IF={m['intensity_factor']:.2f} TSS={m['tss']:3d}")

    print("\n[3] 验证列表 / 详情")
    items = req("GET", "/api/activities")
    assert len(items) >= 5, f"should have at least 5, got {len(items)}"
    print(f"  ✓ activities count = {len(items)} (≥ 5)")

    # 验证详情含 1Hz 样本 + laps + 指标
    detail = req("GET", f"/api/activities/{created_ids[1]}")
    assert detail["samples"], "should have samples"
    assert detail["laps"], "should have laps"
    m = detail["metrics"]
    assert m["power_curve"], "should have power curve"
    assert m["hr_zones"], "should have hr zones"
    print(f"  ✓ activity #{created_ids[1]}: {len(detail['samples'])} samples, "
          f"{len(detail['laps'])} laps, NP={m['normalized_power']}W")

    print("\n[4] 验证 athlete 画像")
    a = req("GET", "/api/athlete")
    assert a["ftp"] == 250, f"default FTP should be 250, got {a['ftp']}"
    assert a["total_activities"] >= 5
    print(f"  ✓ name={a['name']} ftp={a['ftp']} total_acts={a['total_activities']}")

    print("\n[5] 触发 AI 报告")
    r = req("POST", f"/api/activities/{created_ids[0]}/analyze", {})
    assert r["ok"]
    print(f"  ✓ analyze triggered, polling...")

    # 轮询直到完成(最多 30s)
    for i in range(15):
        time.sleep(2)
        d = req("GET", f"/api/activities/{created_ids[0]}")
        if d["report_status"] == "done":
            assert d["report"], "report should be present"
            print(f"  ✓ report generated ({len(d['report'])} chars):")
            print(f"    {d['report'][:100]}...")
            break
        if d["report_status"] == "failed":
            raise SystemExit("report failed")
    else:
        raise SystemExit("report timeout")

    print("\n[6] 验证 dashboard")
    dash = req("GET", "/api/dashboard/overview")
    assert dash["total_activities"] >= 5
    assert dash["this_week"]["tss"] > 0
    print(f"  ✓ total_tss={dash['total_tss']}, "
          f"this_week_tss={dash['this_week']['tss']}, "
          f"distance={dash['total_distance_km']}km")

    print("\n" + "=" * 50)
    print("✅ 所有冒烟测试通过")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
