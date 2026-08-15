// 共享类型(对齐后端 schema)
export interface ActivitySummary {
  id: number;
  start_time: string;
  duration_s: number;
  distance_m: number | null;
  avg_power: number | null;
  normalized_power: number | null;
  tss: number | null;
  avg_hr: number | null;
  avg_cadence: number | null;
  total_elevation_gain: number | null;
  device: string | null;
  source: string;
  has_report: boolean;
}

export interface Sample {
  t_offset: number;
  power: number | null;
  hr: number | null;
  cadence: number | null;
  speed: number | null;
  elevation: number | null;
}

export interface Lap {
  start_offset: number;
  duration_s: number;
  avg_power: number | null;
  avg_hr: number | null;
  avg_cadence: number | null;
  max_power: number | null;
  max_hr: number | null;
  label: string | null;
  trigger: string | null;
}

export interface ActivityMetrics {
  normalized_power: number | null;
  intensity_factor: number | null;
  tss: number | null;
  efficiency_factor: number | null;
  variability_index: number | null;
  power_curve: Record<string, number>;
  hr_zones: Record<string, number>;
  hr_drift: number | null;
  cadence_zones: Record<string, number>;
  ftp_estimated: number | null;
}

export interface ActivityDetail extends ActivitySummary {
  max_power: number | null;
  max_hr: number | null;
  max_speed: number | null;
  calories: number | null;
  metrics: ActivityMetrics | null;
  samples: Sample[];
  laps: Lap[];
  report: string | null;
  report_status: string;
}

export interface Athlete {
  id: number;
  name: string;
  ftp: number | null;
  ftp_estimated: number | null;
  max_hr: number | null;
  lthr: number | null;
  weight_kg: number | null;
  height_cm: number | null;
  total_activities: number;
  weekly_tss: number;
}

export interface DashboardOverview {
  total_activities: number;
  total_distance_km: number;
  total_duration_h: number;
  total_tss: number;
  this_week: {
    activities: number;
    distance_km: number;
    duration_h: number;
    tss: number;
  };
  last_7_days: Array<{
    date: string;
    tss: number;
    distance_km: number;
    duration_h: number;
  }>;
}

export interface MockProfile {
  key: string;
  name: string;
}

export interface DiagnoseInfo {
  ok: boolean;
  version: string;
  m3_mock_mode: boolean;
  m3_model: string;
  python: string;
  system: string;
}
