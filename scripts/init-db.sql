-- init-db-enhanced.sql
-- Initialize database for Autonomous Control Tower with MCP

-- Create updated_at trigger function (if not exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create shipment events hypertable (if not already created)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM _timescaledb_catalog.hypertable 
        WHERE table_name = 'shipment_events'
    ) THEN
        PERFORM create_hypertable(
            'shipment_events', 
            'timestamp',
            chunk_time_interval => INTERVAL '1 week',
            if_not_exists => TRUE
        );
    END IF;
END $$;

-- Create risks hypertable (if not already created)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM _timescaledb_catalog.hypertable 
        WHERE table_name = 'risks'
    ) THEN
        PERFORM create_hypertable(
            'risks', 
            'detected_at',
            chunk_time_interval => INTERVAL '1 week',
            if_not_exists => TRUE
        );
    END IF;
END $$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_shipments_tracking_lower 
ON shipments (LOWER(tracking_number));

CREATE INDEX IF NOT EXISTS idx_shipments_status_risk 
ON shipments (status, is_at_risk, risk_score DESC);

CREATE INDEX IF NOT EXISTS idx_risks_active 
ON risks (status, severity, detected_at DESC) 
WHERE status NOT IN ('RESOLVED', 'ESCALATED');

CREATE INDEX IF NOT EXISTS idx_events_shipment_type 
ON shipment_events (shipment_id, event_type, timestamp DESC);

-- Create MCP agent activity table for monitoring
CREATE TABLE IF NOT EXISTS mcp_agent_activities (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    message_id VARCHAR(100),
    shipment_id INTEGER REFERENCES shipments(id),
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mcp_agent_activities_agent 
ON mcp_agent_activities (agent_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_mcp_agent_activities_shipment 
ON mcp_agent_activities (shipment_id, created_at DESC);

-- Create MCP message queue table for persistence
CREATE TABLE IF NOT EXISTS mcp_messages (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(100) UNIQUE NOT NULL,
    sender_agent VARCHAR(100) NOT NULL,
    recipient_agent VARCHAR(100) NOT NULL,
    message_type VARCHAR(100) NOT NULL,
    content JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mcp_messages_pending 
ON mcp_messages (status, created_at) 
WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_mcp_messages_recipient 
ON mcp_messages (recipient_agent, created_at DESC);

-- Create materialized view for dashboard analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_analytics AS
SELECT 
    DATE_TRUNC('day', s.created_at) as date,
    COUNT(DISTINCT s.id) as total_shipments,
    COUNT(DISTINCT CASE WHEN s.is_at_risk THEN s.id END) as at_risk_shipments,
    COUNT(DISTINCT r.id) as total_risks,
    AVG(s.risk_score) as avg_risk_score,
    COUNT(DISTINCT CASE WHEN r.severity = 'CRITICAL' THEN r.id END) as critical_risks,
    COUNT(DISTINCT CASE WHEN r.severity = 'HIGH' THEN r.id END) as high_risks
FROM shipments s
LEFT JOIN risks r ON s.id = r.shipment_id
WHERE s.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', s.created_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dashboard_analytics_date 
ON dashboard_analytics (date);

-- Refresh analytics view function
CREATE OR REPLACE FUNCTION refresh_dashboard_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_analytics;
END;
$$ LANGUAGE plpgsql;

-- Create function to trigger MCP agent action
CREATE OR REPLACE FUNCTION trigger_mcp_agent_action(
    p_agent_type VARCHAR(50),
    p_action_type VARCHAR(100),
    p_payload JSONB
) RETURNS TABLE(message_id VARCHAR, status VARCHAR) AS $$
DECLARE
    v_message_id VARCHAR;
BEGIN
    v_message_id := 'msg_' || EXTRACT(EPOCH FROM NOW()) || '_' || RANDOM()::VARCHAR;
    
    INSERT INTO mcp_messages (
        message_id,
        sender_agent,
        recipient_agent,
        message_type,
        content,
        status
    ) VALUES (
        v_message_id,
        'system',
        p_agent_type,
        p_action_type,
        p_payload,
        'pending'
    );
    
    -- Return the generated message
    RETURN QUERY 
    SELECT v_message_id, 'queued';
END;
$$ LANGUAGE plpgsql;

-- Create view for active shipments with risk summary
CREATE OR REPLACE VIEW active_shipments_risk_summary AS
SELECT 
    s.id,
    s.tracking_number,
    s.status,
    s.origin,
    s.destination,
    s.current_location,
    s.is_at_risk,
    s.risk_score,
    s.last_risk_check,
    COUNT(r.id) as total_risks,
    COUNT(CASE WHEN r.severity = 'CRITICAL' THEN 1 END) as critical_risks,
    COUNT(CASE WHEN r.severity = 'HIGH' THEN 1 END) as high_risks,
    MAX(r.detected_at) as latest_risk_detected,
    ARRAY_AGG(DISTINCT r.risk_type) as risk_types
FROM shipments s
LEFT JOIN risks r ON s.id = r.shipment_id 
    AND r.status NOT IN ('RESOLVED')
WHERE s.status IN ('PENDING', 'IN_TRANSIT', 'DELAYED')
GROUP BY s.id, s.tracking_number, s.status, s.origin, s.destination, 
         s.current_location, s.is_at_risk, s.risk_score, s.last_risk_check;


GRANT SELECT ON ALL TABLES IN SCHEMA public TO control_tower_user;