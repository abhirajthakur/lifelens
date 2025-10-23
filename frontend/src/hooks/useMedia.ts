import { api } from "@/lib/api";
import type {
  ListMediaResponse,
  TaskStatus,
  UploadResponse,
} from "@/lib/api-types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export const MEDIA_KEYS = {
  all: ["media"] as const,
  list: () => [...MEDIA_KEYS.all, "list"] as const,
  task: (taskId: string) => [...MEDIA_KEYS.all, "task", taskId] as const,
};

export function useListMedia() {
  return useQuery<ListMediaResponse>({
    queryKey: MEDIA_KEYS.list(),
    queryFn: () => api.listMedia(),
  });
}

export function useUploadMedia() {
  const queryClient = useQueryClient();

  return useMutation<UploadResponse, Error, FileList>({
    mutationFn: (files: FileList) => api.uploadMedia(files),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: MEDIA_KEYS.list() });
      toast.success(`Successfully uploaded ${data.media.length} file(s)`);
    },
    onError: (error) => {
      toast.error(error.message || "Upload failed");
    },
  });
}

export function useTaskStatus(
  taskId: string | undefined,
  enabled: boolean = true,
) {
  return useQuery<TaskStatus>({
    queryKey: MEDIA_KEYS.task(taskId || ""),
    queryFn: () => api.getTaskStatus(taskId!),
    enabled: enabled && !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;

      // Stop polling if completed or failed
      if (data.status === "completed" || data.status === "failed") {
        return false;
      }

      // Continue polling for pending and processing states
      if (data.status === "pending" || data.status === "processing") {
        return 2000;
      }

      // Default: stop polling for unknown states
      return false;
    },
  });
}
