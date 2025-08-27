#!/usr/bin/env python3
"""
Enhanced Vessel Dashboard WebSocket Server
Provides categorized vessel data with detailed breakdowns and date filtering
"""

import asyncio
import websockets
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set, Optional
import logging

class EnhancedVessel:
    """Enhanced vessel representation with detailed properties"""
    
    def __init__(self, imo_number: str, mmsi: str, vessel_name: str, vessel_type: str):
        self.imo_number = imo_number
        self.mmsi = mmsi
        self.vessel_name = vessel_name
        self.vessel_type = vessel_type
        
        # Position and navigation
        self.latitude = random.uniform(-80, 80)
        self.longitude = random.uniform(-170, 170)
        self.speed = random.uniform(5, 20)
        self.heading = random.randint(0, 359)
        self.status = random.choice(['at_sea', 'in_port', 'anchored', 'dry_dock'])
        
        # Vessel details
        self.build_year = random.randint(1990, 2023)
        self.flag_country = random.choice(['Norway', 'Panama', 'Liberia', 'Singapore', 'Greece', 'Marshall Islands'])
        self.operator = f"{vessel_name.split()[0]} Shipping Co."
        
        # Specifications based on vessel type
        self._generate_specifications()
        
        # Dry dock information
        self.last_dry_dock = datetime.now() - timedelta(days=random.randint(30, 1095))
        self.dry_dock_duration = random.randint(15, 90)
        self.next_dry_dock = self.last_dry_dock + timedelta(days=random.randint(1095, 1825))
        
        # Location details
        self.current_port = self._get_port_info() if self.status == 'in_port' else None
        self.destination_port = self._get_port_info()
        self.eta = datetime.now() + timedelta(hours=random.randint(6, 168))
        
        # Update timestamps
        self.last_update = datetime.now()
        self.last_position_update = datetime.now()
        
    def _generate_specifications(self):
        """Generate realistic specifications based on vessel type"""
        if self.vessel_type == 'tanker':
            self.length = random.randint(200, 400)
            self.beam = random.randint(30, 60)
            self.gross_tonnage = random.randint(50000, 300000)
            self.deadweight = random.randint(100000, 500000)
            self.cargo_capacity = f"{self.deadweight:,} DWT"
            
        elif self.vessel_type == 'container':
            self.length = random.randint(200, 400)
            self.beam = random.randint(32, 60)
            self.gross_tonnage = random.randint(40000, 250000)
            teu_capacity = random.randint(5000, 24000)
            self.cargo_capacity = f"{teu_capacity:,} TEU"
            self.deadweight = teu_capacity * 14  # Approximate
            
        elif self.vessel_type == 'bulker':
            self.length = random.randint(180, 360)
            self.beam = random.randint(28, 65)
            self.gross_tonnage = random.randint(30000, 200000)
            self.deadweight = random.randint(75000, 400000)
            self.cargo_capacity = f"{self.deadweight:,} DWT"
            
        else:  # general_cargo
            self.length = random.randint(100, 250)
            self.beam = random.randint(16, 35)
            self.gross_tonnage = random.randint(5000, 50000)
            self.deadweight = random.randint(8000, 75000)
            self.cargo_capacity = f"{self.deadweight:,} DWT"
    
    def _get_port_info(self):
        """Generate realistic port information"""
        ports = [
            {"name": "Rotterdam", "country": "Netherlands", "code": "NLRTM"},
            {"name": "Singapore", "country": "Singapore", "code": "SGSIN"},
            {"name": "Shanghai", "country": "China", "code": "CNSHA"},
            {"name": "Antwerp", "country": "Belgium", "code": "BEANR"},
            {"name": "Hamburg", "country": "Germany", "code": "DEHAM"},
            {"name": "Los Angeles", "country": "USA", "code": "USLAX"},
            {"name": "Hong Kong", "country": "Hong Kong", "code": "HKHKG"},
            {"name": "Busan", "country": "South Korea", "code": "KRPUS"},
            {"name": "Dubai", "country": "UAE", "code": "AEDXB"},
            {"name": "Long Beach", "country": "USA", "code": "USLGB"}
        ]
        return random.choice(ports)
    
    @property
    def age_years(self):
        """Calculate vessel age in years"""
        return datetime.now().year - self.build_year
    
    @property
    def days_since_dry_dock(self):
        """Days since last dry dock"""
        return (datetime.now() - self.last_dry_dock).days
    
    @property
    def days_to_next_dry_dock(self):
        """Days until next scheduled dry dock"""
        return (self.next_dry_dock - datetime.now()).days
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'imo_number': self.imo_number,
            'mmsi': self.mmsi,
            'vessel_name': self.vessel_name,
            'vessel_type': self.vessel_type,
            'position': {
                'latitude': round(self.latitude, 6),
                'longitude': round(self.longitude, 6)
            },
            'navigation': {
                'speed': round(self.speed, 1),
                'heading': self.heading,
                'status': self.status
            },
            'specifications': {
                'length': self.length,
                'beam': self.beam,
                'gross_tonnage': self.gross_tonnage,
                'deadweight': self.deadweight,
                'cargo_capacity': self.cargo_capacity
            },
            'details': {
                'build_year': self.build_year,
                'age_years': self.age_years,
                'flag_country': self.flag_country,
                'operator': self.operator
            },
            'dry_dock': {
                'last_dry_dock': self.last_dry_dock.isoformat(),
                'days_since_dry_dock': self.days_since_dry_dock,
                'next_dry_dock': self.next_dry_dock.isoformat(),
                'days_to_next_dry_dock': self.days_to_next_dry_dock,
                'last_duration_days': self.dry_dock_duration
            },
            'ports': {
                'current_port': self.current_port,
                'destination_port': self.destination_port,
                'eta': self.eta.isoformat()
            },
            'timestamps': {
                'last_update': self.last_update.isoformat(),
                'last_position_update': self.last_position_update.isoformat()
            }
        }

