#!/usr/bin/env python3
"""
Simple Live AIS WebSocket Server (No pandas dependency)
Lightweight version for testing WebSocket connectivity
"""

import asyncio
import websockets
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set
import logging

class SimpleLiveVessel:
    """Simple vessel representation without complex dependencies"""
    
    def __init__(self, imo_number: str, mmsi: str, vessel_name: str, vessel_type: str):
        self.imo_number = imo_number
        self.mmsi = mmsi
        self.vessel_name = vessel_name
        self.vessel_type = vessel_type
        self.latitude = random.uniform(-90, 90)
        self.longitude = random.uniform(-180, 180)
        self.speed = random.uniform(5, 20)
        self.heading = random.randint(0, 359)
        self.status = random.choice(['at_sea', 'in_port', 'anchored'])
        self.last_update = datetime.now()

class SimpleLiveWebSocketServer:
    """Simple WebSocket server for testing"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.is_running = False
        
        # Setup logging first
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('SimpleLiveServer')
        
        # Create simple test fleet
        self.vessels = []
        self._create_test_fleet()
    
    def _create_test_fleet(self):
        """Create simple test fleet"""
        vessel_types = ['tanker', 'container', 'bulker', 'general_cargo']
        
        for i in range(20):  # Create 20 test vessels
            vessel = SimpleLiveVessel(
                imo_number=f"IMO{7000000 + i}",
                mmsi=f"{200000000 + i}",
                vessel_name=f"Test Vessel {i+1}",
                vessel_type=random.choice(vessel_types)
            )
            self.vessels.append(vessel)
        
        self.logger.info(f"Created {len(self.vessels)} test vessels")
    
    async def register_client(self, websocket):
        """Register new WebSocket client"""
        self.connected_clients.add(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.logger.info(f"🔗 Client connected: {client_id} (Total: {len(self.connected_clients)})")
        
        # Send initial data
        await self.send_to_client(websocket, {
            'type': 'connection_established',
            'timestamp': datetime.now().isoformat(),
            'message': 'Connected to Simple Live AIS WebSocket server',
            'live_data_enabled': True,
            'fleet_summary': self._generate_fleet_summary()
        })
    
    async def unregister_client(self, websocket):
        """Unregister WebSocket client"""
        self.connected_clients.discard(websocket)
        if hasattr(websocket, 'remote_address'):
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
    
    def _generate_fleet_summary(self) -> Dict[str, Any]:
        """Generate fleet summary"""
        type_counts = {}
        status_counts = {}
        
        for vessel in self.vessels:
            type_counts[vessel.vessel_type] = type_counts.get(vessel.vessel_type, 0) + 1
            status_counts[vessel.status] = status_counts.get(vessel.status, 0) + 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_vessels': len(self.vessels),
            'live_vessels': len(self.vessels),  # Simulate all as live
            'simulated_vessels': 0,
            'live_data_enabled': True,
            'live_vessel_types': type_counts,
            'live_vessel_status': status_counts,
            'connected_clients': len(self.connected_clients)
        }
    
    def _update_vessels(self) -> List[Dict[str, Any]]:
        """Update vessel positions"""
        updates = []
        
        for vessel in self.vessels:
            # Simple movement simulation
            vessel.latitude += random.uniform(-0.001, 0.001)
            vessel.longitude += random.uniform(-0.001, 0.001)
            vessel.speed += random.uniform(-0.5, 0.5)
            vessel.heading = (vessel.heading + random.randint(-5, 5)) % 360
            vessel.last_update = datetime.now()
            
            # Keep within bounds
            vessel.latitude = max(-85, min(85, vessel.latitude))
            vessel.longitude = max(-180, min(180, vessel.longitude))
            vessel.speed = max(0, min(25, vessel.speed))
            
            update = {
                'source': 'live',
                'imo_number': vessel.imo_number,
                'mmsi': vessel.mmsi,
                'vessel_name': vessel.vessel_name,
                'vessel_type': vessel.vessel_type,
                'timestamp': vessel.last_update.isoformat(),
                'position': {
                    'latitude': round(vessel.latitude, 6),
                    'longitude': round(vessel.longitude, 6)
                },
                'kinematics': {
                    'speed_over_ground': round(vessel.speed, 1),
                    'course_over_ground': vessel.heading,
                    'heading': vessel.heading
                },
                'status': vessel.status,
                'is_live_data': True
            }
            updates.append(update)
        
        return updates
    
    async def handle_client_message(self, websocket, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'get_fleet_summary':
                summary = self._generate_fleet_summary()
                response = {
                    'type': 'fleet_summary',
                    'timestamp': datetime.now().isoformat(),
                    'summary': summary
                }
                await self.send_to_client(websocket, response)
            
            elif message_type == 'get_live_status':
                response = {
                    'type': 'live_status',
                    'timestamp': datetime.now().isoformat(),
                    'aisstream_connected': True,
                    'aisstream_stats': {
                        'messages_received': 100,
                        'message_rate_per_second': 2.5,
                        'connection_time': datetime.now().isoformat()
                    },
                    'tracker_stats': {
                        'active_vessels': len(self.vessels),
                        'total_vessels_tracked': len(self.vessels)
                    }
                }
                await self.send_to_client(websocket, response)
            
            elif message_type == 'subscribe':
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
        except Exception as e:
            self.logger.error(f"Error handling client: {e}")
        finally:
            await self.unregister_client(websocket)
    
    async def update_loop(self):
        """Main update loop"""
        self.logger.info("🔄 Starting vessel update loop...")
        
        while self.is_running:
            try:
                # Update vessels
                updates = self._update_vessels()
                
                # Send updates to clients
                if updates and self.connected_clients:
                    # Send 5 random updates
                    sample_updates = random.sample(updates, min(5, len(updates)))
                    
                    message = {
                        'type': 'vessel_updates',
                        'timestamp': datetime.now().isoformat(),
                        'update_count': len(sample_updates),
                        'live_data_count': len(sample_updates),
                        'simulated_data_count': 0,
                        'updates': sample_updates
                    }
                    
                    await self.broadcast_to_all(message)
                    self.logger.info(f"📡 Sent {len(sample_updates)} updates to {len(self.connected_clients)} clients")
                
                # Wait 10 seconds between updates
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(5)
    
    async def start_server(self):
        """Start the WebSocket server"""
        self.is_running = True
        
        self.logger.info(f"🚀 Starting Simple Live WebSocket Server on ws://{self.host}:{self.port}")
        self.logger.info(f"   Test fleet: {len(self.vessels)} vessels")
        self.logger.info(f"   Update interval: 10 seconds")
        
        # Start the WebSocket server
        server = await websockets.serve(self.handle_client, self.host, self.port)
        
        # Start the update loop
        update_task = asyncio.create_task(self.update_loop())
        
        self.logger.info(f"✅ Simple WebSocket server running")
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
            server.close()
            await server.wait_closed()
            self.logger.info(f"🛑 Simple WebSocket server stopped")

async def main():
    """Main function"""
    print("🌊 SIMPLE LIVE AIS WEBSOCKET SERVER")
    print("=" * 50)
    print("Lightweight WebSocket server for testing dashboard connectivity")
    print("=" * 50)
    
    server = SimpleLiveWebSocketServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped by user")

if __name__ == "__main__":
    asyncio.run(main())
