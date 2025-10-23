import { Card, CardContent } from "@/components/ui/card";
import { useListMedia } from "@/hooks/useMedia";
import { File, FileAudio, FileText, Image, Loader2 } from "lucide-react";

const getFileIcon = (fileType: string) => {
  if (fileType.startsWith("image/")) return Image;
  if (fileType.startsWith("audio/")) return FileAudio;
  if (fileType.includes("pdf") || fileType.includes("document"))
    return FileText;
  return File;
};

const getFileTypeColor = (fileType: string) => {
  if (fileType.startsWith("image/")) return "text-blue-500";
  if (fileType.startsWith("audio/")) return "text-purple-500";
  if (fileType.includes("pdf")) return "text-red-500";
  return "text-gray-500";
};

export default function Library() {
  const { data, isLoading } = useListMedia();
  const files = data?.media || [];

  // const formatDate = (dateString: string) => {
  //   return new Date(dateString).toLocaleDateString("en-US", {
  //     year: "numeric",
  //     month: "short",
  //     day: "numeric",
  //   });
  // };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (isLoading) {
    return (
      <div className="container max-w-6xl py-8 px-4">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (files.length === 0) {
    return (
      <div className="container max-w-6xl py-8 px-4">
        <div className="text-center py-16">
          <File className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-xl font-medium mb-2">No files yet</h3>
          <p className="text-muted-foreground">
            Upload your first files to get started
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container max-w-6xl py-8 px-4">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Media Library</h1>
        <p className="text-muted-foreground">
          {files.length} file{files.length !== 1 ? "s" : ""} uploaded
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {files.map((file) => {
          const Icon = getFileIcon(file.file_type);
          const iconColor = getFileTypeColor(file.file_type);

          return (
            <Card key={file.id} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <Icon className={`h-10 w-10 shrink-0 ${iconColor}`} />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate mb-1">
                      {file.file_name}
                    </h3>
                    <p className="text-xs text-muted-foreground mb-2">
                      {formatSize(file.file_size)} •{" "}
                      {/* {formatDate(file.created_at)} */}
                    </p>
                  </div>
                </div>
                {file.storage_url && file.file_type.startsWith("image/") && (
                  <div className="mt-3 rounded-md overflow-hidden bg-muted">
                    <img
                      src={file.storage_url}
                      alt={file.file_name}
                      className="w-full h-40 object-cover"
                      loading="lazy"
                    />
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
