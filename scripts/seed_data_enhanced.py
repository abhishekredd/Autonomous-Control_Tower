#!/usr/bin/env python3
"""
Enhanced seed data with MCP agent integration - FOR AIVEN POSTGRESQL
Working version - Doesn't drop existing tables
"""
import asyncio
import json
import random
import sys
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

# ================================
# AIVEN POSTGRESQL CONFIGURATION
# ================================
# Your Aiven credentials
POSTGRES_USER = ""
POSTGRES_PASSWORD = ""
POSTGRES_DB = ""
POSTGRES_HOST = ""
POSTGRES_PORT = ""

# Connection URL for asyncpg
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

print("🔌 AIVEN POSTGRESQL CONFIGURATION:")
print(f"   Host: {POSTGRES_HOST}")
print(f"   Port: {POSTGRES_PORT}")
print(f"   Database: {POSTGRES_DB}")
print(f"   User: {POSTGRES_USER}")
print("="*50)

# Create SSL context for Aiven
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=5,
    pool_pre_ping=True,
    connect_args={
        "ssl": ssl_context,
        "server_settings": {"jit": "off"}
    }
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class DatabaseConnectionTester:
    """Test database connection before proceeding"""
    
    @staticmethod
    async def test_connection():
        """Test database connection"""
        print("🔍 Testing Aiven PostgreSQL connection...")
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ Connected to Aiven PostgreSQL!")
                print(f"   Version: {version}")
                
                result = await session.execute(text("SELECT current_database()"))
                db_name = result.scalar()
                print(f"   Database: {db_name}")
                
                return True
        except Exception as e:
            print(f"❌ Aiven PostgreSQL connection failed: {type(e).__name__}: {e}")
            return False

async def check_table_exists(table_name: str) -> bool:
    """Check if a table exists"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                )
            """), {"table_name": table_name})
            return result.scalar()
    except Exception as e:
        print(f"⚠️ Error checking table {table_name}: {e}")
        return False

