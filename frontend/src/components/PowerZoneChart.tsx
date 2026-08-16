// 功率区间分布(Coggan 7 区)— 对齐 TP 必有
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface PowerZoneChartProps {
  zones: Record<string, number>; // {"Z1": sec, ...}
}

// Coggan 7 区配色:浅绿到深红(强度递增)
const ZONE_COLORS: Record<string, string> = {
  Z1: "#a7f3d0",  // <55%   浅绿
  Z2: "#86efac",  // 56-75% 绿
  Z3: "#fde047",  // 76-90% 黄
  Z4: "#fbbf24",  // 91-105% 橙黄
  Z5: "#fb923c",  // 106-120% 橙
  Z6: "#f87171",  // 121-150% 红
  Z7: "#dc2626",  // >150%   深红
};

const ZONE_LABELS: Record<string, string> = {
  Z1: "Z1 恢复",
  Z2: "Z2 耐力",
  Z3: "Z3 节奏",
  Z4: "Z4 阈值",
  Z5: "Z5 VO2",
  Z6: "Z6 无氧",
  Z7: "Z7 神经肌肉",
};

export function PowerZoneChart({ zones }: PowerZoneChartProps) {
  const data = Object.entries(zones).map(([k, v]) => ({
    zone: k,
    label: ZONE_LABELS[k] || k,
    seconds: v,
    minutes: Math.round((v / 60) * 10) / 10,
  }));

  if (data.length === 0) {
    return <div className="text-text-muted text-sm p-4">无功率区间数据(需先设置 FTP)</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
        <XAxis
          dataKey="zone"
          stroke="#86909d"
          style={{ fontSize: 11, fontFamily: "monospace" }}
        />
        <YAxis
          stroke="#86909d"
          style={{ fontSize: 11, fontFamily: "monospace" }}
          unit=" min"
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "rgba(255,255,255,0.95)",
            border: "1px solid rgba(15,23,42,0.12)",
            borderRadius: 8,
            fontSize: 12,
            boxShadow: "0 4px 12px rgba(15,23,42,0.08)",
          }}
          labelStyle={{ color: "#1a1f2e" }}
          itemStyle={{ color: "#1a1f2e" }}
          formatter={(v: number, _n, p: any) => [
            `${v} min (${p.payload.seconds}s)`,
            ZONE_LABELS[p.payload.zone] || p.payload.zone,
          ]}
        />
        <Bar dataKey="minutes" radius={[4, 4, 0, 0]}>
          {data.map((entry) => (
            <Cell key={entry.zone} fill={ZONE_COLORS[entry.zone] || "#94a3b8"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
