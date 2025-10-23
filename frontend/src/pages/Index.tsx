import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  FolderOpen,
  MessageSquare,
  Sparkles,
  Upload,
} from "lucide-react";
import { Link } from "react-router";

const Index = () => {
  return (
    <div className="min-h-screen bg-background gradient-mesh relative overflow-hidden">
      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-linear-to-br from-primary/10 via-transparent to-accent/10 pointer-events-none" />

      <div className="container mx-auto px-4 py-16 relative z-10">
        <div className="text-center max-w-4xl mx-auto">
          <div className="flex items-center justify-center gap-3 mb-6">
            <Sparkles className="h-16 w-16 text-primary animate-pulse" />
            <h1 className="text-6xl font-bold bg-linear-to-r from-primary via-primary-glow to-accent bg-clip-text text-transparent">
              LifeLens
            </h1>
          </div>

          <p className="text-2xl text-foreground mb-4 font-semibold">
            Your AI-Powered Personal Media Assistant
          </p>

          <p className="text-lg text-muted-foreground mb-12 max-w-2xl mx-auto">
            Upload, analyze, and chat with your media using advanced AI.
            Discover insights from your images, documents, and audio files like
            never before.
          </p>

          <div className="flex gap-4 justify-center mb-16">
            <Button
              asChild
              size="lg"
              className="text-lg px-8 shadow-lg shadow-primary/20"
            >
              <Link to="/signup">
                Get Started
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button
              asChild
              size="lg"
              variant="outline"
              className="text-lg px-8 glass"
            >
              <Link to="/login">Sign In</Link>
            </Button>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mt-16">
            <div className="p-8 rounded-2xl glass hover:glass-strong transition-all duration-300 group hover:scale-105 relative overflow-hidden">
              <div className="absolute inset-0 bg-linear-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <Upload className="h-12 w-12 mb-4 mx-auto text-primary relative z-10" />
              <h3 className="text-xl font-semibold mb-2 relative z-10">
                Upload Anything
              </h3>
              <p className="text-muted-foreground relative z-10">
                Support for images, documents, audio files, and more
              </p>
            </div>

            <div className="p-8 rounded-2xl glass hover:glass-strong transition-all duration-300 group hover:scale-105 relative overflow-hidden">
              <div className="absolute inset-0 bg-linear-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <FolderOpen className="h-12 w-12 mb-4 mx-auto text-primary relative z-10" />
              <h3 className="text-xl font-semibold mb-2 relative z-10">
                Organize Smartly
              </h3>
              <p className="text-muted-foreground relative z-10">
                AI-powered organization and search across all your media
              </p>
            </div>

            <div className="p-8 rounded-2xl glass hover:glass-strong transition-all duration-300 group hover:scale-105 relative overflow-hidden">
              <div className="absolute inset-0 bg-linear-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <MessageSquare className="h-12 w-12 mb-4 mx-auto text-primary relative z-10" />
              <h3 className="text-xl font-semibold mb-2 relative z-10">
                Chat & Discover
              </h3>
              <p className="text-muted-foreground relative z-10">
                Have natural conversations about your media content
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
