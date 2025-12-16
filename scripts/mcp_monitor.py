#!/usr/bin/env python3
"""
MCP Agent Monitor - Real-time monitoring of MCP agents
"""
import asyncio
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import websockets
import aiohttp

class MCPMonitor:
    def __init__(self):
        self.db_config = {
            "dbname": "control_tower_db",
            "user": "control_tower_user",
            "password": "password",
            "host": "localhost",
            "port": "5432"
        }
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
    async def monitor_agent_health(self):
        """Monitor health of MCP agents"""
        print("🏥 Monitoring MCP Agent Health...")
        
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check recent agent activities
                cur.execute("""
                    SELECT 
                        agent_type,
                        COUNT(*) as activity_count,
                        MAX(created_at) as last_activity,
                        COUNT(DISTINCT shipment_id) as active_shipments
                    FROM mcp_agent_activities
                    WHERE created_at > NOW() - INTERVAL '1 hour'
                    GROUP BY agent_type
                    ORDER BY last_activity DESC
                """)
                
                agents = cur.fetchall()
                
                print("\n🤖 MCP AGENT STATUS (Last Hour)")
                print("-" * 60)
                for agent in agents:
                    status = "✅ ACTIVE" if agent['activity_count'] > 0 else "⚠️  INACTIVE"
                    print(f"{agent['agent_type']:25} {status:15} "
                          f"Activities: {agent['activity_count']:3} | "
                          f"Last: {agent['last_activity'].strftime('%H:%M:%S')}")
    
    async def monitor_message_queue(self):
        """Monitor MCP message queue"""
        print("\n📨 Monitoring MCP Message Queue...")
        
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check pending messages
                cur.execute("""
                    SELECT 
                        recipient_agent,
                        message_type,
                        COUNT(*) as pending_count,
                        MIN(created_at) as oldest_pending
                    FROM mcp_messages
                    WHERE status = 'pending'
                    GROUP BY recipient_agent, message_type
                    ORDER BY pending_count DESC
                """)
                
                messages = cur.fetchall()
                
                if messages:
                    print("⏳ PENDING MESSAGES")
                    print("-" * 60)
                    for msg in messages:
                        age = (datetime.now() - msg['oldest_pending']).total_seconds() / 60
                        print(f"{msg['recipient_agent']:20} → {msg['message_type']:25} "
                              f"Count: {msg['pending_count']:3} | "
                              f"Oldest: {age:.1f} min ago")
                else:
                    print("✅ No pending messages")
    
    async def monitor_risk_detection_rate(self):
        """Monitor risk detection performance"""
        print("\n⚠️  Monitoring Risk Detection...")
        
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Risk detection stats
                cur.execute("""
                    SELECT 
                        DATE_TRUNC('hour', r.detected_at) as detection_hour,
                        COUNT(*) as risks_detected,
                        AVG(CASE WHEN r.severity = 'critical' THEN 1 ELSE 0 END) * 100 as pct_critical,
                        AVG(r.confidence) as avg_confidence
                    FROM risks r
                    WHERE r.detected_at > NOW() - INTERVAL '24 hours'
                    GROUP BY DATE_TRUNC('hour', r.detected_at)
                    ORDER BY detection_hour DESC
                    LIMIT 6
                """)
                
                stats = cur.fetchall()
                
                if stats:
                    print("📊 RISK DETECTION (Last 6 hours)")
                    print("-" * 60)
                    for stat in stats:
                        print(f"{stat['detection_hour'].strftime('%H:%M'):10} | "
                              f"Risks: {stat['risks_detected']:3} | "
                              f"Critical: {stat['pct_critical']:5.1f}% | "
                              f"Confidence: {stat['avg_confidence']:.2f}")
    
    async def monitor_system_performance(self):
        """Monitor overall system performance"""
        print("\n📈 Monitoring System Performance...")
        
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # System performance metrics
                cur.execute("""
                    SELECT 
                        'Shipments' as metric,
                        COUNT(*) as value,
                        AVG(risk_score) * 100 as avg_risk_score
                    FROM shipments
                    WHERE created_at > NOW() - INTERVAL '1 hour'
                    UNION ALL
                    SELECT 
                        'Risks Detected',
                        COUNT(*),
                        AVG(confidence) * 100
                    FROM risks
                    WHERE detected_at > NOW() - INTERVAL '1 hour'
                    UNION ALL
                    SELECT 
                        'MCP Activities',
                        COUNT(*),
                        0
                    FROM mcp_agent_activities
                    WHERE created_at > NOW() - INTERVAL '1 hour'
                    UNION ALL
                    SELECT 
                        'Active Agents',
                        COUNT(DISTINCT agent_type),
                        0
                    FROM mcp_agent_activities
                    WHERE created_at > NOW() - INTERVAL '5 minutes'
                """)
                
                metrics = cur.fetchall()
                
                print("📊 SYSTEM METRICS (Last Hour)")
                print("-" * 60)
                for metric in metrics:
                    print(f"{metric['metric']:20} {metric['value']:10,} "
                          f"{'Score: ' + str(metric['avg_risk_score']) + '%' if metric['avg_risk_score'] else ''}")
    
    async def monitor_redis_channels(self):
        """Monitor Redis channels for MCP communication"""
        print("\n📡 Monitoring Redis MCP Channels...")
        
        try:
            # Check Redis connection
            if self.redis_client.ping():
                print("✅ Redis connected")
                
                # Get Redis info
                info = self.redis_client.info()
                print(f"   Uptime: {info['uptime_in_days']} days")
                print(f"   Memory: {info['used_memory_human']}")
                print(f"   Connections: {info['connected_clients']}")
                
                # Check for active channels (simplified)
                pattern = "agent:*"
                channels = []
                for key in self.redis_client.scan_iter(match=pattern):
                    if self.redis_client.type(key) == b'stream':
                        channels.append(key.decode())
                
                if channels:
                    print(f"   Active MCP channels: {len(channels)}")
                    for channel in channels[:5]:  # Show first 5
                        print(f"     - {channel}")
                    if len(channels) > 5:
                        print(f"     ... and {len(channels) - 5} more")
                else:
                    print("   No active MCP channels")
            else:
                print("❌ Redis not connected")
                
        except Exception as e:
            print(f"❌ Redis monitoring failed: {e}")
    
    async def run_monitoring_loop(self, interval_seconds=30):
        """Run continuous monitoring"""
        print("🚀 Starting MCP System Monitor")
        print("="*60)
        
        try:
            while True:
                await self.monitor_agent_health()
                await self.monitor_message_queue()
                await self.monitor_risk_detection_rate()
                await self.monitor_system_performance()
                await self.monitor_redis_channels()
                
                print("\n" + "="*60)
                print(f"⏰ Next update in {interval_seconds} seconds...")
                print("="*60 + "\n")
                
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"❌ Monitoring error: {e}")

async def main():
    """Main monitoring function"""
    monitor = MCPMonitor()
    await monitor.run_monitoring_loop(interval_seconds=30)

if __name__ == "__main__":
    asyncio.run(main())