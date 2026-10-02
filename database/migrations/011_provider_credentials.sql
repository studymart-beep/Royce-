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
