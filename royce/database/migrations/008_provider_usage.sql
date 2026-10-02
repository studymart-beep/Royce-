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