class EnhancedVesselDashboardServer:
    """Enhanced WebSocket server for categorized vessel dashboard"""
    
    def __init__(self, host: str = "localhost", port: int = 8766):
        self.host = host
        self.port = port
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.is_running = False
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('EnhancedVesselServer')
        
        # Create enhanced vessel fleet
        self.vessels = []
        self._create_enhanced_fleet()
        
        # Historical data for date queries
        self.historical_positions = {}
        self._generate_historical_data()
    
    def _create_enhanced_fleet(self):
        """Create diverse fleet with different vessel types"""
        vessel_configs = [
            # Tankers
            ('Maersk Voyager', 'tanker'), ('Stena Explorer', 'tanker'), ('Nordic Pioneer', 'tanker'),
            ('Atlantic Navigator', 'tanker'), ('Pacific Guardian', 'tanker'),
            
            # Container ships
            ('COSCO Shipping Universe', 'container'), ('Ever Given', 'container'), ('MSC Gülsün', 'container'),
            ('OOCL Hong Kong', 'container'), ('CMA CGM Marco Polo', 'container'), ('APL President Wilson', 'container'),
            
            # Bulk carriers
            ('Vale Brasil', 'bulker'), ('BHP Billiton', 'bulker'), ('Ore Navigator', 'bulker'),
            ('Iron Duke', 'bulker'), ('Mineral Express', 'bulker'), ('Cargo Pioneer', 'bulker'),
            
            # General cargo
            ('Nordic Express', 'general_cargo'), ('Baltic Trader', 'general_cargo'), ('Cargo Master', 'general_cargo'),
            ('Freight Pioneer', 'general_cargo'), ('General Explorer', 'general_cargo')
        ]
        
        for i, (name, vessel_type) in enumerate(vessel_configs):
            vessel = EnhancedVessel(
                imo_number=f"IMO{9000000 + i}",
                mmsi=f"{300000000 + i}",
                vessel_name=name,
                vessel_type=vessel_type
            )
            self.vessels.append(vessel)
        
        self.logger.info(f"Created enhanced fleet: {len(self.vessels)} vessels")
    
    def _generate_historical_data(self):
        """Generate historical position data for date queries"""
        for vessel in self.vessels:
            positions = []
            current_date = datetime.now() - timedelta(days=30)
            
            while current_date <= datetime.now():
                positions.append({
                    'timestamp': current_date.isoformat(),
                    'latitude': vessel.latitude + random.uniform(-2, 2),
                    'longitude': vessel.longitude + random.uniform(-2, 2),
                    'speed': vessel.speed + random.uniform(-3, 3),
                    'status': random.choice(['at_sea', 'in_port', 'anchored'])
                })
                current_date += timedelta(hours=random.randint(4, 12))
            
            self.historical_positions[vessel.imo_number] = positions
    
    def get_vessels_by_type(self, vessel_type: str = None) -> List[EnhancedVessel]:
        """Get vessels filtered by type"""
        if vessel_type:
            return [v for v in self.vessels if v.vessel_type == vessel_type]
        return self.vessels
    
    def get_vessels_by_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get vessel data for specific date range"""
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            return {"error": "Invalid date format"}
        
        filtered_data = {}
        for imo, positions in self.historical_positions.items():
            vessel_positions = []
            for pos in positions:
                pos_dt = datetime.fromisoformat(pos['timestamp'])
                if start_dt <= pos_dt <= end_dt:
                    vessel_positions.append(pos)
            
            if vessel_positions:
                filtered_data[imo] = vessel_positions
        
        return filtered_data
    
    def get_fleet_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive fleet statistics"""
        total_vessels = len(self.vessels)
        
        # Type distribution
        type_stats = {}
        for vessel_type in ['tanker', 'container', 'bulker', 'general_cargo']:
            vessels_of_type = self.get_vessels_by_type(vessel_type)
            type_stats[vessel_type] = {
                'count': len(vessels_of_type),
                'percentage': round(len(vessels_of_type) / total_vessels * 100, 1),
                'average_age': round(sum(v.age_years for v in vessels_of_type) / len(vessels_of_type), 1) if vessels_of_type else 0,
                'in_dry_dock': len([v for v in vessels_of_type if v.status == 'dry_dock']),
                'at_sea': len([v for v in vessels_of_type if v.status == 'at_sea']),
                'in_port': len([v for v in vessels_of_type if v.status == 'in_port'])
            }
        
        # Status distribution
        status_stats = {}
        for status in ['at_sea', 'in_port', 'anchored', 'dry_dock']:
            count = len([v for v in self.vessels if v.status == status])
            status_stats[status] = {
                'count': count,
                'percentage': round(count / total_vessels * 100, 1)
            }
        
        # Age statistics
        ages = [v.age_years for v in self.vessels]
        
        # Dry dock statistics
        dry_dock_stats = {
            'vessels_in_dry_dock': len([v for v in self.vessels if v.status == 'dry_dock']),
            'average_days_since_dry_dock': round(sum(v.days_since_dry_dock for v in self.vessels) / total_vessels, 1),
            'overdue_dry_dock': len([v for v in self.vessels if v.days_to_next_dry_dock < 0])
        }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_vessels': total_vessels,
            'vessel_types': type_stats,
            'vessel_status': status_stats,
            'age_statistics': {
                'average_age': round(sum(ages) / len(ages), 1),
                'oldest_vessel': max(ages),
                'newest_vessel': min(ages)
            },
            'dry_dock_statistics': dry_dock_stats
        }
    
    async def register_client(self, websocket):
        """Register new WebSocket client"""
        self.connected_clients.add(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.logger.info(f"Client connected: {client_id}")
        
        # Send initial data
        await self.send_to_client(websocket, {
            'type': 'connection_established',
            'timestamp': datetime.now().isoformat(),
            'message': 'Connected to Enhanced Vessel Dashboard',
            'fleet_statistics': self.get_fleet_statistics()
        })
    
    async def unregister_client(self, websocket):
        """Unregister WebSocket client"""
        self.connected_clients.discard(websocket)
        if hasattr(websocket, 'remote_address'):
            client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
            self.logger.info(f"Client disconnected: {client_id}")
    
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
            
            if message_type == 'get_fleet_statistics':
                response = {
                    'type': 'fleet_statistics',
                    'data': self.get_fleet_statistics()
                }
                await self.send_to_client(websocket, response)
            
            elif message_type == 'get_vessels_by_type':
                vessel_type = data.get('vessel_type')
                vessels = self.get_vessels_by_type(vessel_type)
                response = {
                    'type': 'vessels_by_type',
                    'vessel_type': vessel_type,
                    'data': [v.to_dict() for v in vessels]
                }
                await self.send_to_client(websocket, response)
            
            elif message_type == 'get_vessel_details':
                imo_number = data.get('imo_number')
                vessel = next((v for v in self.vessels if v.imo_number == imo_number), None)
                if vessel:
                    response = {
                        'type': 'vessel_details',
                        'data': vessel.to_dict()
                    }
                    await self.send_to_client(websocket, response)
            
            elif message_type == 'query_by_date':
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                historical_data = self.get_vessels_by_date_range(start_date, end_date)
                response = {
                    'type': 'historical_data',
                    'start_date': start_date,
                    'end_date': end_date,
                    'data': historical_data
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
        """Main update loop for vessel positions"""
        self.logger.info("Starting vessel update loop...")
        
        while self.is_running:
            try:
                # Update vessel positions
                for vessel in self.vessels:
                    vessel.latitude += random.uniform(-0.001, 0.001)
                    vessel.longitude += random.uniform(-0.001, 0.001)
                    vessel.speed += random.uniform(-0.5, 0.5)
                    vessel.last_update = datetime.now()
                    
                    # Keep within bounds
                    vessel.latitude = max(-85, min(85, vessel.latitude))
                    vessel.longitude = max(-180, min(180, vessel.longitude))
                    vessel.speed = max(0, min(25, vessel.speed))
                
                # Broadcast periodic updates
                if self.connected_clients:
                    sample_vessels = random.sample(self.vessels, min(5, len(self.vessels)))
                    updates = {
                        'type': 'vessel_position_updates',
                        'timestamp': datetime.now().isoformat(),
                        'updates': [v.to_dict() for v in sample_vessels]
                    }
                    await self.broadcast_to_all(updates)
                
                await asyncio.sleep(15)  # Update every 15 seconds
                
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(5)
    
    async def start_server(self):
        """Start the WebSocket server"""
        self.is_running = True
        
        self.logger.info(f"Starting Enhanced Vessel Dashboard Server on ws://{self.host}:{self.port}")
        
        # Start the WebSocket server
        server = await websockets.serve(self.handle_client, self.host, self.port)
        
        # Start the update loop
        update_task = asyncio.create_task(self.update_loop())
        
        self.logger.info(f"Enhanced WebSocket server running")
        
        try:
            await asyncio.gather(
                server.wait_closed(),
                update_task
            )
        except KeyboardInterrupt:
            self.logger.info(f"\nServer shutdown requested")
        finally:
            self.is_running = False
            server.close()
            await server.wait_closed()
            self.logger.info(f"Enhanced WebSocket server stopped")

async def main():
    """Main function"""
    print("ENHANCED VESSEL DASHBOARD SERVER")
    print("=" * 50)
    print("Advanced vessel categorization and date query system")
    print("=" * 50)
    
    server = EnhancedVesselDashboardServer()
    f
    try:
        await server.start_server()
    except KeyboardInterrupt:
        print("\nServer stopped by user")

if __name__ == "__main__":
    asyncio.run(main())
