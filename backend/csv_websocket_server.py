#!/usr/bin/env python3
"""
CSV WebSocket Server
Serves AIS data from CSV file to frontend HTML dashboards
Replaces iostream with real CSV data for frontend consumption
"""

import asyncio
import websockets
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loaders.csv_loader import AISCSVLoader

class CSVWebSocketServer:
    """WebSocket server that serves CSV data to frontend dashboards"""
    
    def __init__(self, csv_file_path: str = None):
        """Initialize with CSV file path"""
        if csv_file_path is None:
            csv_file_path = os.path.join(os.path.dirname(__file__), 'files', 'AIS_2023_01_01.csv')
        
        self.csv_file_path = csv_file_path
        self.vessel_data = []
        self.connected_clients = set()
        self.load_csv_data()
    
    def load_csv_data(self, num_vessels: int = 500):
        """Load vessel data from CSV file"""
        try:
            print(f"🔄 Loading data from: {self.csv_file_path}")
            loader = AISCSVLoader(self.csv_file_path)
            self.vessel_data = loader.load_sample_data(num_vessels)
            print(f"✅ Loaded {len(self.vessel_data)} vessels from CSV")
        except Exception as e:
            print(f"❌ Error loading CSV data: {e}")
            self.vessel_data = []
    
    async def register_client(self, websocket):
        """Register a new client connection"""
        self.connected_clients.add(websocket)
        print(f"🔗 Client connected. Total clients: {len(self.connected_clients)}")
        
        # Send welcome message
        await self.send_to_client(websocket, {
            "type": "connection_established",
            "message": "Connected to CSV data server",
            "vessel_count": len(self.vessel_data)
        })
    
    async def unregister_client(self, websocket):
        """Unregister a client connection"""
        self.connected_clients.discard(websocket)
        print(f"🔌 Client disconnected. Total clients: {len(self.connected_clients)}")
    
    async def send_to_client(self, websocket, message: Dict[str, Any]):
        """Send message to a specific client"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            await self.unregister_client(websocket)
        except Exception as e:
            print(f"Error sending message to client: {e}")
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.connected_clients:
            await asyncio.gather(
                *[self.send_to_client(client, message) for client in self.connected_clients.copy()],
                return_exceptions=True
            )
    
    def format_vessel_for_frontend(self, vessel: Dict[str, Any]) -> Dict[str, Any]:
        """Format vessel data for frontend consumption"""
        return {
            "vessel_name": vessel.get("vessel_name", "Unknown"),
            "imo_number": vessel.get("imo_number", ""),
            "mmsi": vessel.get("mmsi", ""),
            "call_sign": vessel.get("call_sign", ""),
            "vessel_type": self.map_vessel_type(vessel.get("vessel_type", 0)),
            "location": {
                "latitude": vessel.get("latitude", 0),
                "longitude": vessel.get("longitude", 0),
                "timestamp": vessel.get("timestamp", datetime.now()).isoformat() if vessel.get("timestamp") else datetime.now().isoformat()
            },
            "navigation": {
                "speed": vessel.get("speed_over_ground", 0),
                "course": vessel.get("course_over_ground", 0),
                "heading": vessel.get("heading", 0),
                "status": "at_sea" if (vessel.get("speed_over_ground", 0) or 0) > 0.5 else "in_port"
            },
            "specifications": {
                "length": vessel.get("length", 0),
                "width": vessel.get("width", 0),
                "draft": vessel.get("draft", 0)
            },
            "details": {
                "age_years": 15,  # Default age since CSV doesn't have this
                "flag_state": "Unknown",
                "company": "Unknown"
            }
        }
    
    def map_vessel_type(self, ais_type: int) -> str:
        """Map AIS vessel type codes to frontend categories"""
        if 70 <= ais_type <= 79:
            return "general_cargo"
        elif 80 <= ais_type <= 89:
            return "tanker"
        elif ais_type in [30, 31, 32, 33, 34, 35, 36, 37, 52, 53, 54, 55, 58]:
            return "general_cargo"
        else:
            # Randomly assign container or bulker for variety
            import random
            return random.choice(["container", "bulker", "general_cargo"])
    
    def get_fleet_statistics(self) -> Dict[str, Any]:
        """Generate fleet statistics from CSV data"""
        if not self.vessel_data:
            return {
                "total_vessels": 0,
                "vessel_types": {},
                "status": {},
                "average_speed": 0,
                "total_moving": 0
            }
        
        # Calculate statistics
        total_vessels = len(self.vessel_data)
        
        # Vessel types
        vessel_types = {}
        for vessel in self.vessel_data:
            vtype = self.map_vessel_type(vessel.get("vessel_type", 0))
            vessel_types[vtype] = vessel_types.get(vtype, 0) + 1
        
        # Status statistics
        moving_vessels = len([v for v in self.vessel_data if (v.get("speed_over_ground", 0) or 0) > 0.5])
        at_sea = moving_vessels
        in_port = total_vessels - moving_vessels
        dry_dock = 0  # CSV doesn't have dry dock info
        
        # Speed statistics
        speeds = [v.get("speed_over_ground", 0) or 0 for v in self.vessel_data]
        average_speed = sum(speeds) / len(speeds) if speeds else 0
        
        return {
            "total_vessels": total_vessels,
            "vessel_types": {
                vtype: {
                    "total": count,
                    "at_sea": int(count * 0.7),  # Estimate 70% at sea
                    "in_port": int(count * 0.3),  # 30% in port
                    "average_age": 15  # Default age
                }
                for vtype, count in vessel_types.items()
            },
            "status": {
                "at_sea": at_sea,
                "in_port": in_port,
                "dry_dock": dry_dock
            },
            "average_speed": round(average_speed, 1),
            "total_moving": moving_vessels
        }
    
    def get_vessels_by_type(self, vessel_type: str) -> List[Dict[str, Any]]:
        """Get vessels filtered by type"""
        filtered_vessels = []
        for vessel in self.vessel_data:
            if self.map_vessel_type(vessel.get("vessel_type", 0)) == vessel_type:
                filtered_vessels.append(self.format_vessel_for_frontend(vessel))
        return filtered_vessels
    
    async def handle_message(self, websocket, message_data: Dict[str, Any]):
        """Handle incoming messages from clients"""
        message_type = message_data.get("type", "")
        
        print(f"📨 Received message: {message_type}")
        
        if message_type == "get_fleet_summary":
            # Send fleet statistics
            stats = self.get_fleet_statistics()
            await self.send_to_client(websocket, {
                "type": "fleet_summary",
                "data": stats
            })
        
        elif message_type == "get_vessels_by_type":
            vessel_type = message_data.get("vessel_type", "tanker")
            vessels = self.get_vessels_by_type(vessel_type)
            await self.send_to_client(websocket, {
                "type": "vessels_by_type",
                "vessel_type": vessel_type,
                "vessels": vessels[:50]  # Limit to 50 vessels
            })
        
        elif message_type == "get_live_status":
            # Send live status update
            stats = self.get_fleet_statistics()
            await self.send_to_client(websocket, {
                "type": "live_update",
                "data": stats
            })
        
        elif message_type == "get_fleet_statistics":
            # Send fleet statistics (same as fleet summary)
            stats = self.get_fleet_statistics()
            await self.send_to_client(websocket, {
                "type": "fleet_statistics",
                "data": stats
            })
        
        elif message_type == "get_historical_data":
            # For historical data, return data grouped by date
            # since CSV is a snapshot, we'll simulate historical data
            start_date = message_data.get("start_date", "2023-01-01")
            end_date = message_data.get("end_date", "2023-01-01")
            
            print(f"📅 Historical data request: {start_date} to {end_date}")
            
            # Format more vessels for historical data (show more data)
            formatted_vessels = [self.format_vessel_for_frontend(v) for v in self.vessel_data[:200]]
            
            # Create historical data structure that frontend expects
            # Frontend expects data.data to be an object with date keys
            historical_data = {}
            
            # Since CSV is a snapshot from 2023-01-01, use that date
            csv_date = "2023-01-01"
            historical_data[csv_date] = {
                "vessels": formatted_vessels,
                "summary": self.get_fleet_statistics(),
                "count": len(formatted_vessels),
                "date": csv_date
            }
            
            # Also add some simulated data for other dates in the range
            if start_date != csv_date:
                historical_data[start_date] = {
                    "vessels": formatted_vessels[:50],  # Fewer vessels for simulated dates
                    "summary": self.get_fleet_statistics(),
                    "count": len(formatted_vessels[:50]),
                    "date": start_date
                }
            
            await self.send_to_client(websocket, {
                "type": "historical_data",
                "data": historical_data,  # This should be an object with date keys
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "total_count": len(formatted_vessels),
                "available_dates": list(historical_data.keys())
            })
        
        else:
            print(f"❓ Unknown message type: {message_type}")
    
    async def handle_client(self, websocket, path):
        """Handle a client connection"""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                try:
                    message_data = json.loads(message)
                    await self.handle_message(websocket, message_data)
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON received: {message}")
                except Exception as e:
                    print(f"❌ Error handling message: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def start_server(self, host: str = "localhost", port: int = 8765):
        """Start the WebSocket server"""
        print(f"🚀 Starting CSV WebSocket Server...")
        print(f"📊 Serving {len(self.vessel_data)} vessels from CSV")
        print(f"🌐 WebSocket URL: ws://{host}:{port}")
        print(f"🔗 Frontend dashboards can now connect!")
        
        async with websockets.serve(self.handle_client, host, port):
            print(f"✅ Server running on ws://{host}:{port}")
            await asyncio.Future()  # Run forever

def main():
    """Main function to run the server"""
    server = CSVWebSocketServer()
    
    if len(server.vessel_data) == 0:
        print("❌ No CSV data loaded. Please check that AIS_2023_01_01.csv exists in the files/ directory")
        return
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")

if __name__ == "__main__":
    main()
