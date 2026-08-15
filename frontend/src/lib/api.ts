// API 客户端
import type {
  ActivityDetail,
  ActivitySummary,
  Athlete,
  DashboardOverview,
  DiagnoseInfo,
  MockProfile,
} from "./types";

const BASE = "/api"; // 通过 Vite 代理转发到 127.0.0.1:8765

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`HTTP ${r.status}: ${text || r.statusText}`);
  }
  return r.json();
}

export const api = {
  diagnose: () => jsonFetch<DiagnoseInfo>("/diagnose"),

  // 运动员
  getAthlete: () => jsonFetch<Athlete>("/athlete"),
  updateAthlete: (data: Partial<Athlete>) =>
    jsonFetch<Athlete>("/athlete", { method: "PATCH", body: JSON.stringify(data) }),

  // 活动
  listActivities: (limit = 50) =>
    jsonFetch<ActivitySummary[]>(`/activities?limit=${limit}`),
  getActivity: (id: number) => jsonFetch<ActivityDetail>(`/activities/${id}`),
  uploadActivity: async (file: File, onProgress?: (pct: number) => void) => {
    // 用 XHR 拿真实进度
    return new Promise<{ ok: boolean; id: number; metrics: any }>((resolve, reject) => {
      const form = new FormData();
      form.append("file", file);
      const xhr = new XMLHttpRequest();
      xhr.open("POST", BASE + "/activities/upload");
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch (e) {
            reject(new Error("Bad response: " + xhr.responseText));
          }
        } else {
          reject(new Error(`HTTP ${xhr.status}: ${xhr.responseText}`));
        }
      };
      xhr.onerror = () => reject(new Error("Network error"));
      xhr.send(form);
    });
  },
  analyzeActivity: (id: number, focus?: string) =>
    jsonFetch<{ ok: boolean; report: string | null; reason: string | null }>(
      `/activities/${id}/analyze`,
      { method: "POST", body: JSON.stringify({ focus: focus || null }) }
    ),
  deleteActivity: (id: number) =>
    jsonFetch<{ ok: boolean }>(`/activities/${id}`, { method: "DELETE" }),

  // Dashboard
  getOverview: () => jsonFetch<DashboardOverview>("/dashboard/overview"),

  // Dev(mock)
  listMockProfiles: () =>
    jsonFetch<{ profiles: MockProfile[] }>("/dev/mock-profiles"),
  generateMock: (profileKey: string) =>
    jsonFetch<{ ok: boolean; id: number; name: string; metrics: any }>(
      `/dev/generate-mock?profile_key=${encodeURIComponent(profileKey)}`,
      { method: "POST" }
    ),

  // AI 教练对话 — SSE 流式
  chatStream: async function* (
    messages: { role: string; content: string }[],
    message: string,
    signal?: AbortSignal
  ): AsyncGenerator<{ type: "text" | "think" | "done" | "error"; data: string }> {
    const r = await fetch(BASE + "/coach/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages, message }),
      signal,
    });
    if (!r.ok || !r.body) {
      throw new Error(`HTTP ${r.status}: ${await r.text().catch(() => r.statusText)}`);
    }
    const reader = r.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      // SSE 帧以 \n\n 分隔
      let idx;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        const line = frame.replace(/^data: /, "").trim();
        if (!line) continue;
        if (line === "[DONE]") {
          yield { type: "done", data: "" };
          return;
        }
        if (line.startsWith("[ERROR]")) {
          yield { type: "error", data: line.slice(7).trim() };
          return;
        }
        // unescape \n
        yield { type: "text", data: line.replace(/\\n/g, "\n") };
      }
    }
  },
};
