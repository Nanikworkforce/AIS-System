#!/usr/bin/env python3
"""
Real-Time AIS API Extension
Integrates WebSocket real-time capabilities with existing Flask API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import asyncio
import threading
from datetime import datetime
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.vessel import Vessel, VesselFleet, VesselType, VesselStatus
from generators.ais_data_generator import generate_sample_fleet
from analytics.comprehensive_reports import ComprehensiveVesselReports

class RealtimeAISAPI:
    """Extended Flask API with real-time WebSocket capabilities"""
    
    def __init__(self, fleet_size: int = 500):
        """Initialize real-time API"""
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'your-secret-key-here'
        CORS(self.app)
        
        # Initialize SocketIO for WebSocket support
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Generate initial fleet
        print(f"🚢 Generating fleet with {fleet_size} vessels for real-time API...")
        self.fleet = generate_sample_fleet(fleet_size)
        self.reports = ComprehensiveVesselReports(self.fleet)
        
        # Real-time tracking data
        self.realtime_vessels = {}
        self.connected_clients = set()
        self.update_interval = 30  # seconds
        self.is_running = False
        
        # Initialize real-time tracking
        self._initialize_realtime_tracking()
        
        # Setup routes and WebSocket handlers
        self._setup_rest_routes()
        self._setup_websocket_handlers()
        
        print(f"✅ Real-time AIS API initialized with {len(self.fleet.vessels)} vessels")
    
    def _initialize_realtime_tracking(self):
        """Initialize vessels for real-time tracking"""
        import random
        from datetime import datetime
        
        for vessel in self.fleet.vessels:
            self.realtime_vessels[vessel.imo_number] = {
                'vessel': vessel,
                'last_update': datetime.now(),
                'movement_vector': {
                    'speed': random.uniform(8, 20),
                    'heading': random.randint(0, 359)
                },
                'track_history': []
            }
    
    def _setup_rest_routes(self):
        """Setup REST API endpoints"""
        
        @self.app.route('/')
        def home():
            """API documentation"""
            return jsonify({
                'name': 'Real-Time AIS API',
                'version': '2.0.0',
                'description': 'REST API + WebSocket for real-time marine vessel tracking',
                'endpoints': {
                    'REST API': {
                        'GET /api/vessels': 'Get all vessels',
                        'GET /api/vessels/<imo>': 'Get specific vessel',
                        'GET /api/realtime/status': 'Get real-time system status',
                        'GET /api/realtime/vessels': 'Get all vessels with real-time data',
                        'GET /api/realtime/vessels/<imo>/track': 'Get vessel track history',
                        'POST /api/realtime/vessels/<imo>/subscribe': 'Subscribe to vessel updates'
                    },
                    'WebSocket': {
                        'connect /': 'Connect to real-time stream',
                        'subscribe': 'Subscribe to vessel updates',
                        'get_vessel': 'Request specific vessel data',
                        'get_fleet_summary': 'Request fleet summary'
                    }
                },
                'websocket_url': 'ws://localhost:5000',
                'update_frequency': f'{self.update_interval} seconds'
            })
        
        @self.app.route('/api/vessels', methods=['GET'])
        def get_vessels():
            """Get all vessels (existing endpoint)"""
            try:
                vessels_data = [vessel.to_dict() for vessel in self.fleet.vessels]
                return jsonify({
                    'vessels': vessels_data,
                    'total_count': len(vessels_data),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/vessels/<imo_number>', methods=['GET'])
        def get_vessel_by_imo(imo_number):
            """Get specific vessel by IMO (existing endpoint)"""
            try:
                vessel = next((v for v in self.fleet.vessels if v.imo_number == imo_number), None)
                if not vessel:
                    return jsonify({'error': 'Vessel not found'}), 404
                
                return jsonify(vessel.to_dict())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/realtime/status', methods=['GET'])
        def realtime_status():
            """Get real-time system status"""
            return jsonify({
                'realtime_enabled': True,
                'connected_clients': len(self.connected_clients),
                'total_vessels': len(self.realtime_vessels),
                'update_interval': self.update_interval,
                'is_running': self.is_running,
                'last_update': datetime.now().isoformat()
            })
        
        @self.app.route('/api/realtime/vessels', methods=['GET'])
        def get_realtime_vessels():
            """Get all vessels with real-time data"""
            try:
                realtime_data = []
                for imo_number, vessel_data in self.realtime_vessels.items():
                    vessel = vessel_data['vessel']
                    
                    realtime_data.append({
                        'imo_number': vessel.imo_number,
                        'vessel_name': vessel.vessel_name,
                        'vessel_type': vessel.vessel_type.value,
                        'current_position': {
                            'latitude': vessel.current_location.latitude if vessel.current_location else None,
                            'longitude': vessel.current_location.longitude if vessel.current_location else None,
                            'port_name': vessel.current_location.port_name if vessel.current_location else None
                        },
                        'status': vessel.current_status.value,
                        'movement': vessel_data['movement_vector'],
                        'last_update': vessel_data['last_update'].isoformat()
                    })
                
                return jsonify({
                    'vessels': realtime_data,
                    'total_count': len(realtime_data),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/realtime/vessels/<imo_number>/track', methods=['GET'])
        def get_vessel_track(imo_number):
            """Get vessel track history"""
            try:
                if imo_number not in self.realtime_vessels:
                    return jsonify({'error': 'Vessel not found'}), 404
                
                vessel_data = self.realtime_vessels[imo_number]
                track_history = vessel_data.get('track_history', [])
                
                return jsonify({
                    'imo_number': imo_number,
                    'track_points': len(track_history),
                    'track_history': track_history[-100:],  # Last 100 points
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/realtime/vessels/<imo_number>/subscribe', methods=['POST'])
        def subscribe_to_vessel(imo_number):
            """Subscribe to specific vessel updates"""
            try:
                if imo_number not in self.realtime_vessels:
                    return jsonify({'error': 'Vessel not found'}), 404
                
                # In a real implementation, this would register the client for specific updates
                return jsonify({
                    'subscribed': True,
                    'imo_number': imo_number,
                    'vessel_name': self.realtime_vessels[imo_number]['vessel'].vessel_name,
                    'message': 'Subscription successful. Connect to WebSocket for live updates.'
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reports/realtime', methods=['GET'])
        def get_realtime_reports():
            """Get real-time fleet reports"""
            try:
                # Generate real-time fleet summary
                summary = self._generate_realtime_fleet_summary()
                
                return jsonify({
                    'realtime_summary': summary,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _setup_websocket_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            client_id = request.sid
            self.connected_clients.add(client_id)
            
            print(f"🔗 WebSocket client connected: {client_id} (Total: {len(self.connected_clients)})")
            
            # Send initial data
            emit('connection_established', {
                'client_id': client_id,
                'timestamp': datetime.now().isoformat(),
                'message': 'Connected to real-time AIS stream',
                'fleet_summary': self._generate_realtime_fleet_summary()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            client_id = request.sid
            self.connected_clients.discard(client_id)
            print(f"🔌 WebSocket client disconnected: {client_id} (Remaining: {len(self.connected_clients)})")
        
        @self.socketio.on('subscribe')
        def handle_subscribe(data):
            """Handle subscription requests"""
            subscription_type = data.get('subscription_type', 'all')
            client_id = request.sid
            
            # Join subscription room
            join_room(f"subscription_{subscription_type}")
            
            emit('subscription_confirmed', {
                'subscription_type': subscription_type,
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"📡 Client {client_id} subscribed to: {subscription_type}")
        
        @self.socketio.on('get_vessel')
        def handle_get_vessel(data):
            """Handle specific vessel data requests"""
            imo_number = data.get('imo_number')
            
            if imo_number and imo_number in self.realtime_vessels:
                vessel_data = self.realtime_vessels[imo_number]
                vessel = vessel_data['vessel']
                
                emit('vessel_data', {
                    'imo_number': imo_number,
                    'vessel': {
                        'imo_number': vessel.imo_number,
                        'vessel_name': vessel.vessel_name,
                        'vessel_type': vessel.vessel_type.value,
                        'current_position': {
                            'latitude': vessel.current_location.latitude if vessel.current_location else None,
                            'longitude': vessel.current_location.longitude if vessel.current_location else None,
                            'port_name': vessel.current_location.port_name if vessel.current_location else None
                        },
                        'status': vessel.current_status.value,
                        'movement': vessel_data['movement_vector'],
                        'last_update': vessel_data['last_update'].isoformat()
                    },
                    'timestamp': datetime.now().isoformat()
                })
            else:
                emit('error', {'message': f'Vessel {imo_number} not found'})
        
        @self.socketio.on('get_fleet_summary')
        def handle_get_fleet_summary():
            """Handle fleet summary requests"""
            summary = self._generate_realtime_fleet_summary()
            
            emit('fleet_summary', {
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            })
    
    def _generate_realtime_fleet_summary(self) -> dict:
        """Generate real-time fleet summary"""
        total_vessels = len(self.realtime_vessels)
        status_counts = {}
        type_counts = {}
        
        for vessel_data in self.realtime_vessels.values():
            vessel = vessel_data['vessel']
            
            # Count by status
            status = vessel.current_status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by type
            vessel_type = vessel.vessel_type.value
            type_counts[vessel_type] = type_counts.get(vessel_type, 0) + 1
        
        return {
            'total_vessels': total_vessels,
            'connected_clients': len(self.connected_clients),
            'status_distribution': status_counts,
            'type_distribution': type_counts,
            'update_interval': self.update_interval
        }
    
    def _simulate_vessel_updates(self):
        """Simulate vessel position updates"""
        import random
        import math
        from models.vessel import Location
        
        updates = []
        current_time = datetime.now()
        
        for imo_number, vessel_data in self.realtime_vessels.items():
            vessel = vessel_data['vessel']
            
            # Skip if in dry dock
            if vessel.current_status == VesselStatus.DRY_DOCK:
                continue
            
            # Calculate time since last update
            time_delta = (current_time - vessel_data['last_update']).total_seconds()
            
            # Simulate movement
            if vessel.current_location and vessel.current_status == VesselStatus.AT_SEA:
                movement = vessel_data['movement_vector']
                speed_knots = movement['speed']
                heading = movement['heading']
                
                # Calculate distance moved (simplified)
                distance_nm = speed_knots * (time_delta / 3600.0)
                
                # Convert to lat/lon change
                lat_change = (distance_nm / 60.0) * math.cos(math.radians(heading))
                lon_change = (distance_nm / 60.0) * math.sin(math.radians(heading))
                
                new_lat = vessel.current_location.latitude + lat_change
                new_lon = vessel.current_location.longitude + lon_change
                
                # Keep within bounds
                new_lat = max(-85, min(85, new_lat))
                new_lon = max(-180, min(180, new_lon))
                
                # Update vessel location
                vessel.current_location = Location(
                    latitude=new_lat,
                    longitude=new_lon
                )
                
                # Add to track history
                track_point = {
                    'timestamp': current_time.isoformat(),
                    'latitude': new_lat,
                    'longitude': new_lon,
                    'speed': speed_knots,
                    'heading': heading
                }
                vessel_data['track_history'].append(track_point)
                
                # Keep only last 1000 track points
                if len(vessel_data['track_history']) > 1000:
                    vessel_data['track_history'] = vessel_data['track_history'][-1000:]
                
                # Occasionally change heading/speed
                if random.random() < 0.1:
                    movement['heading'] = (movement['heading'] + random.randint(-30, 30)) % 360
                    movement['speed'] = max(5, min(25, movement['speed'] + random.uniform(-2, 2)))
                
                updates.append({
                    'imo_number': imo_number,
                    'vessel_name': vessel.vessel_name,
                    'vessel_type': vessel.vessel_type.value,
                    'position': {
                        'latitude': new_lat,
                        'longitude': new_lon
                    },
                    'kinematics': {
                        'speed': speed_knots,
                        'heading': heading
                    },
                    'status': vessel.current_status.value,
                    'timestamp': current_time.isoformat()
                })
            
            vessel_data['last_update'] = current_time
        
        return updates
    
    def _start_realtime_updates(self):
        """Start the real-time update loop"""
        def update_loop():
            while self.is_running:
                try:
                    # Generate vessel updates
                    updates = self._simulate_vessel_updates()
                    
                    if updates and self.connected_clients:
                        # Broadcast to all connected clients
                        self.socketio.emit('vessel_updates', {
                            'type': 'vessel_updates',
                            'timestamp': datetime.now().isoformat(),
                            'update_count': len(updates),
                            'updates': updates
                        })
                        
                        print(f"📡 Broadcasted {len(updates)} updates to {len(self.connected_clients)} clients")
                    
                    # Send periodic fleet summary
                    if random.random() < 0.2:  # 20% chance
                        summary = self._generate_realtime_fleet_summary()
                        self.socketio.emit('fleet_summary_update', {
                            'type': 'fleet_summary_update',
                            'timestamp': datetime.now().isoformat(),
                            'summary': summary
                        })
                    
                    # Wait for next update
                    import time
                    time.sleep(self.update_interval)
                
                except Exception as e:
                    print(f"Error in update loop: {e}")
                    import time
                    time.sleep(5)
        
        # Start update thread
        self.is_running = True
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
        print(f"🔄 Real-time update loop started (interval: {self.update_interval}s)")
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the real-time API server"""
        print(f"🚀 Starting Real-Time AIS API Server...")
        print(f"   Fleet size: {len(self.fleet.vessels)} vessels")
        print(f"   REST API: http://{host}:{port}")
        print(f"   WebSocket: ws://{host}:{port}")
        print(f"   Update interval: {self.update_interval} seconds")
        
        # Start real-time updates
        self._start_realtime_updates()
        
        # Run the server
        self.socketio.run(self.app, host=host, port=port, debug=debug)

def create_realtime_app(fleet_size: int = 500):
    """Factory function to create real-time app"""
    return RealtimeAISAPI(fleet_size=fleet_size)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-Time AIS API Server')
    parser.add_argument('--fleet-size', type=int, default=500,
                       help='Number of vessels to generate (default: 500)')
    parser.add_argument('--host', default='0.0.0.0',
                       help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--update-interval', type=int, default=30,
                       help='Update interval in seconds (default: 30)')
    
    args = parser.parse_args()
    
    # Create and run the real-time API
    api = RealtimeAISAPI(fleet_size=args.fleet_size)
    api.update_interval = args.update_interval
    api.run(host=args.host, port=args.port, debug=args.debug)
