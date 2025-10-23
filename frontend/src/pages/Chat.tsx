import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useMessages, useSendMessage } from "@/hooks/useChat";
import { cn } from "@/lib/utils";
import { useChatStore } from "@/stores/chatStore";
import { Loader2, MessageSquare, Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export default function Chat() {
  const {
    currentConversation,
    messages,
    isStreaming,
    setMessages,
    addMessage,
    updateLastMessage,
    addFunctionCallToLastMessage,
    setStreaming,
  } = useChatStore();

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: messagesData } = useMessages(currentConversation?.id || null);
  const sendMessageMutation = useSendMessage();

  useEffect(() => {
    if (messagesData) {
      setMessages(messagesData || []);
    }
  }, [messagesData, setMessages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || !currentConversation || isStreaming) return;

    const userMessage = {
      id: Date.now(),
      role: "user" as const,
      content: input,
      created_at: new Date().toISOString(),
    };

    addMessage(userMessage);
    const messageContent = input;
    setInput("");
    setStreaming(true);

    const assistantMessage = {
      id: Date.now() + 1,
      role: "assistant" as const,
      content: "",
      created_at: new Date().toISOString(),
    };

    addMessage(assistantMessage);

    let fullContent = "";

    try {
      await sendMessageMutation.mutateAsync({
        conversationId: currentConversation.id,
        message: messageContent,
        onEvent: (event) => {
          switch (event.type) {
            case "text":
              if (event.content) {
                fullContent += event.content;
                updateLastMessage(fullContent);
              }
              break;
            case "function_call":
              if (event.name && event.args) {
                addFunctionCallToLastMessage(event.name, event.args);
              }
              break;
            case "done":
              setStreaming(false);
              break;
            case "error":
              updateLastMessage(
                event.message ||
                  "Sorry, I encountered an error. Please try again.",
              );
              setStreaming(false);
              break;
          }
        },
      });
    } catch (error) {
      console.error(error);
      updateLastMessage("Sorry, I encountered an error. Please try again.");
      setStreaming(false);
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {!currentConversation ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <MessageSquare className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-xl font-medium mb-2">
              Select or create a conversation
            </h3>
            <p className="text-muted-foreground">
              Start chatting with your AI assistant about your media
            </p>
          </div>
        </div>
      ) : (
        <>
          <ScrollArea className="flex-1 p-4">
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex gap-3",
                    message.role === "user" ? "justify-end" : "justify-start",
                  )}
                >
                  <Card
                    className={cn(
                      "p-4 max-w-[80%]",
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-card",
                    )}
                  >
                    <div className="space-y-3">
                      {message.function_calls && message.function_calls.length > 0 && (
                        <div className="space-y-2">
                          {message.function_calls.map((funcCall, idx) => (
                            <div key={idx} className="bg-muted/50 p-3 rounded-lg border">
                              <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground mb-2">
                                <Loader2 className="h-3 w-3 animate-spin" />
                                Function: {funcCall.name}
                              </div>
                              <pre className="text-xs bg-background p-2 rounded overflow-x-auto">
                                {JSON.stringify(funcCall.args, null, 2)}
                              </pre>
                            </div>
                          ))}
                        </div>
                      )}
                      {message.content && (
                        <p className="text-sm whitespace-pre-wrap">
                          {message.content}
                        </p>
                      )}
                    </div>
                    {(message.content || (message.function_calls && message.function_calls.length > 0)) && (
                      <p className="text-xs opacity-70 mt-2">
                        {formatTime(message.created_at)}
                      </p>
                    )}
                  </Card>
                </div>
              ))}
              {isStreaming && (
                <div className="flex gap-3">
                  <Card className="p-4">
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </Card>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          <div className="border-t border-border p-4">
            <div className="max-w-3xl mx-auto flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) =>
                  e.key === "Enter" && !e.shiftKey && sendMessage()
                }
                placeholder="Type your message..."
                disabled={isStreaming}
                className="flex-1"
              />
              <Button
                onClick={sendMessage}
                disabled={isStreaming || !input.trim()}
              >
                {isStreaming ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
