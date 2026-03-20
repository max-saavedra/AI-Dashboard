-- scripts/migrations/001_initial_schema.sql
--
-- Initial schema for the IA Dashboard backend.
-- Run once against your Supabase project (SQL Editor) or via psql.
-- The 'users' table is managed by Supabase Auth; we only create the
-- application tables here.

-- ------------------------------------------------------------------ --
-- Enable UUID extension
-- ------------------------------------------------------------------ --
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ------------------------------------------------------------------ --
-- chats: analysis session threads (RF-04)
-- ------------------------------------------------------------------ --
CREATE TABLE IF NOT EXISTS chats (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name        VARCHAR(120) NOT NULL DEFAULT 'New Analysis',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast user-session queries
CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id);

-- Automatically update updated_at on row changes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS chats_updated_at ON chats;
CREATE TRIGGER chats_updated_at
    BEFORE UPDATE ON chats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ------------------------------------------------------------------ --
-- dashboards: core analytical entity (DA section 3)
-- ------------------------------------------------------------------ --
CREATE TABLE IF NOT EXISTS dashboards (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id      UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    cleaned_data JSONB NOT NULL DEFAULT '{}',
    kpi_data     JSONB NOT NULL DEFAULT '{}',
    ai_insights  JSONB NOT NULL DEFAULT '{}',
    chart_config JSONB NOT NULL DEFAULT '[]',
    metadata     JSONB NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dashboards_chat_id ON dashboards(chat_id);


-- ------------------------------------------------------------------ --
-- Row Level Security (DA section 4.2)
-- ------------------------------------------------------------------ --
ALTER TABLE chats      ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboards ENABLE ROW LEVEL SECURITY;

-- Users can only SELECT / INSERT / UPDATE / DELETE their own chats
CREATE POLICY chats_owner_policy ON chats
    USING (user_id = auth.uid() OR user_id IS NULL);

CREATE POLICY chats_insert_policy ON chats
    FOR INSERT WITH CHECK (user_id = auth.uid() OR user_id IS NULL);

-- Dashboard access is mediated through the chat relationship
CREATE POLICY dashboards_owner_policy ON dashboards
    USING (
        chat_id IN (
            SELECT id FROM chats
            WHERE user_id = auth.uid() OR user_id IS NULL
        )
    );


-- ------------------------------------------------------------------ --
-- Scheduled cleanup of anonymous data (DA section 4.1)
-- ------------------------------------------------------------------ --
-- Run this as a pg_cron job or Supabase Edge Function cron:
--
--   DELETE FROM dashboards
--   WHERE chat_id IN (
--       SELECT id FROM chats
--       WHERE user_id IS NULL
--       AND created_at < NOW() - INTERVAL '24 hours'
--   );
--
--   DELETE FROM chats
--   WHERE user_id IS NULL
--   AND created_at < NOW() - INTERVAL '24 hours';
