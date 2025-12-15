"""align enum labels to python enum values (lowercase)

Revision ID: 20251215_align_enum_labels
Revises: 
Create Date: 2025-12-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251215_align_enum_labels'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create new enum types with lowercase labels to match Python enums
    op.execute("CREATE TYPE risktype_new AS ENUM ('port_congestion', 'customs_delay', 'quality_hold', 'weather_impact', 'equipment_failure', 'labor_strike', 'security_issue', 'route_blockage', 'capacity_shortage', 'other')")
    op.execute("CREATE TYPE riskseverity_new AS ENUM ('low','medium','high','critical')")
    op.execute("CREATE TYPE riskstatus_new AS ENUM ('detected','analyzing','mitigating','resolved','escalated')")
    op.execute("CREATE TYPE simulationtype_new AS ENUM ('mitigation_analysis','route_optimization','what_if_scenario','cost_benefit')")
    op.execute("CREATE TYPE simulationstatus_new AS ENUM ('pending','running','completed','failed')")
    op.execute("CREATE TYPE shipmentstatus_new AS ENUM ('pending','in_transit','delayed','arrived','cancelled','diverted')")
    op.execute("CREATE TYPE shipmentmode_new AS ENUM ('air','sea','land','rail','multimodal')")

    # Alter columns to use new enum types (cast via text -> lower -> new enum)
    op.execute("ALTER TABLE risks ALTER COLUMN risk_type TYPE risktype_new USING lower(risk_type::text)::risktype_new")
    op.execute("ALTER TABLE risks ALTER COLUMN severity TYPE riskseverity_new USING lower(severity::text)::riskseverity_new")
    op.execute("ALTER TABLE risks ALTER COLUMN status TYPE riskstatus_new USING lower(status::text)::riskstatus_new")

    op.execute("ALTER TABLE simulations ALTER COLUMN simulation_type TYPE simulationtype_new USING lower(simulation_type::text)::simulationtype_new")
    op.execute("ALTER TABLE simulations ALTER COLUMN status TYPE simulationstatus_new USING lower(status::text)::simulationstatus_new")

    op.execute("ALTER TABLE shipments ALTER COLUMN status TYPE shipmentstatus_new USING lower(status::text)::shipmentstatus_new")
    op.execute("ALTER TABLE shipments ALTER COLUMN mode TYPE shipmentmode_new USING lower(mode::text)::shipmentmode_new")

    # Drop old types if they exist and rename new types to original names
    # (wrap in plpgsql block to ignore errors if old types missing)
    op.execute("""
    DO $$
    BEGIN
        -- Drop old types if present
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risktype') THEN
            DROP TYPE risktype;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'riskseverity') THEN
            DROP TYPE riskseverity;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'riskstatus') THEN
            DROP TYPE riskstatus;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'simulationtype') THEN
            DROP TYPE simulationtype;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'simulationstatus') THEN
            DROP TYPE simulationstatus;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'shipmentstatus') THEN
            DROP TYPE shipmentstatus;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'shipmentmode') THEN
            DROP TYPE shipmentmode;
        END IF;
        -- Rename new types to canonical names
        ALTER TYPE risktype_new RENAME TO risktype;
        ALTER TYPE riskseverity_new RENAME TO riskseverity;
        ALTER TYPE riskstatus_new RENAME TO riskstatus;
        ALTER TYPE simulationtype_new RENAME TO simulationtype;
        ALTER TYPE simulationstatus_new RENAME TO simulationstatus;
        ALTER TYPE shipmentstatus_new RENAME TO shipmentstatus;
        ALTER TYPE shipmentmode_new RENAME TO shipmentmode;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Enum migration encountered an error';
        RAISE;
    END$$;
    """)


def downgrade():
    # Re-create the prior (uppercase) enum labels by transforming back to uppercase
    op.execute("CREATE TYPE risktype_old AS ENUM ('PORT_CONGESTION','CUSTOMS_DELAY','QUALITY_HOLD','WEATHER_IMPACT','EQUIPMENT_FAILURE','LABOR_STRIKE','SECURITY_ISSUE','ROUTE_BLOCKAGE','CAPACITY_SHORTAGE','OTHER')")
    op.execute("CREATE TYPE riskseverity_old AS ENUM ('LOW','MEDIUM','HIGH','CRITICAL')")
    op.execute("CREATE TYPE riskstatus_old AS ENUM ('DETECTED','ANALYZING','MITIGATING','RESOLVED','ESCALATED')")
    op.execute("CREATE TYPE simulationtype_old AS ENUM ('MITIGATION_ANALYSIS','ROUTE_OPTIMIZATION','WHAT_IF_SCENARIO','COST_BENEFIT')")
    op.execute("CREATE TYPE simulationstatus_old AS ENUM ('PENDING','RUNNING','COMPLETED','FAILED')")
    op.execute("CREATE TYPE shipmentstatus_old AS ENUM ('PENDING','IN_TRANSIT','DELAYED','ARRIVED','CANCELLED','DIVERTED')")
    op.execute("CREATE TYPE shipmentmode_old AS ENUM ('AIR','SEA','LAND','RAIL','MULTIMODAL')")

    # Alter columns back to old uppercase enums using upper()
    op.execute("ALTER TABLE risks ALTER COLUMN risk_type TYPE risktype_old USING upper(risk_type::text)::risktype_old")
    op.execute("ALTER TABLE risks ALTER COLUMN severity TYPE riskseverity_old USING upper(severity::text)::riskseverity_old")
    op.execute("ALTER TABLE risks ALTER COLUMN status TYPE riskstatus_old USING upper(status::text)::riskstatus_old")

    op.execute("ALTER TABLE simulations ALTER COLUMN simulation_type TYPE simulationtype_old USING upper(simulation_type::text)::simulationtype_old")
    op.execute("ALTER TABLE simulations ALTER COLUMN status TYPE simulationstatus_old USING upper(status::text)::simulationstatus_old")

    op.execute("ALTER TABLE shipments ALTER COLUMN status TYPE shipmentstatus_old USING upper(status::text)::shipmentstatus_old")
    op.execute("ALTER TABLE shipments ALTER COLUMN mode TYPE shipmentmode_old USING upper(mode::text)::shipmentmode_old")

    # Drop current lowercase types and rename old uppercase back to originals
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risktype') THEN
            DROP TYPE risktype;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'riskseverity') THEN
            DROP TYPE riskseverity;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'riskstatus') THEN
            DROP TYPE riskstatus;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'simulationtype') THEN
            DROP TYPE simulationtype;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'simulationstatus') THEN
            DROP TYPE simulationstatus;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'shipmentstatus') THEN
            DROP TYPE shipmentstatus;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'shipmentmode') THEN
            DROP TYPE shipmentmode;
        END IF;
        ALTER TYPE risktype_old RENAME TO risktype;
        ALTER TYPE riskseverity_old RENAME TO riskseverity;
        ALTER TYPE riskstatus_old RENAME TO riskstatus;
        ALTER TYPE simulationtype_old RENAME TO simulationtype;
        ALTER TYPE simulationstatus_old RENAME TO simulationstatus;
        ALTER TYPE shipmentstatus_old RENAME TO shipmentstatus;
        ALTER TYPE shipmentmode_old RENAME TO shipmentmode;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Enum rollback encountered an error';
        RAISE;
    END$$;
    """)
