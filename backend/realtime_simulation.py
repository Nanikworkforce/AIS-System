#!/usr/bin/env python3
"""
Real-Time AIS Data Simulation System
Demonstrates how the system can be extended for real-time data updates
"""

import time
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
from dataclasses import dataclass

# Simple models for real-time simulation
@dataclass
class RealtimeVessel:
    imo_number: str
    name: str
    vessel_type: str
    latitude: float
    longitude: float
    speed_knots: float
    heading: int
    status: str
    last_update: datetime
    destination_port: str = None
    eta: datetime = None

class RealtimeAISSimulator:
    """Simulates real-time AIS data updates"""
    
    def __init__(self, fleet_size: int = 100):
        """Initialize real-time simulator"""
        self.fleet_size = fleet_size
        self.vessels = self._generate_initial_fleet()
        self.is_running = False
        self.update_interval = 30  # seconds
        self.callbacks = []
        
        # Major shipping routes (simplified)
        self.shipping_routes = [
            # Asia-Europe route
            {'start': (1.2966, 103.8764), 'end': (51.9225, 4.4792), 'name': 'Singapore-Rotterdam'},
            # Trans-Pacific route  
            {'start': (22.3526, 114.1417), 'end': (33.7701, -118.1937), 'name': 'Hong Kong-Los Angeles'},
            # Trans-Atlantic route
            {'start': (51.9225, 4.4792), 'end': (40.6892, -74.0445), 'name': 'Rotterdam-New York'},
        ]
    
    def _generate_initial_fleet(self) -> List[RealtimeVessel]:
        """Generate initial fleet positions"""
        vessels = []
        vessel_types = ['tanker', 'bulker', 'container', 'general_cargo']
        statuses = ['at_sea', 'in_port', 'anchored']
        
        for i in range(self.fleet_size):
            # Random position (simplified to major shipping areas)
            lat = random.uniform(-60, 70)
            lon = random.uniform(-180, 180)
            
            vessel = RealtimeVessel(
                imo_number=f"IMO{7000000 + i}",
                name=f"MV Realtime {i+1}",
                vessel_type=random.choice(vessel_types),
                latitude=lat,
                longitude=lon,
                speed_knots=random.uniform(0, 25),
                heading=random.randint(0, 359),
                status=random.choice(statuses),
                last_update=datetime.now()
            )
            vessels.append(vessel)
        
        return vessels
    
    def add_update_callback(self, callback):
        """Add callback function to be called on each update"""
        self.callbacks.append(callback)
    
    def start_simulation(self):
        """Start real-time simulation"""
        self.is_running = True
        simulation_thread = threading.Thread(target=self._run_simulation)
        simulation_thread.daemon = True
        simulation_thread.start()
        print(f"✅ Real-time AIS simulation started with {len(self.vessels)} vessels")
        print(f"   Update interval: {self.update_interval} seconds")
    
    def stop_simulation(self):
        """Stop real-time simulation"""
        self.is_running = False
        print("🛑 Real-time AIS simulation stopped")
    
    def _run_simulation(self):
        """Main simulation loop"""
        while self.is_running:
            try:
                # Update vessel positions and status
                updates = self._update_vessels()
                
                # Notify all callbacks
                for callback in self.callbacks:
                    try:
                        callback(updates)
                    except Exception as e:
                        print(f"Callback error: {e}")
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"Simulation error: {e}")
                break
    
    def _update_vessels(self) -> List[Dict[str, Any]]:
        """Update vessel positions and generate update records"""
        updates = []
        current_time = datetime.now()
        
        for vessel in self.vessels:
            # Simulate movement if vessel is at sea
            if vessel.status == 'at_sea' and vessel.speed_knots > 0:
                # Simple movement simulation (move in heading direction)
                distance_nm = vessel.speed_knots * (self.update_interval / 3600)  # nautical miles
                
                # Convert to lat/lon change (simplified)
                lat_change = (distance_nm / 60) * (1 if vessel.heading < 180 else -1)
                lon_change = (distance_nm / 60) * (1 if 90 < vessel.heading < 270 else -1)
                
                vessel.latitude += lat_change * random.uniform(0.8, 1.2)
                vessel.longitude += lon_change * random.uniform(0.8, 1.2)
                
                # Keep within reasonable bounds
                vessel.latitude = max(-85, min(85, vessel.latitude))
                vessel.longitude = max(-180, min(180, vessel.longitude))
            
            # Randomly change speed and heading occasionally
            if random.random() < 0.1:  # 10% chance
                vessel.speed_knots = max(0, vessel.speed_knots + random.uniform(-2, 2))
                vessel.heading = (vessel.heading + random.randint(-30, 30)) % 360
            
            # Randomly change status occasionally
            if random.random() < 0.05:  # 5% chance
                new_status = random.choice(['at_sea', 'in_port', 'anchored'])
                if new_status != vessel.status:
                    vessel.status = new_status
                    if new_status == 'in_port':
                        vessel.speed_knots = 0
            
            vessel.last_update = current_time
            
            # Create update record
            update = {
                'imo_number': vessel.imo_number,
                'timestamp': current_time.isoformat(),
                'position': {
                    'latitude': round(vessel.latitude, 6),
                    'longitude': round(vessel.longitude, 6)
                },
                'kinematics': {
                    'speed_knots': round(vessel.speed_knots, 1),
                    'heading': vessel.heading
                },
                'status': vessel.status,
                'vessel_type': vessel.vessel_type
            }
            updates.append(update)
        
        return updates
    
    def get_current_fleet_status(self) -> Dict[str, Any]:
        """Get current status of entire fleet"""
        total_vessels = len(self.vessels)
        at_sea = len([v for v in self.vessels if v.status == 'at_sea'])
        in_port = len([v for v in self.vessels if v.status == 'in_port'])
        anchored = len([v for v in self.vessels if v.status == 'anchored'])
        
        # Average speed of moving vessels
        moving_vessels = [v for v in self.vessels if v.speed_knots > 0]
        avg_speed = sum(v.speed_knots for v in moving_vessels) / len(moving_vessels) if moving_vessels else 0
        
        # Vessel type distribution
        type_counts = {}
        for vessel in self.vessels:
            type_counts[vessel.vessel_type] = type_counts.get(vessel.vessel_type, 0) + 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'fleet_summary': {
                'total_vessels': total_vessels,
                'at_sea': at_sea,
                'in_port': in_port,
                'anchored': anchored,
                'average_speed_moving': round(avg_speed, 1)
            },
            'vessel_types': type_counts,
            'vessels': [
                {
                    'imo_number': v.imo_number,
                    'name': v.name,
                    'type': v.vessel_type,
                    'position': (round(v.latitude, 4), round(v.longitude, 4)),
                    'speed': round(v.speed_knots, 1),
                    'status': v.status,
                    'last_update': v.last_update.isoformat()
                }
                for v in self.vessels
            ]
        }
    
    def get_vessel_by_imo(self, imo_number: str) -> Dict[str, Any]:
        """Get specific vessel by IMO number"""
        vessel = next((v for v in self.vessels if v.imo_number == imo_number), None)
        if not vessel:
            return None
        
        return {
            'imo_number': vessel.imo_number,
            'name': vessel.name,
            'vessel_type': vessel.vessel_type,
            'current_position': {
                'latitude': vessel.latitude,
                'longitude': vessel.longitude,
                'last_update': vessel.last_update.isoformat()
            },
            'kinematics': {
                'speed_knots': vessel.speed_knots,
                'heading': vessel.heading
            },
            'status': vessel.status,
            'destination': vessel.destination_port,
            'eta': vessel.eta.isoformat() if vessel.eta else None
        }

