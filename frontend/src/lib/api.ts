import { useAuthStore } from "@/stores/authStore";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  public status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export const api = {
  async request(endpoint: string, options: RequestInit = {}) {
    const token = useAuthStore.getState().token;

    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = "/login";
      throw new ApiError(401, "Unauthorized");
    }

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "An error occurred" }));
      throw new ApiError(response.status, error.detail || "An error occurred");
    }

    return response;
  },

  async get(endpoint: string) {
    const response = await this.request(endpoint);
    return response.json();
  },

  async post(endpoint: string, data?: unknown) {
    const response = await this.request(endpoint, {
      method: "POST",
      body: data instanceof FormData ? data : JSON.stringify(data),
    });
    return response.json();
  },

  async delete(endpoint: string) {
    await this.request(endpoint, { method: "DELETE" });
  },

  // Auth endpoints
  async signup(email: string, password: string, name: string) {
    return this.post("/auth/signup", { email, password, name });
  },

  async login(email: string, password: string) {
    return this.post("/auth/login", { email, password });
  },

  // Media endpoints
  async uploadMedia(files: FileList) {
    const formData = new FormData();
    Array.from(files).forEach((file) => {
      formData.append("files", file);
    });
    return this.post("/api/media/upload", formData);
  },

  async listMedia() {
    return this.get("/api/media/list");
  },

  async getTaskStatus(taskId: string) {
    return this.get(`/api/media/status/${taskId}`);
  },

  // Chat endpoints
  async createConversation() {
    return this.post("/api/chat/conversations");
  },

  async listConversations() {
    return this.get("/api/chat/conversations");
  },

  async getMessages(conversationId: string) {
    return this.get(`/api/chat/conversations/${conversationId}/messages`);
  },

  async deleteConversation(conversationId: string) {
    return this.delete(`/api/chat/conversations/${conversationId}`);
  },

  // SSE for chat streaming
  async sendMessage(
    conversationId: string,
    message: string,
    onEvent: (event: {
      type: "function_call" | "text" | "done" | "error";
      name?: string;
      args?: Record<string, unknown>;
      content?: string;
      message_id?: number;
      message?: string;
    }) => void,
  ) {
    const token = useAuthStore.getState().token;

    const response = await fetch(
      `${API_BASE_URL}/api/chat/conversations/${conversationId}/messages`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      },
    );

    if (!response.ok) {
      throw new ApiError(response.status, "Failed to send message");
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error("No response body");
    }

    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");

      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith("data: ")) {
          const data = trimmedLine.slice(6).trim();
          if (data === "[DONE]") continue;

          try {
            const parsed = JSON.parse(data);
            onEvent(parsed);
          } catch (e) {
            console.error("Failed to parse SSE data:", data, e);
          }
        }
      }
    }
  },
};
