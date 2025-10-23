export interface User {
  id: string;
  email: string;
  name: string;
}

export interface AuthResponse {
  access_token: string;
}

export interface MediaFile {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
}

export interface UploadResponse {
  media: MediaFile &
    {
      task_id: string;
    }[];
}

export interface ListMediaResponse {
  media: MediaFile[];
}

export interface TaskStatus {
  task_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  result?: string;
}

export interface Conversation {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  function_calls?: Array<{
    name: string;
    args: unknown;
  }>;
}
