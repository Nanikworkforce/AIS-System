#!/usr/bin/env python3
"""
Real-Time AIS WebSocket Server
Generates and streams real-time vessel data using WebSockets
"""

import asyncio
import websockets
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set
import threading
from dataclasses import dataclass, asdict
import uuid
import math

# Import your existing models
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.vessel import Vessel, VesselType, VesselStatus, ServiceLine, Location, VesselSpecifications
from generators.ais_data_generator import AISDataGenerator

@dataclass
class RealtimeVesselUpdate:
    """Real-time vessel update message"""
    imo_number: str
    mmsi: str
    vessel_name: str
    vessel_type: str
    timestamp: str
    position: Dict[str, float]
    kinematics: Dict[str, float]
    status: str
    destination: str = None
    eta: str = None
    course_over_ground: float = 0.0
    rate_of_turn: float = 0.0

class RealtimeVesselManager:
    """Manages real-time vessel data and movement simulation"""
    
    def __init__(self, initial_fleet_size: int = 500):
        """Initialize with vessels from your existing generator"""
        print(f"🚢 Initializing real-time vessel manager with {initial_fleet_size} vessels...")
        
        # Generate initial fleet using your existing system
        generator = AISDataGenerator()
        self.fleet = generator.generate_fleet(initial_fleet_size)
        
        # Convert to real-time tracking format
        self.vessels = {}
        self.initialize_realtime_vessels()
        
        # Shipping routes for realistic movement
        self.shipping_routes = self._define_shipping_routes()
        
        # Update parameters
        self.update_interval = 30  # seconds
        self.movement_speed_factor = 1.0  # 1.0 = realistic speed
        
        print(f"✅ Initialized {len(self.vessels)} vessels for real-time tracking")
    
    def initialize_realtime_vessels(self):
        """Convert fleet vessels to real-time tracking format"""
        for vessel in self.fleet.vessels:
            # Assign random route or stationary behavior
            route = random.choice(self.shipping_routes) if random.random() > 0.3 else None
            
            self.vessels[vessel.imo_number] = {
                'vessel': vessel,
                'current_position': vessel.current_location,
                'target_position': None,
                'route': route,
                'route_progress': random.uniform(0, 1) if route else 0,
                'last_update': datetime.now(),
                'movement_pattern': random.choice(['route', 'port_to_port', 'stationary', 'coastal']),
                'speed_variation': random.uniform(0.8, 1.2),
                'heading': random.randint(0, 359),
                'course_over_ground': random.randint(0, 359),
                'rate_of_turn': 0.0
            }
    
    def _define_shipping_routes(self) -> List[Dict[str, Any]]:
        """Define major shipping routes for realistic movement"""
        return [
            {
                'name': 'Asia-Europe (Suez)',
                'waypoints': [
                    {'lat': 1.2966, 'lon': 103.7764, 'name': 'Singapore'},
                    {'lat': 12.7820, 'lon': 45.0370, 'name': 'Bab el-Mandeb'},
                    {'lat': 30.0444, 'lon': 31.2357, 'name': 'Suez Canal'},
                    {'lat': 51.9225, 'lon': 4.4792, 'name': 'Rotterdam'}
                ],
                'vessel_types': ['container', 'general_cargo']
            },
            {
                'name': 'Trans-Pacific',
                'waypoints': [
                    {'lat': 22.3526, 'lon': 114.1417, 'name': 'Hong Kong'},
                    {'lat': 35.6762, 'lon': 139.6503, 'name': 'Tokyo'},
                    {'lat': 33.7701, 'lon': -118.1937, 'name': 'Los Angeles'}
                ],
                'vessel_types': ['container', 'bulker']
            },
            {
                'name': 'Trans-Atlantic',
                'waypoints': [
                    {'lat': 51.9225, 'lon': 4.4792, 'name': 'Rotterdam'},
                    {'lat': 40.6892, 'lon': -74.0445, 'name': 'New York'},
                    {'lat': 25.7617, 'lon': -80.1918, 'name': 'Miami'}
                ],
                'vessel_types': ['container', 'general_cargo']
            },
            {
                'name': 'Middle East Oil Route',
                'waypoints': [
                    {'lat': 26.2050, 'lon': 50.0920, 'name': 'Bahrain'},
                    {'lat': 24.4539, 'lon': 54.3773, 'name': 'Abu Dhabi'},
                    {'lat': 30.0444, 'lon': 31.2357, 'name': 'Suez Canal'},
                    {'lat': 43.2965, 'lon': 5.3698, 'name': 'Marseille'}
                ],
                'vessel_types': ['tanker']
            },
            {
                'name': 'Brazil-China Iron Ore',
                'waypoints': [
                    {'lat': -20.2976, 'lon': -40.2958, 'name': 'Vitoria'},
                    {'lat': -23.9608, 'lon': -46.3969, 'name': 'Santos'},
                    {'lat': 1.2966, 'lon': 103.7764, 'name': 'Singapore'},
                    {'lat': 36.0986, 'lon': 120.3719, 'name': 'Qingdao'}
                ],
                'vessel_types': ['bulker']
            }
        ]
    
    def update_vessel_positions(self) -> List[RealtimeVesselUpdate]:
        """Update all vessel positions and return changes"""
        updates = []
        current_time = datetime.now()
        
        for imo_number, vessel_data in self.vessels.items():
            vessel = vessel_data['vessel']
            
            # Skip if vessel is in dry dock
            if vessel.current_status == VesselStatus.DRY_DOCK:
                continue
            
            # Calculate time since last update
            time_delta = (current_time - vessel_data['last_update']).total_seconds()
            
            # Update position based on movement pattern
            new_position, new_heading, new_speed = self._calculate_new_position(
                vessel_data, time_delta
            )
            
            # Update vessel data
            if new_position:
                vessel_data['current_position'] = Location(
                    latitude=new_position['lat'],
                    longitude=new_position['lon'],
                    port_name=new_position.get('port_name'),
                    country=new_position.get('country')
                )
                vessel_data['heading'] = new_heading
                vessel_data['last_update'] = current_time
                
                # Update vessel object
                vessel.current_location = vessel_data['current_position']
                
                # Occasionally change status
                if random.random() < 0.02:  # 2% chance
                    vessel.current_status = self._random_status_change(vessel.current_status)
                
                # Create update message
                update = RealtimeVesselUpdate(
                    imo_number=vessel.imo_number,
                    mmsi=vessel.mmsi,
                    vessel_name=vessel.vessel_name,
                    vessel_type=vessel.vessel_type.value,
                    timestamp=current_time.isoformat(),
                    position={
                        'latitude': round(new_position['lat'], 6),
                        'longitude': round(new_position['lon'], 6),
                        'port_name': new_position.get('port_name'),
                        'country': new_position.get('country')
                    },
                    kinematics={
                        'speed_over_ground': round(new_speed, 1),
                        'course_over_ground': round(new_heading, 1),
                        'heading': round(vessel_data['heading'], 1),
                        'rate_of_turn': round(vessel_data.get('rate_of_turn', 0), 1)
                    },
                    status=vessel.current_status.value,
                    destination=self._get_destination(vessel_data),
                    eta=self._calculate_eta(vessel_data)
                )
                
                updates.append(update)
        
        return updates
    
    def _calculate_new_position(self, vessel_data: Dict, time_delta: float) -> tuple:
        """Calculate new vessel position based on movement pattern"""
        vessel = vessel_data['vessel']
        current_pos = vessel_data['current_position']
        
        if not current_pos:
            return None, vessel_data['heading'], 0
        
        # Base speed from vessel specifications
        base_speed = 12.0  # Default speed in knots
        if vessel.specifications:
            base_speed = vessel.specifications.max_speed_knots * 0.7  # 70% of max speed
        
        # Apply speed variation
        current_speed = base_speed * vessel_data['speed_variation']
        
        # Handle different movement patterns
        movement_pattern = vessel_data['movement_pattern']
        
        if movement_pattern == 'stationary' or vessel.current_status == VesselStatus.IN_PORT:
            # Vessel is stationary (in port or anchored)
            return {
                'lat': current_pos.latitude + random.uniform(-0.001, 0.001),
                'lon': current_pos.longitude + random.uniform(-0.001, 0.001),
                'port_name': current_pos.port_name,
                'country': current_pos.country
            }, vessel_data['heading'], 0
        
        elif movement_pattern == 'route' and vessel_data['route']:
            # Following a shipping route
            return self._move_along_route(vessel_data, current_speed, time_delta)
        
        else:
            # Random movement (coastal or open ocean)
            return self._move_randomly(vessel_data, current_speed, time_delta)
    
    def _move_along_route(self, vessel_data: Dict, speed_knots: float, time_delta: float) -> tuple:
        """Move vessel along predefined shipping route"""
        route = vessel_data['route']
        progress = vessel_data['route_progress']
        waypoints = route['waypoints']
        
        if len(waypoints) < 2:
            return self._move_randomly(vessel_data, speed_knots, time_delta)
        
        # Find current segment
        segment_index = int(progress * (len(waypoints) - 1))
        segment_index = min(segment_index, len(waypoints) - 2)
        
        start_point = waypoints[segment_index]
        end_point = waypoints[segment_index + 1]
        
        # Calculate segment progress
        segment_progress = (progress * (len(waypoints) - 1)) - segment_index
        
        # Calculate distance moved in nautical miles
        distance_nm = speed_knots * (time_delta / 3600.0) * self.movement_speed_factor
        
        # Total segment distance (approximate)
        segment_distance = self._calculate_distance(
            start_point['lat'], start_point['lon'],
            end_point['lat'], end_point['lon']
        )
        
        # Update progress
        progress_increment = distance_nm / segment_distance if segment_distance > 0 else 0
        new_segment_progress = segment_progress + progress_increment
        
        # Calculate new position
        if new_segment_progress >= 1.0:
            # Move to next segment
            vessel_data['route_progress'] = min(progress + progress_increment, 0.99)
            new_segment_progress = 1.0
        
        # Interpolate position
        lat = start_point['lat'] + (end_point['lat'] - start_point['lat']) * new_segment_progress
        lon = start_point['lon'] + (end_point['lon'] - start_point['lon']) * new_segment_progress
        
        # Calculate heading
        heading = self._calculate_bearing(start_point['lat'], start_point['lon'], 
                                        end_point['lat'], end_point['lon'])
        
        return {
            'lat': lat,
            'lon': lon,
            'port_name': end_point['name'] if new_segment_progress > 0.9 else None,
            'country': None
        }, heading, speed_knots
    
    def _move_randomly(self, vessel_data: Dict, speed_knots: float, time_delta: float) -> tuple:
        """Move vessel randomly (coastal or open ocean movement)"""
        current_pos = vessel_data['current_position']
        heading = vessel_data['heading']
        
        # Add some random variation to heading
        heading_change = random.uniform(-10, 10)
        new_heading = (heading + heading_change) % 360
        vessel_data['heading'] = new_heading
        
        # Calculate distance moved
        distance_nm = speed_knots * (time_delta / 3600.0) * self.movement_speed_factor
        
        # Convert to lat/lon change (approximate)
        lat_change = (distance_nm / 60.0) * math.cos(math.radians(new_heading))
        lon_change = (distance_nm / 60.0) * math.sin(math.radians(new_heading))
        
        new_lat = current_pos.latitude + lat_change
        new_lon = current_pos.longitude + lon_change
        
        # Keep within reasonable bounds
        new_lat = max(-85, min(85, new_lat))
        new_lon = max(-180, min(180, new_lon))
        
        return {
            'lat': new_lat,
            'lon': new_lon
        }, new_heading, speed_knots
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in nautical miles"""
        # Haversine formula
        R = 3440.065  # Earth radius in nautical miles
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing between two points"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)
        
        y = math.sin(delta_lon) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
        
        bearing = math.atan2(y, x)
        return (math.degrees(bearing) + 360) % 360
    
    def _random_status_change(self, current_status: VesselStatus) -> VesselStatus:
        """Randomly change vessel status"""
        if current_status == VesselStatus.AT_SEA:
            return random.choice([VesselStatus.IN_PORT, VesselStatus.ANCHORED])
        elif current_status == VesselStatus.IN_PORT:
            return VesselStatus.AT_SEA
        else:
            return random.choice([VesselStatus.AT_SEA, VesselStatus.IN_PORT])
    
    def _get_destination(self, vessel_data: Dict) -> str:
        """Get vessel destination"""
        route = vessel_data.get('route')
        if route and route['waypoints']:
            # Return the final waypoint as destination
            return route['waypoints'][-1]['name']
        return None
    
    def _calculate_eta(self, vessel_data: Dict) -> str:
        """Calculate estimated time of arrival"""
        route = vessel_data.get('route')
        if route and route['waypoints']:
            # Simple ETA calculation
            eta = datetime.now() + timedelta(hours=random.randint(6, 72))
            return eta.isoformat()
        return None
    
    def get_vessel_by_imo(self, imo_number: str) -> Dict[str, Any]:
        """Get specific vessel real-time data"""
        if imo_number in self.vessels:
            vessel_data = self.vessels[imo_number]
            vessel = vessel_data['vessel']
            pos = vessel_data['current_position']
            
            return {
                'imo_number': vessel.imo_number,
                'mmsi': vessel.mmsi,
                'vessel_name': vessel.vessel_name,
                'vessel_type': vessel.vessel_type.value,
                'current_position': {
                    'latitude': pos.latitude if pos else None,
                    'longitude': pos.longitude if pos else None,
                    'port_name': pos.port_name if pos else None,
                    'country': pos.country if pos else None,
                    'last_update': vessel_data['last_update'].isoformat()
                },
                'status': vessel.current_status.value,
                'route': vessel_data.get('route', {}).get('name'),
                'destination': self._get_destination(vessel_data),
                'eta': self._calculate_eta(vessel_data)
            }
        return None
    
    def get_fleet_summary(self) -> Dict[str, Any]:
        """Get real-time fleet summary"""
        total_vessels = len(self.vessels)
        status_counts = {}
        type_counts = {}
        
        for vessel_data in self.vessels.values():
            vessel = vessel_data['vessel']
            
            # Count by status
            status = vessel.current_status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by type
            vessel_type = vessel.vessel_type.value
            type_counts[vessel_type] = type_counts.get(vessel_type, 0) + 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_vessels': total_vessels,
            'status_distribution': status_counts,
            'type_distribution': type_counts,
            'vessels_with_routes': len([v for v in self.vessels.values() if v.get('route')])
        }

class WebSocketServer:
    """WebSocket server for real-time AIS data streaming"""
    
    def __init__(self, vessel_manager: RealtimeVesselManager, host: str = "localhost", port: int = 8765):
        self.vessel_manager = vessel_manager
        self.host = host
        self.port = port
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.is_running = False
        
    async def register_client(self, websocket):
        """Register new WebSocket client"""
        self.connected_clients.add(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        print(f"🔗 Client connected: {client_id} (Total: {len(self.connected_clients)})")
        
        # Send initial fleet summary
        await self.send_to_client(websocket, {
            'type': 'connection_established',
            'timestamp': datetime.now().isoformat(),
            'message': 'Connected to real-time AIS stream',
            'fleet_summary': self.vessel_manager.get_fleet_summary()
        })
    
    async def unregister_client(self, websocket):
        """Unregister WebSocket client"""
        self.connected_clients.discard(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        print(f"🔌 Client disconnected: {client_id} (Remaining: {len(self.connected_clients)})")
    
    async def send_to_client(self, websocket, message: Dict[str, Any]):
        """Send message to specific client"""
        try:
            await websocket.send(json.dumps(message, default=str))
        except websockets.exceptions.ConnectionClosed:
            await self.unregister_client(websocket)
        except Exception as e:
            print(f"Error sending to client: {e}")
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.connected_clients:
            # Create a copy of the set to avoid modification during iteration
            clients = self.connected_clients.copy()
            await asyncio.gather(
                *[self.send_to_client(client, message) for client in clients],
                return_exceptions=True
            )
    
    async def handle_client_message(self, websocket, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'get_vessel':
                # Get specific vessel data
                imo_number = data.get('imo_number')
                vessel_data = self.vessel_manager.get_vessel_by_imo(imo_number)
                
                response = {
                    'type': 'vessel_data',
                    'timestamp': datetime.now().isoformat(),
                    'vessel': vessel_data
                }
                await self.send_to_client(websocket, response)
            
            elif message_type == 'get_fleet_summary':
                # Get fleet summary
                summary = self.vessel_manager.get_fleet_summary()
                response = {
                    'type': 'fleet_summary',
                    'timestamp': datetime.now().isoformat(),
                    'summary': summary
                }
                await self.send_to_client(websocket, response)
            
            elif message_type == 'subscribe':
                # Subscribe to specific updates
                subscription_type = data.get('subscription_type', 'all')
                response = {
                    'type': 'subscription_confirmed',
                    'subscription_type': subscription_type,
                    'timestamp': datetime.now().isoformat()
                }
                await self.send_to_client(websocket, response)
        
        except json.JSONDecodeError:
            await self.send_to_client(websocket, {
                'type': 'error',
                'message': 'Invalid JSON format'
            })
        except Exception as e:
            await self.send_to_client(websocket, {
                'type': 'error',
                'message': f'Error processing message: {str(e)}'
            })
    
    async def handle_client(self, websocket):
        """Handle individual client connection"""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def update_loop(self):
        """Main update loop for vessel positions"""
        print(f"🔄 Starting vessel update loop (interval: {self.vessel_manager.update_interval}s)")
        
        while self.is_running:
            try:
                # Update vessel positions
                updates = self.vessel_manager.update_vessel_positions()
                
                if updates and self.connected_clients:
                    # Broadcast updates to all clients
                    message = {
                        'type': 'vessel_updates',
                        'timestamp': datetime.now().isoformat(),
                        'update_count': len(updates),
                        'updates': [asdict(update) for update in updates]
                    }
                    
                    await self.broadcast_to_all(message)
                    print(f"📡 Broadcasted {len(updates)} vessel updates to {len(self.connected_clients)} clients")
                
                # Send periodic fleet summary
                if random.random() < 0.1:  # 10% chance each cycle
                    summary_message = {
                        'type': 'fleet_summary_update',
                        'timestamp': datetime.now().isoformat(),
                        'summary': self.vessel_manager.get_fleet_summary()
                    }
                    await self.broadcast_to_all(summary_message)
                
                await asyncio.sleep(self.vessel_manager.update_interval)
                
            except Exception as e:
                print(f"Error in update loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def start_server(self):
        """Start the WebSocket server"""
        self.is_running = True
        
        print(f"🚀 Starting WebSocket server on ws://{self.host}:{self.port}")
        print(f"   Fleet size: {len(self.vessel_manager.vessels)} vessels")
        print(f"   Update interval: {self.vessel_manager.update_interval} seconds")
        
        # Start the WebSocket server
        server = await websockets.serve(self.handle_client, self.host, self.port)
        
        # Start the update loop
        update_task = asyncio.create_task(self.update_loop())
        
        print(f"✅ WebSocket server running. Connect with: ws://{self.host}:{self.port}")
        print(f"🔗 Waiting for client connections...")
        
        try:
            await asyncio.gather(
                server.wait_closed(),
                update_task
            )
        except KeyboardInterrupt:
            print(f"\n⏹️ Server shutdown requested")
        finally:
            self.is_running = False
            server.close()
            await server.wait_closed()
            print(f"🛑 WebSocket server stopped")

async def main():
    """Main function to start the real-time AIS WebSocket server"""
    print("🌊 REAL-TIME AIS WEBSOCKET SERVER")
    print("=" * 50)
    
    # Initialize vessel manager with your existing fleet
    vessel_manager = RealtimeVesselManager(initial_fleet_size=500)
    
    # Create and start WebSocket server
    websocket_server = WebSocketServer(vessel_manager, host="localhost", port=8765)
    
    try:
        await websocket_server.start_server()
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped by user")

if __name__ == "__main__":
    # Run the WebSocket server
    asyncio.run(main())
