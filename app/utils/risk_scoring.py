from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import pickle
from app.core.redis import redis_client
import json

class RiskScoringEngine:
    """Engine for calculating and predicting risk scores"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        self.risk_factors = self._initialize_risk_factors()
        
    def _initialize_risk_factors(self) -> Dict[str, Dict[str, Any]]:
        """Initialize risk factor definitions and weights"""
        return {
            "port_congestion": {
                "weight": 0.25,
                "factors": ["congestion_level", "wait_time", "historical_delays"],
                "thresholds": {"low": 0.3, "medium": 0.6, "high": 0.8}
            },
            "customs_delay": {
                "weight": 0.20,
                "factors": ["clearance_time", "document_completeness", "historical_issues"],
                "thresholds": {"low": 0.4, "medium": 0.7, "high": 0.9}
            },
            "quality_hold": {
                "weight": 0.15,
                "factors": ["inspection_rate", "rejection_history", "product_type"],
                "thresholds": {"low": 0.2, "medium": 0.5, "high": 0.8}
            },
            "weather_impact": {
                "weight": 0.10,
                "factors": ["storm_probability", "wind_speed", "visibility"],
                "thresholds": {"low": 0.3, "medium": 0.6, "high": 0.9}
            },
            "equipment_failure": {
                "weight": 0.10,
                "factors": ["equipment_age", "maintenance_history", "load_factor"],
                "thresholds": {"low": 0.1, "medium": 0.4, "high": 0.7}
            },
            "schedule_deviation": {
                "weight": 0.20,
                "factors": ["current_delay", "buffer_time", "historical_punctuality"],
                "thresholds": {"low": 0.2, "medium": 0.5, "high": 0.8}
            }
        }
    
    async def calculate_shipment_risk_score(self, shipment_data: Dict[str, Any]) -> float:
        """Calculate comprehensive risk score for a shipment"""
        risk_scores = {}
        
        # Calculate individual risk factor scores
        for risk_type, config in self.risk_factors.items():
            score = await self._calculate_individual_risk_score(
                risk_type, shipment_data, config
            )
            risk_scores[risk_type] = score
        
        # Calculate weighted overall score
        overall_score = 0.0
        total_weight = 0.0
        
        for risk_type, score in risk_scores.items():
            weight = self.risk_factors[risk_type]["weight"]
            overall_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            overall_score = overall_score / total_weight
        
        return min(1.0, max(0.0, overall_score))
    
    async def _calculate_individual_risk_score(self, risk_type: str,
                                             shipment_data: Dict[str, Any],
                                             config: Dict[str, Any]) -> float:
        """Calculate score for an individual risk type"""
        if risk_type == "port_congestion":
            return await self._calculate_port_congestion_score(shipment_data)
        elif risk_type == "customs_delay":
            return await self._calculate_customs_delay_score(shipment_data)
        elif risk_type == "quality_hold":
            return await self._calculate_quality_hold_score(shipment_data)
        elif risk_type == "weather_impact":
            return await self._calculate_weather_impact_score(shipment_data)
        elif risk_type == "schedule_deviation":
            return await self._calculate_schedule_deviation_score(shipment_data)
        else:
            return 0.0
    
    async def _calculate_port_congestion_score(self, shipment_data: Dict[str, Any]) -> float:
        """Calculate port congestion risk score"""
        next_port = shipment_data.get("next_port")
        if not next_port:
            return 0.0
        
        # Get congestion data (simulated)
        congestion_data = await self._get_port_congestion_data(next_port)
        
        if not congestion_data:
            return 0.3  # Default low risk
        
        congestion_level = congestion_data.get("congestion_level", 0.0)
        wait_time = congestion_data.get("wait_time_hours", 0)
        
        # Calculate score
        congestion_score = min(1.0, congestion_level * 1.2)  # Weight congestion
        wait_score = min(1.0, wait_time / 72)  # Normalize wait time (max 72 hours)
        
        return max(congestion_score, wait_score)
    
    async def _calculate_customs_delay_score(self, shipment_data: Dict[str, Any]) -> float:
        """Calculate customs delay risk score"""
        customs_status = shipment_data.get("customs_status", "pending")
        document_status = shipment_data.get("document_status", "complete")
        
        score = 0.0
        
        # Status-based scoring
        status_scores = {
            "cleared": 0.0,
            "pending": 0.3,
            "under_review": 0.6,
            "delayed": 0.8,
            "held": 0.9
        }
        
        score += status_scores.get(customs_status, 0.5)
        
        # Document status
        if document_status != "complete":
            score += 0.2
        
        # Historical data (simulated)
        historical_delay = shipment_data.get("historical_customs_delay", 0)
        if historical_delay > 24:  # More than 24 hours historically
            score += 0.1
        
        return min(1.0, score)
    
    async def _calculate_quality_hold_score(self, shipment_data: Dict[str, Any]) -> float:
        """Calculate quality hold risk score"""
        quality_status = shipment_data.get("quality_status", "clear")
        product_type = shipment_data.get("product_type", "general")
        inspection_history = shipment_data.get("inspection_history", [])
        
        score = 0.0
        
        # Status-based scoring
        if quality_status == "hold":
            score = 0.8
        elif quality_status == "inspection":
            score = 0.6
        elif quality_status == "passed":
            score = 0.1
        
        # Product type risk
        high_risk_products = ["pharmaceutical", "food", "electronics", "hazardous"]
        if product_type in high_risk_products:
            score += 0.2
        
        # Inspection history
        if inspection_history:
            failure_rate = sum(1 for i in inspection_history if i.get("result") == "fail")
            failure_rate = failure_rate / len(inspection_history)
            score += failure_rate * 0.3
        
        return min(1.0, score)
    
    async def _calculate_weather_impact_score(self, shipment_data: Dict[str, Any]) -> float:
        """Calculate weather impact risk score"""
        current_location = shipment_data.get("current_location")
        route_coordinates = shipment_data.get("route_coordinates", [])
        season = datetime.utcnow().month
        
        if not current_location and not route_coordinates:
            return 0.2  # Default low risk
        
        score = 0.0
        
        # Seasonal risk
        hurricane_season = season in [6, 7, 8, 9, 10]  # June-October
        monsoon_season = season in [5, 6, 7, 8, 9]  # May-September
        
        if hurricane_season or monsoon_season:
            score += 0.3
        
        # Region-specific risk (simplified)
        high_risk_regions = ["South China Sea", "Bay of Bengal", "Caribbean Sea"]
        if any(region in str(current_location) for region in high_risk_regions):
            score += 0.4
        
        # Storm probability (simulated)
        storm_probability = await self._get_storm_probability(current_location)
        score += storm_probability * 0.3
        
        return min(1.0, score)
    
    async def _calculate_schedule_deviation_score(self, shipment_data: Dict[str, Any]) -> float:
        """Calculate schedule deviation risk score"""
        estimated_arrival = shipment_data.get("estimated_arrival")
        current_time = datetime.utcnow()
        
        if not estimated_arrival:
            return 0.2
        
        # Calculate delay
        if isinstance(estimated_arrival, str):
            estimated_arrival = datetime.fromisoformat(estimated_arrival.replace('Z', '+00:00'))
        
        delay_hours = 0
        if current_time > estimated_arrival:
            delay_hours = (current_time - estimated_arrival).total_seconds() / 3600
        
        # Calculate score based on delay
        if delay_hours <= 4:
            score = 0.1
        elif delay_hours <= 12:
            score = 0.3
        elif delay_hours <= 24:
            score = 0.6
        elif delay_hours <= 48:
            score = 0.8
        else:
            score = 0.95
        
        # Add buffer consideration
        buffer_hours = shipment_data.get("buffer_hours", 0)
        if delay_hours > buffer_hours:
            score += 0.1
        
        return min(1.0, score)
    
    async def _get_port_congestion_data(self, port_code: str) -> Optional[Dict[str, Any]]:
        """Get port congestion data (simulated)"""
        # In production, this would call an external API
        congestion_db = {
            "CNSHA": {"congestion_level": 0.8, "wait_time_hours": 48},
            "NLRTM": {"congestion_level": 0.6, "wait_time_hours": 24},
            "SGSIN": {"congestion_level": 0.4, "wait_time_hours": 12},
            "USLAX": {"congestion_level": 0.7, "wait_time_hours": 36},
            "DEHAM": {"congestion_level": 0.5, "wait_time_hours": 18},
            "CNNGB": {"congestion_level": 0.3, "wait_time_hours": 8}
        }
        return congestion_db.get(port_code.upper())
    
    async def _get_storm_probability(self, location: str) -> float:
        """Get storm probability for location (simulated)"""
        # In production, this would call a weather API
        high_storm_areas = ["Pacific Ocean", "Atlantic Ocean", "Indian Ocean", "South China Sea"]
        if any(area in str(location) for area in high_storm_areas):
            return 0.6
        return 0.1
    
    async def train_risk_model(self, training_data: List[Dict[str, Any]]):
        """Train the risk prediction model"""
        if not training_data:
            return
        
        # Prepare features and labels
        features = []
        labels = []
        
        for data in training_data:
            # Extract features
            feature_vector = self._extract_features(data)
            if feature_vector:
                features.append(feature_vector)
                labels.append(data.get("actual_risk_level", 0))
        
        if not features:
            return
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train model
        self.model.fit(features_scaled, labels)
        self.is_trained = True
        
        # Save model
        await self._save_model()
    
    def _extract_features(self, data: Dict[str, Any]) -> List[float]:
        """Extract feature vector from data"""
        features = []
        
        # Port congestion features
        features.append(data.get("congestion_level", 0.0))
        features.append(min(1.0, data.get("wait_time_hours", 0) / 72))
        
        # Customs features
        customs_status = data.get("customs_status", "pending")
        customs_scores = {"cleared": 0.0, "pending": 0.3, "delayed": 0.7, "held": 0.9}
        features.append(customs_scores.get(customs_status, 0.5))
        
        # Quality features
        quality_status = data.get("quality_status", "clear")
        quality_scores = {"clear": 0.0, "inspection": 0.5, "hold": 0.8}
        features.append(quality_scores.get(quality_status, 0.3))
        
        # Schedule features
        delay_hours = data.get("delay_hours", 0)
        features.append(min(1.0, delay_hours / 48))
        
        return features
    
    async def predict_risk(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict risk using trained model"""
        if not self.is_trained:
            # Fallback to rule-based scoring
            score = await self.calculate_shipment_risk_score(shipment_data)
            return {
                "score": score,
                "level": self._score_to_level(score),
                "method": "rule_based",
                "confidence": 0.7
            }
        
        # Extract features
        features = self._extract_features(shipment_data)
        if not features:
            score = await self.calculate_shipment_risk_score(shipment_data)
            return {
                "score": score,
                "level": self._score_to_level(score),
                "method": "rule_based",
                "confidence": 0.7
            }
        
        # Scale features and predict
        features_scaled = self.scaler.transform([features])
        prediction = self.model.predict_proba(features_scaled)[0]
        
        # Get risk score (probability of high risk)
        score = float(prediction[1]) if len(prediction) > 1 else 0.5
        
        return {
            "score": score,
            "level": self._score_to_level(score),
            "method": "ml_model",
            "confidence": float(max(prediction)),
            "feature_importance": self._get_feature_importance()
        }
    
    def _score_to_level(self, score: float) -> str:
        """Convert numerical score to risk level"""
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "low"
        else:
            return "minimal"
    
    def _get_feature_importance(self) -> List[Dict[str, Any]]:
        """Get feature importance from model"""
        if not self.is_trained:
            return []
        
        feature_names = ["congestion", "wait_time", "customs", "quality", "delay"]
        importances = self.model.feature_importances_
        
        return [
            {"feature": name, "importance": float(imp)}
            for name, imp in zip(feature_names, importances)
        ]
    
    async def _save_model(self):
        """Save trained model to disk"""
        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "is_trained": self.is_trained
        }
        
        # Save to Redis for distributed access
        model_bytes = pickle.dumps(model_data)
        await redis_client.set("risk_scoring_model", model_bytes)
        
        # Also save to disk
        joblib.dump(model_data, "data/risk_model.joblib")
    
    async def load_model(self):
        """Load trained model"""
        try:
            # Try loading from Redis first
            model_bytes = await redis_client.get("risk_scoring_model")
            if model_bytes:
                model_data = pickle.loads(model_bytes)
                self.model = model_data["model"]
                self.scaler = model_data["scaler"]
                self.is_trained = model_data["is_trained"]
                return True
            
            # Try loading from disk
            model_data = joblib.load("data/risk_model.joblib")
            self.model = model_data["model"]
            self.scaler = model_data["scaler"]
            self.is_trained = model_data["is_trained"]
            return True
            
        except Exception as e:
            print(f"Failed to load model: {e}")
            return False

# Global instance
risk_scoring_engine = RiskScoringEngine()

# Utility functions
async def calculate_risk_score(shipment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate risk score for shipment"""
    score = await risk_scoring_engine.calculate_shipment_risk_score(shipment_data)
    prediction = await risk_scoring_engine.predict_risk(shipment_data)
    
    return {
        "rule_based_score": score,
        "ml_prediction": prediction,
        "combined_score": (score + prediction["score"]) / 2,
        "risk_level": prediction["level"],
        "calculation_method": prediction["method"],
        "confidence": prediction.get("confidence", 0.7),
        "timestamp": datetime.utcnow().isoformat()
    }

async def update_risk_factors(weights: Dict[str, float]):
    """Update risk factor weights"""
    for risk_type, weight in weights.items():
        if risk_type in risk_scoring_engine.risk_factors:
            risk_scoring_engine.risk_factors[risk_type]["weight"] = weight
    
    # Save updated weights
    await redis_client.set(
        "risk_factor_weights",
        json.dumps(risk_scoring_engine.risk_factors)
    )