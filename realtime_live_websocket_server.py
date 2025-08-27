#!/usr/bin/env python3
"""
Live AIS WebSocket Server with AISStream.io Integration
Combines live AIS data from AISStream.io with WebSocket streaming
"""

import asyncio
import websockets
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set, Optional
import threading
from dataclasses import dataclass, asdict
import uuid
import math
import logging
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.vessel import Vessel, VesselType, VesselStatus, ServiceLine, Location, VesselSpecifications
from generators.ais_data_generator import AISDataGenerator
from integrations.aisstream_client import AISStreamClient, LiveVesselTracker, LiveAISMessage

@dataclass
class HybridVesselUpdate:
    """Unified vessel update from live or simulated data"""
    source: str  # 'live' or 'simulated'
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
    is_live_data: bool = False

class LiveAISWebSocketServer:
    """Enhanced WebSocket server with live AISStream.io integration"""
    
    def __init__(self, aisstream_api_key: str, host: str = "localhost", port: int = 8765):
        """Initialize live AIS WebSocket server"""
        self.aisstream_api_key = aisstream_api_key
        self.host = host
        self.port = port
        
        # WebSocket management
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.is_running = False
        
        # AISStream.io integration
        self.aisstream_client = None
        self.live_vessel_tracker = LiveVesselTracker()
        self.is_live_connected = False
        
        # Simulated data fallback
        self.simulated_fleet = None
        self.simulated_vessels = {}
        
        # Data management
        self.hybrid_vessels = {}  # Combined live + simulated vessels
        self.update_interval = 30  # seconds
        self.live_data_priority = True  # Prefer live data over simulated
        
        # Statistics
        self.stats = {
            'total_clients': 0,
            'live_vessels': 0,
            'simulated_vessels': 0,
            'total_updates_sent': 0,
            'live_messages_received': 0,
            'start_time': datetime.now()
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('LiveAISServer')
        
        # Initialize components
        self._initialize_aisstream()
        self._initialize_simulated_fallback()
    
    def _initialize_aisstream(self):
        """Initialize AISStream.io client"""
        self.logger.info("🔌 Initializing AISStream.io client...")
        
        try:
            self.aisstream_client = AISStreamClient(self.aisstream_api_key)
            
            # Add callbacks for live data
            self.aisstream_client.add_message_callback(self._handle_live_ais_message)
            self.aisstream_client.add_error_callback(self._handle_aisstream_error)
            
            self.live_vessel_tracker.add_update_callback(self._handle_live_vessel_update)
            
            self.logger.info("✅ AISStream.io client initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize AISStream.io client: {e}")
    
    def _initialize_simulated_fallback(self):
        """Initialize simulated data as fallback"""
        self.logger.info("🎭 Initializing simulated data fallback...")
        
        try:
            # Generate smaller simulated fleet to complement live data
            generator = AISDataGenerator()
            self.simulated_fleet = generator.generate_fleet(200)  # Reduced fleet size
            
            # Convert to tracking format
            for vessel in self.simulated_fleet.vessels:
                self.simulated_vessels[vessel.imo_number] = {
                    'vessel': vessel,
                    'last_update': datetime.now(),
                    'movement_vector': {
                        'speed': random.uniform(8, 20),
                        'heading': random.randint(0, 359)
                    },
                    'track_history': []
                }
            
            self.logger.info(f"✅ Simulated fallback initialized with {len(self.simulated_vessels)} vessels")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize simulated fallback: {e}")
    
    def _handle_live_ais_message(self, ais_message: LiveAISMessage):
        """Handle incoming live AIS message"""
        self.stats['live_messages_received'] += 1
        
        # Update live vessel tracker
        self.live_vessel_tracker.update_vessel(ais_message)
        
        # Log significant updates
        if self.stats['live_messages_received'] % 50 == 0:
            self.logger.info(f"📡 Processed {self.stats['live_messages_received']} live AIS messages")
    
    def _handle_live_vessel_update(self, updates: List[Dict[str, Any]]):
        """Handle live vessel updates from tracker"""
        for update in updates:
            mmsi = update['mmsi']
            
            # Add to hybrid vessel tracking
            self.hybrid_vessels[f"live_{mmsi}"] = {
                'source': 'live',
                'data': update,
                'last_update': datetime.now()
            }
        
        # Broadcast to WebSocket clients if any are connected
        if self.connected_clients and updates:
            asyncio.create_task(self._broadcast_live_updates(updates))
    
    def _handle_aisstream_error(self, error_msg: str):
        """Handle AISStream.io errors"""
        self.logger.error(f"AISStream.io error: {error_msg}")
        self.is_live_connected = False
    
    async def _connect_to_aisstream(self):
        """Connect to AISStream.io"""
        if not self.aisstream_client:
            return False
        
        try:
            self.logger.info("🌐 Connecting to AISStream.io for live data...")
            
            # Connect to global coverage (can be customized)
            bounding_boxes = [
                # Major shipping areas for better performance
                {"north": 70, "south": 40, "east": 30, "west": -30},    # North Atlantic
                {"north": 40, "south": 10, "east": 180, "west": 100},   # Asia-Pacific
                {"north": 50, "south": 30, "east": 15, "west": -10},    # Mediterranean
                {"north": 30, "south": -10, "east": 60, "west": 20},    # Middle East
            ]
            
            # Use first bounding box for initial connection
            success = await self.aisstream_client.connect(
                bounding_box=bounding_boxes[0]
            )
            
            if success:
                self.is_live_connected = True
                self.logger.info("✅ Connected to AISStream.io successfully")
                
                # Start listening for live data
                asyncio.create_task(self._listen_to_aisstream())
                return True
            else:
                self.logger.warning("⚠️ Failed to connect to AISStream.io, using simulated data only")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error connecting to AISStream.io: {e}")
            self.is_live_connected = False
            return False
    
    async def _listen_to_aisstream(self):
        """Listen to AISStream.io data"""
        try:
            await self.aisstream_client.listen()
        except Exception as e:
            self.logger.error(f"❌ Error listening to AISStream.io: {e}")
            self.is_live_connected = False
    
    async def _broadcast_live_updates(self, updates: List[Dict[str, Any]]):
        """Broadcast live updates to WebSocket clients"""
        if not self.connected_clients:
            return
        
        # Convert to WebSocket format
        websocket_updates = []
        for update in updates:
            ws_update = HybridVesselUpdate(
                source='live',
                imo_number=update.get('imo_number', ''),
                mmsi=update['mmsi'],
                vessel_name=update['vessel_name'],
                vessel_type=update['vessel_type'],
                timestamp=update['timestamp'],
                position=update['position'],
                kinematics=update['kinematics'],
                status=update['status'],
                destination=update.get('destination'),
                eta=update.get('eta'),
                is_live_data=True
            )
            websocket_updates.append(ws_update)
        
        # Broadcast to all clients
        message = {
            'type': 'vessel_updates',
            'timestamp': datetime.now().isoformat(),
            'update_count': len(websocket_updates),
            'live_data_count': len(websocket_updates),
            'simulated_data_count': 0,
            'updates': [asdict(update) for update in websocket_updates]
        }
        
        await self.broadcast_to_all(message)
        self.stats['total_updates_sent'] += len(websocket_updates)
    
    def _update_simulated_vessels(self) -> List[HybridVesselUpdate]:
        """Update simulated vessels (fallback/supplement)"""
        updates = []
        current_time = datetime.now()
        
        # Only update a subset of simulated vessels to reduce load
        vessels_to_update = list(self.simulated_vessels.items())[:50]  # Update 50 at a time
        
        for imo_number, vessel_data in vessels_to_update:
            vessel = vessel_data['vessel']
            
            # Skip if vessel is in dry dock
            if vessel.current_status == VesselStatus.DRY_DOCK:
                continue
            
            # Calculate time since last update
            time_delta = (current_time - vessel_data['last_update']).total_seconds()
            
            # Simple movement simulation
            if vessel.current_location and vessel.current_status == VesselStatus.AT_SEA:
                movement = vessel_data['movement_vector']
                speed_knots = movement['speed']
                heading = movement['heading']
                
                # Calculate new position
                distance_nm = speed_knots * (time_delta / 3600.0)
                lat_change = (distance_nm / 60.0) * math.cos(math.radians(heading))
                lon_change = (distance_nm / 60.0) * math.sin(math.radians(heading))
                
                new_lat = max(-85, min(85, vessel.current_location.latitude + lat_change))
                new_lon = max(-180, min(180, vessel.current_location.longitude + lon_change))
                
                # Update vessel location
                vessel.current_location = Location(latitude=new_lat, longitude=new_lon)
                
                # Create update
                update = HybridVesselUpdate(
                    source='simulated',
                    imo_number=vessel.imo_number,
                    mmsi=vessel.mmsi,
                    vessel_name=vessel.vessel_name,
                    vessel_type=vessel.vessel_type.value,
                    timestamp=current_time.isoformat(),
                    position={
                        'latitude': new_lat,
                        'longitude': new_lon
                    },
                    kinematics={
                        'speed_over_ground': speed_knots,
                        'course_over_ground': heading,
                        'heading': heading
                    },
                    status=vessel.current_status.value,
                    is_live_data=False
                )
                
                updates.append(update)
                vessel_data['last_update'] = current_time
                
                # Occasionally change heading/speed
                if random.random() < 0.1:
                    movement['heading'] = (movement['heading'] + random.randint(-20, 20)) % 360
                    movement['speed'] = max(5, min(25, movement['speed'] + random.uniform(-1, 1)))
        
        return updates
    
    async def register_client(self, websocket):
        """Register new WebSocket client"""
        self.connected_clients.add(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.stats['total_clients'] += 1
        
        self.logger.info(f"🔗 Client connected: {client_id} (Total: {len(self.connected_clients)})")
        
        # Send initial data
        await self.send_to_client(websocket, {
            'type': 'connection_established',
            'timestamp': datetime.now().isoformat(),
            'message': 'Connected to Live AIS + WebSocket stream',
            'live_data_enabled': self.is_live_connected,
            'fleet_summary': self._generate_fleet_summary()
        })
    
    async def unregister_client(self, websocket):
        """Unregister WebSocket client"""
        self.connected_clients.discard(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.logger.info(f"🔌 Client disconnected: {client_id} (Remaining: {len(self.connected_clients)})")
    
    async def send_to_client(self, websocket, message: Dict[str, Any]):
        """Send message to specific client"""
        try:
            await websocket.send(json.dumps(message, default=str))
        except websockets.exceptions.ConnectionClosed:
            await self.unregister_client(websocket)
        except Exception as e:
            self.logger.error(f"Error sending to client: {e}")
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.connected_clients:
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
                identifier = data.get('imo_number') or data.get('mmsi')
                vessel_data = self._get_vessel_data(identifier)
                
                response = {
                    'type': 'vessel_data',
                    'timestamp': datetime.now().isoformat(),
                    'vessel': vessel_data
                }
                await self.send_to_client(websocket, response)
            
            elif message_type == 'get_fleet_summary':
                # Get fleet summary
                summary = self._generate_fleet_summary()
                response = {
                    'type': 'fleet_summary',
                    'timestamp': datetime.now().isoformat(),
                    'summary': summary
                }
                await self.send_to_client(websocket, response)
            
            elif message_type == 'get_live_status':
                # Get live data status
                aisstream_stats = self.aisstream_client.get_statistics() if self.aisstream_client else {}
                tracker_stats = self.live_vessel_tracker.get_statistics()
                
                response = {
                    'type': 'live_status',
                    'timestamp': datetime.now().isoformat(),
                    'aisstream_connected': self.is_live_connected,
                    'aisstream_stats': aisstream_stats,
                    'tracker_stats': tracker_stats
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
    
    def _get_vessel_data(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Get vessel data by IMO or MMSI"""
        # Try live data first
        for key, vessel_data in self.hybrid_vessels.items():
            if key.startswith('live_'):
                data = vessel_data['data']
                if data.get('imo_number') == identifier or data.get('mmsi') == identifier:
                    return {
                        'source': 'live',
                        'vessel_data': data,
                        'last_update': vessel_data['last_update'].isoformat()
                    }
        
        # Try simulated data
        if identifier in self.simulated_vessels:
            vessel_data = self.simulated_vessels[identifier]
            vessel = vessel_data['vessel']
            return {
                'source': 'simulated',
                'vessel_data': {
                    'imo_number': vessel.imo_number,
                    'mmsi': vessel.mmsi,
                    'vessel_name': vessel.vessel_name,
                    'vessel_type': vessel.vessel_type.value,
                    'position': {
                        'latitude': vessel.current_location.latitude if vessel.current_location else None,
                        'longitude': vessel.current_location.longitude if vessel.current_location else None
                    },
                    'status': vessel.current_status.value
                },
                'last_update': vessel_data['last_update'].isoformat()
            }
        
        return None
    
    def _generate_fleet_summary(self) -> Dict[str, Any]:
        """Generate comprehensive fleet summary"""
        # Live vessel stats
        live_vessels = self.live_vessel_tracker.get_active_vessels()
        live_count = len(live_vessels)
        
        # Simulated vessel stats
        simulated_count = len(self.simulated_vessels)
        
        # Combined stats
        total_vessels = live_count + simulated_count
        
        # Type distribution from live vessels
        live_type_counts = {}
        for vessel in live_vessels:
            vessel_type = vessel.get('vessel_type', 'unknown')
            live_type_counts[vessel_type] = live_type_counts.get(vessel_type, 0) + 1
        
        # Status distribution from live vessels
        live_status_counts = {}
        for vessel in live_vessels:
            status = vessel.get('status', 'unknown')
            live_status_counts[status] = live_status_counts.get(status, 0) + 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_vessels': total_vessels,
            'live_vessels': live_count,
            'simulated_vessels': simulated_count,
            'live_data_enabled': self.is_live_connected,
            'live_vessel_types': live_type_counts,
            'live_vessel_status': live_status_counts,
            'connected_clients': len(self.connected_clients),
            'system_stats': self.stats
        }
    
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
        self.logger.info(f"🔄 Starting hybrid update loop (interval: {self.update_interval}s)")
        
        while self.is_running:
            try:
                # Update simulated vessels (as fallback/supplement)
                simulated_updates = self._update_simulated_vessels()
                
                # Broadcast simulated updates if we have clients
                if simulated_updates and self.connected_clients:
                    message = {
                        'type': 'vessel_updates',
                        'timestamp': datetime.now().isoformat(),
                        'update_count': len(simulated_updates),
                        'live_data_count': 0,
                        'simulated_data_count': len(simulated_updates),
                        'updates': [asdict(update) for update in simulated_updates]
                    }
                    
                    await self.broadcast_to_all(message)
                    self.stats['total_updates_sent'] += len(simulated_updates)
                
                # Send periodic fleet summary
                if random.random() < 0.1:  # 10% chance each cycle
                    summary_message = {
                        'type': 'fleet_summary_update',
                        'timestamp': datetime.now().isoformat(),
                        'summary': self._generate_fleet_summary()
                    }
                    await self.broadcast_to_all(summary_message)
                
                # Cleanup old vessels
                self.live_vessel_tracker.cleanup_old_vessels()
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(5)
    
    async def start_server(self):
        """Start the live AIS WebSocket server"""
        self.is_running = True
        
        self.logger.info(f"🚀 Starting Live AIS WebSocket Server on ws://{self.host}:{self.port}")
        self.logger.info(f"   Live data: AISStream.io integration")
        self.logger.info(f"   Fallback: {len(self.simulated_vessels)} simulated vessels")
        self.logger.info(f"   Update interval: {self.update_interval} seconds")
        
        # Start AISStream.io connection
        await self._connect_to_aisstream()
        
        # Start the WebSocket server
        server = await websockets.serve(self.handle_client, self.host, self.port)
        
        # Start the update loop
        update_task = asyncio.create_task(self.update_loop())
        
        self.logger.info(f"✅ Live AIS WebSocket server running")
        self.logger.info(f"🔗 Connect with: ws://{self.host}:{self.port}")
        
        try:
            await asyncio.gather(
                server.wait_closed(),
                update_task
            )
        except KeyboardInterrupt:
            self.logger.info(f"\n⏹️ Server shutdown requested")
        finally:
            self.is_running = False
            if self.aisstream_client:
                await self.aisstream_client.disconnect()
            server.close()
            await server.wait_closed()
            self.logger.info(f"🛑 Live AIS WebSocket server stopped")

async def main():
    """Main function to start the live AIS WebSocket server"""
    print("🌊 LIVE AIS WEBSOCKET SERVER WITH AISSTREAM.IO")
    print("=" * 65)
    
    # AISStream.io API key
    API_KEY = "8b22dbe883acb80d0c43c53d13713019791cc71f"
    
    # Create and start live WebSocket server
    server = LiveAISWebSocketServer(
        aisstream_api_key=API_KEY,
        host="localhost",
        port=8765
    )
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped by user")

if __name__ == "__main__":
    # Run the live WebSocket server
    asyncio.run(main())
