#!/usr/bin/env python3
"""
Live AIS WebSocket Client
Connects to live AIS WebSocket server and displays both live and simulated data
"""

import asyncio
import websockets
import json
from datetime import datetime
from typing import Dict, Any
import signal
import sys

class LiveAISWebSocketClient:
    """Client for connecting to live AIS WebSocket server"""
    
    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.is_running = False
        self.vessel_count = 0
        self.live_vessel_count = 0
        self.simulated_vessel_count = 0
        self.updates_received = 0
        self.live_updates_received = 0
        self.start_time = None
        self.live_data_enabled = False
        
    async def connect(self):
        """Connect to live AIS WebSocket server"""
        try:
            print(f"🔗 Connecting to Live AIS WebSocket server: {self.server_url}")
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
    
    async def request_vessel_data(self, identifier: str):
        """Request specific vessel data by IMO or MMSI"""
        message = {
            'type': 'get_vessel',
            'imo_number': identifier
        }
        await self.send_message(message)
    
    async def request_fleet_summary(self):
        """Request fleet summary"""
        message = {
            'type': 'get_fleet_summary'
        }
        await self.send_message(message)
    
    async def request_live_status(self):
        """Request live data status"""
        message = {
            'type': 'get_live_status'
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
        
        self.live_data_enabled = data.get('live_data_enabled', False)
        print(f"   Live data: {'✅ Enabled' if self.live_data_enabled else '❌ Disabled'}")
        
        if 'fleet_summary' in data:
            summary = data['fleet_summary']
            self.vessel_count = summary.get('total_vessels', 0)
            self.live_vessel_count = summary.get('live_vessels', 0)
            self.simulated_vessel_count = summary.get('simulated_vessels', 0)
            
            print(f"   Total vessels: {self.vessel_count}")
            print(f"   Live vessels: {self.live_vessel_count}")
            print(f"   Simulated vessels: {self.simulated_vessel_count}")
            
            # Display live vessel types if available
            live_types = summary.get('live_vessel_types', {})
            if live_types:
                print(f"   Live vessel types:")
                for vessel_type, count in live_types.items():
                    print(f"     {vessel_type.replace('_', ' ').title()}: {count}")
    
    def handle_vessel_updates(self, data: Dict[str, Any]):
        """Handle real-time vessel updates"""
        updates = data.get('updates', [])
        update_count = len(updates)
        live_count = data.get('live_data_count', 0)
        simulated_count = data.get('simulated_data_count', 0)
        
        self.updates_received += update_count
        self.live_updates_received += live_count
        
        if update_count > 0:
            # Calculate update rate
            runtime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 1
            rate = self.updates_received / runtime
            live_rate = self.live_updates_received / runtime
            
            print(f"\n📡 VESSEL UPDATES RECEIVED: {update_count} vessels")
            print(f"   Live data: {live_count} updates")
            print(f"   Simulated data: {simulated_count} updates")
            print(f"   Total updates: {self.updates_received} ({rate:.1f} updates/sec)")
            print(f"   Live updates: {self.live_updates_received} ({live_rate:.1f} live/sec)")
            print(f"   Timestamp: {data.get('timestamp', 'Unknown')}")
            
            # Show sample updates, prioritizing live data
            live_updates = [u for u in updates if u.get('is_live_data', False)]
            simulated_updates = [u for u in updates if not u.get('is_live_data', False)]
            
            print(f"   Sample updates:")
            
            # Show live updates first
            if live_updates:
                print(f"     🔴 LIVE DATA:")
                for i, update in enumerate(live_updates[:2]):
                    vessel_name = update.get('vessel_name', 'Unknown')
                    mmsi = update.get('mmsi', 'Unknown')
                    position = update.get('position', {})
                    kinematics = update.get('kinematics', {})
                    status = update.get('status', 'Unknown')
                    
                    lat = position.get('latitude', 0)
                    lon = position.get('longitude', 0)
                    speed = kinematics.get('speed_over_ground', 0)
                    heading = kinematics.get('course_over_ground', 0)
                    
                    print(f"       {i+1}. {vessel_name} (MMSI: {mmsi})")
                    print(f"          Position: ({lat:.4f}, {lon:.4f})")
                    print(f"          Speed: {speed or 0} kts, Heading: {heading or 0}°")
                    print(f"          Status: {status}")
                    if update.get('destination'):
                        print(f"          Destination: {update['destination']}")
            
            # Show simulated updates
            if simulated_updates:
                print(f"     🎭 SIMULATED DATA:")
                for i, update in enumerate(simulated_updates[:2]):
                    vessel_name = update.get('vessel_name', 'Unknown')
                    position = update.get('position', {})
                    kinematics = update.get('kinematics', {})
                    status = update.get('status', 'Unknown')
                    
                    lat = position.get('latitude', 0)
                    lon = position.get('longitude', 0)
                    speed = kinematics.get('speed_over_ground', 0)
                    heading = kinematics.get('course_over_ground', 0)
                    
                    print(f"       {i+1}. {vessel_name}")
                    print(f"          Position: ({lat:.4f}, {lon:.4f})")
                    print(f"          Speed: {speed} kts, Heading: {heading}°")
                    print(f"          Status: {status}")
            
            remaining = len(updates) - len(live_updates[:2]) - len(simulated_updates[:2])
            if remaining > 0:
                print(f"     ... and {remaining} more vessels")
    
    def handle_fleet_summary_update(self, data: Dict[str, Any]):
        """Handle fleet summary updates"""
        summary = data.get('summary', {})
        
        print(f"\n📊 FLEET SUMMARY UPDATE")
        print(f"   Total vessels: {summary.get('total_vessels', 0)}")
        print(f"   Live vessels: {summary.get('live_vessels', 0)}")
        print(f"   Simulated vessels: {summary.get('simulated_vessels', 0)}")
        print(f"   Live data enabled: {summary.get('live_data_enabled', False)}")
        print(f"   Connected clients: {summary.get('connected_clients', 0)}")
        
        # Show live vessel status
        live_status = summary.get('live_vessel_status', {})
        if live_status:
            print(f"   Live vessel status:")
            for status, count in live_status.items():
                print(f"     {status.replace('_', ' ').title()}: {count}")
        
        # Show system stats
        system_stats = summary.get('system_stats', {})
        if system_stats:
            print(f"   System stats:")
            print(f"     Live messages: {system_stats.get('live_messages_received', 0)}")
            print(f"     Total updates sent: {system_stats.get('total_updates_sent', 0)}")
    
    def handle_vessel_data(self, data: Dict[str, Any]):
        """Handle individual vessel data response"""
        vessel = data.get('vessel')
        if vessel:
            source = vessel.get('source', 'Unknown')
            vessel_data = vessel.get('vessel_data', {})
            
            print(f"\n🚢 VESSEL DATA ({source.upper()}):")
            print(f"   Name: {vessel_data.get('vessel_name', 'Unknown')}")
            
            if vessel_data.get('imo_number'):
                print(f"   IMO: {vessel_data['imo_number']}")
            if vessel_data.get('mmsi'):
                print(f"   MMSI: {vessel_data['mmsi']}")
            
            print(f"   Type: {vessel_data.get('vessel_type', 'Unknown')}")
            print(f"   Status: {vessel_data.get('status', 'Unknown')}")
            
            position = vessel_data.get('position', {})
            if position:
                lat = position.get('latitude', 0)
                lon = position.get('longitude', 0)
                print(f"   Position: ({lat:.4f}, {lon:.4f})")
            
            print(f"   Last update: {vessel.get('last_update', 'Unknown')}")
            
            if vessel_data.get('destination'):
                print(f"   Destination: {vessel_data['destination']}")
            if vessel_data.get('eta'):
                print(f"   ETA: {vessel_data['eta']}")
        else:
            print(f"   Vessel not found")
    
    def handle_live_status(self, data: Dict[str, Any]):
        """Handle live data status response"""
        print(f"\n📡 LIVE DATA STATUS:")
        print(f"   AISStream.io connected: {data.get('aisstream_connected', False)}")
        
        aisstream_stats = data.get('aisstream_stats', {})
        if aisstream_stats:
            print(f"   AISStream.io stats:")
            print(f"     Messages received: {aisstream_stats.get('messages_received', 0)}")
            print(f"     Message rate: {aisstream_stats.get('message_rate_per_second', 0)} msg/sec")
            if aisstream_stats.get('connection_time'):
                print(f"     Connected since: {aisstream_stats['connection_time']}")
        
        tracker_stats = data.get('tracker_stats', {})
        if tracker_stats:
            print(f"   Vessel tracker stats:")
            print(f"     Vessels tracked: {tracker_stats.get('total_vessels_tracked', 0)}")
            print(f"     Active vessels: {tracker_stats.get('active_vessels', 0)}")
            print(f"     Updates received: {tracker_stats.get('total_updates_received', 0)}")
    
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
        print(f"👂 Listening for live AIS updates...")
        
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
                    elif message_type == 'live_status':
                        self.handle_live_status(data)
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
        print(f"   Available commands will be shown periodically")
        print(f"   The client will automatically request data")
        
        command_cycle = 0
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Wait 30 seconds between commands
                command_cycle += 1
                
                if command_cycle == 1:
                    print(f"\n🔄 Requesting live data status...")
                    await self.request_live_status()
                elif command_cycle == 2:
                    print(f"\n🔄 Requesting fleet summary...")
                    await self.request_fleet_summary()
                elif command_cycle >= 3:
                    command_cycle = 0  # Reset cycle
                
            except KeyboardInterrupt:
                break
    
    async def run_demo(self):
        """Run demonstration of live AIS WebSocket client"""
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
    print("🌊 LIVE AIS WEBSOCKET CLIENT")
    print("=" * 50)
    print("This client connects to the Live AIS WebSocket server and displays:")
    print("• 🔴 LIVE vessel data from AISStream.io")
    print("• 🎭 SIMULATED vessel data as fallback")
    print("• Fleet statistics and composition")
    print("• Individual vessel tracking")
    print("• Live movement and status updates")
    print()
    print("Make sure the Live AIS WebSocket server is running:")
    print("python realtime_live_websocket_server.py")
    print()

async def main():
    """Main function"""
    print_client_info()
    
    # Create and run client
    client = LiveAISWebSocketClient("ws://localhost:8765")
    
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
