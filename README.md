# 🔍 LifeLens

**Your AI-Powered Personal Media Assistant**

LifeLens is an intelligent media management platform that uses advanced AI to help you upload, analyze, and interact with your personal media collection. Upload images, documents, and audio files, then chat with an AI assistant to discover insights, extract information, and explore your content like never before.

![LifeLens Banner](https://img.shields.io/badge/LifeLens-AI%20Media%20Assistant-blue?style=for-the-badge)

## ✨ Features

### 🤖 **AI-Powered Analysis**

- **Image Processing**: Automatic caption generation and OCR text extraction
- **Document Analysis**: Text extraction from PDFs, Word documents, and more
- **Audio Transcription**: Speech-to-text conversion with speaker identification
- **Smart Summarization**: AI-generated summaries and topic extraction
- **Vector Search**: Semantic search across all your media using embeddings

### 💬 **Intelligent Chat Interface**

- **Natural Language Queries**: Ask questions about your media in plain English
- **Streaming Responses**: Real-time AI responses with function call visibility
- **Conversation Management**: Persistent chat history with easy conversation switching
- **Multi-Step Reasoning**: AI can chain multiple operations to answer complex queries

### 📁 **Media Management**

- **Multi-Format Support**: Images (JPEG, PNG), Documents (PDF, DOCX), Audio files
- **Drag & Drop Upload**: Easy file uploading with progress tracking
- **Media Library**: Visual grid view of all uploaded files
- **File Organization**: Automatic categorization and metadata extraction

### 🔍 **Advanced Search & Filtering**

- **Semantic Search**: Find content by meaning, not just keywords
- **Date Filtering**: Search by upload date or time periods
- **Content Analysis**: Extract names, dates, addresses, and other structured data
- **File Type Filtering**: Filter by images, PDFs, documents, or audio files

## 🏗️ Architecture

### **Frontend** (React + TypeScript)

- **Framework**: React 19 with TypeScript
- **State Management**: Zustand for global state, TanStack Query for server state
- **Styling**: Tailwind CSS
- **Production Serving**: nginx with optimized static file serving and SPA routing

### **Backend** (FastAPI + Python)

- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with pgvector extension for vector storage
- **AI Integration**: Google Gemini 2.5 Flash for text/image/audio processing
- **Authentication**: JWT-based auth with bcrypt password hashing
- **Background Tasks**: Celery with Redis for async media processing
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **Configuration**: Environment-based database URL and settings

### **Containerization** (Docker + Docker Compose)

- **Multi-service orchestration**: PostgreSQL, Redis, Backend API, Celery Worker, Frontend
- **Production-ready**: nginx for frontend, health checks, persistent volumes
- **Environment-driven**: Database connections and API keys via environment variables

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

#### Prerequisites

- **Docker** and **Docker Compose**
- **Google Gemini API Key**

#### Setup

```bash
# 1. Clone the repository
git clone https://github.com/abhirajthakur/lifelens.git
cd lifelens

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your configuration:
# - GEMINI_API_KEY=your_gemini_api_key
# - JWT_SECRET_KEY=your_jwt_secret_key

# 3. Start all services
docker-compose up -d

# 4. Run database migrations
docker-compose exec backend uv run alembic upgrade head

# 5. Access the application
- Frontend: http://localhost:5173 (served by nginx)
```

#### What's Included

- **PostgreSQL** with pgvector extension for vector storage
- **Redis** for background task processing
- **Backend API** (FastAPI) with automatic database migrations
- **Celery Worker** for async media processing
- **Frontend** (React) served by nginx for production-ready performance
- **Environment-based configuration** for easy deployment

### Option 2: Manual Setup

#### Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **PostgreSQL 17** (with pgvector extension)
- **Redis** (for Celery background tasks)
- **Google Gemini API Key**

#### 1. Clone the Repository

```bash
git clone https://github.com/abhirajthakur/lifelens.git
cd lifelens
```

#### 2. Backend Setup

```bash
cd backend

# Install dependencies with uv (recommended) or pip
uv sync
# OR
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration:
# - GEMINI_API_KEY=your_gemini_api_key
# - DATABASE_URL=postgresql://postgres:password@localhost:5432/lifelens_db
# - JWT_SECRET_KEY=your_secret_key
# - FRONTEND_URL=http://localhost:5173

# Start PostgreSQL with pgvector and Redis
docker run -d --name postgres-pgvector -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=lifelens_db \
  pgvector/pgvector:pg17

docker run -d --name redis -p 6379:6379 redis:7-alpine

# Run database migrations (Alembic automatically uses DATABASE_URL from environment)
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A app.tasks worker --loglevel=info
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install
# OR
npm install

# Start the development server
pnpm dev
# OR
npm run dev
```

#### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 Usage Guide

### Getting Started

1. **Sign Up**: Create an account at http://localhost:5173/signup
2. **Upload Media**: Go to "Upload Media" and drag & drop your files
3. **Wait for Processing**: Files are processed in the background (check progress)
4. **Start Chatting**: Go to "Chat" and ask questions about your media

### Example Queries

```
"What kind of files do I have?"
"Show me all my screenshots"
"Find documents about machine learning"
"What was written in the PDF I uploaded yesterday?"
"Summarize the content of my Word documents"
"Extract all phone numbers from my images"
"Show me photos with text in them"
```

### Supported File Types

- **Images**: JPEG, PNG (with OCR and caption generation)
- **Documents**: PDF, DOCX (with text extraction and summarization)
- **Audio**: MP3, WAV, M4A (with transcription)
- **Text**: TXT, MD (with content analysis)

### Key Technologies

- **AI/ML**: Google Gemini 2.5 Flash, pgvector, embeddings
- **Backend**: FastAPI, SQLAlchemy, Celery, Redis, PostgreSQL
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Radix UI, nginx
- **Authentication**: JWT tokens with bcrypt hashing
- **File Processing**: PIL (images), PyPDF2 (PDFs), python-docx (Word)
- **Containerization**: Docker, Docker Compose with multi-service orchestration

## 🐳 Docker Configuration

### Container Architecture

The Docker setup includes the following services:

- **PostgreSQL** (`pgvector/pgvector:pg17`) - Database with vector extension on port 5432
- **Redis** (`redis:7-alpine`) - Task queue backend on port 6379
- **Backend** (FastAPI) - API server on port 8000 (mapped from container port 80)
- **Celery Worker** - Background task processor for media analysis
- **Frontend** (nginx) - React app served by nginx on port 5173 (mapped from container port 80)

### Environment Variables

```bash
# Backend (.env) - Required for Docker Compose
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET_KEY=your_jwt_secret_key

# The following are automatically configured in Docker Compose:
# DATABASE_URL=postgresql://postgres:mysecretpassword@db:5432/lifelens_db
# REDIS_URL=redis://redis:6379
# FRONTEND_URL=http://localhost:5173

# Frontend build-time variable (configured in docker-compose.yml)
# VITE_API_BASE_URL=http://localhost:8000
```

### Database Configuration

The application uses PostgreSQL with the pgvector extension for vector similarity search. Database configuration is environment-driven:

- **Docker**: Automatically configured via `DATABASE_URL` environment variable
- **Alembic**: Reads `DATABASE_URL` from environment, falls back to default connection string
- **Schema**: Includes Users, Media, MediaMetadata, and Conversations tables
- **Migrations**: Run automatically with `docker-compose exec backend uv run alembic upgrade head`

## 🌐 API Reference

### Authentication Endpoints

```
POST /api/auth/signup          # Create new user account
POST /api/auth/login           # User login
```

### Media Management

```
GET  /api/media               # List user's media files
POST /api/media/upload        # Upload new media file
GET  /api/media/{id}          # Get specific media details
DELETE /api/media/{id}        # Delete media file
```

### Chat & AI

```
GET  /api/chat/conversations  # List user's conversations
POST /api/chat/conversations  # Create new conversation
DELETE /api/chat/conversations/{id}  # Delete conversation
GET  /api/chat/conversations/{id}/messages  # Get conversation messages
POST /api/chat/conversations/{id}/chat  # Send message (streaming)
```

### AI Functions (Available in Chat)

- `semantic_search(query)` - Find relevant media using vector search
- `get_media_details(media_ids)` - Get full details of specific files
- `count_media(media_type)` - Count files by type
- `filter_media_by_date(date_filter)` - Filter files by date range
