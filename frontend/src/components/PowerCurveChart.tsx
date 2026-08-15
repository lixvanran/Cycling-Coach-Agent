// 功率曲线图(MMP)
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

interface PowerCurveChartProps {
  powerCurve: Record<string, number>; // {"5s": 280, "60s": 250, ...}
  ftp?: number | null;
}

export function PowerCurveChart({ powerCurve, ftp }: PowerCurveChartProps) {
  const data = Object.entries(powerCurve)
    .map(([k, v]) => {
      // k 可能是 "5s" / "60s" / "300s" 等
      const seconds = parseInt(k.replace("s", ""));
      return { seconds, label: formatDuration(seconds), watts: v };
    })
    .sort((a, b) => a.seconds - b.seconds);

  if (data.length === 0) {
    return <div className="text-text-muted text-sm p-4">无功率数据</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#252b3b" />
        <XAxis
          dataKey="label"
          stroke="#5a6376"
          style={{ fontSize: 11, fontFamily: "monospace" }}
        />
        <YAxis
          stroke="#5a6376"
          style={{ fontSize: 11, fontFamily: "monospace" }}
          unit="W"
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1a2030",
            border: "1px solid #2e3548",
            borderRadius: 6,
            fontSize: 12,
          }}
          labelStyle={{ color: "#e8ecf2" }}
          itemStyle={{ color: "#3b82f6" }}
          formatter={(v: number) => [`${v} W`, "平均功率"]}
        />
        {ftp && (
          <ReferenceLine
            y={ftp}
            stroke="#10b981"
            strokeDasharray="3 3"
            label={{ value: `FTP ${ftp}W`, position: "right", fill: "#10b981", fontSize: 10 }}
          />
        )}
        <Line
          type="monotone"
          dataKey="watts"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={{ fill: "#3b82f6", r: 3 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

function formatDuration(s: number): string {
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  return `${Math.floor(s / 3600)}h`;
}
