import { useTaskStatus } from "@/hooks/useMedia";
import { useCallback, useEffect } from "react";

interface TaskStatusPollerProps {
  taskId: string | undefined;
  onStatusChange: (
    status: "pending" | "processing" | "done" | "failed",
  ) => void;
}

export function TaskStatusPoller({
  taskId,
  onStatusChange,
}: TaskStatusPollerProps) {
  const { data: taskStatus } = useTaskStatus(taskId, !!taskId);

  const checkTaskStatus = useCallback(() => {
    if (taskStatus) {
      let status: "pending" | "processing" | "done" | "failed";

      switch (taskStatus.status) {
        case "completed":
          status = "done";
          break;
        case "failed":
          status = "failed";
          break;
        case "pending":
          status = "pending";
          break;
        case "processing":
        default:
          status = "processing";
          break;
      }

      onStatusChange(status);
    }
  }, [taskStatus, onStatusChange]);

  useEffect(() => {
    checkTaskStatus();
  }, [checkTaskStatus]);

  return null;
}
