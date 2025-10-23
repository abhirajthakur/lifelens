import { create } from "zustand";

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

export interface Conversation {
  id: string;
  title?: string;
  created_at: string;
  updated_at?: string;
}

interface ChatState {
  currentConversation: Conversation | null;
  messages: Message[];
  isStreaming: boolean;
  setCurrentConversation: (conversation: Conversation | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateLastMessage: (content: string) => void;
  addFunctionCallToLastMessage: (name: string, args: unknown) => void;
  setStreaming: (streaming: boolean) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  currentConversation: null,
  messages: [],
  isStreaming: false,
  setCurrentConversation: (conversation) =>
    set({ currentConversation: conversation, messages: [] }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  updateLastMessage: (content) =>
    set((state) => ({
      messages: state.messages.map((msg, idx) =>
        idx === state.messages.length - 1 ? { ...msg, content } : msg,
      ),
    })),
  addFunctionCallToLastMessage: (name, args) =>
    set((state) => ({
      messages: state.messages.map((msg, idx) =>
        idx === state.messages.length - 1
          ? {
              ...msg,
              function_calls: [...(msg.function_calls || []), { name, args }]
            }
          : msg,
      ),
    })),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
}));
