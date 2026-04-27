"use client";

import { ArchiveIcon, CheckCircleIcon, CircleDotIcon, PencilIcon } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useArchiveSkill } from "@/core/eaib";
import type { RobotSkill } from "@/core/eaib";

const STATUS_META: Record<
  RobotSkill["status"],
  { label: string; icon: React.ReactNode; variant: "default" | "secondary" | "outline" | "destructive" }
> = {
  stable: {
    label: "Stable",
    icon: <CheckCircleIcon className="size-3" />,
    variant: "default",
  },
  tested: {
    label: "Tested",
    icon: <CircleDotIcon className="size-3" />,
    variant: "secondary",
  },
  draft: {
    label: "Draft",
    icon: <PencilIcon className="size-3" />,
    variant: "outline",
  },
  archived: {
    label: "Archived",
    icon: <ArchiveIcon className="size-3" />,
    variant: "destructive",
  },
};

interface SkillCardProps {
  skill: RobotSkill;
}

export function SkillCard({ skill }: SkillCardProps) {
  const archiveMutation = useArchiveSkill();
  const meta = STATUS_META[skill.status];

  const handleArchive = () => {
    archiveMutation.mutate(skill.skill_id, {
      onSuccess: () => toast.success(`Archived: ${skill.name}`),
      onError: (e) => toast.error(String(e)),
    });
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-sm font-medium">{skill.name}</CardTitle>
          <Badge
            variant={meta.variant}
            className="flex shrink-0 items-center gap-1 text-xs"
          >
            {meta.icon}
            {meta.label}
          </Badge>
        </div>
        <CardDescription className="line-clamp-2 text-xs">
          {skill.description}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {skill.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {skill.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
        <div className="text-muted-foreground flex items-center justify-between text-xs">
          <span>
            {skill.usage_count} run{skill.usage_count !== 1 ? "s" : ""} ·{" "}
            {skill.success_count} ok
          </span>
          {skill.status !== "archived" && (
            <Button
              size="sm"
              variant="ghost"
              className="h-6 px-2 text-xs"
              onClick={handleArchive}
              disabled={archiveMutation.isPending}
            >
              <ArchiveIcon className="mr-1 size-3" />
              Archive
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
