-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create shipment events hypertable
SELECT create_hypertable('shipment_events', 'timestamp');