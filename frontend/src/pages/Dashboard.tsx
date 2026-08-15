// Dashboard 主页
import { useEffect, useState } from "react";
import { Activity, Clock, Flame, Mountain } from "lucide-react";
import { MetricCard } from "../components/MetricCard";
import { api } from "../lib/api";
import type { DashboardOverview, Athlete } from "../lib/types";
import { useAppStore } from "../store/useAppStore";

export function Dashboard() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [athlete, setAthlete] = useState<Athlete | null>(null);
  const [loading, setLoading] = useState(true);
  const setView = useAppStore((s) => s.setView);

  useEffect(() => {
    Promise.all([api.getOverview(), api.getAthlete()])
      .then(([o, a]) => {
        setOverview(o);
        setAthlete(a);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-6 text-text-muted">加载中…</div>;
  }

  if (!overview || overview.total_activities === 0) {
    return <EmptyState onImport={() => setView("import")} />;
  }

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* 头部 */}
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">
          欢迎回来,{athlete?.name || "Rider"}
        </h1>
        <p className="text-sm text-text-muted mt-1">
          这是你目前的训练概览。继续坚持。
        </p>
      </div>

      {/* 本周 */}
      <section>
        <h2 className="text-sm uppercase tracking-wider text-text-secondary mb-3">本周</h2>
        <div className="grid grid-cols-4 gap-3">
          <MetricCard
            label="训练次数"
            value={overview.this_week.activities}
            unit="次"
          />
          <MetricCard
            label="距离"
            value={overview.this_week.distance_km}
            unit="km"
          />
          <MetricCard
            label="时长"
            value={overview.this_week.duration_h}
            unit="h"
          />
          <MetricCard
            label="TSS"
            value={overview.this_week.tss}
            unit=""
            accent="primary"
            hint="训练压力"
          />
        </div>
      </section>

      {/* 累计 */}
      <section>
        <h2 className="text-sm uppercase tracking-wider text-text-secondary mb-3">累计</h2>
        <div className="grid grid-cols-4 gap-3">
          <MetricCard
            label="总训练"
            value={overview.total_activities}
            unit="次"
          />
          <MetricCard
            label="总距离"
            value={overview.total_distance_km}
            unit="km"
          />
          <MetricCard
            label="总时长"
            value={overview.total_duration_h}
            unit="h"
          />
          <MetricCard
            label="总 TSS"
            value={overview.total_tss}
            accent="warning"
          />
        </div>
      </section>

      {/* 最近 7 天 */}
      <section>
        <h2 className="text-sm uppercase tracking-wider text-text-secondary mb-3">最近 7 天</h2>
        <div className="panel p-4">
          <div className="grid grid-cols-7 gap-2">
            {overview.last_7_days.map((d, i) => (
              <div key={i} className="text-center">
                <div className="text-xs text-text-muted mb-2">
                  {new Date(d.date).toLocaleDateString("zh-CN", { weekday: "short" })}
                </div>
                <div className="h-24 bg-bg-input rounded flex items-end justify-center p-1">
                  <div
                    className="w-full bg-accent-primary rounded-sm"
                    style={{
                      height: `${Math.min(100, (d.tss / Math.max(1, ...overview.last_7_days.map(x => x.tss))) * 100)}%`,
                    }}
                  />
                </div>
                <div className="text-xs font-mono text-text-primary mt-1">{d.tss}</div>
                <div className="text-[10px] text-text-muted">{d.distance_km}km</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 快速操作 */}
      <section>
        <h2 className="text-sm uppercase tracking-wider text-text-secondary mb-3">快速操作</h2>
        <div className="flex gap-3">
          <button onClick={() => setView("import")} className="btn-primary">
            <Activity size={14} />
            导入训练数据
          </button>
          <button onClick={() => setView("activities")} className="btn-ghost">
            查看所有训练
          </button>
        </div>
      </section>
    </div>
  );
}

function EmptyState({ onImport }: { onImport: () => void }) {
  return (
    <div className="h-full flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 rounded-full bg-bg-elevated mx-auto mb-4 flex items-center justify-center">
          <Activity size={28} className="text-text-muted" />
        </div>
        <h2 className="text-xl font-semibold text-text-primary mb-2">还没有训练数据</h2>
        <p className="text-sm text-text-muted mb-6">
          上传一个 FIT 文件,或者先生成一些示例训练看看效果。
        </p>
        <button onClick={onImport} className="btn-primary">
          开始训练 →
        </button>
      </div>
    </div>
  );
}
