import { getBackendBaseURL } from "@/core/config";

import type {
  BodySummary,
  CreateSkillRequest,
  HardwareScanResult,
  RobotSkill,
} from "./types";

// ── Body API ──────────────────────────────────────────────────────────────────

export async function listBodies(): Promise<BodySummary[]> {
  const res = await fetch(`${getBackendBaseURL()}/api/eaib/body/`);
  if (!res.ok) throw new Error(`Failed to list bodies: ${res.statusText}`);
  return res.json() as Promise<BodySummary[]>;
}

export async function getCurrentBody(): Promise<BodySummary> {
  const res = await fetch(`${getBackendBaseURL()}/api/eaib/body/current`);
  if (!res.ok) throw new Error(`Failed to get current body: ${res.statusText}`);
  return res.json() as Promise<BodySummary>;
}

export async function setCurrentBody(body_id: string): Promise<void> {
  const res = await fetch(`${getBackendBaseURL()}/api/eaib/body/current`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ body_id }),
  });
  if (!res.ok)
    throw new Error(`Failed to set current body: ${res.statusText}`);
}

export async function scanHardware(): Promise<HardwareScanResult> {
  const res = await fetch(`${getBackendBaseURL()}/api/eaib/body/scan`);
  if (!res.ok) throw new Error(`Failed to scan hardware: ${res.statusText}`);
  return res.json() as Promise<HardwareScanResult>;
}

export async function deleteBody(body_id: string): Promise<void> {
  const res = await fetch(
    `${getBackendBaseURL()}/api/eaib/body/${encodeURIComponent(body_id)}`,
    { method: "DELETE" },
  );
  if (!res.ok) throw new Error(`Failed to delete body: ${res.statusText}`);
}

// ── Skills API ────────────────────────────────────────────────────────────────

export async function listSkills(
  body_id?: string,
  status?: string,
): Promise<RobotSkill[]> {
  const params = new URLSearchParams();
  if (body_id) params.set("body_id", body_id);
  if (status) params.set("status", status);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`${getBackendBaseURL()}/api/eaib/skills/${qs}`);
  if (!res.ok) throw new Error(`Failed to list skills: ${res.statusText}`);
  return res.json() as Promise<RobotSkill[]>;
}

export async function searchSkills(
  q: string,
  body_id?: string,
): Promise<RobotSkill[]> {
  const params = new URLSearchParams({ q });
  if (body_id) params.set("body_id", body_id);
  const res = await fetch(
    `${getBackendBaseURL()}/api/eaib/skills/search?${params.toString()}`,
  );
  if (!res.ok) throw new Error(`Failed to search skills: ${res.statusText}`);
  const data = (await res.json()) as { results: RobotSkill[] };
  return data.results;
}

export async function createSkill(req: CreateSkillRequest): Promise<RobotSkill> {
  const res = await fetch(`${getBackendBaseURL()}/api/eaib/skills/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Failed to create skill: ${res.statusText}`);
  return res.json() as Promise<RobotSkill>;
}

export async function archiveSkill(skill_id: string): Promise<void> {
  const res = await fetch(
    `${getBackendBaseURL()}/api/eaib/skills/${encodeURIComponent(skill_id)}`,
    { method: "DELETE" },
  );
  if (!res.ok) throw new Error(`Failed to archive skill: ${res.statusText}`);
}
