import { api } from "@/lib/api";
import type {
  Conversation,
  Message,
} from "@/lib/api-types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export const CHAT_KEYS = {
  all: ["chat"] as const,
  conversations: () => [...CHAT_KEYS.all, "conversations"] as const,
  messages: (conversationId: string) =>
    [...CHAT_KEYS.all, "messages", conversationId] as const,
};

export function useConversations() {
  return useQuery<Conversation[]>({
    queryKey: CHAT_KEYS.conversations(),
    queryFn: () => api.listConversations(),
  });
}

export function useMessages(conversationId: string | null) {
  return useQuery<Message[]>({
    queryKey: CHAT_KEYS.messages(conversationId || ""),
    queryFn: () => api.getMessages(conversationId!),
    enabled: !!conversationId,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation<Conversation, Error>({
    mutationFn: () => api.createConversation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHAT_KEYS.conversations() });
      toast.success("New conversation created");
    },
    onError: (error) => {
      toast.error(error.message || "Failed to create conversation");
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: (conversationId: string) =>
      api.deleteConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHAT_KEYS.conversations() });
      toast.success("Conversation deleted");
    },
    onError: (error) => {
      toast.error(error.message || "Failed to delete conversation");
    },
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation<
    void,
    Error,
    {
      conversationId: string;
      message: string;
      onEvent: (event: {
        type: "function_call" | "text" | "done" | "error";
        name?: string;
        args?: Record<string, unknown>;
        content?: string;
        message_id?: number;
        message?: string;
      }) => void;
    }>({
    mutationFn: ({ conversationId, message, onEvent }) =>
      api.sendMessage(conversationId, message, onEvent),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: CHAT_KEYS.messages(variables.conversationId),
      });
    },
    onError: (error) => {
      toast.error(error.message || "Failed to send message");
    },
  });
}