class RealtimeDataLogger:
    """Logs real-time updates for analysis"""
    
    def __init__(self, log_file: str = "realtime_ais_log.json"):
        self.log_file = log_file
        self.updates_received = 0
        self.start_time = datetime.now()
    
    def log_update(self, updates: List[Dict[str, Any]]):
        """Log vessel updates"""
        self.updates_received += len(updates)
        
        log_entry = {
            'batch_timestamp': datetime.now().isoformat(),
            'update_count': len(updates),
            'updates': updates
        }
        
        # Append to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"Logging error: {e}")
        
        # Print summary every 10 updates
        if self.updates_received % (10 * len(updates)) < len(updates):
            runtime = (datetime.now() - self.start_time).total_seconds()
            rate = self.updates_received / runtime if runtime > 0 else 0
            print(f"📊 Logged {self.updates_received} updates ({rate:.1f} updates/sec)")

def demonstrate_realtime_ais():
    """Demonstrate real-time AIS capabilities"""
    print("🌊 REAL-TIME AIS DATA SIMULATION DEMO")
    print("=" * 60)
    
    # Create simulator
    simulator = RealtimeAISSimulator(fleet_size=50)
    
    # Create logger
    logger = RealtimeDataLogger("demo_realtime_log.json")
    simulator.add_update_callback(logger.log_update)
    
    # Add custom callback for real-time monitoring
    def monitor_fleet(updates):
        # Count status changes
        status_changes = len([u for u in updates if 'status' in u])
        moving_vessels = len([u for u in updates if u.get('kinematics', {}).get('speed_knots', 0) > 0])
        
        if len(updates) > 0:  # Only print occasionally
            print(f"🚢 Real-time update: {len(updates)} vessels, {moving_vessels} moving")
    
    simulator.add_update_callback(monitor_fleet)
    
    try:
        # Start simulation
        simulator.start_simulation()
        
        # Show initial fleet status
        print("\n📍 INITIAL FLEET STATUS:")
        status = simulator.get_current_fleet_status()
        summary = status['fleet_summary']
        print(f"  Total Vessels: {summary['total_vessels']}")
        print(f"  At Sea: {summary['at_sea']}")
        print(f"  In Port: {summary['in_port']}")
        print(f"  Anchored: {summary['anchored']}")
        print(f"  Average Speed (moving): {summary['average_speed_moving']} knots")
        
        print(f"\n🔄 REAL-TIME SIMULATION RUNNING...")
        print(f"   Updates every {simulator.update_interval} seconds")
        print(f"   Press Ctrl+C to stop")
        
        # Run for demonstration
        for i in range(6):  # Run for 3 minutes (6 * 30 seconds)
            time.sleep(30)
            
            # Show sample vessel
            if i % 2 == 0:  # Every minute
                sample_vessel = simulator.get_vessel_by_imo(simulator.vessels[0].imo_number)
                print(f"📍 Sample vessel {sample_vessel['name']}: "
                      f"({sample_vessel['current_position']['latitude']:.4f}, "
                      f"{sample_vessel['current_position']['longitude']:.4f}) "
                      f"@ {sample_vessel['kinematics']['speed_knots']} kts, "
                      f"status: {sample_vessel['status']}")
        
        # Final status
        print(f"\n📊 FINAL FLEET STATUS:")
        final_status = simulator.get_current_fleet_status()
        final_summary = final_status['fleet_summary']
        print(f"  At Sea: {final_summary['at_sea']}")
        print(f"  In Port: {final_summary['in_port']}")
        print(f"  Anchored: {final_summary['anchored']}")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Demo interrupted by user")
    finally:
        simulator.stop_simulation()
        print(f"✅ Total updates logged: {logger.updates_received}")
        print(f"📁 Log file: {logger.log_file}")

