-- Royce user files storage bucket + policies
-- Run after core tables exist.

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'royce-files',
  'royce-files',
  false,
  20971520,
  ARRAY[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/csv',
    'image/png',
    'image/jpeg',
    'image/webp',
    'image/gif'
  ]
)
ON CONFLICT (id) DO UPDATE SET
  file_size_limit = EXCLUDED.file_size_limit,
  allowed_mime_types = EXCLUDED.allowed_mime_types;

-- Users can upload only into their own folder: {user_id}/...
CREATE POLICY "Users upload own files"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (
  bucket_id = 'royce-files'
  AND (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users read own files"
ON storage.objects FOR SELECT TO authenticated
USING (
  bucket_id = 'royce-files'
  AND (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users update own files"
ON storage.objects FOR UPDATE TO authenticated
USING (
  bucket_id = 'royce-files'
  AND (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users delete own files"
ON storage.objects FOR DELETE TO authenticated
USING (
  bucket_id = 'royce-files'
  AND (storage.foldername(name))[1] = auth.uid()::text
);
