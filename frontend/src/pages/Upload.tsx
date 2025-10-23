import { TaskStatusPoller } from "@/components/task-status-poller";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useUploadMedia } from "@/hooks/useMedia";
import { cn } from "@/lib/utils";
import {
  CheckCircle2,
  File,
  Loader2,
  Upload as UploadIcon,
  XCircle,
} from "lucide-react";
import { useRef, useState } from "react";

interface UploadingFile {
  file: File;
  status: "pending" | "uploading" | "processing" | "done" | "failed";
  progress: number;
  taskId?: string;
}

export default function Upload() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadMedia();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      handleFiles(files);
    }
  };

  const handleFiles = async (files: File[]) => {
    const newFiles = files.map((file) => ({
      file,
      status: "pending" as const,
      progress: 0,
    }));

    setUploadingFiles((prev) => [...prev, ...newFiles]);

    newFiles.forEach((_, index) => {
      const interval = setInterval(() => {
        setUploadingFiles((prev) => {
          const updated = [...prev];
          const fileIndex = prev.length - newFiles.length + index;
          if (updated[fileIndex] && updated[fileIndex].progress < 90) {
            updated[fileIndex] = {
              ...updated[fileIndex],
              status: "uploading",
              progress: updated[fileIndex].progress + 10,
            };
          }
          return updated;
        });
      }, 2000);

      setTimeout(() => clearInterval(interval), 2000);
    });

    try {
      const fileList = new DataTransfer();
      files.forEach((file) => fileList.items.add(file));

      const response = await uploadMutation.mutateAsync(fileList.files);

      setUploadingFiles((prev) =>
        prev.map((uf, idx) => {
          if (idx >= prev.length - newFiles.length) {
            const mediaFile =
              response.media[idx - (prev.length - newFiles.length)];

            return {
              ...uf,
              status: "processing",
              progress: 100,
              taskId: mediaFile?.task_id,
            };
          }
          return uf;
        }),
      );
    } catch (error) {
      console.error("Error occured while uploading files:", error);
      setUploadingFiles((prev) =>
        prev.map((uf, idx) =>
          idx >= prev.length - newFiles.length
            ? { ...uf, status: "failed", progress: 100 }
            : uf,
        ),
      );
    }
  };

  const getStatusIcon = (status: UploadingFile["status"]) => {
    switch (status) {
      case "pending":
      case "uploading":
      case "processing":
        return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
      case "done":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-destructive" />;
      default:
        return <File className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-8 pb-6">
        <h1 className="text-3xl font-semibold text-foreground mb-2">
          Upload Media
        </h1>
        <p className="text-muted-foreground">
          Drag and drop files or click to browse
        </p>
      </div>

      {/* Upload Zone */}
      <div className="flex-1 px-8 pb-8">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "h-full border-2 border-dashed rounded-2xl flex flex-col items-center justify-center transition-all cursor-pointer glass",
            isDragging
              ? "border-primary bg-primary/5"
              : "border-border/50 hover:border-primary/50",
          )}
          onClick={() => fileInputRef.current?.click()}
        >
          <UploadIcon className="h-16 w-16 mb-6 text-muted-foreground" />
          <h3 className="text-xl font-medium mb-2 text-foreground">
            Drop files here or click to browse
          </h3>
          <p className="text-sm text-muted-foreground">
            Supports images, audio, PDFs, and documents
          </p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileInput}
            accept="image/*,audio/*,.pdf,.doc,.docx,.txt"
          />
        </div>
      </div>

      {/* Uploading Files List */}
      {uploadingFiles.length > 0 && (
        <div className="px-8 pb-8 space-y-3">
          <h4 className="font-medium text-foreground">Uploading Files</h4>
          {uploadingFiles.map((uf, index) => (
            <Card key={index} className="p-4 glass">
              {uf.taskId && (
                <TaskStatusPoller
                  taskId={uf.taskId}
                  onStatusChange={(status) => {
                    setUploadingFiles((prev) =>
                      prev.map((file, idx) =>
                        idx === index ? { ...file, status } : file,
                      ),
                    );
                  }}
                />
              )}
              <div className="flex items-center gap-3">
                {getStatusIcon(uf.status)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{uf.file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(uf.file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <span className="text-xs text-muted-foreground capitalize">
                  {uf.status}
                </span>
              </div>
              {(uf.status === "uploading" || uf.status === "processing") && (
                <Progress value={uf.progress} className="mt-2" />
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
