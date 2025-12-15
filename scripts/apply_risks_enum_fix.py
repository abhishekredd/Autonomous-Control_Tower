import os
from sqlalchemy import create_engine, text

url = os.environ.get('DATABASE_URL')
print('DATABASE_URL=', url)
engine = create_engine(url)
with engine.begin() as conn:
    print('Creating risktype_new')
    conn.execute(text("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risktype_new') THEN CREATE TYPE risktype_new AS ENUM ('port_congestion', 'customs_delay', 'quality_hold', 'weather_impact', 'equipment_failure', 'labor_strike', 'security_issue', 'route_blockage', 'capacity_shortage', 'other'); END IF; END$$;"))
    print('Altering risks.risk_type')
    conn.execute(text("ALTER TABLE risks ALTER COLUMN risk_type TYPE risktype_new USING lower(risk_type::text)::risktype_new"))

    print('Creating riskseverity_new')
    conn.execute(text("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'riskseverity_new') THEN CREATE TYPE riskseverity_new AS ENUM ('low','medium','high','critical'); END IF; END$$;"))
    print('Altering risks.severity')
    conn.execute(text("ALTER TABLE risks ALTER COLUMN severity TYPE riskseverity_new USING lower(severity::text)::riskseverity_new"))

    print('Creating riskstatus_new')
    conn.execute(text("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'riskstatus_new') THEN CREATE TYPE riskstatus_new AS ENUM ('detected','analyzing','mitigating','resolved','escalated'); END IF; END$$;"))
    print('Dropping default on risks.status (if any)')
    try:
        conn.execute(text("ALTER TABLE risks ALTER COLUMN status DROP DEFAULT"))
    except Exception:
        pass
    print('Altering risks.status')
    conn.execute(text("ALTER TABLE risks ALTER COLUMN status TYPE riskstatus_new USING lower(status::text)::riskstatus_new"))
    # set sensible default (use the new type name)
    conn.execute(text("ALTER TABLE risks ALTER COLUMN status SET DEFAULT 'detected'::riskstatus_new"))

    print('Drop old types if exist and rename')
    # Drop any old types named risktype etc (best-effort)
    conn.execute(text("DROP TYPE IF EXISTS risktype CASCADE"))
    conn.execute(text("DROP TYPE IF EXISTS riskseverity CASCADE"))
    conn.execute(text("DROP TYPE IF EXISTS riskstatus CASCADE"))

    conn.execute(text("ALTER TYPE risktype_new RENAME TO risktype"))
    conn.execute(text("ALTER TYPE riskseverity_new RENAME TO riskseverity"))
    conn.execute(text("ALTER TYPE riskstatus_new RENAME TO riskstatus"))

print('Done')
