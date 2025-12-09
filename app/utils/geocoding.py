from typing import Dict, List, Tuple, Optional
import asyncio
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import aiohttp
from app.core.config import settings

class GeoCodingService:
    """Service for geocoding and distance calculations"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="control_tower")
        self.cache = {}
        
    async def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode an address to coordinates"""
        if address in self.cache:
            return self.cache[address]
        
        try:
            location = await asyncio.to_thread(
                self.geolocator.geocode,
                address,
                timeout=10
            )
            
            if location:
                coords = (location.latitude, location.longitude)
                self.cache[address] = coords
                return coords
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Geocoding error for {address}: {e}")
        
        return None
    
    async def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """Reverse geocode coordinates to address"""
        cache_key = f"{lat},{lon}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            location = await asyncio.to_thread(
                self.geolocator.reverse,
                (lat, lon),
                timeout=10
            )
            
            if location:
                address = location.address
                self.cache[cache_key] = address
                return address
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Reverse geocoding error for ({lat}, {lon}): {e}")
        
        return None
    
    def calculate_distance(self, point1: Tuple[float, float], 
                         point2: Tuple[float, float]) -> float:
        """Calculate distance between two points in kilometers"""
        return geodesic(point1, point2).kilometers
    
    async def calculate_route_distance(self, points: List[Tuple[float, float]]) -> float:
        """Calculate total distance for a route"""
        if len(points) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(len(points) - 1):
            distance = self.calculate_distance(points[i], points[i + 1])
            total_distance += distance
        
        return total_distance
    
    async def find_nearest_port(self, coordinates: Tuple[float, float], 
                              port_list: List[Dict]) -> Optional[Dict]:
        """Find nearest port to given coordinates"""
        if not port_list:
            return None
        
        nearest_port = None
        min_distance = float('inf')
        
        for port in port_list:
            port_coords = (port.get("latitude"), port.get("longitude"))
            if None in port_coords:
                continue
            
            distance = self.calculate_distance(coordinates, port_coords)
            if distance < min_distance:
                min_distance = distance
                nearest_port = port
        
        if nearest_port:
            nearest_port["distance_km"] = min_distance
        
        return nearest_port
    
    async def get_port_coordinates(self, port_code: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for a port code"""
        # Common port coordinates (in production, use a port database)
        port_coordinates = {
            "CNSHA": (31.2304, 121.4737),  # Shanghai
            "NLRTM": (51.9244, 4.4777),    # Rotterdam
            "SGSIN": (1.3521, 103.8198),   # Singapore
            "USLAX": (34.0522, -118.2437), # Los Angeles
            "DEHAM": (53.5511, 9.9937),    # Hamburg
            "CNNGB": (29.8683, 121.5435),  # Ningbo
            "BEANR": (51.2194, 4.4025),    # Antwerp
            "JPTYO": (35.6762, 139.6503),  # Tokyo
            "AEDXB": (25.2048, 55.2708),   # Dubai
            "HKHKG": (22.3193, 114.1694),  # Hong Kong
        }
        
        return port_coordinates.get(port_code.upper())
    
    async def calculate_estimated_time(self, distance_km: float, 
                                     mode: str = "sea") -> float:
        """Calculate estimated time in hours based on distance and transport mode"""
        # Average speeds in km/h
        speeds = {
            "sea": 40,      # Container ship
            "air": 800,     # Cargo plane
            "land": 60,     # Truck
            "rail": 80,     # Train
            "multimodal": 50  # Average
        }
        
        speed = speeds.get(mode, 40)
        time_hours = distance_km / speed
        
        # Add buffer based on mode
        buffers = {
            "sea": 1.2,      # 20% buffer for sea
            "air": 1.1,      # 10% buffer for air
            "land": 1.15,    # 15% buffer for land
            "rail": 1.15,    # 15% buffer for rail
            "multimodal": 1.25  # 25% buffer for multimodal
        }
        
        buffer = buffers.get(mode, 1.2)
        return time_hours * buffer
    
    async def generate_route_waypoints(self, origin: Tuple[float, float],
                                     destination: Tuple[float, float],
                                     mode: str = "sea") -> List[Tuple[float, float]]:
        """Generate route waypoints between origin and destination"""
        # Simplified route generation
        # In production, use routing APIs like Google Maps, OpenRouteService
        
        waypoints = [origin]
        
        if mode == "sea":
            # Add major sea route waypoints
            mid_point = (
                (origin[0] + destination[0]) / 2,
                (origin[1] + destination[1]) / 2
            )
            waypoints.append(mid_point)
        
        waypoints.append(destination)
        return waypoints

# Global instance
geocoding_service = GeoCodingService()

# Utility functions
async def calculate_route(origin: str, destination: str, 
                        mode: str = "sea") -> Dict[str, any]:
    """Calculate route between two locations"""
    origin_coords = await geocoding_service.geocode_address(origin)
    dest_coords = await geocoding_service.geocode_address(destination)
    
    if not origin_coords or not dest_coords:
        return {"error": "Could not geocode addresses"}
    
    waypoints = await geocoding_service.generate_route_waypoints(
        origin_coords, dest_coords, mode
    )
    
    total_distance = await geocoding_service.calculate_route_distance(waypoints)
    estimated_time = await geocoding_service.calculate_estimated_time(
        total_distance, mode
    )
    
    return {
        "origin": origin,
        "destination": destination,
        "origin_coords": origin_coords,
        "destination_coords": dest_coords,
        "waypoints": waypoints,
        "total_distance_km": total_distance,
        "estimated_time_hours": estimated_time,
        "mode": mode,
        "waypoint_count": len(waypoints)
    }

async def find_alternative_routes(origin: str, destination: str,
                                mode: str = "sea") -> List[Dict[str, any]]:
    """Find alternative routes between locations"""
    alternatives = []
    
    # Base route
    base_route = await calculate_route(origin, destination, mode)
    alternatives.append({**base_route, "route_type": "direct"})
    
    # Alternative 1: Different mode
    if mode != "air":
        air_route = await calculate_route(origin, destination, "air")
        alternatives.append({**air_route, "route_type": "air_alternative"})
    
    # Alternative 2: Via major hub
    if mode == "sea":
        # Add Singapore as hub for Asia-Europe routes
        via_singapore = await calculate_route(origin, "Singapore", mode)
        singapore_to_dest = await calculate_route("Singapore", destination, mode)
        
        if via_singapore and singapore_to_dest:
            combined_route = {
                "origin": origin,
                "destination": destination,
                "via": "Singapore",
                "total_distance_km": via_singapore["total_distance_km"] + 
                                   singapore_to_dest["total_distance_km"],
                "estimated_time_hours": via_singapore["estimated_time_hours"] + 
                                      singapore_to_dest["estimated_time_hours"],
                "mode": mode,
                "route_type": "via_hub",
                "waypoints": via_singapore["waypoints"] + 
                           singapore_to_dest["waypoints"][1:]  # Skip duplicate Singapore
            }
            alternatives.append(combined_route)
    
    return alternatives