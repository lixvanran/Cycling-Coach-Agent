// 训练列表
import { useEffect, useState } from "react";
import { Trash2, FileText, ChevronRight, Plus } from "lucide-react";
import { api } from "../lib/api";
import type { ActivitySummary } from "../lib/types";
import { useAppStore } from "../store/useAppStore";

export function ActivityList() {
  const [items, setItems] = useState<ActivitySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const setView = useAppStore((s) => s.setView);
  const setSelected = useAppStore((s) => s.setSelectedActivity);

  const load = () => {
    setLoading(true);
    api.listActivities(50).then(setItems).finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const onSelect = (id: number) => {
    setSelected(id);
    setView("activity-detail");
  };

  const onDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("删除这条训练?原文件不会删除。")) return;
    await api.deleteActivity(id);
    load();
  };

  if (loading) {
    return <div className="p-6 text-text-muted">加载中…</div>;
  }

  if (items.length === 0) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="text-center">
          <p className="text-text-muted mb-4">还没有训练数据</p>
          <button onClick={() => setView("import")} className="btn-primary">
            <Plus size={14} />
            导入
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-text-primary">训练记录</h1>
        <button onClick={() => setView("import")} className="btn-primary">
          <Plus size={14} />
          导入
        </button>
      </div>

      <div className="panel overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-bg-elevated">
            <tr className="text-xs text-text-secondary uppercase tracking-wider">
              <th className="text-left px-4 py-2.5 font-medium">日期</th>
              <th className="text-right px-4 py-2.5 font-medium">时长</th>
              <th className="text-right px-4 py-2.5 font-medium">距离</th>
              <th className="text-right px-4 py-2.5 font-medium">NP</th>
              <th className="text-right px-4 py-2.5 font-medium">IF</th>
              <th className="text-right px-4 py-2.5 font-medium">TSS</th>
              <th className="text-right px-4 py-2.5 font-medium">设备</th>
              <th className="text-right px-4 py-2.5 font-medium">报告</th>
              <th className="w-8"></th>
            </tr>
          </thead>
          <tbody>
            {items.map((a) => {
              const dt = new Date(a.start_time);
              const ifV = (a as any).intensity_factor;
              return (
                <tr
                  key={a.id}
                  onClick={() => onSelect(a.id)}
                  className="border-t border-border hover:bg-bg-elevated cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="text-text-primary font-medium">
                      {dt.toLocaleDateString("zh-CN", { month: "short", day: "numeric" })}
                    </div>
                    <div className="text-xs text-text-muted">
                      {dt.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
                      {" · "}
                      {weekdayCn(dt)}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-text-primary">
                    {formatDuration(a.duration_s)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-text-primary">
                    {a.distance_m ? (a.distance_m / 1000).toFixed(1) : "—"} km
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-text-primary">
                    {a.normalized_power ?? "—"}
                    <span className="text-xs text-text-muted ml-1">W</span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-text-primary">
                    {ifV ? ifV.toFixed(2) : "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={`font-mono ${
                        (a.tss || 0) >= 150
                          ? "text-accent-danger"
                          : (a.tss || 0) >= 100
                          ? "text-accent-warning"
                          : "text-text-primary"
                      }`}
                    >
                      {a.tss ?? "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-xs text-text-muted">
                    {a.device || a.source}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {a.has_report ? (
                      <span className="badge bg-accent-success/20 text-accent-success">
                        <FileText size={10} className="mr-1" />
                        已生成
                      </span>
                    ) : (
                      <span className="badge bg-bg-elevated text-text-muted">无</span>
                    )}
                  </td>
                  <td className="px-2 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={(e) => onDelete(a.id, e)}
                        className="p-1 hover:bg-bg-base rounded text-text-muted hover:text-accent-danger"
                      >
                        <Trash2 size={12} />
                      </button>
                      <ChevronRight size={14} className="text-text-muted" />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatDuration(s: number): string {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h > 0) return `${h}h${m}m`;
  return `${m}m`;
}

function weekdayCn(d: Date): string {
  return ["周日", "周一", "周二", "周三", "周四", "周五", "周六"][d.getDay()];
}
