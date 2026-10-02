CREATE OR REPLACE FUNCTION public.match_file_chunks(
  query_embedding vector(1536),
  match_user_id uuid,
  match_count int DEFAULT 6,
  match_threshold float DEFAULT 0.2
)
RETURNS TABLE (
  id uuid,
  file_id uuid,
  user_id uuid,
  chunk_index int,
  content text,
  similarity float
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    c.id,
    c.file_id,
    c.user_id,
    c.chunk_index,
    c.content,
    (1 - (c.embedding <=> query_embedding))::float AS similarity
  FROM public.file_chunks c
  WHERE c.user_id = match_user_id
    AND c.embedding IS NOT NULL
    AND (1 - (c.embedding <=> query_embedding)) >= match_threshold
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
$$;

GRANT EXECUTE ON FUNCTION public.match_file_chunks TO authenticated, service_role, anon;
