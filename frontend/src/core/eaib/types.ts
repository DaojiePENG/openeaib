export interface BodySummary {
  body_id: string;
  display_name: string;
  hardware_type: string;
  is_current: boolean;
  sensor_count: number;
  sdk_packages: string[];
}

export interface HardwareScanResult {
  os: string;
  cameras: unknown[];
  serial_ports: unknown[];
  [key: string]: unknown;
}

export interface RobotSkill {
  skill_id: string;
  name: string;
  description: string;
  body_id: string;
  status: "draft" | "tested" | "stable" | "archived";
  tags: string[];
  usage_count: number;
  success_count: number;
  created_at: string;
}

export interface CreateSkillRequest {
  name: string;
  description: string;
  body_id: string;
  code_path?: string;
  tags?: string[];
}
