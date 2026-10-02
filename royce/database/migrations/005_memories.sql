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
CREATE INDEX IF NOT EXISTS idx_memories_embedding
    ON public.memories
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
