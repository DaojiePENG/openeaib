import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  archiveSkill,
  createSkill,
  deleteBody,
  listBodies,
  listSkills,
  scanHardware,
  searchSkills,
  setCurrentBody,
} from "./api";
import type { CreateSkillRequest } from "./types";

// ── Body hooks ────────────────────────────────────────────────────────────────

export function useBodies() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["eaib", "bodies"],
    queryFn: listBodies,
  });
  return { bodies: data ?? [], isLoading, error };
}

export function useSetCurrentBody() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body_id: string) => setCurrentBody(body_id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["eaib", "bodies"] });
    },
  });
}

export function useDeleteBody() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body_id: string) => deleteBody(body_id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["eaib", "bodies"] });
    },
  });
}

export function useHardwareScan() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["eaib", "hardware-scan"],
    queryFn: scanHardware,
    enabled: false, // only run on demand
  });
  return { scanResult: data ?? null, isScanning: isLoading, refetch };
}

// ── Skill hooks ───────────────────────────────────────────────────────────────

export function useSkills(body_id?: string, status?: string) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["eaib", "skills", body_id, status],
    queryFn: () => listSkills(body_id, status),
  });
  return { skills: data ?? [], isLoading, error };
}

export function useSkillSearch(query: string, body_id?: string) {
  const { data, isLoading } = useQuery({
    queryKey: ["eaib", "skills", "search", query, body_id],
    queryFn: () => searchSkills(query, body_id),
    enabled: query.trim().length > 1,
  });
  return { results: data ?? [], isLoading };
}

export function useCreateSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (req: CreateSkillRequest) => createSkill(req),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["eaib", "skills"] });
    },
  });
}

export function useArchiveSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (skill_id: string) => archiveSkill(skill_id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["eaib", "skills"] });
    },
  });
}
