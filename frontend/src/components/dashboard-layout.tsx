import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  useConversations,
  useCreateConversation,
  useDeleteConversation,
} from "@/hooks/useChat";
import type { Conversation } from "@/lib/api-types";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/authStore";
import { useChatStore } from "@/stores/chatStore";
import {
  FolderOpen,
  Loader2,
  LogOut,
  MessageSquare,
  Plus,
  Trash2,
  Upload,
} from "lucide-react";
import { useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router";

const navigation = [
  { name: "Upload Media", href: "/dashboard/upload", icon: Upload },
  { name: "My Library", href: "/dashboard/library", icon: FolderOpen },
  { name: "Chat", href: "/dashboard/chat", icon: MessageSquare },
];

export default function DashboardLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuthStore();
  const { currentConversation, setCurrentConversation } = useChatStore();
  const { data: conversationsData, isLoading: isLoadingConversations } =
    useConversations();
  const createConversationMutation = useCreateConversation();
  const deleteConversationMutation = useDeleteConversation();

  const conversations = conversationsData || [];

  // State for delete confirmation dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState<Conversation | null>(null);

  const handleLogout = () => {
    logout();
    window.location.href = "/login";
  };

  const handleCreateConversation = async () => {
    const newConv = await createConversationMutation.mutateAsync();
    setCurrentConversation(newConv);
    navigate("/dashboard/chat");
  };

  const handleSelectConversation = (conv: Conversation) => {
    setCurrentConversation(conv);
    navigate("/dashboard/chat");
  };

  const handleDeleteConversation = (conversation: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setConversationToDelete(conversation);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteConversation = async () => {
    if (!conversationToDelete) return;

    try {
      await deleteConversationMutation.mutateAsync(conversationToDelete.id);
      if (currentConversation?.id === conversationToDelete.id) {
        setCurrentConversation(null);
      }
    } finally {
      setDeleteDialogOpen(false);
      setConversationToDelete(null);
    }
  };

  const cancelDeleteConversation = () => {
    setDeleteDialogOpen(false);
    setConversationToDelete(null);
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  };

  return (
    <div className="min-h-screen flex bg-background">
      {/* Sidebar */}
      <aside className="w-80 bg-card border-r border-border flex flex-col">
        {/* Logo */}
        <div className="p-6">
          <Link to="/dashboard" className="font-bold text-2xl text-foreground">
            LifeLens
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 space-y-2">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent",
                )}
              >
                {isActive && <Plus className="h-4 w-4" />}
                {!isActive && <item.icon className="h-4 w-4" />}
                {item.name}
              </Link>
            );
          })}

          {/* Conversations Section */}
          <div className="pt-8 flex-1 flex flex-col min-h-0">
            <div className="flex items-center justify-between px-4 mb-3">
              <h3 className="text-sm font-medium text-foreground">
                Conversations
              </h3>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={handleCreateConversation}
                disabled={createConversationMutation.isPending}
              >
                {createConversationMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="h-4 w-4" />
                )}
              </Button>
            </div>

            <ScrollArea className="flex-1">
              {isLoadingConversations ? (
                <div className="flex items-center justify-center p-4">
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                </div>
              ) : conversations.length === 0 ? (
                <p className="px-4 text-sm text-muted-foreground">
                  No conversations yet
                </p>
              ) : (
                <div className="space-y-1">
                  {conversations.map((conv) => (
                    <div
                      key={conv.id}
                      className={cn(
                        "group flex items-center gap-2 px-3 py-2 mx-2 rounded-lg cursor-pointer hover:bg-accent transition-colors",
                        {
                          "bg-accent": currentConversation?.id === conv.id,
                        },
                      )}
                      onClick={() => handleSelectConversation(conv)}
                    >
                      <MessageSquare className="h-3 w-3 text-muted-foreground shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs truncate">
                          {/*  TODO: Update title of the conversation */}
                          {`Chat ${conv.id.slice(0, 6)}`}
                        </p>
                        <p className="text-[10px] text-muted-foreground">
                          {formatTime(conv.created_at)}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => handleDeleteConversation(conv, e)}
                        disabled={deleteConversationMutation.isPending}
                      >
                        {deleteConversationMutation.isPending ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <Trash2 className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>
        </nav>

        {/* Logout Button */}
        <div className="p-4 border-t border-border">
          <Button
            variant="ghost"
            className="w-full justify-start text-muted-foreground hover:text-foreground"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4 mr-3" />
            Logout
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Conversation</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this conversation? This action cannot be undone.
              {conversationToDelete && (
                <span className="block mt-2 font-medium">
                  Chat {conversationToDelete.id.slice(0, 6)}
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={cancelDeleteConversation}
              disabled={deleteConversationMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDeleteConversation}
              disabled={deleteConversationMutation.isPending}
            >
              {deleteConversationMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
