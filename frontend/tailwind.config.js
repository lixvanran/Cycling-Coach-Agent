/** @type {import('tailwindcss').Config} */
// 浅色毛玻璃风格 — 模仿 Photographer-Copilot / ZhangXuefeng-Agent
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // 浅色背景层
        bg: {
          base: "#f5f7fa",         // 主背景(灰白)
          panel: "#ffffff",        // 卡片
          elevated: "rgba(255,255,255,0.75)", // 毛玻璃悬浮层
          input: "#f1f4f8",
        },
        border: {
          DEFAULT: "rgba(15, 23, 42, 0.08)",
          strong: "rgba(15, 23, 42, 0.14)",
        },
        text: {
          primary: "#1a1f2e",      // 主文字(深)
          secondary: "#4a5364",
          muted: "#86909d",
        },
        // 训练区间色
        zone: {
          z1: "#9aa3b1",   // 灰 — 恢复
          z2: "#3b82f6",   // 蓝 — 耐力
          z3: "#10b981",   // 绿 — 节奏
          z4: "#f59e0b",   // 橙 — 阈值
          z5: "#ef4444",   // 红 — VO2
        },
        accent: {
          primary: "#6366f1",   // 主色 — 紫蓝
          success: "#10b981",
          warning: "#f59e0b",
          danger: "#ef4444",
          cyan: "#06b6d4",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "PingFang SC",
          "Hiragino Sans GB",
          "Microsoft YaHei",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "SF Mono",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
      boxShadow: {
        panel: "0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.04)",
        elevated: "0 4px 16px -2px rgba(15, 23, 42, 0.08), 0 2px 6px -2px rgba(15, 23, 42, 0.04)",
      },
      backdropBlur: {
        glass: "16px",
      },
    },
  },
  plugins: [],
};
