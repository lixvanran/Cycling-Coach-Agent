// 训练图:功率 + HR 随时间变化
import { useMemo } from "react";
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import type { Sample } from "../lib/types";

interface PowerHrTimeChartProps {
  samples: Sample[];
  ftp?: number | null;
}

export function PowerHrTimeChart({ samples, ftp }: PowerHrTimeChartProps) {
  // 降采样:把 1Hz 降到 5Hz(每秒 5 个数据点 → 每 12s 1 个)
  const data = useMemo(() => {
    if (samples.length === 0) return [];
    const stride = Math.max(1, Math.floor(samples.length / 1500));
    return samples
      .filter((_, i) => i % stride === 0)
      .map((s) => ({
        t: s.t_offset,
        tLabel: formatTime(s.t_offset),
        power: s.power,
        hr: s.hr,
        cadence: s.cadence,
        elevation: s.elevation,
      }));
  }, [samples]);

  if (data.length === 0) {
    return <div className="text-text-muted text-sm p-4">无样本数据</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
        <defs>
          <linearGradient id="elevGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.4} />
            <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.05} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#252b3b" />
        <XAxis
          dataKey="tLabel"
          stroke="#5a6376"
          style={{ fontSize: 11, fontFamily: "monospace" }}
          minTickGap={50}
        />
        <YAxis
          yAxisId="power"
          stroke="#3b82f6"
          style={{ fontSize: 11, fontFamily: "monospace" }}
          unit="W"
        />
        <YAxis
          yAxisId="hr"
          orientation="right"
          stroke="#ef4444"
          style={{ fontSize: 11, fontFamily: "monospace" }}
          unit="bpm"
        />
        <YAxis
          yAxisId="elev"
          orientation="right"
          hide
          domain={["dataMin - 10", "dataMax + 10"]}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1a2030",
            border: "1px solid #2e3548",
            borderRadius: 6,
            fontSize: 12,
          }}
          labelStyle={{ color: "#e8ecf2" }}
        />
        <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
        <Area
          yAxisId="elev"
          type="monotone"
          dataKey="elevation"
          fill="url(#elevGrad)"
          stroke="#06b6d4"
          strokeWidth={1}
          name="海拔 (m)"
        />
        <Line
          yAxisId="power"
          type="monotone"
          dataKey="power"
          stroke="#3b82f6"
          strokeWidth={1.5}
          dot={false}
          name="功率 (W)"
        />
        <Line
          yAxisId="hr"
          type="monotone"
          dataKey="hr"
          stroke="#ef4444"
          strokeWidth={1.5}
          dot={false}
          name="心率 (bpm)"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

function formatTime(s: number): string {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}`;
  return `${m}:${String(sec).padStart(2, "0")}`;
}