async def create_table_if_not_exists(table_name: str, create_sql: str):
    """Create a table only if it doesn't exist"""
    try:
        async with AsyncSessionLocal() as session:
            # Check if table exists
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                )
            """), {"table_name": table_name})
            
            if not result.scalar():
                print(f"📊 Creating table: {table_name}")
                await session.execute(text(create_sql))
                await session.commit()
                print(f"✅ Table '{table_name}' created")
            else:
                print(f"✅ Table '{table_name}' already exists, skipping")
                
    except Exception as e:
        print(f"❌ Error creating table {table_name}: {e}")
        raise

async def create_tables_safely():
    """Create tables only if they don't exist"""
    print("📊 Checking and creating tables if needed...")
    
    # Define table schemas
    table_definitions = {
        "shipments": """
            CREATE TABLE shipments (
                id SERIAL PRIMARY KEY,
                tracking_number VARCHAR(100) UNIQUE,
                reference_number VARCHAR(100),
                origin VARCHAR(255) NOT NULL,
                destination VARCHAR(255) NOT NULL,
                current_location VARCHAR(255),
                current_port VARCHAR(50),
                next_port VARCHAR(50),
                status VARCHAR(50),
                mode VARCHAR(50) NOT NULL,
                weight DECIMAL(10, 2),
                volume DECIMAL(10, 2),
                value DECIMAL(15, 2),
                estimated_departure TIMESTAMP,
                estimated_arrival TIMESTAMP,
                actual_departure TIMESTAMP,
                actual_arrival TIMESTAMP,
                shipper VARCHAR(255),
                carrier VARCHAR(255),
                consignee VARCHAR(255),
                customs_broker VARCHAR(255),
                is_at_risk BOOLEAN DEFAULT FALSE,
                risk_score DECIMAL(3, 2) DEFAULT 0.00,
                last_risk_check TIMESTAMP,
                shipment_metadata JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "risks": """
            CREATE TABLE risks (
                id SERIAL PRIMARY KEY,
                shipment_id INTEGER,
                risk_type VARCHAR(50),
                severity VARCHAR(50),
                status VARCHAR(50) DEFAULT 'detected',
                description TEXT,
                confidence DECIMAL(3, 2),
                detected_at TIMESTAMPTZ NOT NULL,
                resolved_at TIMESTAMPTZ,
                expected_delay_hours DECIMAL(5, 1),
                expected_cost_impact DECIMAL(10, 2),
                affected_parties JSONB,
                mitigation_actions JSONB,
                selected_mitigation JSONB,
                mitigation_result JSONB,
                source VARCHAR(100),
                risk_metadata JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "mcp_agent_activities": """
            CREATE TABLE mcp_agent_activities (
                id SERIAL PRIMARY KEY,
                agent_id VARCHAR(100) NOT NULL,
                agent_type VARCHAR(50) NOT NULL,
                activity_type VARCHAR(100) NOT NULL,
                shipment_id INTEGER,
                details JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """
    }
    
    # Create tables that don't exist
    for table_name, create_sql in table_definitions.items():
        try:
            await create_table_if_not_exists(table_name, create_sql)
        except Exception as e:
            print(f"❌ Failed to create table {table_name}: {e}")
            return False
    
    # Create foreign keys if they don't exist (after tables are created)
    try:
        async with AsyncSessionLocal() as session:
            # Check if foreign key already exists for risks.shipment_id
            result = await session.execute(text("""
                SELECT COUNT(*) FROM information_schema.table_constraints 
                WHERE constraint_name = 'risks_shipment_id_fkey' 
                AND table_name = 'risks'
            """))
            
            if result.scalar() == 0:
                print("🔗 Adding foreign key: risks.shipment_id → shipments.id")
                await session.execute(text("""
                    ALTER TABLE risks 
                    ADD CONSTRAINT risks_shipment_id_fkey 
                    FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE CASCADE
                """))
            
            # Check if foreign key already exists for mcp_agent_activities.shipment_id
            result = await session.execute(text("""
                SELECT COUNT(*) FROM information_schema.table_constraints 
                WHERE constraint_name = 'mcp_agent_activities_shipment_id_fkey' 
                AND table_name = 'mcp_agent_activities'
            """))
            
            if result.scalar() == 0:
                print("🔗 Adding foreign key: mcp_agent_activities.shipment_id → shipments.id")
                await session.execute(text("""
                    ALTER TABLE mcp_agent_activities 
                    ADD CONSTRAINT mcp_agent_activities_shipment_id_fkey 
                    FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE SET NULL
                """))
            
            await session.commit()
            
    except Exception as e:
        print(f"⚠️ Note: Could not add foreign keys (they might already exist): {e}")
        # Don't fail if foreign keys already exist
    
    # Create indexes
    try:
        async with AsyncSessionLocal() as session:
            indexes = [
                ("CREATE INDEX IF NOT EXISTS idx_shipments_tracking ON shipments(tracking_number)", "shipments_tracking"),
                ("CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments(status)", "shipments_status"),
                ("CREATE INDEX IF NOT EXISTS idx_risks_shipment ON risks(shipment_id)", "risks_shipment"),
                ("CREATE INDEX IF NOT EXISTS idx_risks_severity ON risks(severity)", "risks_severity"),
                ("CREATE INDEX IF NOT EXISTS idx_mcp_agent ON mcp_agent_activities(agent_id, created_at)", "mcp_agent")
            ]
            
            for index_sql, index_name in indexes:
                try:
                    await session.execute(text(index_sql))
                    print(f"📈 Created index: {index_name}")
                except Exception as e:
                    print(f"⚠️ Could not create index {index_name}: {e}")
            
            await session.commit()
            
    except Exception as e:
        print(f"⚠️ Note: Could not create some indexes: {e}")
        # Don't fail if indexes already exist
    
    print("✅ Tables checked/created successfully")
    return True

def generate_shipment_data(count: int = 10) -> List[Dict]:
    """Generate realistic shipment data"""
    shipments = []
    
    ports = [
        ("Shanghai", "China", "CNSHA"),
        ("Rotterdam", "Netherlands", "NLRTM"),
        ("Los Angeles", "USA", "USLAX"),
        ("Singapore", "Singapore", "SGSIN"),
        ("Tokyo", "Japan", "JPTYO"),
        ("Dubai", "UAE", "AEDXB")
    ]
    
    for i in range(count):
        origin = random.choice(ports)
        dest = random.choice([p for p in ports if p != origin])
        
        days_ago = random.randint(1, 30)
        departure_date = datetime.utcnow() - timedelta(days=days_ago)
        transit_days = random.randint(14, 42)
        arrival_date = departure_date + timedelta(days=transit_days)
        
        if arrival_date < datetime.utcnow():
            status = 'arrived'
        elif departure_date > datetime.utcnow():
            status = 'pending'
        else:
            status = random.choice(['in_transit', 'delayed'])
        
        shipment = {
            "tracking_number": f"TRK{800000 + i:06d}",
            "reference_number": f"SH-{100 + i:03d}",
            "origin": f"{origin[0]}, {origin[1]}",
            "destination": f"{dest[0]}, {dest[1]}",
            "current_location": f"At sea" if status == 'in_transit' else f"At {origin[0]}",
            "current_port": origin[2] if status in ['pending', 'delayed'] else dest[2] if status == 'arrived' else None,
            "next_port": dest[2] if status == 'in_transit' else None,
            "status": status,
            "mode": random.choice(['sea', 'air']),
            "weight": round(random.uniform(1000, 50000), 2),
            "volume": round(random.uniform(10, 200), 2),
            "value": round(random.uniform(50000, 1000000), 2),
            "estimated_departure": departure_date,
            "estimated_arrival": arrival_date,
            "actual_departure": departure_date if departure_date < datetime.utcnow() else None,
            "actual_arrival": arrival_date if arrival_date < datetime.utcnow() else None,
            "shipper": random.choice(["Acme Corp", "Global Exports"]),
            "carrier": random.choice(["Maersk", "MSC", "COSCO"]),
            "consignee": random.choice(["Import Co Ltd", "Retail Chain Inc"]),
            "customs_broker": random.choice(["Quick Clear", "Global Customs"]),
            "is_at_risk": random.random() > 0.7,
            "risk_score": round(random.uniform(0, 0.9), 2) if random.random() > 0.7 else 0.0,
            "last_risk_check": datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
            "shipment_metadata": json.dumps({
                "container_number": f"CONT{random.randint(1000000, 9999999)}",
                "product_type": random.choice(['electronics', 'clothing'])
            })
        }
        
        shipments.append(shipment)
    
    return shipments

async def insert_shipments(shipments: List[Dict]):
    """Insert shipments into database"""
    print(f"📦 Inserting {len(shipments)} shipments...")
    
    inserted_ids = []
    
    async with AsyncSessionLocal() as session:
        for i, shipment in enumerate(shipments, 1):
            try:
                # Build dynamic INSERT query
                columns = []
                values = []
                params = {}
                
                for key, value in shipment.items():
                    columns.append(key)
                    values.append(f":{key}")
                    params[key] = value
                
                query = text(f"""
                    INSERT INTO shipments ({', '.join(columns)})
                    VALUES ({', '.join(values)})
                    ON CONFLICT (tracking_number) DO NOTHING
                    RETURNING id
                """)
                
                result = await session.execute(query, params)
                row = result.fetchone()
                
                if row:
                    shipment_id = row[0]
                    inserted_ids.append(shipment_id)
                    print(f"  ✅ [{i}/{len(shipments)}] Inserted shipment {shipment_id}: {shipment['tracking_number']}")
                else:
                    print(f"  ⚠️ [{i}/{len(shipments)}] Skipped duplicate: {shipment['tracking_number']}")
                
            except Exception as e:
                print(f"  ❌ [{i}/{len(shipments)}] Error inserting shipment: {e}")
        
        await session.commit()
    
    print(f"✅ {len(inserted_ids)} shipments inserted/updated")
    return inserted_ids

async def simulate_risks_and_mcp(shipment_ids: List[int]):
    """Simulate risks and MCP activities"""
    print("🤖 Simulating risks and MCP activities...")
    
    if not shipment_ids:
        print("⚠️ No shipments to simulate activities for")
        return
    
    async with AsyncSessionLocal() as session:
        for shipment_id in shipment_ids[:5]:  # Simulate for first 5 shipments
            try:
                # Add MCP activity
                await session.execute(text("""
                    INSERT INTO mcp_agent_activities 
                    (agent_id, agent_type, activity_type, shipment_id, details)
                    VALUES (:agent_id, :agent_type, :activity_type, :shipment_id, :details)
                """), {
                    "agent_id": "risk_detector_01",
                    "agent_type": "risk_detector",
                    "activity_type": "shipment_monitoring",
                    "shipment_id": shipment_id,
                    "details": json.dumps({"action": "periodic_check", "result": "completed"})
                })
                
                # Add risk if shipment is at risk (50% chance)
                if random.random() > 0.5:
                    risk_types = ['port_congestion', 'customs_delay', 'weather_impact']
                    risk_data = {
                        "shipment_id": shipment_id,
                        "risk_type": random.choice(risk_types),
                        "severity": random.choice(['low', 'medium']),
                        "description": f"Potential issue detected",
                        "confidence": round(random.uniform(0.6, 0.8), 2),
                        "detected_at": datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
                        "expected_delay_hours": round(random.uniform(6, 24), 1),
                        "expected_cost_impact": round(random.uniform(1000, 5000), 2),
                        "affected_parties": json.dumps(['shipper']),
                        "mitigation_actions": json.dumps([{"action": "monitor"}]),
                        "source": "MCP Agent"
                    }
                    
                    await session.execute(text("""
                        INSERT INTO risks 
                        (shipment_id, risk_type, severity, description, confidence, 
                         detected_at, expected_delay_hours, expected_cost_impact, 
                         affected_parties, mitigation_actions, source)
                        VALUES 
                        (:shipment_id, :risk_type, :severity, :description, :confidence,
                         :detected_at, :expected_delay_hours, :expected_cost_impact,
                         :affected_parties, :mitigation_actions, :source)
                    """), risk_data)
                    
                    print(f"  ⚠️ Added risk for shipment {shipment_id}")
            
            except Exception as e:
                print(f"  ⚠️ Error simulating activities for shipment {shipment_id}: {e}")
        
        await session.commit()
    
    print("✅ Risks and MCP activities simulated")

async def print_summary():
    """Print summary of seeded data"""
    print("\n" + "="*50)
    print("📊 AIVEN POSTGRESQL SEEDING SUMMARY")
    print("="*50)
    
    async with AsyncSessionLocal() as session:
        try:
            # Count shipments
            result = await session.execute(text("SELECT COUNT(*) FROM shipments"))
            total_shipments = result.scalar()
            print(f"📦 Total shipments: {total_shipments}")
            
            # Count risks
            result = await session.execute(text("SELECT COUNT(*) FROM risks"))
            total_risks = result.scalar()
            print(f"⚠️  Total risks: {total_risks}")
            
            # Count MCP activities
            result = await session.execute(text("SELECT COUNT(*) FROM mcp_agent_activities"))
            total_activities = result.scalar()
            print(f"🤖 MCP activities: {total_activities}")
            
            # Recent shipments
            result = await session.execute(text("""
                SELECT tracking_number, status, risk_score 
                FROM shipments 
                ORDER BY created_at DESC 
                LIMIT 3
            """))
            
            print("\n📋 RECENT SHIPMENTS:")
            for row in result.fetchall():
                print(f"  {row.tracking_number}: {row.status} (risk: {row.risk_score:.2f})")
            
            print("\n✅ Seeding completed successfully!")
            
        except Exception as e:
            print(f"⚠️ Error getting summary: {e}")

async def main():
    """Main function"""
    print("="*60)
    print("🚀 AIVEN POSTGRESQL MCP DATA SEEDING")
    print("="*60)
    
    try:
        # Test connection
        print("1. Testing database connection...")
        tester = DatabaseConnectionTester()
        if not await tester.test_connection():
            print("❌ Cannot proceed without database connection")
            sys.exit(1)
        
        # Create tables safely (won't drop existing ones)
        print("\n2. Checking/creating tables...")
        if not await create_tables_safely():
            print("❌ Could not create tables")
            sys.exit(1)
        
        # Generate and insert shipments
        print("\n3. Generating and inserting shipments...")
        shipments = generate_shipment_data(8)  # Smaller batch for testing
        shipment_ids = await insert_shipments(shipments)
        
        if not shipment_ids:
            print("⚠️ No new shipments were inserted (may already exist)")
        
        # Simulate MCP activities
        print("\n4. Simulating MCP activities...")
        await simulate_risks_and_mcp(shipment_ids)
        
        # Print summary
        print("\n5. Generating summary...")
        await print_summary()
        
        print("\n" + "="*60)
        print("🎉 SUCCESS! Aiven PostgreSQL is ready for MCP system")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n🛑 Seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())