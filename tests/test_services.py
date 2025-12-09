import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.shipment_service import ShipmentService
from app.services.risk_service import RiskService
from app.services.simulation_service import SimulationService
from app.services.orchestrator import CentralOrchestrator
from app.schemas.shipment import ShipmentCreate
from app.schemas.risk import RiskCreate
from app.models.shipment import Shipment, ShipmentStatus, ShipmentMode
from app.models.risk import Risk, RiskType, RiskSeverity, RiskStatus

class TestShipmentService:
    """Test shipment service functionality"""
    
    @pytest.mark.asyncio
    async def test_create_shipment(self):
        """Test creating a shipment"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        service = ShipmentService()
        shipment_data = ShipmentCreate(
            tracking_number="TEST123",
            reference_number="TEST-SH-001",
            origin="Test Origin",
            destination="Test Destination",
            mode=ShipmentMode.SEA,
            weight=1000.0,
            volume=10.0,
            value=50000.0,
            estimated_departure=datetime.utcnow(),
            estimated_arrival=datetime.utcnow() + timedelta(days=14),
            shipper="Test Shipper",
            carrier="Test Carrier",
            consignee="Test Consignee"
        )
        
        with patch('app.core.redis.redis_client.publish', new_callable=AsyncMock) as mock_publish:
            result = await service.create_shipment(shipment_data, mock_session)
            
            assert isinstance(result, Shipment)
            assert result.tracking_number == shipment_data.tracking_number
            assert result.status == ShipmentStatus.PENDING
            mock_session.add.assert_called()
            mock_session.commit.assert_called_once()
            mock_publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_shipment(self):
        """Test getting a shipment"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_shipment = Shipment(
            id=1,
            tracking_number="TEST123",
            status=ShipmentStatus.IN_TRANSIT
        )
        
        mock_session.get = AsyncMock(return_value=mock_shipment)
        
        service = ShipmentService()
        result = await service.get_shipment(1, mock_session)
        
        assert result == mock_shipment
        mock_session.get.assert_called_once_with(Shipment, 1)
    
    @pytest.mark.asyncio
    async def test_update_shipment_location(self):
        """Test updating shipment location"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_shipment = Shipment(
            id=1,
            tracking_number="TEST123",
            current_location="Old Location"
        )
        
        mock_session.get = AsyncMock(return_value=mock_shipment)
        mock_session.commit = AsyncMock()
        
        service = ShipmentService()
        
        with patch('app.core.redis.redis_client.publish', new_callable=AsyncMock) as mock_publish:
            result = await service.update_shipment_location(
                shipment_id=1,
                location="New Location",
                port="TEST",
                session=mock_session
            )
            
            assert result is True
            assert mock_shipment.current_location == "New Location"
            assert mock_shipment.current_port == "TEST"
            mock_session.commit.assert_called_once()
            mock_publish.assert_called_once()

class TestRiskService:
    """Test risk service functionality"""
    
    @pytest.mark.asyncio
    async def test_detect_risks_port_congestion(self):
        """Test detecting port congestion risks"""
        mock_session = AsyncMock(spec=AsyncSession)
        
        shipment = Shipment(
            id=1,
            next_port="CNSHA",  # Shanghai - high congestion
            metadata={}
        )
        
        mock_session.get = AsyncMock(return_value=shipment)
        
        service = RiskService()
        
        with patch.object(service, '_get_congestion_level', new_callable=AsyncMock) as mock_congestion:
            mock_congestion.return_value = 0.8  # High congestion
            
            risks = await service.detect_risks(1, mock_session)
            
            assert len(risks) > 0
            assert any(r.risk_type == "port_congestion" for r in risks)
            assert any(r.severity == RiskSeverity.HIGH for r in risks)
    
    @pytest.mark.asyncio
    async def test_detect_risks_customs_delay(self):
        """Test detecting customs delay risks"""
        mock_session = AsyncMock(spec=AsyncSession)
        
        shipment = Shipment(
            id=1,
            metadata={"customs_status": "delayed"}
        )
        
        mock_session.get = AsyncMock(return_value=shipment)
        
        service = RiskService()
        risks = await service.detect_risks(1, mock_session)
        
        assert len(risks) > 0
        assert any(r.risk_type == "customs_delay" for r in risks)
        assert any(r.severity == RiskSeverity.HIGH for r in risks)
    
    @pytest.mark.asyncio
    async def test_detect_risks_quality_hold(self):
        """Test detecting quality hold risks"""
        mock_session = AsyncMock(spec=AsyncSession)
        
        shipment = Shipment(
            id=1,
            metadata={"quality_status": "hold"}
        )
        
        mock_session.get = AsyncMock(return_value=shipment)
        
        service = RiskService()
        risks = await service.detect_risks(1, mock_session)
        
        assert len(risks) > 0
        assert any(r.risk_type == "quality_hold" for r in risks)
        assert any(r.severity == RiskSeverity.MEDIUM for r in risks)
    
    @pytest.mark.asyncio
    async def test_detect_risks_delay(self):
        """Test detecting delay risks"""
        mock_session = AsyncMock(spec=AsyncSession)
        
        shipment = Shipment(
            id=1,
            estimated_arrival=datetime.utcnow() - timedelta(hours=6)  # 6 hours late
        )
        
        mock_session.get = AsyncMock(return_value=shipment)
        
        service = RiskService()
        risks = await service.detect_risks(1, mock_session)
        
        assert len(risks) > 0
        assert any(r.risk_type == "other" for r in risks)  # Delay is "other" type
        assert any(r.severity == RiskSeverity.MEDIUM for r in risks)

class TestSimulationService:
    """Test simulation service functionality"""
    
    @pytest.mark.asyncio
    async def test_simulate_mitigations(self):
        """Test simulating mitigation options"""
        mock_session = AsyncMock(spec=AsyncSession)
        
        risk = Risk(
            id=1,
            risk_type=RiskType.PORT_CONGESTION,
            severity=RiskSeverity.HIGH
        )
        
        shipment = Shipment(
            id=1,
            next_port="CNSHA"
        )
        
        mock_session.get = AsyncMock(side_effect=[risk, shipment])
        
        service = SimulationService()
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            results = await service.simulate_mitigations(1, 1)
            
            assert isinstance(results, list)
            assert len(results) > 0
            
            # Check structure of results
            for result in results:
                assert "scenario_name" in result
                assert "action_type" in result
                assert "cost_impact" in result
                assert "time_impact" in result
                assert "risk_reduction" in result
                assert "overall_score" in result
    
    @pytest.mark.asyncio
    async def test_generate_mitigation_scenarios(self):
        """Test generating mitigation scenarios"""
        service = SimulationService()
        
        # Test port congestion scenarios
        scenarios = service._generate_mitigation_scenarios(
            "port_congestion", "high", 1
        )
        
        assert isinstance(scenarios, list)
        assert len(scenarios) > 0
        
        for scenario in scenarios:
            assert "id" in scenario
            assert "name" in scenario
            assert "type" in scenario
            assert "description" in scenario
            assert "parameters" in scenario
        
        # Test customs delay scenarios
        scenarios = service._generate_mitigation_scenarios(
            "customs_delay", "medium", 1
        )
        assert len(scenarios) > 0
        
        # Test quality hold scenarios
        scenarios = service._generate_mitigation_scenarios(
            "quality_hold", "low", 1
        )
        assert len(scenarios) > 0

class TestCentralOrchestrator:
    """Test central orchestrator functionality"""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test orchestrator initialization"""
        orchestrator = CentralOrchestrator()
        
        with patch('app.core.redis.redis_client.subscribe', new_callable=AsyncMock) as mock_subscribe:
            await orchestrator.initialize()
            
            # Check that subscriptions were set up
            assert mock_subscribe.call_count >= 1
            
            # Check that monitoring loops were started
            assert hasattr(orchestrator, 'active_shipments')
    
    @pytest.mark.asyncio
    async def test_check_delays(self):
        """Test checking for shipment delays"""
        orchestrator = CentralOrchestrator()
        
        shipment_id = 1
        shipment_data = {
            "estimated_arrival": datetime.utcnow() - timedelta(hours=6),  # 6 hours late
            "current_location": "Test Location",
            "next_port": "TEST",
            "metadata": {}
        }
        
        with patch.object(orchestrator, '_create_risk', new_callable=AsyncMock) as mock_create_risk:
            await orchestrator._check_delays(shipment_id, shipment_data)
            
            # Should create a risk for 6-hour delay
            mock_create_risk.assert_called_once()
            args = mock_create_risk.call_args[1]
            assert args["shipment_id"] == shipment_id
            assert args["risk_type"] == RiskType.OTHER
            assert args["severity"] in [RiskSeverity.MEDIUM, RiskSeverity.HIGH]
    
    @pytest.mark.asyncio
    async def test_check_port_congestion(self):
        """Test checking port congestion"""
        orchestrator = CentralOrchestrator()
        
        shipment_id = 1
        port_code = "CNSHA"  # Shanghai - high congestion
        
        with patch.object(orchestrator, '_get_port_congestion_level', 
                         new_callable=AsyncMock) as mock_congestion:
            mock_congestion.return_value = 0.8  # High congestion
            
            with patch.object(orchestrator, '_create_risk', 
                            new_callable=AsyncMock) as mock_create_risk:
                await orchestrator._check_port_congestion(shipment_id, port_code)
                
                # Should create a port congestion risk
                mock_create_risk.assert_called_once()
                args = mock_create_risk.call_args[1]
                assert args["shipment_id"] == shipment_id
                assert args["risk_type"] == RiskType.PORT_CONGESTION
                assert args["severity"] == RiskSeverity.HIGH
    
    @pytest.mark.asyncio
    async def test_handle_new_risk(self):
        """Test handling a newly detected risk"""
        orchestrator = CentralOrchestrator()
        
        risk_id = 1
        shipment_id = 1
        
        # Mock simulation results
        mock_simulation_results = [
            {
                "scenario_name": "Test Scenario",
                "action_type": "reroute",
                "overall_score": 0.85,
                "confidence": 0.9
            }
        ]
        
        with patch.object(orchestrator.simulation_service, 'simulate_mitigations',
                         new_callable=AsyncMock) as mock_simulate:
            mock_simulate.return_value = mock_simulation_results
            
            with patch.object(orchestrator.action_service, 'execute_action',
                            new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {"success": True}
                
                with patch.object(orchestrator.communication_service, 'notify_stakeholders',
                                new_callable=AsyncMock) as mock_notify:
                    
                    await orchestrator._handle_new_risk(risk_id, shipment_id)
                    
                    # Should simulate mitigations
                    mock_simulate.assert_called_once_with(
                        shipment_id=shipment_id,
                        risk_id=risk_id
                    )
                    
                    # Should execute action (confidence > 0.7)
                    mock_execute.assert_called_once()
                    
                    # Should notify stakeholders
                    mock_notify.assert_called_once()

@pytest.mark.asyncio
async def test_geocoding_utils():
    """Test geocoding utility functions"""
    from app.utils.geocoding import calculate_distance, geocoding_service
    
    # Test distance calculation
    point1 = (31.2304, 121.4737)  # Shanghai
    point2 = (51.9244, 4.4777)    # Rotterdam
    
    distance = calculate_distance(point1, point2)
    assert isinstance(distance, float)
    assert distance > 0
    
    # Test port coordinates
    port_coords = await geocoding_service.get_port_coordinates("CNSHA")
    assert port_coords is not None
    assert len(port_coords) == 2
    assert all(isinstance(coord, float) for coord in port_coords)

@pytest.mark.asyncio
async def test_risk_scoring():
    """Test risk scoring functionality"""
    from app.utils.risk_scoring import calculate_risk_score
    
    shipment_data = {
        "next_port": "CNSHA",
        "customs_status": "pending",
        "quality_status": "clear",
        "estimated_arrival": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "metadata": {}
    }
    
    result = await calculate_risk_score(shipment_data)
    
    assert isinstance(result, dict)
    assert "rule_based_score" in result
    assert "ml_prediction" in result
    assert "combined_score" in result
    assert "risk_level" in result
    
    # Scores should be between 0 and 1
    assert 0 <= result["rule_based_score"] <= 1
    assert 0 <= result["combined_score"] <= 1
    
    # Risk level should be a string
    assert result["risk_level"] in ["critical", "high", "medium", "low", "minimal"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])