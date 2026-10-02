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

GRANT EXECUTE ON FUNCTION public.match_memories TO authenticated, service_role, anon;
