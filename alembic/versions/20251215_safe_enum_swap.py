"""safe enum swap: add new enum types, new columns, backfill, swap

Revision ID: 20251215_safe_enum_swap
Revises: 20251215_align_enum_labels
Create Date: 2025-12-15 00:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251215_safe_enum_swap'
down_revision = '20251215_align_enum_labels'
branch_labels = None
depends_on = None


def _add_temp_column(table, col, new_type):
    op.add_column(table, sa.Column(f"{col}_tmp", sa.Enum(*new_type, name=f"{col}__tmp_enum"), nullable=True))


def upgrade():
    # This migration uses temporary columns to minimize blocking and allow
    # backfilling before swapping columns.

    # Define the lowercase enum label lists
    risktype_vals = ['port_congestion', 'customs_delay', 'quality_hold', 'weather_impact', 'equipment_failure', 'labor_strike', 'security_issue', 'route_blockage', 'capacity_shortage', 'other']
    riskseverity_vals = ['low', 'medium', 'high', 'critical']
    riskstatus_vals = ['detected','analyzing','mitigating','resolved','escalated']
    simulationtype_vals = ['mitigation_analysis','route_optimization','what_if_scenario','cost_benefit']
    simulationstatus_vals = ['pending','running','completed','failed']
    shipmentstatus_vals = ['pending','in_transit','delayed','arrived','cancelled','diverted']
    shipmentmode_vals = ['air','sea','land','rail','multimodal']

    # Create temporary enum types and columns, then backfill from existing columns
    op.execute("CREATE TYPE risktype_tmp AS ENUM ('port_congestion','customs_delay','quality_hold','weather_impact','equipment_failure','labor_strike','security_issue','route_blockage','capacity_shortage','other')")
    op.execute("ALTER TABLE risks ADD COLUMN risk_type_tmp risktype_tmp")
    op.execute("UPDATE risks SET risk_type_tmp = lower(risk_type::text)::risktype_tmp")
    op.execute("ALTER TABLE risks ALTER COLUMN risk_type_tmp SET NOT NULL")

    op.execute("CREATE TYPE riskseverity_tmp AS ENUM ('low','medium','high','critical')")
    op.execute("ALTER TABLE risks ADD COLUMN severity_tmp riskseverity_tmp")
    op.execute("UPDATE risks SET severity_tmp = lower(severity::text)::riskseverity_tmp")
    op.execute("ALTER TABLE risks ALTER COLUMN severity_tmp SET NOT NULL")

    op.execute("CREATE TYPE riskstatus_tmp AS ENUM ('detected','analyzing','mitigating','resolved','escalated')")
    op.execute("ALTER TABLE risks ADD COLUMN status_tmp riskstatus_tmp")
    op.execute("UPDATE risks SET status_tmp = lower(status::text)::riskstatus_tmp")
    op.execute("ALTER TABLE risks ALTER COLUMN status_tmp SET NOT NULL")

    # Simulations
    op.execute("CREATE TYPE simulationtype_tmp AS ENUM ('mitigation_analysis','route_optimization','what_if_scenario','cost_benefit')")
    op.execute("ALTER TABLE simulations ADD COLUMN simulation_type_tmp simulationtype_tmp")
    op.execute("UPDATE simulations SET simulation_type_tmp = lower(simulation_type::text)::simulationtype_tmp")
    op.execute("ALTER TABLE simulations ALTER COLUMN simulation_type_tmp SET NOT NULL")

    op.execute("CREATE TYPE simulationstatus_tmp AS ENUM ('pending','running','completed','failed')")
    op.execute("ALTER TABLE simulations ADD COLUMN status_tmp simulationstatus_tmp")
    op.execute("UPDATE simulations SET status_tmp = lower(status::text)::simulationstatus_tmp")
    op.execute("ALTER TABLE simulations ALTER COLUMN status_tmp SET NOT NULL")

    # Shipments
    op.execute("CREATE TYPE shipmentstatus_tmp AS ENUM ('pending','in_transit','delayed','arrived','cancelled','diverted')")
    op.execute("ALTER TABLE shipments ADD COLUMN status_tmp shipmentstatus_tmp")
    op.execute("UPDATE shipments SET status_tmp = lower(status::text)::shipmentstatus_tmp")
    op.execute("ALTER TABLE shipments ALTER COLUMN status_tmp SET NOT NULL")

    op.execute("CREATE TYPE shipmentmode_tmp AS ENUM ('air','sea','land','rail','multimodal')")
    op.execute("ALTER TABLE shipments ADD COLUMN mode_tmp shipmentmode_tmp")
    op.execute("UPDATE shipments SET mode_tmp = lower(mode::text)::shipmentmode_tmp")
    op.execute("ALTER TABLE shipments ALTER COLUMN mode_tmp SET NOT NULL")

    # Swap columns: drop old columns and rename tmp columns
    # Use transactional block for safety
    op.execute("BEGIN")
    op.execute("ALTER TABLE risks DROP COLUMN risk_type")
    op.execute("ALTER TABLE risks RENAME COLUMN risk_type_tmp TO risk_type")
    op.execute("ALTER TABLE risks DROP COLUMN severity")
    op.execute("ALTER TABLE risks RENAME COLUMN severity_tmp TO severity")
    op.execute("ALTER TABLE risks DROP COLUMN status")
    op.execute("ALTER TABLE risks RENAME COLUMN status_tmp TO status")

    op.execute("ALTER TABLE simulations DROP COLUMN simulation_type")
    op.execute("ALTER TABLE simulations RENAME COLUMN simulation_type_tmp TO simulation_type")
    op.execute("ALTER TABLE simulations DROP COLUMN status")
    op.execute("ALTER TABLE simulations RENAME COLUMN status_tmp TO status")

    op.execute("ALTER TABLE shipments DROP COLUMN status")
    op.execute("ALTER TABLE shipments RENAME COLUMN status_tmp TO status")
    op.execute("ALTER TABLE shipments DROP COLUMN mode")
    op.execute("ALTER TABLE shipments RENAME COLUMN mode_tmp TO mode")
    op.execute("COMMIT")

    # Drop old enum types if any leftover (best-effort)
    op.execute("DROP TYPE IF EXISTS risktype")
    op.execute("DROP TYPE IF EXISTS riskseverity")
    op.execute("DROP TYPE IF EXISTS riskstatus")
    op.execute("DROP TYPE IF EXISTS simulationtype")
    op.execute("DROP TYPE IF EXISTS simulationstatus")
    op.execute("DROP TYPE IF EXISTS shipmentstatus")
    op.execute("DROP TYPE IF EXISTS shipmentmode")

    # Rename tmp types to canonical names
    op.execute("ALTER TYPE risktype_tmp RENAME TO risktype")
    op.execute("ALTER TYPE riskseverity_tmp RENAME TO riskseverity")
    op.execute("ALTER TYPE riskstatus_tmp RENAME TO riskstatus")
    op.execute("ALTER TYPE simulationtype_tmp RENAME TO simulationtype")
    op.execute("ALTER TYPE simulationstatus_tmp RENAME TO simulationstatus")
    op.execute("ALTER TYPE shipmentstatus_tmp RENAME TO shipmentstatus")
    op.execute("ALTER TYPE shipmentmode_tmp RENAME TO shipmentmode")


def downgrade():
    # The downgrade attempts to reverse the swap: create uppercase tmp types,
    # copy data uppercased, swap back.
    op.execute("CREATE TYPE risktype_old AS ENUM ('PORT_CONGESTION','CUSTOMS_DELAY','QUALITY_HOLD','WEATHER_IMPACT','EQUIPMENT_FAILURE','LABOR_STRIKE','SECURITY_ISSUE','ROUTE_BLOCKAGE','CAPACITY_SHORTAGE','OTHER')")
    op.execute("ALTER TABLE risks ADD COLUMN risk_type_old risktype_old")
    op.execute("UPDATE risks SET risk_type_old = upper(risk_type::text)::risktype_old")
    op.execute("ALTER TABLE risks ALTER COLUMN risk_type_old SET NOT NULL")

    op.execute("CREATE TYPE riskseverity_old AS ENUM ('LOW','MEDIUM','HIGH','CRITICAL')")
    op.execute("ALTER TABLE risks ADD COLUMN severity_old riskseverity_old")
    op.execute("UPDATE risks SET severity_old = upper(severity::text)::riskseverity_old")
    op.execute("ALTER TABLE risks ALTER COLUMN severity_old SET NOT NULL")

    op.execute("CREATE TYPE riskstatus_old AS ENUM ('DETECTED','ANALYZING','MITIGATING','RESOLVED','ESCALATED')")
    op.execute("ALTER TABLE risks ADD COLUMN status_old riskstatus_old")
    op.execute("UPDATE risks SET status_old = upper(status::text)::riskstatus_old")
    op.execute("ALTER TABLE risks ALTER COLUMN status_old SET NOT NULL")

    op.execute("CREATE TYPE simulationtype_old AS ENUM ('MITIGATION_ANALYSIS','ROUTE_OPTIMIZATION','WHAT_IF_SCENARIO','COST_BENEFIT')")
    op.execute("ALTER TABLE simulations ADD COLUMN simulation_type_old simulationtype_old")
    op.execute("UPDATE simulations SET simulation_type_old = upper(simulation_type::text)::simulationtype_old")
    op.execute("ALTER TABLE simulations ALTER COLUMN simulation_type_old SET NOT NULL")

    op.execute("CREATE TYPE simulationstatus_old AS ENUM ('PENDING','RUNNING','COMPLETED','FAILED')")
    op.execute("ALTER TABLE simulations ADD COLUMN status_old simulationstatus_old")
    op.execute("UPDATE simulations SET status_old = upper(status::text)::simulationstatus_old")
    op.execute("ALTER TABLE simulations ALTER COLUMN status_old SET NOT NULL")

    op.execute("CREATE TYPE shipmentstatus_old AS ENUM ('PENDING','IN_TRANSIT','DELAYED','ARRIVED','CANCELLED','DIVERTED')")
    op.execute("ALTER TABLE shipments ADD COLUMN status_old shipmentstatus_old")
    op.execute("UPDATE shipments SET status_old = upper(status::text)::shipmentstatus_old")
    op.execute("ALTER TABLE shipments ALTER COLUMN status_old SET NOT NULL")

    op.execute("CREATE TYPE shipmentmode_old AS ENUM ('AIR','SEA','LAND','RAIL','MULTIMODAL')")
    op.execute("ALTER TABLE shipments ADD COLUMN mode_old shipmentmode_old")
    op.execute("UPDATE shipments SET mode_old = upper(mode::text)::shipmentmode_old")
    op.execute("ALTER TABLE shipments ALTER COLUMN mode_old SET NOT NULL")

    op.execute("BEGIN")
    op.execute("ALTER TABLE risks DROP COLUMN risk_type")
    op.execute("ALTER TABLE risks RENAME COLUMN risk_type_old TO risk_type")
    op.execute("ALTER TABLE risks DROP COLUMN severity")
    op.execute("ALTER TABLE risks RENAME COLUMN severity_old TO severity")
    op.execute("ALTER TABLE risks DROP COLUMN status")
    op.execute("ALTER TABLE risks RENAME COLUMN status_old TO status")

    op.execute("ALTER TABLE simulations DROP COLUMN simulation_type")
    op.execute("ALTER TABLE simulations RENAME COLUMN simulation_type_old TO simulation_type")
    op.execute("ALTER TABLE simulations DROP COLUMN status")
    op.execute("ALTER TABLE simulations RENAME COLUMN status_old TO status")

    op.execute("ALTER TABLE shipments DROP COLUMN status")
    op.execute("ALTER TABLE shipments RENAME COLUMN status_old TO status")
    op.execute("ALTER TABLE shipments DROP COLUMN mode")
    op.execute("ALTER TABLE shipments RENAME COLUMN mode_old TO mode")
    op.execute("COMMIT")

    # Drop tmp lowercase types and rename old uppercase back
    op.execute("DROP TYPE IF EXISTS risktype")
    op.execute("ALTER TYPE risktype_old RENAME TO risktype")
    op.execute("DROP TYPE IF EXISTS riskseverity")
    op.execute("ALTER TYPE riskseverity_old RENAME TO riskseverity")
    op.execute("DROP TYPE IF EXISTS riskstatus")
    op.execute("ALTER TYPE riskstatus_old RENAME TO riskstatus")
    op.execute("DROP TYPE IF EXISTS simulationtype")
    op.execute("ALTER TYPE simulationtype_old RENAME TO simulationtype")
    op.execute("DROP TYPE IF EXISTS simulationstatus")
    op.execute("ALTER TYPE simulationstatus_old RENAME TO simulationstatus")
    op.execute("DROP TYPE IF EXISTS shipmentstatus")
    op.execute("ALTER TYPE shipmentstatus_old RENAME TO shipmentstatus")
    op.execute("DROP TYPE IF EXISTS shipmentmode")
    op.execute("ALTER TYPE shipmentmode_old RENAME TO shipmentmode")
