-- Pestino (پستینو) - AI administration
-- Admin-managed Gemini configuration, per-feature AI controls, usage metering and admin audit trail.
-- The Gemini API key is stored only encrypted (AES-256-GCM, see src/lib/secretbox.ts) and is never returned by the API.

-- ---------------------------------------------------------------------------
-- Singleton AI runtime settings (exactly one row, id = 1)
-- ---------------------------------------------------------------------------
CREATE TABLE ai_settings (
    id                  SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    gemini_api_key_enc  TEXT,                       -- "v1:<iv>:<tag>:<ciphertext>" base64url parts; NULL = fall back to env
    gemini_api_key_hint VARCHAR(8),                 -- last 4 characters only, for display
    default_model       VARCHAR(80),                -- NULL = fall back to env GEMINI_MODEL
    timeout_ms          INTEGER CHECK (timeout_ms IS NULL OR timeout_ms BETWEEN 5000 AND 120000),
    ai_enabled          BOOLEAN NOT NULL DEFAULT TRUE,  -- global kill switch for every Gemini call
    updated_by          UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO ai_settings (id) VALUES (1);

-- ---------------------------------------------------------------------------
-- Per-feature configuration. Feature keys are validated in code against a fixed catalogue.
-- Vision analysis ('image_analysis') keeps its safety-critical prompt in code; only switches and limits are editable.
-- ---------------------------------------------------------------------------
CREATE TABLE ai_feature_configs (
    feature_key         VARCHAR(64) PRIMARY KEY,
    enabled             BOOLEAN NOT NULL DEFAULT TRUE,
    model               VARCHAR(80),                -- NULL = inherit default model
    system_prompt       TEXT,                       -- NULL = use the built-in prompt for this feature
    max_output_tokens   INTEGER NOT NULL DEFAULT 1024 CHECK (max_output_tokens BETWEEN 128 AND 8192),
    temperature         NUMERIC(3,2) NOT NULL DEFAULT 0.20 CHECK (temperature BETWEEN 0 AND 1),
    daily_limit_free    INTEGER NOT NULL DEFAULT 5 CHECK (daily_limit_free >= 0),
    daily_limit_premium INTEGER NOT NULL DEFAULT 50 CHECK (daily_limit_premium >= 0),
    version             INTEGER NOT NULL DEFAULT 1,
    updated_by          UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Usage metering. One row per Gemini call (successful or not). Used for quotas, cost and monitoring.
-- ---------------------------------------------------------------------------
CREATE TABLE ai_usage_logs (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    feature_key     VARCHAR(64) NOT NULL,
    model           VARCHAR(80) NOT NULL,
    status          VARCHAR(16) NOT NULL CHECK (status IN ('ok', 'error', 'blocked', 'unsafe_replaced')),
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    latency_ms      INTEGER,
    error_code      VARCHAR(64),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ai_usage_user_feature_day_idx ON ai_usage_logs (user_id, feature_key, created_at);
CREATE INDEX ai_usage_created_idx ON ai_usage_logs (created_at);

-- ---------------------------------------------------------------------------
-- Admin audit trail. Stores who changed what; never stores secrets.
-- ---------------------------------------------------------------------------
CREATE TABLE admin_audit_logs (
    id          BIGSERIAL PRIMARY KEY,
    actor_id    UUID REFERENCES users(id) ON DELETE SET NULL,
    action      VARCHAR(64) NOT NULL,
    target      VARCHAR(128),
    details     JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX admin_audit_created_idx ON admin_audit_logs (created_at);
