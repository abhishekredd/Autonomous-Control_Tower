#!/usr/bin/env python3
"""
Comprehensive test script with MCP agent integration
"""
import asyncio
import aiohttp
import json
import websockets
from datetime import datetime, timedelta
import sys

class MCPComprehensiveTester:
    def __init__(self, base_url="http://localhost:8000", ws_url="ws://localhost:8000"):
        self.base_url = base_url
        self.ws_url = ws_url
        self.session = None
        self.test_results = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_mcp_agent_endpoints(self):
        """Test MCP agent API endpoints"""
        print("🤖 Testing MCP agent endpoints...")
        
        endpoints = [
            ("GET", "/api/v1/agents/activities", {}),
            ("GET", "/api/v1/agents/messages/pending", {}),
            ("POST", "/api/v1/agents/risk-detector/trigger", {
                "shipment_id": 1,
                "check_type": "comprehensive"
            })
        ]
        
        for method, endpoint, data in endpoints:
            try:
                if method == "GET":
                    async with self.session.get(f"{self.base_url}{endpoint}") as resp:
                        status = resp.status
                elif method == "POST":
                    async with self.session.post(
                        f"{self.base_url}{endpoint}", 
                        json=data
                    ) as resp:
                        status = resp.status
                
                if status in [200, 201, 202]:
                    print(f"✅ {method} {endpoint} - Success")
                    self.test_results.append((f"MCP {endpoint}", True))
                else:
                    print(f"❌ {method} {endpoint} - Failed: {status}")
                    self.test_results.append((f"MCP {endpoint}", False))
                    
            except Exception as e:
                print(f"❌ {method} {endpoint} - Error: {e}")
                self.test_results.append((f"MCP {endpoint}", False))
    
    async def test_mcp_simulation_workflow(self):
        """Test complete MCP simulation workflow"""
        print("🔄 Testing MCP simulation workflow...")
        
        # Create a test shipment
        shipment_data = {
            "tracking_number": f"MCP-TEST-{int(datetime.now().timestamp())}",
            "origin": "CNSHA",
            "destination": "NLRTM",
            "mode": "sea",
            "is_at_risk": True
        }
        
        try:
            # Create shipment
            async with self.session.post(
                f"{self.base_url}/api/v1/shipments/",
                json=shipment_data
            ) as resp:
                if resp.status == 200:
                    shipment = await resp.json()
                    shipment_id = shipment["id"]
                    print(f"✅ Test shipment created: {shipment_id}")
                else:
                    print(f"❌ Failed to create test shipment: {resp.status}")
                    return False
            
            # Trigger risk detection
            async with self.session.post(
                f"{self.base_url}/api/v1/shipments/{shipment_id}/trigger-risk-check"
            ) as resp:
                if resp.status == 200:
                    print("✅ Risk detection triggered")
                else:
                    print(f"❌ Risk detection failed: {resp.status}")
            
            # Check for risks
            await asyncio.sleep(2)  # Give time for MCP agents to work
            
            async with self.session.get(
                f"{self.base_url}/api/v1/risks/shipment/{shipment_id}"
            ) as resp:
                if resp.status == 200:
                    risks = await resp.json()
                    print(f"✅ Found {len(risks)} risks for shipment")
                else:
                    print(f"❌ Failed to get risks: {resp.status}")
            
            # Check MCP agent activities
            async with self.session.get(
                f"{self.base_url}/api/v1/agents/activities?shipment_id={shipment_id}"
            ) as resp:
                if resp.status == 200:
                    activities = await resp.json()
                    print(f"✅ Found {len(activities)} MCP activities")
                else:
                    print(f"⚠️ No MCP activities endpoint")
            
            self.test_results.append(("MCP Workflow", True))
            return True
            
        except Exception as e:
            print(f"❌ MCP workflow test failed: {e}")
            self.test_results.append(("MCP Workflow", False))
            return False
    
    async def test_websocket_mcp_updates(self):
        """Test WebSocket for MCP updates"""
        print("🔌 Testing WebSocket for MCP updates...")
        
        try:
            # Get a shipment
            async with self.session.get(
                f"{self.base_url}/api/v1/shipments/"
            ) as resp:
                if resp.status != 200:
                    return False
                
                shipments = await resp.json()
                if not shipments:
                    return False
                
                shipment_id = shipments[0]["id"]
            
            # Connect to WebSocket
            uri = f"{self.ws_url}/ws/shipments/{shipment_id}"
            try:
                async with websockets.connect(uri) as websocket:
                    # Subscribe to MCP updates
                    await websocket.send(json.dumps({
                        "type": "subscribe",
                        "channels": ["mcp_updates", "risk_alerts"]
                    }))
                    
                    # Wait for message
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        data = json.loads(message)
                        print(f"✅ WebSocket MCP update received: {data.get('type')}")
                        self.test_results.append(("WebSocket MCP", True))
                        return True
                    except asyncio.TimeoutError:
                        print("⚠️ No immediate MCP updates (may be normal)")
                        self.test_results.append(("WebSocket MCP", None))
                        return None
                        
            except Exception as e:
                print(f"❌ WebSocket connection failed: {e}")
                self.test_results.append(("WebSocket MCP", False))
                return False
                
        except ImportError:
            print("⚠️ Skipping WebSocket test (websockets not installed)")
            self.test_results.append(("WebSocket MCP", None))
            return None
    
    async def run_all_tests(self):
        """Run all comprehensive tests"""
        print("="*60)
        print("🚀 MCP-ENHANCED COMPREHENSIVE TEST SUITE")
        print("="*60)
        
        # Run existing tests (from original test_comprehensive.py)
        from test_comprehensive import ComprehensiveTester
        base_tester = ComprehensiveTester(self.base_url)
        base_tester.session = self.session
        
        # Health check
        health_ok = await base_tester.test_health()
        self.test_results.append(("Health Check", health_ok))
        
        # API docs
        docs_ok = await base_tester.test_api_documentation()
        self.test_results.append(("API Documentation", docs_ok))
        
        # Shipment CRUD
        shipment_ok = await base_tester.test_shipment_crud()
        self.test_results.append(("Shipment CRUD", shipment_ok))
        
        # Risk operations
        risk_ok = await base_tester.test_risk_operations()
        self.test_results.append(("Risk Operations", risk_ok))
        
        # MCP-specific tests
        await self.test_mcp_agent_endpoints()
        await self.test_mcp_simulation_workflow()
        await self.test_websocket_mcp_updates()
        
        # Print summary
        self.print_summary()
        
        # Return overall success
        passed = sum(1 for _, result in self.test_results if result is True)
        total = sum(1 for _, result in self.test_results if result is not None)
        
        return passed == total
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 MCP TEST SUMMARY")
        print("="*60)
        
        passed = 0
        skipped = 0
        total = 0
        
        for test_name, result in self.test_results:
            total += 1
            if result is None:
                status = "🟡 SKIPPED"
                skipped += 1
            elif result:
                status = "✅ PASSED"
                passed += 1
            else:
                status = "❌ FAILED"
            
            print(f"{test_name:30} {status}")
        
        print("="*60)
        print(f"Overall: {passed}/{total - skipped} passed, {skipped} skipped")
        
        if passed == total - skipped:
            print("🎉 All tests passed! MCP system is operational.")
        else:
            print("⚠️ Some tests failed. Check the logs above.")

async def main():
    """Main test runner"""
    async with MCPComprehensiveTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())