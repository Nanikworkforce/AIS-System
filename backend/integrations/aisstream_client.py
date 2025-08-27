#!/usr/bin/env python3
"""
AISStream.io Integration Client
Connects to AISStream.io for live AIS data and integrates with WebSocket system
"""

import asyncio
import websockets
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import logging
from dataclasses import dataclass
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.vessel import Vessel, VesselType, VesselStatus, ServiceLine, Location

@dataclass
class LiveAISMessage:
    """Parsed AIS message from AISStream.io"""
    mmsi: str
    imo_number: Optional[str]
    vessel_name: Optional[str]
    timestamp: datetime
    latitude: float
    longitude: float
    speed_over_ground: Optional[float]
    course_over_ground: Optional[float]
    heading: Optional[float]
    vessel_type: Optional[str]
    destination: Optional[str]
    eta: Optional[str]
    draught: Optional[float]
    length: Optional[int]
    width: Optional[int]
    status: Optional[str]
    raw_data: Dict[str, Any]

class AISStreamClient:
    """Client for connecting to AISStream.io live data"""
    
    def __init__(self, api_key: str):
        """Initialize AISStream client"""
        self.api_key = api_key
        self.websocket = None
        self.is_connected = False
        self.message_callbacks = []
        self.error_callbacks = []
        self.stats = {
            'messages_received': 0,
            'vessels_tracked': 0,
            'connection_time': None,
            'last_message_time': None
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('AISStream')
        
        # AISStream.io WebSocket URL
        self.ws_url = "wss://stream.aisstream.io/v0/stream"
        
        # Vessel type mapping from AIS to our system
        self.vessel_type_mapping = {
            30: 'general_cargo',  # Fishing
            31: 'general_cargo',  # Towing
            32: 'general_cargo',  # Dredging
            33: 'general_cargo',  # Diving ops
            34: 'general_cargo',  # Military ops
            35: 'general_cargo',  # Sailing
            36: 'general_cargo',  # Pleasure craft
            37: 'general_cargo',  # High speed craft
            40: 'general_cargo',  # Pilot vessel
            50: 'general_cargo',  # Law enforcement
            51: 'general_cargo',  # SAR
            52: 'general_cargo',  # Tug
            53: 'general_cargo',  # Port tender
            54: 'general_cargo',  # Anti-pollution
            55: 'general_cargo',  # Law enforcement
            56: 'general_cargo',  # Spare
            57: 'general_cargo',  # Spare
            58: 'general_cargo',  # Medical transport
            59: 'general_cargo',  # Ships according to RR Resolution
            60: 'general_cargo',  # Passenger
            61: 'general_cargo',  # Passenger
            62: 'general_cargo',  # Passenger
            63: 'general_cargo',  # Passenger
            64: 'general_cargo',  # Passenger
            65: 'general_cargo',  # Passenger
            66: 'general_cargo',  # Passenger
            67: 'general_cargo',  # Passenger
            68: 'general_cargo',  # Passenger
            69: 'general_cargo',  # Passenger
            70: 'general_cargo',  # Cargo
            71: 'general_cargo',  # Cargo
            72: 'general_cargo',  # Cargo
            73: 'general_cargo',  # Cargo
            74: 'general_cargo',  # Cargo
            75: 'general_cargo',  # Cargo
            76: 'general_cargo',  # Cargo
            77: 'general_cargo',  # Cargo
            78: 'general_cargo',  # Cargo
            79: 'general_cargo',  # Cargo
            80: 'tanker',         # Tanker
            81: 'tanker',         # Tanker
            82: 'tanker',         # Tanker
            83: 'tanker',         # Tanker
            84: 'tanker',         # Tanker
            85: 'tanker',         # Tanker
            86: 'tanker',         # Tanker
            87: 'tanker',         # Tanker
            88: 'tanker',         # Tanker
            89: 'tanker',         # Tanker
        }
        
        # Navigation status mapping
        self.status_mapping = {
            0: 'at_sea',          # Under way using engine
            1: 'anchored',        # At anchor
            2: 'at_sea',          # Not under command
            3: 'at_sea',          # Restricted manoeuvrability
            4: 'at_sea',          # Constrained by draught
            5: 'in_port',         # Moored
            6: 'at_sea',          # Aground
            7: 'at_sea',          # Engaged in fishing
            8: 'at_sea',          # Under way sailing
            9: 'at_sea',          # Reserved for future use
            10: 'at_sea',         # Reserved for future use
            11: 'at_sea',         # Power-driven vessel towing astern
            12: 'at_sea',         # Power-driven vessel pushing ahead
            13: 'at_sea',         # Reserved for future use
            14: 'at_sea',         # AIS-SART
            15: 'at_sea',         # Undefined
        }
    
    def add_message_callback(self, callback: Callable[[LiveAISMessage], None]):
        """Add callback for AIS messages"""
        self.message_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str], None]):
        """Add callback for errors"""
        self.error_callbacks.append(callback)
    
    async def connect(self, bounding_box: Dict[str, float] = None, 
                     vessel_types: List[str] = None) -> bool:
        """
        Connect to AISStream.io
        
        Args:
            bounding_box: Geographic area to monitor
                         {"north": 90, "south": -90, "east": 180, "west": -180}
            vessel_types: List of vessel types to filter
        """
        try:
            self.logger.info("Connecting to AISStream.io...")
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(self.ws_url)
            self.is_connected = True
            self.stats['connection_time'] = datetime.now()
            
            # Send subscription message
            subscription = {
                "APIKey": self.api_key,
                "BoundingBoxes": [bounding_box] if bounding_box else [
                    # Default: Global coverage (split into regions for performance)
                    {"north": 90, "south": 0, "east": 180, "west": -180},    # Northern hemisphere
                    {"north": 0, "south": -90, "east": 180, "west": -180}    # Southern hemisphere
                ],
                "FilterMessageTypes": ["PositionReport"],  # Focus on position updates
            }
            
            # Add vessel type filter if specified
            if vessel_types:
                subscription["FilterShipAndCargoTypes"] = vessel_types
            
            await self.websocket.send(json.dumps(subscription))
            self.logger.info("✅ Connected to AISStream.io successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to AISStream.io: {e}")
            self.is_connected = False
            for callback in self.error_callbacks:
                callback(f"Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from AISStream.io"""
        self.is_connected = False
        if self.websocket:
            await self.websocket.close()
            self.logger.info("🔌 Disconnected from AISStream.io")
    
    def parse_ais_message(self, raw_data: Dict[str, Any]) -> Optional[LiveAISMessage]:
        """Parse raw AIS message from AISStream.io"""
        try:
            # Extract message data
            message = raw_data.get('Message', {})
            position_report = message.get('PositionReport', {})
            metadata = raw_data.get('MetaData', {})
            
            # Skip if no position data
            if not position_report:
                return None
            
            # Extract MMSI (required)
            mmsi = str(message.get('UserID', ''))
            if not mmsi:
                return None
            
            # Extract position (required)
            latitude = position_report.get('Latitude')
            longitude = position_report.get('Longitude')
            if latitude is None or longitude is None:
                return None
            
            # Parse timestamp
            timestamp_str = metadata.get('time_utc', '')
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.utcnow()
            
            # Extract optional fields
            speed = position_report.get('Sog')  # Speed over ground
            course = position_report.get('Cog')  # Course over ground
            heading = position_report.get('TrueHeading')
            nav_status = position_report.get('NavigationalStatus')
            
            # Extract ship and voyage data if available
            ship_data = message.get('ShipAndCargoData', {})
            voyage_data = message.get('VoyageData', {})
            
            vessel_name = ship_data.get('Name', '').strip() or None
            imo_number = ship_data.get('ImoNumber')
            if imo_number:
                imo_number = f"IMO{imo_number}"
            
            destination = voyage_data.get('Destination', '').strip() or None
            eta = voyage_data.get('Eta')
            draught = voyage_data.get('MaximumStaticDraught')
            
            # Map vessel type
            ais_ship_type = ship_data.get('Type')
            vessel_type = None
            if ais_ship_type:
                # Determine vessel type based on AIS ship type
                if 80 <= ais_ship_type <= 89:
                    vessel_type = 'tanker'
                elif 70 <= ais_ship_type <= 79:
                    if 'container' in (vessel_name or '').lower():
                        vessel_type = 'container'
                    elif 'bulk' in (vessel_name or '').lower():
                        vessel_type = 'bulker'
                    else:
                        vessel_type = 'general_cargo'
                else:
                    vessel_type = self.vessel_type_mapping.get(ais_ship_type, 'general_cargo')
            
            # Map navigation status
            status = None
            if nav_status is not None:
                status = self.status_mapping.get(nav_status, 'at_sea')
            
            # Get vessel dimensions
            dimensions = ship_data.get('Dimensions', {})
            length = None
            width = None
            if dimensions:
                length = dimensions.get('A', 0) + dimensions.get('B', 0)
                width = dimensions.get('C', 0) + dimensions.get('D', 0)
            
            return LiveAISMessage(
                mmsi=mmsi,
                imo_number=imo_number,
                vessel_name=vessel_name,
                timestamp=timestamp,
                latitude=latitude,
                longitude=longitude,
                speed_over_ground=speed,
                course_over_ground=course,
                heading=heading,
                vessel_type=vessel_type,
                destination=destination,
                eta=eta,
                draught=draught,
                length=length,
                width=width,
                status=status,
                raw_data=raw_data
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to parse AIS message: {e}")
            return None
    
    async def listen(self):
        """Listen for AIS messages from AISStream.io"""
        if not self.is_connected or not self.websocket:
            raise RuntimeError("Not connected to AISStream.io")
        
        self.logger.info("👂 Listening for live AIS messages...")
        
        try:
            async for message in self.websocket:
                try:
                    # Parse JSON message
                    raw_data = json.loads(message)
                    
                    # Parse AIS message
                    ais_message = self.parse_ais_message(raw_data)
                    
                    if ais_message:
                        # Update statistics
                        self.stats['messages_received'] += 1
                        self.stats['last_message_time'] = datetime.now()
                        
                        # Notify callbacks
                        for callback in self.message_callbacks:
                            try:
                                callback(ais_message)
                            except Exception as e:
                                self.logger.error(f"Callback error: {e}")
                        
                        # Log every 100th message
                        if self.stats['messages_received'] % 100 == 0:
                            self.logger.info(f"📡 Processed {self.stats['messages_received']} AIS messages")
                
                except json.JSONDecodeError:
                    self.logger.warning("Received invalid JSON from AISStream.io")
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("🔌 Connection to AISStream.io closed")
            self.is_connected = False
        except Exception as e:
            self.logger.error(f"❌ Error in AISStream listener: {e}")
            self.is_connected = False
            for callback in self.error_callbacks:
                callback(f"Listener error: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connection and message statistics"""
        runtime = None
        message_rate = 0
        
        if self.stats['connection_time']:
            runtime = (datetime.now() - self.stats['connection_time']).total_seconds()
            if runtime > 0:
                message_rate = self.stats['messages_received'] / runtime
        
        return {
            'connected': self.is_connected,
            'connection_time': self.stats['connection_time'].isoformat() if self.stats['connection_time'] else None,
            'runtime_seconds': runtime,
            'messages_received': self.stats['messages_received'],
            'message_rate_per_second': round(message_rate, 2),
            'last_message_time': self.stats['last_message_time'].isoformat() if self.stats['last_message_time'] else None,
            'vessels_tracked': self.stats['vessels_tracked']
        }

class LiveVesselTracker:
    """Tracks live vessels from AISStream.io data"""
    
    def __init__(self):
        """Initialize vessel tracker"""
        self.vessels = {}  # MMSI -> vessel data
        self.vessel_updates = []  # Recent updates
        self.update_callbacks = []
        self.max_vessel_age = timedelta(hours=6)  # Remove vessels older than 6 hours
        
        # Setup logging
        self.logger = logging.getLogger('VesselTracker')
    
    def add_update_callback(self, callback: Callable[[List[Dict[str, Any]]], None]):
        """Add callback for vessel updates"""
        self.update_callbacks.append(callback)
    
    def update_vessel(self, ais_message: LiveAISMessage):
        """Update vessel from AIS message"""
        mmsi = ais_message.mmsi
        
        # Create or update vessel record
        if mmsi not in self.vessels:
            # New vessel
            self.vessels[mmsi] = {
                'mmsi': mmsi,
                'imo_number': ais_message.imo_number,
                'vessel_name': ais_message.vessel_name or f"Unknown-{mmsi}",
                'vessel_type': ais_message.vessel_type or 'general_cargo',
                'first_seen': ais_message.timestamp,
                'track_history': []
            }
            self.logger.info(f"🆕 New vessel: {self.vessels[mmsi]['vessel_name']} (MMSI: {mmsi})")
        
        vessel = self.vessels[mmsi]
        
        # Update vessel data
        vessel['last_update'] = ais_message.timestamp
        vessel['position'] = {
            'latitude': ais_message.latitude,
            'longitude': ais_message.longitude
        }
        vessel['kinematics'] = {
            'speed_over_ground': ais_message.speed_over_ground,
            'course_over_ground': ais_message.course_over_ground,
            'heading': ais_message.heading
        }
        vessel['status'] = ais_message.status or 'at_sea'
        vessel['destination'] = ais_message.destination
        vessel['eta'] = ais_message.eta
        
        # Update vessel info if available
        if ais_message.vessel_name and vessel['vessel_name'].startswith('Unknown-'):
            vessel['vessel_name'] = ais_message.vessel_name
            
        if ais_message.imo_number and not vessel['imo_number']:
            vessel['imo_number'] = ais_message.imo_number
        
        # Add to track history
        track_point = {
            'timestamp': ais_message.timestamp.isoformat(),
            'latitude': ais_message.latitude,
            'longitude': ais_message.longitude,
            'speed': ais_message.speed_over_ground,
            'heading': ais_message.heading
        }
        vessel['track_history'].append(track_point)
        
        # Keep only last 100 track points
        if len(vessel['track_history']) > 100:
            vessel['track_history'] = vessel['track_history'][-100:]
        
        # Create update record
        update = {
            'type': 'live_ais_update',
            'source': 'aisstream.io',
            'timestamp': ais_message.timestamp.isoformat(),
            'mmsi': mmsi,
            'imo_number': ais_message.imo_number,
            'vessel_name': vessel['vessel_name'],
            'vessel_type': vessel['vessel_type'],
            'position': vessel['position'],
            'kinematics': vessel['kinematics'],
            'status': vessel['status'],
            'destination': ais_message.destination,
            'eta': ais_message.eta
        }
        
        # Add to recent updates
        self.vessel_updates.append(update)
        
        # Keep only last 1000 updates
        if len(self.vessel_updates) > 1000:
            self.vessel_updates = self.vessel_updates[-1000:]
        
        # Notify callbacks
        for callback in self.update_callbacks:
            try:
                callback([update])
            except Exception as e:
                self.logger.error(f"Update callback error: {e}")
    
    def cleanup_old_vessels(self):
        """Remove vessels that haven't been seen recently"""
        current_time = datetime.utcnow()
        old_vessels = []
        
        for mmsi, vessel in self.vessels.items():
            if current_time - vessel.get('last_update', vessel['first_seen']) > self.max_vessel_age:
                old_vessels.append(mmsi)
        
        for mmsi in old_vessels:
            del self.vessels[mmsi]
            self.logger.info(f"🗑️ Removed old vessel: MMSI {mmsi}")
    
    def get_active_vessels(self) -> List[Dict[str, Any]]:
        """Get list of currently active vessels"""
        current_time = datetime.utcnow()
        active_vessels = []
        
        for vessel in self.vessels.values():
            # Only include vessels seen in last hour
            if current_time - vessel.get('last_update', vessel['first_seen']) <= timedelta(hours=1):
                active_vessels.append(vessel)
        
        return active_vessels
    
    def get_vessel_by_mmsi(self, mmsi: str) -> Optional[Dict[str, Any]]:
        """Get vessel by MMSI"""
        return self.vessels.get(mmsi)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        total_vessels = len(self.vessels)
        active_vessels = len(self.get_active_vessels())
        
        # Count by vessel type
        type_counts = {}
        for vessel in self.vessels.values():
            vessel_type = vessel.get('vessel_type', 'unknown')
            type_counts[vessel_type] = type_counts.get(vessel_type, 0) + 1
        
        # Count by status
        status_counts = {}
        for vessel in self.get_active_vessels():
            status = vessel.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_vessels_tracked': total_vessels,
            'active_vessels': active_vessels,
            'total_updates_received': len(self.vessel_updates),
            'vessel_types': type_counts,
            'vessel_status': status_counts,
            'timestamp': datetime.utcnow().isoformat()
        }

# Example usage and testing
async def test_aisstream_integration():
    """Test AISStream.io integration"""
    API_KEY = "8b22dbe883acb80d0c43c53d13713019791cc71f"
    
    print("🧪 Testing AISStream.io Integration")
    print("=" * 50)
    
    # Create client and tracker
    client = AISStreamClient(API_KEY)
    tracker = LiveVesselTracker()
    
    # Add vessel tracker callback
    def handle_ais_message(ais_message: LiveAISMessage):
        tracker.update_vessel(ais_message)
        print(f"📡 {ais_message.vessel_name or 'Unknown'} (MMSI: {ais_message.mmsi}) "
              f"at ({ais_message.latitude:.4f}, {ais_message.longitude:.4f}) "
              f"@ {ais_message.speed_over_ground or 0} kts")
    
    client.add_message_callback(handle_ais_message)
    
    # Add error callback
    def handle_error(error_msg: str):
        print(f"❌ Error: {error_msg}")
    
    client.add_error_callback(handle_error)
    
    try:
        # Connect to AISStream.io
        # Focus on a specific area for testing (North Sea)
        bounding_box = {
            "north": 60.0,
            "south": 50.0, 
            "east": 10.0,
            "west": -5.0
        }
        
        connected = await client.connect(bounding_box=bounding_box)
        
        if connected:
            print(f"✅ Connected to AISStream.io")
            print(f"📡 Monitoring North Sea area...")
            print(f"🎯 Press Ctrl+C to stop")
            
            # Listen for messages for 60 seconds
            try:
                await asyncio.wait_for(client.listen(), timeout=60.0)
            except asyncio.TimeoutError:
                print(f"\n⏰ Test completed after 60 seconds")
            
            # Show statistics
            client_stats = client.get_statistics()
            tracker_stats = tracker.get_statistics()
            
            print(f"\n📊 AISStream.io Statistics:")
            print(f"   Messages received: {client_stats['messages_received']}")
            print(f"   Message rate: {client_stats['message_rate_per_second']:.2f} msg/sec")
            
            print(f"\n🚢 Vessel Tracking Statistics:")
            print(f"   Vessels tracked: {tracker_stats['total_vessels_tracked']}")
            print(f"   Active vessels: {tracker_stats['active_vessels']}")
            print(f"   Vessel types: {tracker_stats['vessel_types']}")
        
        else:
            print(f"❌ Failed to connect to AISStream.io")
    
    except KeyboardInterrupt:
        print(f"\n⏹️ Test stopped by user")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_aisstream_integration())
