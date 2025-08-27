#!/usr/bin/env python3
"""
Real-Time AIS WebSocket Client
Connects to WebSocket server and displays real-time vessel updates
"""

import asyncio
import websockets
import json
from datetime import datetime
from typing import Dict, Any
import signal
import sys

class AISWebSocketClient:
    """Client for connecting to real-time AIS WebSocket server"""
    
    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.is_running = False
        self.vessel_count = 0
        self.updates_received = 0
        self.start_time = None
        
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            print(f"🔗 Connecting to AIS WebSocket server: {self.server_url}")
            self.websocket = await websockets.connect(self.server_url)
            self.is_running = True
            self.start_time = datetime.now()
            print(f"✅ Connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        self.is_running = False
        if self.websocket:
            await self.websocket.close()
            print(f"🔌 Disconnected from server")
    
    async def send_message(self, message: Dict[str, Any]):
        """Send message to server"""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                print(f"Error sending message: {e}")
    
    async def request_vessel_data(self, imo_number: str):
        """Request specific vessel data"""
        message = {
            'type': 'get_vessel',
            'imo_number': imo_number
        }
        await self.send_message(message)
    
    async def request_fleet_summary(self):
        """Request fleet summary"""
        message = {
            'type': 'get_fleet_summary'
        }
        await self.send_message(message)
    
    async def subscribe_to_updates(self, subscription_type: str = 'all'):
        """Subscribe to specific update types"""
        message = {
            'type': 'subscribe',
            'subscription_type': subscription_type
        }
        await self.send_message(message)
    
    def handle_connection_established(self, data: Dict[str, Any]):
        """Handle initial connection message"""
        print(f"\n🚢 CONNECTION ESTABLISHED")
        print(f"   Server time: {data.get('timestamp', 'Unknown')}")
        print(f"   Message: {data.get('message', 'No message')}")
        
        if 'fleet_summary' in data:
            summary = data['fleet_summary']
            self.vessel_count = summary.get('total_vessels', 0)
            print(f"   Fleet size: {self.vessel_count} vessels")
            
            # Display fleet composition
            type_dist = summary.get('type_distribution', {})
            if type_dist:
                print(f"   Fleet composition:")
                for vessel_type, count in type_dist.items():
                    percentage = (count / self.vessel_count * 100) if self.vessel_count > 0 else 0
                    print(f"     {vessel_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
    
    def handle_vessel_updates(self, data: Dict[str, Any]):
        """Handle real-time vessel updates"""
        updates = data.get('updates', [])
        update_count = len(updates)
        self.updates_received += update_count
        
        if update_count > 0:
            # Calculate update rate
            runtime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 1
            rate = self.updates_received / runtime
            
            print(f"\n📡 VESSEL UPDATES RECEIVED: {update_count} vessels")
            print(f"   Total updates: {self.updates_received} ({rate:.1f} updates/sec)")
            print(f"   Timestamp: {data.get('timestamp', 'Unknown')}")
            
            # Show sample updates
            sample_size = min(3, len(updates))
            print(f"   Sample updates:")
            
            for i, update in enumerate(updates[:sample_size]):
                vessel_name = update.get('vessel_name', 'Unknown')
                position = update.get('position', {})
                kinematics = update.get('kinematics', {})
                status = update.get('status', 'Unknown')
                
                lat = position.get('latitude', 0)
                lon = position.get('longitude', 0)
                speed = kinematics.get('speed_over_ground', 0)
                heading = kinematics.get('course_over_ground', 0)
                
                print(f"     {i+1}. {vessel_name}")
                print(f"        Position: ({lat:.4f}, {lon:.4f})")
                print(f"        Speed: {speed} kts, Heading: {heading}°")
                print(f"        Status: {status}")
            
            if len(updates) > sample_size:
                print(f"     ... and {len(updates) - sample_size} more vessels")
    
    def handle_fleet_summary_update(self, data: Dict[str, Any]):
        """Handle fleet summary updates"""
        summary = data.get('summary', {})
        
        print(f"\n📊 FLEET SUMMARY UPDATE")
        print(f"   Total vessels: {summary.get('total_vessels', 0)}")
        
        # Status distribution
        status_dist = summary.get('status_distribution', {})
        if status_dist:
            print(f"   Status distribution:")
            for status, count in status_dist.items():
                print(f"     {status.replace('_', ' ').title()}: {count}")
        
        # Vessels with routes
        routed_vessels = summary.get('vessels_with_routes', 0)
        total_vessels = summary.get('total_vessels', 1)
        route_percentage = (routed_vessels / total_vessels * 100) if total_vessels > 0 else 0
        print(f"   Vessels following routes: {routed_vessels} ({route_percentage:.1f}%)")
    
    def handle_vessel_data(self, data: Dict[str, Any]):
        """Handle individual vessel data response"""
        vessel = data.get('vessel')
        if vessel:
            print(f"\n🚢 VESSEL DATA:")
            print(f"   Name: {vessel.get('vessel_name', 'Unknown')}")
            print(f"   IMO: {vessel.get('imo_number', 'Unknown')}")
            print(f"   Type: {vessel.get('vessel_type', 'Unknown')}")
            print(f"   Status: {vessel.get('status', 'Unknown')}")
            
            position = vessel.get('current_position', {})
            if position:
                print(f"   Position: ({position.get('latitude', 0):.4f}, {position.get('longitude', 0):.4f})")
                if position.get('port_name'):
                    print(f"   Port: {position['port_name']}")
                print(f"   Last update: {position.get('last_update', 'Unknown')}")
            
            if vessel.get('route'):
                print(f"   Route: {vessel['route']}")
            if vessel.get('destination'):
                print(f"   Destination: {vessel['destination']}")
            if vessel.get('eta'):
                print(f"   ETA: {vessel['eta']}")
        else:
            print(f"   Vessel not found")
    
    def handle_subscription_confirmed(self, data: Dict[str, Any]):
        """Handle subscription confirmation"""
        subscription_type = data.get('subscription_type', 'unknown')
        print(f"✅ Subscription confirmed: {subscription_type}")
    
    def handle_error(self, data: Dict[str, Any]):
        """Handle error messages"""
        error_message = data.get('message', 'Unknown error')
        print(f"❌ Server error: {error_message}")
    
    async def listen_for_messages(self):
        """Listen for messages from server"""
        print(f"👂 Listening for real-time updates...")
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type', 'unknown')
                    
                    # Route message to appropriate handler
                    if message_type == 'connection_established':
                        self.handle_connection_established(data)
                    elif message_type == 'vessel_updates':
                        self.handle_vessel_updates(data)
                    elif message_type == 'fleet_summary_update':
                        self.handle_fleet_summary_update(data)
                    elif message_type == 'vessel_data':
                        self.handle_vessel_data(data)
                    elif message_type == 'fleet_summary':
                        self.handle_fleet_summary_update(data)
                    elif message_type == 'subscription_confirmed':
                        self.handle_subscription_confirmed(data)
                    elif message_type == 'error':
                        self.handle_error(data)
                    else:
                        print(f"🔔 Unknown message type: {message_type}")
                
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON received: {message}")
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 Connection closed by server")
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    async def interactive_commands(self):
        """Handle interactive commands from user"""
        print(f"\n💡 INTERACTIVE COMMANDS:")
        print(f"   Type 'help' for available commands")
        print(f"   Type 'quit' to exit")
        
        while self.is_running:
            try:
                # Simple input handling (in real app, use proper async input)
                await asyncio.sleep(1)
                
                # For demo purposes, automatically request data periodically
                if self.updates_received > 0 and self.updates_received % 50 == 0:
                    print(f"\n🔄 Requesting fleet summary...")
                    await self.request_fleet_summary()
                
            except KeyboardInterrupt:
                break
    
    async def run_demo(self):
        """Run demonstration of WebSocket client"""
        if not await self.connect():
            return
        
        try:
            # Subscribe to all updates
            await self.subscribe_to_updates('all')
            
            # Start listening for messages and handling commands concurrently
            await asyncio.gather(
                self.listen_for_messages(),
                self.interactive_commands()
            )
        
        except KeyboardInterrupt:
            print(f"\n⏹️ Demo interrupted by user")
        finally:
            await self.disconnect()

def print_client_info():
    """Print client information and instructions"""
    print("🌊 REAL-TIME AIS WEBSOCKET CLIENT")
    print("=" * 50)
    print("This client connects to the AIS WebSocket server and displays:")
    print("• Real-time vessel position updates")
    print("• Fleet status and composition")
    print("• Individual vessel tracking")
    print("• Live movement along shipping routes")
    print()
    print("Make sure the WebSocket server is running:")
    print("python realtime_websocket_server.py")
    print()

async def main():
    """Main function"""
    print_client_info()
    
    # Create and run client
    client = AISWebSocketClient("ws://localhost:8765")
    
    try:
        await client.run_demo()
    except KeyboardInterrupt:
        print(f"\n👋 Client stopped by user")

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print(f"\n⏹️ Stopping client...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the client
    asyncio.run(main())
