-- ============================================
-- RULE EXECUTION AND BACKTESTING SYSTEM
-- ============================================
-- This file contains all SQL for the automated rule execution and backtesting system

-- ============================================
-- 1. RULE EXECUTIONS TABLE
-- ============================================
-- Stores actual executions of rules (when they trigger and execute orders)

CREATE TABLE IF NOT EXISTS public.rule_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relations
    rule_id UUID NOT NULL REFERENCES public.rules(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    broker_connection_id UUID REFERENCES public.broker_connections(id) ON DELETE SET NULL,
    
    -- Execution details
    execution_type VARCHAR(20) NOT NULL CHECK (execution_type IN ('ALERT_ONLY', 'BUY', 'SELL', 'SIMULATION')),
    ticker VARCHAR(20) NOT NULL,
    quantity DECIMAL(20, 8),
    price DECIMAL(20, 4),
    total_amount DECIMAL(20, 4),
    
    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'EXECUTED', 'FAILED', 'CANCELLED', 'REJECTED')),
    error_message TEXT,
    
    -- Broker response (store full response for debugging)
    broker_response JSONB,
    broker_order_id VARCHAR(100), -- Order ID from broker API
    
    -- Timestamps
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), -- When rule condition was met
    executed_at TIMESTAMPTZ, -- When order was actually executed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for rule_executions
