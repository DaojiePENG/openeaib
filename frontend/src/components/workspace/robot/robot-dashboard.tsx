"use client";

import { CpuIcon, ScanSearchIcon } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useBodies, useHardwareScan, useSkills } from "@/core/eaib";

import { BodyCard } from "./body-card";
import { SkillCard } from "./skill-card";

export function RobotDashboard() {
  const { bodies, isLoading: bodiesLoading } = useBodies();
  const { scanResult, isScanning, refetch: runScan } = useHardwareScan();

  const currentBody = bodies.find((b) => b.is_current);

  const [selectedBodyId, setSelectedBodyId] = useState<string>("");
  const [skillFilter, setSkillFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  const effectiveBodyId = selectedBodyId || currentBody?.body_id;
  const { skills, isLoading: skillsLoading } = useSkills(
    effectiveBodyId,
    statusFilter || undefined,
  );

  const filtered = skillFilter
    ? skills.filter(
        (s) =>
          s.name.toLowerCase().includes(skillFilter.toLowerCase()) ||
          s.description.toLowerCase().includes(skillFilter.toLowerCase()) ||
          s.tags.some((t) => t.toLowerCase().includes(skillFilter.toLowerCase())),
      )
    : skills;

  return (
    <div className="flex size-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-6 py-4">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-semibold">
            <CpuIcon className="size-5" />
            Robot Dashboard
          </h1>
          <p className="text-muted-foreground mt-0.5 text-sm">
            Manage robot bodies, hardware, and learned skills
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void runScan()}
          disabled={isScanning}
        >
          <ScanSearchIcon className="mr-1.5 size-4" />
          Scan Hardware
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-8 p-6">
        {/* Hardware scan result */}
        {scanResult && (
          <div className="bg-muted rounded-lg p-4 text-xs">
            <p className="font-medium mb-1">Hardware Scan</p>
            <pre className="overflow-auto whitespace-pre-wrap">
              {JSON.stringify(scanResult, null, 2)}
            </pre>
          </div>
        )}

        {/* Bodies section */}
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Robot Bodies
          </h2>
          {bodiesLoading ? (
            <p className="text-muted-foreground text-sm">Loading…</p>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {bodies.map((body) => (
                <BodyCard key={body.body_id} body={body} />
              ))}
            </div>
          )}
        </section>

        <Separator />

        {/* Skills section */}
        <section>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Robot Skills
            </h2>
            <div className="flex gap-2">
              <Select
                value={selectedBodyId}
                onValueChange={setSelectedBodyId}
              >
                <SelectTrigger className="h-8 w-40 text-xs">
                  <SelectValue placeholder="All bodies" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All bodies</SelectItem>
                  {bodies.map((b) => (
                    <SelectItem key={b.body_id} value={b.body_id}>
                      {b.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="h-8 w-32 text-xs">
                  <SelectValue placeholder="Any status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Any status</SelectItem>
                  <SelectItem value="stable">Stable</SelectItem>
                  <SelectItem value="tested">Tested</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                </SelectContent>
              </Select>

              <div className="relative">
                <Input
                  className="h-8 w-48 text-xs"
                  placeholder="Filter skills…"
                  value={skillFilter}
                  onChange={(e) => setSkillFilter(e.target.value)}
                />
              </div>
            </div>
          </div>

          {skillsLoading ? (
            <p className="text-muted-foreground text-sm">Loading…</p>
          ) : filtered.length === 0 ? (
            <div className="flex h-32 flex-col items-center justify-center gap-2 text-center">
              <p className="text-muted-foreground text-sm">
                No skills found. Start a chat to teach the robot new skills.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {filtered.map((skill) => (
                <SkillCard key={skill.skill_id} skill={skill} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
