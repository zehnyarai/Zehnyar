-- Pestino (پستینو) - initial schema
-- PostgreSQL 13+. Each migration file is executed inside a transaction by the runner.


-- gen_random_uuid() is built into PostgreSQL 13+, so no extension is required.

-- ---------------------------------------------------------------------------
-- Users & authentication
-- ---------------------------------------------------------------------------
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone           VARCHAR(16) NOT NULL UNIQUE,          -- normalized: 09XXXXXXXXX
    full_name       VARCHAR(120),
    province        VARCHAR(80),
    city            VARCHAR(80),
    role            VARCHAR(16) NOT NULL DEFAULT 'farmer'
                    CHECK (role IN ('farmer', 'expert', 'admin')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One-time passwords. Only a keyed hash of the code is stored.
CREATE TABLE otp_codes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone           VARCHAR(16) NOT NULL,
    code_hash       VARCHAR(128) NOT NULL,
    attempts        INTEGER NOT NULL DEFAULT 0,
    expires_at      TIMESTAMPTZ NOT NULL,
    consumed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_otp_codes_phone_created ON otp_codes (phone, created_at DESC);

-- Refresh tokens are rotated on every use. Reuse of a revoked token revokes the whole family.
CREATE TABLE refresh_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    family_id       UUID NOT NULL,
    token_hash      VARCHAR(128) NOT NULL UNIQUE,
    user_agent      VARCHAR(255),
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ,
    replaced_by     UUID REFERENCES refresh_tokens (id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens (user_id);
CREATE INDEX idx_refresh_tokens_family ON refresh_tokens (family_id);

-- ---------------------------------------------------------------------------
-- Farm management
-- ---------------------------------------------------------------------------
CREATE TABLE farms (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name                VARCHAR(120) NOT NULL,
    province            VARCHAR(80) NOT NULL,
    city                VARCHAR(80) NOT NULL,
    latitude            NUMERIC(9, 6),
    longitude           NUMERIC(9, 6),
    area_hectares       NUMERIC(10, 2) CHECK (area_hectares IS NULL OR area_hectares >= 0),
    pistachio_variety   VARCHAR(80),                       -- e.g. Ohadi, Akbari, Kalleghochi, Fandoghi
    average_tree_age    SMALLINT CHECK (average_tree_age IS NULL OR average_tree_age BETWEEN 0 AND 150),
    irrigation_method   VARCHAR(24) CHECK (irrigation_method IS NULL OR irrigation_method IN
                        ('drip', 'flood', 'sprinkler', 'micro_sprinkler', 'rainfed', 'other')),
    soil_type           VARCHAR(40),                       -- loam, clay, sandy, saline, calcareous ...
    soil_notes          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at          TIMESTAMPTZ                        -- soft delete
);
CREATE INDEX idx_farms_user_active ON farms (user_id) WHERE deleted_at IS NULL;

CREATE TABLE trees (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms (id) ON DELETE CASCADE,
    label           VARCHAR(80) NOT NULL,
    planted_year    SMALLINT CHECK (planted_year IS NULL OR planted_year BETWEEN 1300 AND 1500),
    variety         VARCHAR(80),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_trees_farm ON trees (farm_id);

-- ---------------------------------------------------------------------------
-- Uploaded images (files live on private storage; DB keeps metadata only)
-- ---------------------------------------------------------------------------
CREATE TABLE images (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    storage_key     VARCHAR(255) NOT NULL UNIQUE,
    mime_type       VARCHAR(32) NOT NULL,
    size_bytes      INTEGER NOT NULL CHECK (size_bytes > 0),
    sha256          CHAR(64) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_images_user ON images (user_id);

-- ---------------------------------------------------------------------------
-- Scientific knowledge base
-- ---------------------------------------------------------------------------
CREATE TABLE knowledge_articles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            VARCHAR(80) NOT NULL UNIQUE,
    kind            VARCHAR(20) NOT NULL CHECK (kind IN ('pest', 'disease', 'nutrient', 'environmental')),
    title_fa        VARCHAR(160) NOT NULL,
    title_en        VARCHAR(160) NOT NULL,
    summary_fa      TEXT NOT NULL,
    symptoms        JSONB NOT NULL DEFAULT '[]'::jsonb,     -- string[]
    causes          JSONB NOT NULL DEFAULT '[]'::jsonb,     -- string[]
    management      JSONB NOT NULL DEFAULT '[]'::jsonb,     -- string[] (principles, IPM-oriented)
    image_urls      JSONB NOT NULL DEFAULT '[]'::jsonb,     -- string[]
    is_published    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_knowledge_kind ON knowledge_articles (kind) WHERE is_published;

-- Pest-specific attributes (1:1 with knowledge_articles where kind = 'pest')
CREATE TABLE pests (
    article_id          UUID PRIMARY KEY REFERENCES knowledge_articles (id) ON DELETE CASCADE,
    scientific_name     VARCHAR(160),
    damage_type         VARCHAR(80),
    monitoring_method   TEXT
);

-- Disease-specific attributes (1:1 with knowledge_articles where kind = 'disease')
CREATE TABLE diseases (
    article_id          UUID PRIMARY KEY REFERENCES knowledge_articles (id) ON DELETE CASCADE,
    pathogen            VARCHAR(160),
    pathogen_type       VARCHAR(40)   -- fungus, bacterium, oomycete, abiotic ...
);

CREATE TABLE knowledge_references (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    citation        TEXT NOT NULL UNIQUE,
    url             VARCHAR(500),
    doi             VARCHAR(120),
    year            SMALLINT,
    verified        BOOLEAN NOT NULL DEFAULT FALSE,           -- set TRUE only after expert review
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE article_references (
    article_id      UUID NOT NULL REFERENCES knowledge_articles (id) ON DELETE CASCADE,
    reference_id    UUID NOT NULL REFERENCES knowledge_references (id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, reference_id)
);

-- ---------------------------------------------------------------------------
-- Analyses (AI image diagnostics)
-- ---------------------------------------------------------------------------
CREATE TABLE analyses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    farm_id             UUID REFERENCES farms (id) ON DELETE SET NULL,
    tree_id             UUID REFERENCES trees (id) ON DELETE SET NULL,
    image_id            UUID NOT NULL REFERENCES images (id) ON DELETE CASCADE,
    category            VARCHAR(20) NOT NULL CHECK (category IN ('leaf', 'fruit_cluster', 'trunk', 'pest', 'soil')),
    season              VARCHAR(12) NOT NULL CHECK (season IN ('spring', 'summer', 'autumn', 'winter')),
    tree_age_years      SMALLINT CHECK (tree_age_years IS NULL OR tree_age_years BETWEEN 0 AND 150),
    location_text       VARCHAR(200),
    user_notes          TEXT,
    status              VARCHAR(12) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
    primary_issue_slug  VARCHAR(80) REFERENCES knowledge_articles (slug) ON DELETE SET NULL,
    primary_title_fa    VARCHAR(200),
    confidence          SMALLINT CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 100),
    result              JSONB,                                -- validated AI report (see docs/API_SPEC.md)
    model               VARCHAR(64),
    prompt_version      VARCHAR(16),
    error_message       TEXT,
    latency_ms          INTEGER,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at        TIMESTAMPTZ,
    deleted_at          TIMESTAMPTZ
);
CREATE INDEX idx_analyses_user_created ON analyses (user_id, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_analyses_user_month ON analyses (user_id, created_at) WHERE status <> 'failed';
CREATE INDEX idx_analyses_farm ON analyses (farm_id);

-- ---------------------------------------------------------------------------
-- Subscriptions (monetization-ready)
-- ---------------------------------------------------------------------------
CREATE TABLE subscriptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    plan            VARCHAR(16) NOT NULL CHECK (plan IN ('free', 'premium')),
    status          VARCHAR(16) NOT NULL CHECK (status IN ('pending', 'active', 'expired', 'cancelled')),
    provider        VARCHAR(32),                           -- zarinpal, idpay, bazaar_iap, myket_iap, google_play, app_store
    provider_ref    VARCHAR(120),
    started_at      TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_subscriptions_user ON subscriptions (user_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- updated_at maintenance
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_farms_updated BEFORE UPDATE ON farms FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_articles_updated BEFORE UPDATE ON knowledge_articles FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_subscriptions_updated BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION set_updated_at();