CREATE INDEX IF NOT EXISTS idx_rule_executions_rule_id ON public.rule_executions(rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_executions_user_id ON public.rule_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_rule_executions_broker_connection_id ON public.rule_executions(broker_connection_id);
CREATE INDEX IF NOT EXISTS idx_rule_executions_status ON public.rule_executions(status);
CREATE INDEX IF NOT EXISTS idx_rule_executions_triggered_at ON public.rule_executions(triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_rule_executions_ticker ON public.rule_executions(ticker);

-- ============================================
-- 2. RULE BACKTESTS TABLE
-- ============================================
-- Stores backtest results for rules

CREATE TABLE IF NOT EXISTS public.rule_backtests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relations
    rule_id UUID NOT NULL REFERENCES public.rules(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Backtest parameters
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(20, 4) NOT NULL DEFAULT 10000,
    
    -- Results
    total_executions INTEGER DEFAULT 0, -- How many times rule would have triggered
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    
    -- Financial metrics
    final_capital DECIMAL(20, 4),
    total_return DECIMAL(10, 4), -- Percentage
    total_profit_loss DECIMAL(20, 4),
    max_drawdown DECIMAL(10, 4), -- Maximum loss from peak
    win_rate DECIMAL(5, 2), -- Percentage of winning trades
    
    -- Performance metrics
    sharpe_ratio DECIMAL(10, 4),
    profit_factor DECIMAL(10, 4), -- Gross profit / Gross loss
    
    -- Detailed results (JSON for flexibility)
    execution_details JSONB, -- Array of all executions with dates and results
    daily_equity_curve JSONB, -- Daily portfolio value for charting
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED')),
    error_message TEXT,
    
    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for rule_backtests
CREATE INDEX IF NOT EXISTS idx_rule_backtests_rule_id ON public.rule_backtests(rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_backtests_user_id ON public.rule_backtests(user_id);
CREATE INDEX IF NOT EXISTS idx_rule_backtests_status ON public.rule_backtests(status);
CREATE INDEX IF NOT EXISTS idx_rule_backtests_created_at ON public.rule_backtests(created_at DESC);

-- ============================================
-- 3. UPDATE RULES TABLE
-- ============================================
-- Add new columns to rules table for execution settings

ALTER TABLE public.rules 
ADD COLUMN IF NOT EXISTS execution_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS execution_type VARCHAR(20) DEFAULT 'ALERT_ONLY' CHECK (execution_type IN ('ALERT_ONLY', 'BUY', 'SELL', 'SIMULATION')),
ADD COLUMN IF NOT EXISTS broker_connection_id UUID REFERENCES public.broker_connections(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS quantity DECIMAL(20, 8), -- Quantity to buy/sell
ADD COLUMN IF NOT EXISTS max_execution_amount DECIMAL(20, 4), -- Maximum amount per execution
ADD COLUMN IF NOT EXISTS stop_loss_percent DECIMAL(5, 2), -- Stop loss percentage (optional)
ADD COLUMN IF NOT EXISTS take_profit_percent DECIMAL(5, 2), -- Take profit percentage (optional)
ADD COLUMN IF NOT EXISTS cooldown_minutes INTEGER DEFAULT 60, -- Minutes to wait before re-executing same rule
ADD COLUMN IF NOT EXISTS last_execution_at TIMESTAMPTZ; -- Last time this rule was executed

-- Index for execution-enabled rules
CREATE INDEX IF NOT EXISTS idx_rules_execution_enabled ON public.rules(execution_enabled) WHERE execution_enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_rules_broker_connection_id ON public.rules(broker_connection_id);

-- ============================================
-- 4. TRIGGERS
-- ============================================

-- Update updated_at for rule_executions
CREATE OR REPLACE FUNCTION update_rule_executions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_rule_executions_updated_at
    BEFORE UPDATE ON public.rule_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_rule_executions_updated_at();

-- Update updated_at for rule_backtests
CREATE OR REPLACE FUNCTION update_rule_backtests_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_rule_backtests_updated_at
    BEFORE UPDATE ON public.rule_backtests
    FOR EACH ROW
    EXECUTE FUNCTION update_rule_backtests_updated_at();

-- ============================================
-- 5. ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS
ALTER TABLE public.rule_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rule_backtests ENABLE ROW LEVEL SECURITY;

-- Policies for rule_executions
DROP POLICY IF EXISTS "Users can view own rule executions" ON public.rule_executions;
CREATE POLICY "Users can view own rule executions"
    ON public.rule_executions FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own rule executions" ON public.rule_executions;
CREATE POLICY "Users can create own rule executions"
    ON public.rule_executions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own rule executions" ON public.rule_executions;
CREATE POLICY "Users can update own rule executions"
    ON public.rule_executions FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policies for rule_backtests
DROP POLICY IF EXISTS "Users can view own rule backtests" ON public.rule_backtests;
CREATE POLICY "Users can view own rule backtests"
    ON public.rule_backtests FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own rule backtests" ON public.rule_backtests;
CREATE POLICY "Users can create own rule backtests"
    ON public.rule_backtests FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own rule backtests" ON public.rule_backtests;
CREATE POLICY "Users can update own rule backtests"
    ON public.rule_backtests FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ============================================
-- 6. HELPER FUNCTIONS
-- ============================================

-- Function to get execution statistics for a rule
CREATE OR REPLACE FUNCTION get_rule_execution_stats(p_rule_id UUID)
RETURNS TABLE (
    total_executions BIGINT,
    successful_executions BIGINT,
    failed_executions BIGINT,
    total_profit_loss DECIMAL,
    avg_profit_loss DECIMAL,
    last_execution_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_executions,
        COUNT(*) FILTER (WHERE status = 'EXECUTED')::BIGINT as successful_executions,
        COUNT(*) FILTER (WHERE status = 'FAILED')::BIGINT as failed_executions,
        COALESCE(SUM(
            CASE 
                WHEN execution_type = 'BUY' THEN -total_amount
                WHEN execution_type = 'SELL' THEN total_amount
                ELSE 0
            END
        ), 0) as total_profit_loss,
        COALESCE(AVG(
            CASE 
                WHEN execution_type = 'BUY' THEN -total_amount
                WHEN execution_type = 'SELL' THEN total_amount
                ELSE 0
            END
        ), 0) as avg_profit_loss,
        MAX(executed_at) as last_execution_at
    FROM public.rule_executions
    WHERE rule_id = p_rule_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if rule can be executed (cooldown check)
CREATE OR REPLACE FUNCTION can_execute_rule(p_rule_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_last_execution TIMESTAMPTZ;
    v_cooldown_minutes INTEGER;
BEGIN
    SELECT last_execution_at, cooldown_minutes
    INTO v_last_execution, v_cooldown_minutes
    FROM public.rules
    WHERE id = p_rule_id;
    
    -- If no cooldown set, allow execution
    IF v_cooldown_minutes IS NULL OR v_cooldown_minutes = 0 THEN
        RETURN TRUE;
    END IF;
    
    -- If never executed, allow
    IF v_last_execution IS NULL THEN
        RETURN TRUE;
    END IF;
    
    -- Check if cooldown period has passed
    RETURN (NOW() - v_last_execution) >= (v_cooldown_minutes || ' minutes')::INTERVAL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

