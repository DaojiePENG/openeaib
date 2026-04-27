"use client";

import { CheckIcon, CpuIcon, TrashIcon } from "lucide-react";
import { useState } from "react";
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
import { useDeleteBody, useSetCurrentBody } from "@/core/eaib";
import type { BodySummary } from "@/core/eaib";

interface BodyCardProps {
  body: BodySummary;
}

const HARDWARE_TYPE_LABELS: Record<string, string> = {
  humanoid: "Humanoid",
  quadruped: "Quadruped",
  arm: "Arm",
  wheeled: "Wheeled",
  custom: "Custom",
  host: "Host (software)",
};

export function BodyCard({ body }: BodyCardProps) {
  const [confirming, setConfirming] = useState(false);
  const setCurrentMutation = useSetCurrentBody();
  const deleteMutation = useDeleteBody();

  const handleSetCurrent = () => {
    setCurrentMutation.mutate(body.body_id, {
      onSuccess: () => toast.success(`Switched to ${body.display_name}`),
      onError: (e) => toast.error(String(e)),
    });
  };

  const handleDelete = () => {
    if (!confirming) {
      setConfirming(true);
      setTimeout(() => setConfirming(false), 3000);
      return;
    }
    deleteMutation.mutate(body.body_id, {
      onSuccess: () => toast.success(`Removed ${body.display_name}`),
      onError: (e) => toast.error(String(e)),
    });
  };

  return (
    <Card className={body.is_current ? "border-primary" : undefined}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base">{body.display_name}</CardTitle>
          {body.is_current && (
            <Badge variant="default" className="shrink-0 text-xs">
              Active
            </Badge>
          )}
        </div>
        <CardDescription className="font-mono text-xs">
          {body.body_id}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-muted-foreground flex items-center gap-1.5 text-xs">
          <CpuIcon className="size-3" />
          {HARDWARE_TYPE_LABELS[body.hardware_type] ?? body.hardware_type}
          <span className="ml-2">
            {body.sensor_count} sensor{body.sensor_count !== 1 ? "s" : ""}
          </span>
        </div>
        {body.sdk_packages.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {body.sdk_packages.map((pkg) => (
              <Badge key={pkg} variant="secondary" className="text-xs">
                {pkg}
              </Badge>
            ))}
          </div>
        )}
        <div className="flex gap-2 pt-1">
          {!body.is_current && (
            <Button
              size="sm"
              variant="outline"
              className="flex-1"
              onClick={handleSetCurrent}
              disabled={setCurrentMutation.isPending}
            >
              <CheckIcon className="mr-1 size-3" />
              Set Active
            </Button>
          )}
          {body.body_id !== "host" && (
            <Button
              size="sm"
              variant={confirming ? "destructive" : "ghost"}
              onClick={handleDelete}
              disabled={deleteMutation.isPending || body.is_current}
              title={
                body.is_current ? "Cannot remove the active body" : "Remove"
              }
            >
              <TrashIcon className="size-3" />
              {confirming ? "Confirm" : ""}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
