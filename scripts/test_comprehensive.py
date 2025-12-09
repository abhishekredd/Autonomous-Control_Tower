#!/usr/bin/env python3
"""
Comprehensive test script for Autonomous Control Tower
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import sys

class ComprehensiveTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health(self):
        """Test health endpoint"""
        print("🩺 Testing health endpoint...")
        async with self.session.get(f"{self.base_url}/health") as response:
            data = await response.json()
            if data.get("status") == "healthy":
                print("✅ Health check passed")
                return True
            else:
                print("❌ Health check failed")
                return False
    
    async def test_api_documentation(self):
        """Test API documentation endpoints"""
        print("📚 Testing API documentation...")
        
        endpoints = ["/docs", "/redoc", "/openapi.json"]
        results = []
        
        for endpoint in endpoints:
            async with self.session.get(f"{self.base_url}{endpoint}") as response:
                if response.status == 200:
                    print(f"✅ {endpoint} accessible")
                    results.append(True)
                else:
                    print(f"❌ {endpoint} not accessible")
                    results.append(False)
        
        return all(results)
    
    async def test_shipment_crud(self):
        """Test shipment CRUD operations"""
        print("🚢 Testing shipment CRUD operations...")
        
        # Create shipment
        shipment_data = {
            "tracking_number": f"TEST-{int(datetime.now().timestamp())}",
            "reference_number": "CRUD-TEST-001",
            "origin": "Test Origin",
            "destination": "Test Destination",
            "mode": "sea",
            "weight": 10000.0,
            "volume": 25.0,
            "value": 100000.0,
            "estimated_departure": datetime.utcnow().isoformat(),
            "estimated_arrival": (datetime.utcnow() + asyncio.timedelta(days=14)).isoformat(),
            "shipper": "Test Shipper Corp",
            "carrier": "Test Carrier Line",
            "consignee": "Test Consignee Ltd"
        }
        
        async with self.session.post(
            f"{self.base_url}/api/v1/shipments/",
            json=shipment_data
        ) as response:
            if response.status == 200:
                created_shipment = await response.json()
                shipment_id = created_shipment["id"]
                print(f"✅ Shipment created (ID: {shipment_id})")
            else:
                print(f"❌ Failed to create shipment: {response.status}")
                return False
        
        # Read shipment
        async with self.session.get(
            f"{self.base_url}/api/v1/shipments/{shipment_id}"
        ) as response:
            if response.status == 200:
                read_shipment = await response.json()
                if read_shipment["tracking_number"] == shipment_data["tracking_number"]:
                    print("✅ Shipment read successfully")
                else:
                    print("❌ Shipment read mismatch")
                    return False
            else:
                print(f"❌ Failed to read shipment: {response.status}")
                return False
        
        # Update shipment
        update_data = {
            "current_location": "Updated Location",
            "status": "in_transit"
        }
        
        async with self.session.put(
            f"{self.base_url}/api/v1/shipments/{shipment_id}",
            json=update_data
        ) as response:
            if response.status == 200:
                updated_shipment = await response.json()
                if updated_shipment["current_location"] == update_data["current_location"]:
                    print("✅ Shipment updated successfully")
                else:
                    print("❌ Shipment update mismatch")
                    return False
            else:
                print(f"❌ Failed to update shipment: {response.status}")
                return False
        
        # List shipments
        async with self.session.get(
            f"{self.base_url}/api/v1/shipments/"
        ) as response:
            if response.status == 200:
                shipments = await response.json()
                if isinstance(shipments, list):
                    print(f"✅ Listed {len(shipments)} shipments")
                else:
                    print("❌ Invalid shipments list format")
                    return False
            else:
                print(f"❌ Failed to list shipments: {response.status}")
                return False
        
        # Test risk check trigger
        async with self.session.post(
            f"{self.base_url}/api/v1/shipments/{shipment_id}/trigger-risk-check"
        ) as response:
            if response.status == 200:
                print("✅ Risk check triggered")
            else:
                print(f"❌ Failed to trigger risk check: {response.status}")
        
        return True
    
    async def test_risk_operations(self):
        """Test risk operations"""
        print("⚠️ Testing risk operations...")
        
        # First, get a shipment to associate with risk
        async with self.session.get(
            f"{self.base_url}/api/v1/shipments/"
        ) as response:
            if response.status != 200:
                print("❌ Need a shipment first")
                return False
            
            shipments = await response.json()
            if not shipments:
                print("❌ No shipments available")
                return False
            
            shipment_id = shipments[0]["id"]
        
        # Create a risk
        risk_data = {
            "shipment_id": shipment_id,
            "risk_type": "port_congestion",
            "severity": "high",
            "description": "Test risk for automated testing",
            "confidence": 0.85,
            "expected_delay_hours": 24.0,
            "expected_cost_impact": 5000.0
        }
        
        async with self.session.post(
            f"{self.base_url}/api/v1/risks/",
            json=risk_data
        ) as response:
            if response.status == 201:
                created_risk = await response.json()
                risk_id = created_risk["id"]
                print(f"✅ Risk created (ID: {risk_id})")
            else:
                print(f"❌ Failed to create risk: {response.status}")
                return False
        
        # List risks
        async with self.session.get(
            f"{self.base_url}/api/v1/risks/"
        ) as response:
            if response.status == 200:
                risks = await response.json()
                print(f"✅ Listed {len(risks)} risks")
            else:
                print(f"❌ Failed to list risks: {response.status}")
        
        # Get risks for shipment
        async with self.session.get(
            f"{self.base_url}/api/v1/risks/shipment/{shipment_id}"
        ) as response:
            if response.status == 200:
                shipment_risks = await response.json()
                print(f"✅ Got {len(shipment_risks)} risks for shipment")
            else:
                print(f"❌ Failed to get shipment risks: {response.status}")
        
        return True
    
    async def test_simulation_operations(self):
        """Test simulation operations"""
        print("🔮 Testing simulation operations...")
        
        # Get a shipment
        async with self.session.get(
            f"{self.base_url}/api/v1/shipments/"
        ) as response:
            if response.status != 200:
                return False
            
            shipments = await response.json()
            if not shipments:
                print("❌ No shipments available")
                return False
            
            shipment_id = shipments[0]["id"]
        
        # Create simulation
        simulation_data = {
            "shipment_id": shipment_id,
            "simulation_type": "mitigation_analysis",
            "parameters": {
                "risk_type": "port_congestion",
                "scenario": "what_if_analysis"
            },
            "scenario_description": "Test simulation scenario"
        }
        
        async with self.session.post(
            f"{self.base_url}/api/v1/simulations/",
            json=simulation_data
        ) as response:
            if response.status == 200:
                simulation = await response.json()
                print(f"✅ Simulation created (ID: {simulation['id']})")
            else:
                print(f"❌ Failed to create simulation: {response.status}")
                return False
        
        return True
    
    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        print("🔌 Testing WebSocket connection...")
        
        try:
            # This is a basic test - actual WebSocket testing would need websockets library
            import websockets
            
            # Get a shipment ID first
            async with self.session.get(
                f"{self.base_url}/api/v1/shipments/"
            ) as response:
                if response.status != 200:
                    return False
                
                shipments = await response.json()
                if not shipments:
                    return False
                
                shipment_id = shipments[0]["id"]
            
            # Try to connect to WebSocket
            ws_url = f"ws://localhost:8000/ws/shipments/{shipment_id}"
            try:
                async with websockets.connect(ws_url) as websocket:
                    # Send a test message
                    await websocket.send(json.dumps({"type": "test"}))
                    
                    # Try to receive (with timeout)
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        print(f"✅ WebSocket connected and received: {message[:100]}...")
                        return True
                    except asyncio.TimeoutError:
                        print("⚠️ WebSocket connected but no message received (might be normal)")
                        return True
                    
            except Exception as e:
                print(f"❌ WebSocket connection failed: {e}")
                return False
                
        except ImportError:
            print("⚠️ Skipping WebSocket test (websockets library not installed)")
            print("   Install with: pip install websockets")
            return None
    
    async def run_all_tests(self):
        """Run all comprehensive tests"""
        print("="*60)
        print("🚀 COMPREHENSIVE BACKEND TEST SUITE")
        print("="*60)
        
        test_results = []
        
        # Health check
        health_ok = await self.test_health()
        test_results.append(("Health Check", health_ok))
        
        # API documentation
        docs_ok = await self.test_api_documentation()
        test_results.append(("API Documentation", docs_ok))
        
        # Shipment CRUD
        shipment_ok = await self.test_shipment_crud()
        test_results.append(("Shipment CRUD", shipment_ok))
        
        # Risk operations
        risk_ok = await self.test_risk_operations()
        test_results.append(("Risk Operations", risk_ok))
        
        # Simulation operations
        simulation_ok = await self.test_simulation_operations()
        test_results.append(("Simulation Operations", simulation_ok))
        
        # WebSocket (optional)
        ws_result = await self.test_websocket_connection()
        test_results.append(("WebSocket Connection", ws_result))
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = 0
        total = 0
        
        for test_name, result in test_results:
            total += 1
            if result is None:
                status = "SKIPPED"
            elif result:
                status = "✅ PASSED"
                passed += 1
            else:
                status = "❌ FAILED"
            
            print(f"{test_name:25} {status}")
        
        print("="*60)
        print(f"Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Backend is ready.")
            return True
        else:
            print("⚠️ Some tests failed. Check the logs above.")
            return False

async def main():
    """Main test runner"""
    async with ComprehensiveTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())