def explain_realtime_implementation():
    """Explain how real-time data works"""
    print("\n" + "=" * 80)
    print("HOW REAL-TIME AIS DATA WORKS")
    print("=" * 80)
    
    print(f"""
🔄 CURRENT SYSTEM (Simulated Data):
   • Generates realistic but static vessel data
   • Uses historical patterns and random generation
   • Perfect for testing, development, and demonstrations
   • Data represents a "snapshot" of fleet status

🌐 REAL-TIME IMPLEMENTATION OPTIONS:

1. 📡 LIVE AIS DATA SOURCES:
   • Marine Traffic APIs (MarineTraffic, VesselFinder)
   • Satellite AIS providers (Spire, ExactEarth)
   • Terrestrial AIS receivers
   • Government maritime databases

2. 🔌 INTEGRATION METHODS:
   • REST API polling (every 1-5 minutes)
   • WebSocket streams for live updates
   • MQTT message queues for vessel updates
   • Database triggers for automatic updates

3. 🏗️ REAL-TIME ARCHITECTURE:
   • Message queue (Redis/RabbitMQ) for data ingestion
   • Background workers for data processing
   • WebSocket connections for dashboard updates
   • Caching layer for high-performance access

🛠️ IMPLEMENTATION STEPS:

1. DATA SOURCE INTEGRATION:
   ```python
   # Example: MarineTraffic API integration
   import requests
   
   def fetch_live_vessel_data():
       response = requests.get(
           'https://api.marinetraffic.com/ships',
           params={{'apikey': 'your_key', 'timespan': 10}}
       )
       return response.json()
   ```

2. REAL-TIME UPDATE SYSTEM:
   ```python
   # Background task for continuous updates
   async def update_vessel_positions():
       while True:
           live_data = fetch_live_vessel_data()
           update_database(live_data)
           broadcast_to_clients(live_data)
           await asyncio.sleep(60)  # Update every minute
   ```

3. WEBSOCKET STREAMING:
   ```python
   # Real-time dashboard updates
   @app.websocket('/ws/vessel-updates')
   async def vessel_updates(websocket):
       while True:
           updates = get_recent_updates()
           await websocket.send_json(updates)
           await asyncio.sleep(30)
   ```

💰 COST CONSIDERATIONS:
   • Free tier: Limited vessels/updates (OpenSky, some AIS feeds)
   • Commercial: $100-$1000+/month depending on coverage
   • Satellite AIS: $500-$5000+/month for global coverage
   • Self-hosted AIS receiver: $200-$1000 hardware + maintenance

🎯 USE CASE RECOMMENDATIONS:

FOR DEVELOPMENT/TESTING:
   ✅ Use current simulated system
   ✅ Perfect for proof-of-concept
   ✅ No API costs or rate limits

FOR PRODUCTION SYSTEMS:
   🔄 Integrate live AIS data sources
   🔄 Implement caching and rate limiting  
   🔄 Add data validation and error handling
   🔄 Monitor data quality and coverage

FOR DEMONSTRATIONS:
   🎭 Use real-time simulation (like above demo)
   🎭 Shows live update capabilities
   🎭 No external dependencies
""")

if __name__ == '__main__':
    try:
        demonstrate_realtime_ais()
        explain_realtime_implementation()
    except KeyboardInterrupt:
        print(f"\n👋 Demo ended")
