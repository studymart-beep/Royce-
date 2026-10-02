-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Profiles (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    display_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, display_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1))
    );
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    model TEXT,
    provider TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON public.conversations(user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('system', 'user', 'assistant', 'tool')),
    content TEXT,
    tool_calls JSONB,
    tool_call_id TEXT,
    provider TEXT,
    model TEXT,
    token_usage JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON public.messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON public.messages(conversation_id, created_at);

CREATE TABLE IF NOT EXISTS public.memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),          -- adjust dimension to chosen embedding model
    memory_type TEXT NOT NULL DEFAULT 'fact'
        CHECK (memory_type IN (
            'preference', 'fact', 'project', 'goal',
            'instruction', 'recurring', 'other'
        )),
    importance REAL NOT NULL DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
    source_message_id UUID REFERENCES public.messages(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    confidence REAL DEFAULT 1.0,
    last_accessed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memories_user_id ON public.memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_type ON public.memories(user_id, memory_type);
-- IVFFlat or HNSW index for similarity search (created after data exists or with lists=100)
-- IVFFlat requires some rows for best results; create with lists=1 for empty DB
DO $$ BEGIN
  CREATE INDEX IF NOT EXISTS idx_memories_embedding
    ON public.memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1);
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'idx_memories_embedding skipped: %', SQLERRM;
END $$;

CREATE TABLE IF NOT EXISTS public.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'todo'
        CHECK (status IN ('todo', 'in_progress', 'done', 'cancelled')),
    due_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON public.tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON public.tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON public.tasks(user_id, due_at);

CREATE TABLE IF NOT EXISTS public.files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    mime_type TEXT,
    size_bytes BIGINT,
    storage_path TEXT NOT NULL,          -- path inside Supabase Storage bucket
    status TEXT NOT NULL DEFAULT 'uploaded'
        CHECK (status IN ('uploaded', 'processing', 'ready', 'failed')),
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_files_user_id ON public.files(user_id);
CREATE INDEX IF NOT EXISTS idx_files_status ON public.files(user_id, status);

-- Document chunks for RAG (kept separate from personal memories)
CREATE TABLE IF NOT EXISTS public.file_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES public.files(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_file_chunks_file_id ON public.file_chunks(file_id);
CREATE INDEX IF NOT EXISTS idx_file_chunks_user_id ON public.file_chunks(user_id);
DO $$ BEGIN
  CREATE INDEX IF NOT EXISTS idx_file_chunks_embedding
    ON public.file_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1);
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'idx_file_chunks_embedding skipped: %', SQLERRM;
END $$;

CREATE TABLE IF NOT EXISTS public.provider_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    request_id TEXT,
    provider TEXT NOT NULL,
    model TEXT,
    success BOOLEAN NOT NULL,
    latency_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    error_code TEXT,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_provider_usage_user_id ON public.provider_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_provider_usage_provider ON public.provider_usage(provider, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_provider_usage_created_at ON public.provider_usage(created_at DESC);

CREATE TABLE IF NOT EXISTS public.settings (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    preferred_provider TEXT,
    preferred_model TEXT,
    theme TEXT DEFAULT 'system',
    memory_enabled BOOLEAN DEFAULT TRUE,
    tools_enabled BOOLEAN DEFAULT TRUE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security on all user-owned tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.file_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.provider_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.settings ENABLE ROW LEVEL SECURITY;

-- Profiles
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Conversations
CREATE POLICY "Users can CRUD own conversations"
    ON public.conversations FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Messages
CREATE POLICY "Users can CRUD own messages"
    ON public.messages FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Memories
CREATE POLICY "Users can CRUD own memories"
    ON public.memories FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Tasks
CREATE POLICY "Users can CRUD own tasks"
    ON public.tasks FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Files
CREATE POLICY "Users can CRUD own files"
    ON public.files FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- File chunks
CREATE POLICY "Users can CRUD own file chunks"
    ON public.file_chunks FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Provider usage (users can read their own; inserts done via service role)
CREATE POLICY "Users can view own usage"
    ON public.provider_usage FOR SELECT
    USING (auth.uid() = user_id);

-- Settings
CREATE POLICY "Users can CRUD own settings"
    ON public.settings FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Per-user encrypted AI provider credentials (dashboard-managed)
CREATE TABLE IF NOT EXISTS public.provider_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,                    -- gemini | groq | cerebras | ...
    encrypted_api_key TEXT NOT NULL,           -- Fernet ciphertext; never plaintext
    key_hint TEXT,                            -- last 4 chars only, for UI display
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 100,    -- lower = higher priority
    preferred_model TEXT,
    metadata JSONB DEFAULT '{}',
    last_tested_at TIMESTAMPTZ,
    last_test_status TEXT,                    -- ok | error | null
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_provider_credentials_user_id
    ON public.provider_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_provider_credentials_enabled
    ON public.provider_credentials(user_id, is_enabled);

ALTER TABLE public.provider_credentials ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can CRUD own provider credentials"
    ON public.provider_credentials FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Semantic match function for memories (user-scoped)
CREATE OR REPLACE FUNCTION public.match_memories(
  query_embedding vector(1536),
  match_user_id uuid,
  match_count int DEFAULT 8,
  match_threshold float DEFAULT 0.25
)
RETURNS TABLE (
  id uuid,
  user_id uuid,
  content text,
  memory_type text,
  importance real,
  source_message_id uuid,
  metadata jsonb,
  confidence real,
  created_at timestamptz,
  updated_at timestamptz,
  similarity float
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    m.id,
    m.user_id,
    m.content,
    m.memory_type,
    m.importance,
    m.source_message_id,
    m.metadata,
    m.confidence,
    m.created_at,
    m.updated_at,
    (1 - (m.embedding <=> query_embedding))::float AS similarity
  FROM public.memories m
  WHERE m.user_id = match_user_id
    AND m.embedding IS NOT NULL
    AND (1 - (m.embedding <=> query_embedding)) >= match_threshold
  ORDER BY m.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Grant execute to authenticated + service
GRANT EXECUTE ON FUNCTION public.match_memories TO authenticated, service_role, anon;
