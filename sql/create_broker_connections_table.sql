-- ============================================
-- BROKER CONNECTIONS TABLE
-- ============================================
-- This table stores encrypted broker API credentials for premium users
-- Supported brokers: IOL (InvertirOnline) and Binance

-- Create broker_connections table
CREATE TABLE IF NOT EXISTS broker_connections (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    broker_name VARCHAR(50) NOT NULL CHECK (broker_name IN ('IOL', 'BINANCE')),
    
    -- Encrypted credentials (using Fernet encryption)
    api_key_encrypted TEXT,           -- For Binance API Key, or IOL username
    api_secret_encrypted TEXT,        -- For Binance API Secret
    username_encrypted TEXT,          -- For IOL username
    password_encrypted TEXT,          -- For IOL password
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_synced TIMESTAMPTZ,         -- Last time portfolio was synced
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure one connection per broker per user
    UNIQUE(user_id, broker_name)
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_broker_connections_user_id 
    ON broker_connections(user_id);

CREATE INDEX IF NOT EXISTS idx_broker_connections_broker_name 
    ON broker_connections(broker_name);

CREATE INDEX IF NOT EXISTS idx_broker_connections_is_active 
    ON broker_connections(is_active);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================
ALTER TABLE broker_connections ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view own broker connections" ON broker_connections;
DROP POLICY IF EXISTS "Users can create own broker connections" ON broker_connections;
DROP POLICY IF EXISTS "Users can update own broker connections" ON broker_connections;
DROP POLICY IF EXISTS "Users can delete own broker connections" ON broker_connections;

-- Users can only view their own connections
CREATE POLICY "Users can view own broker connections"
    ON broker_connections FOR SELECT
    USING (auth.uid() = user_id);

-- Users can create their own connections
CREATE POLICY "Users can create own broker connections"
    ON broker_connections FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own connections
CREATE POLICY "Users can update own broker connections"
    ON broker_connections FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can delete their own connections
CREATE POLICY "Users can delete own broker connections"
    ON broker_connections FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- TRIGGERS
-- ============================================
-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_broker_connections_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at on every update
DROP TRIGGER IF EXISTS trigger_update_broker_connections_timestamp ON broker_connections;

CREATE TRIGGER trigger_update_broker_connections_timestamp
    BEFORE UPDATE ON broker_connections
    FOR EACH ROW
    EXECUTE FUNCTION update_broker_connections_updated_at();

-- ============================================
-- COMMENTS
-- ============================================
COMMENT ON TABLE broker_connections IS 'Stores encrypted broker API credentials for premium users';
COMMENT ON COLUMN broker_connections.broker_name IS 'Broker identifier: IOL or BINANCE';
COMMENT ON COLUMN broker_connections.api_key_encrypted IS 'Encrypted API key (Binance) or username (IOL)';
COMMENT ON COLUMN broker_connections.api_secret_encrypted IS 'Encrypted API secret (Binance only)';
COMMENT ON COLUMN broker_connections.username_encrypted IS 'Encrypted username (IOL only)';
COMMENT ON COLUMN broker_connections.password_encrypted IS 'Encrypted password (IOL only)';
COMMENT ON COLUMN broker_connections.is_active IS 'Whether the connection is active';
COMMENT ON COLUMN broker_connections.last_synced IS 'Last successful portfolio synchronization';


