import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

# Test database
SQLALCHEMY_DATABASE_URL = "postgresql://test:test@localhost/test_control_tower"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Test client
client = TestClient(app)

# Test data
test_shipment_data = {
    "tracking_number": "TEST12345",
    "reference_number": "TEST-SH-001",
    "origin": "Test Origin",
    "destination": "Test Destination",
    "mode": "sea",
    "weight": 1000.0,
    "volume": 10.0,
    "value": 50000.0,
    "estimated_departure": "2024-01-01T00:00:00Z",
    "estimated_arrival": "2024-01-15T00:00:00Z",
    "shipper": "Test Shipper",
    "carrier": "Test Carrier",
    "consignee": "Test Consignee"
}

test_risk_data = {
    "shipment_id": 1,
    "risk_type": "port_congestion",
    "severity": "high",
    "description": "Test risk description",
    "confidence": 0.85,
    "expected_delay_hours": 24.0,
    "expected_cost_impact": 5000.0
}

test_simulation_data = {
    "shipment_id": 1,
    "simulation_type": "mitigation_analysis",
    "parameters": {"test": "data"},
    "scenario_description": "Test simulation scenario"
}

class TestShipmentsAPI:
    """Test shipment API endpoints"""
    
    def setup_method(self):
        """Setup test database"""
        Base.metadata.create_all(bind=engine)
    
    def teardown_method(self):
        """Cleanup test database"""
        Base.metadata.drop_all(bind=engine)
    
    def test_create_shipment(self):
        """Test creating a shipment"""
        response = client.post("/api/v1/shipments/", json=test_shipment_data)
        assert response.status_code == 200
        data = response.json()
        assert data["tracking_number"] == test_shipment_data["tracking_number"]
        assert data["status"] == "pending"
        assert "id" in data
    
    def test_get_shipments(self):
        """Test getting shipments"""
        # First create a shipment
        client.post("/api/v1/shipments/", json=test_shipment_data)
        
        response = client.get("/api/v1/shipments/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_shipment_by_id(self):
        """Test getting a specific shipment"""
        # Create a shipment
        create_response = client.post("/api/v1/shipments/", json=test_shipment_data)
        shipment_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/shipments/{shipment_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == shipment_id
        assert data["tracking_number"] == test_shipment_data["tracking_number"]
    
    def test_update_shipment(self):
        """Test updating a shipment"""
        # Create a shipment
        create_response = client.post("/api/v1/shipments/", json=test_shipment_data)
        shipment_id = create_response.json()["id"]
        
        update_data = {
            "current_location": "Updated Location",
            "status": "in_transit"
        }
        
        response = client.put(f"/api/v1/shipments/{shipment_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["current_location"] == update_data["current_location"]
        assert data["status"] == update_data["status"]
    
    def test_trigger_risk_check(self):
        """Test triggering risk check"""
        # Create a shipment
        create_response = client.post("/api/v1/shipments/", json=test_shipment_data)
        shipment_id = create_response.json()["id"]
        
        response = client.post(f"/api/v1/shipments/{shipment_id}/trigger-risk-check")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "successfully" in data["message"].lower()

class TestRisksAPI:
    """Test risk API endpoints"""
    
    def setup_method(self):
        """Setup test database"""
        Base.metadata.create_all(bind=engine)
        
        # Create a shipment first
        response = client.post("/api/v1/shipments/", json=test_shipment_data)
        self.shipment_id = response.json()["id"]
        
        # Update test risk data with shipment ID
        self.test_risk = test_risk_data.copy()
        self.test_risk["shipment_id"] = self.shipment_id
    
    def teardown_method(self):
        """Cleanup test database"""
        Base.metadata.drop_all(bind=engine)
    
    def test_create_risk(self):
        """Test creating a risk"""
        response = client.post("/api/v1/risks/", json=self.test_risk)
        assert response.status_code == 201
        data = response.json()
        assert data["shipment_id"] == self.shipment_id
        assert data["risk_type"] == self.test_risk["risk_type"]
        assert data["severity"] == self.test_risk["severity"]
    
    def test_get_risks(self):
        """Test getting risks"""
        # First create a risk
        client.post("/api/v1/risks/", json=self.test_risk)
        
        response = client.get("/api/v1/risks/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_shipment_risks(self):
        """Test getting risks for a shipment"""
        # Create a risk
        client.post("/api/v1/risks/", json=self.test_risk)
        
        response = client.get(f"/api/v1/risks/shipment/{self.shipment_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(r["shipment_id"] == self.shipment_id for r in data)
    
    def test_update_risk(self):
        """Test updating a risk"""
        # Create a risk
        create_response = client.post("/api/v1/risks/", json=self.test_risk)
        risk_id = create_response.json()["id"]
        
        update_data = {
            "status": "resolved",
            "mitigation_actions": [{"action": "test", "result": "success"}]
        }
        
        response = client.put(f"/api/v1/risks/{risk_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == update_data["status"]
    
    def test_mitigate_risk(self):
        """Test applying mitigation to a risk"""
        # Create a risk
        create_response = client.post("/api/v1/risks/", json=self.test_risk)
        risk_id = create_response.json()["id"]
        
        mitigation_data = {
            "action": "reroute",
            "parameters": {"alternative_port": "TEST"},
            "expected_result": "delay_reduction"
        }
        
        response = client.post(f"/api/v1/risks/{risk_id}/mitigate", json=mitigation_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "mitigation" in data["message"].lower()

class TestSimulationsAPI:
    """Test simulation API endpoints"""
    
    def setup_method(self):
        """Setup test database"""
        Base.metadata.create_all(bind=engine)
        
        # Create a shipment first
        response = client.post("/api/v1/shipments/", json=test_shipment_data)
        self.shipment_id = response.json()["id"]
        
        # Update test simulation data with shipment ID
        self.test_simulation = test_simulation_data.copy()
        self.test_simulation["shipment_id"] = self.shipment_id
    
    def teardown_method(self):
        """Cleanup test database"""
        Base.metadata.drop_all(bind=engine)
    
    def test_create_simulation(self):
        """Test creating a simulation"""
        response = client.post("/api/v1/simulations/", json=self.test_simulation)
        assert response.status_code == 200
        data = response.json()
        assert data["shipment_id"] == self.shipment_id
        assert data["simulation_type"] == self.test_simulation["simulation_type"]
        assert data["status"] == "pending"
    
    def test_get_shipment_simulations(self):
        """Test getting simulations for a shipment"""
        # Create a simulation
        client.post("/api/v1/simulations/", json=self.test_simulation)
        
        response = client.get(f"/api/v1/simulations/shipment/{self.shipment_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(s["shipment_id"] == self.shipment_id for s in data)
    
    def test_rerun_simulation(self):
        """Test rerunning a simulation"""
        # Create a simulation
        create_response = client.post("/api/v1/simulations/", json=self.test_simulation)
        simulation_id = create_response.json()["id"]
        
        response = client.post(f"/api/v1/simulations/{simulation_id}/rerun")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "rerun" in data["message"].lower()
        assert simulation_id == data["simulation_id"]

class TestHealthAPI:
    """Test health check endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "control tower" in data["message"].lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])