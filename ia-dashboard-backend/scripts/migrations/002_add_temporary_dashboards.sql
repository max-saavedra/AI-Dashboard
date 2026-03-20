-- scripts/migrations/002_add_temporary_dashboards.sql
--
-- Add temporary storage for dashboards created by unauthenticated users.
-- These expire automatically after 24 hours.
-- ------------------------------------------------------------------ --
-- temporary_dashboards: ephemeral storage for anon user sessions
-- ------------------------------------------------------------------ --
CREATE TABLE IF NOT EXISTS temporary_dashboards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL UNIQUE,
    cleaned_data JSONB NOT NULL DEFAULT '{}',
    kpi_data JSONB NOT NULL DEFAULT '{}',
    ai_insights JSONB NOT NULL DEFAULT '{}',
    chart_config JSONB NOT NULL DEFAULT '[]',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT temp_dash_expires_after_created CHECK (expires_at > created_at)
);
-- Indexes for efficiency
CREATE INDEX IF NOT EXISTS idx_temp_dashboards_session_id ON temporary_dashboards(session_id);
CREATE INDEX IF NOT EXISTS idx_temp_dashboards_expires_at ON temporary_dashboards(expires_at);
-- Auto-cleanup: delete expired rows (can also run manually)
CREATE OR REPLACE FUNCTION cleanup_expired_temporary_dashboards() RETURNS void AS $$ BEGIN
DELETE FROM temporary_dashboards
WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;
-- Optionally, schedule cleanup with pg_cron (requires extension):
-- SELECT cron.schedule('cleanup_temp_dashboards', '0 * * * *', 'SELECT cleanup_expired_temporary_dashboards();');