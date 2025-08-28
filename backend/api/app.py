"""
Flask API Backend for AIS Marine Vessel System
Provides REST endpoints for vessel data retrieval and management
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Any, Optional

# Import our custom modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.vessel import Vessel, VesselFleet, VesselType, VesselStatus, ServiceLine
from generators.ais_data_generator import AISDataGenerator, generate_sample_fleet
from data_loaders.csv_loader import AISCSVLoader
from analytics.vessel_analytics import VesselAnalytics, create_analytics_dashboard_data
from analytics.comprehensive_reports import ComprehensiveVesselReports


class AISFlaskApp:
    """Main Flask application for AIS system"""
    
    def __init__(self, fleet_size: int = 1000, use_csv_data: bool = False):
        """Initialize Flask app with vessel fleet"""
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'your-secret-key-here'
        
        # Enable CORS for frontend access with specific configuration
        CORS(self.app, 
             origins=["*"],  # Allow all origins for development
             supports_credentials=True,
             allow_headers=["Content-Type", "Authorization"],
             methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
        
        # Initialize SocketIO for WebSocket support with compatible async mode
        self.socketio = SocketIO(
            self.app, 
            cors_allowed_origins="*",
            async_mode='threading',  # Use threading for maximum compatibility
            logger=True,  # Enable logging to debug connection issues
            engineio_logger=True,
            ping_timeout=60,
            ping_interval=25,
            allow_upgrades=True,
            transports=['polling', 'websocket']
        )
        
        # Generate or load vessel fleet
        print(f"Generating fleet with {fleet_size} vessels...")
        self.fleet = generate_sample_fleet(fleet_size)
        self.analytics = VesselAnalytics(self.fleet)
        self.comprehensive_reports = ComprehensiveVesselReports(self.fleet)
        print("Fleet generated successfully!")
        
        # Initialize CSV loader for historical data
        try:
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'files', 'AIS_2023_01_01.csv')
            self.csv_loader = AISCSVLoader(csv_path)
            print(f"✅ CSV loader initialized: {csv_path}")
        except Exception as e:
            print(f"⚠️ CSV loader not available: {e}")
            self.csv_loader = None
        
        # Setup routes and WebSocket handlers
        self._setup_routes()
        self._setup_websocket_handlers()
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        @self.app.route('/')
        def home():
            """Home page with API documentation"""
            return jsonify({
                'message': 'AIS Marine Vessel System API',
                'version': '1.0.0',
                'description': 'REST API for marine vessel tracking and analytics',
                'endpoints': {
                    'GET /api/vessels': 'Get all vessels with optional filtering',
                    'GET /api/vessels/<imo>': 'Get specific vessel by IMO number',
                    'GET /api/vessels/type/<vessel_type>': 'Get vessels by type',
                    'GET /api/vessels/status/<status>': 'Get vessels by status',
                    'GET /api/vessels/country/<country>': 'Get vessels by flag state',
                    'GET /api/dry-dock': 'Get dry dock information',
                    'GET /api/analytics': 'Get fleet analytics',
                    'GET /api/analytics/dashboard': 'Get dashboard data',
                    'GET /api/statistics': 'Get fleet statistics',
                    'GET /api/locations': 'Get vessel locations',
                    'GET /api/recommendations': 'Get fleet management recommendations',
                    'GET /api/reports/comprehensive': 'Get comprehensive fleet report',
                    'GET /api/reports/vessel-types': 'Get detailed vessel type analysis',
                    'GET /api/reports/dry-dock': 'Get comprehensive dry dock analysis',
                    'GET /api/reports/countries': 'Get countries and service areas analysis',
                    'GET /api/reports/age-analysis': 'Get vessel age comprehensive analysis'
                },
                'query_parameters': {
                    'limit': 'Limit number of results',
                    'offset': 'Offset for pagination',
                    'vessel_type': 'Filter by vessel type (tanker, bulker, container, general_cargo)',
                    'status': 'Filter by status (at_sea, in_port, dry_dock, anchored, under_repair)',
                    'country': 'Filter by flag state country',
                    'min_age': 'Minimum vessel age in years',
                    'max_age': 'Maximum vessel age in years'
                }
            })
        
        @self.app.route('/api/vessels', methods=['GET'])
        def get_vessels():
            """Get all vessels with optional filtering"""
            try:
                # Get query parameters
                limit = request.args.get('limit', type=int, default=100)
                offset = request.args.get('offset', type=int, default=0)
                vessel_type = request.args.get('vessel_type')
                status = request.args.get('status')
                country = request.args.get('country')
                min_age = request.args.get('min_age', type=float)
                max_age = request.args.get('max_age', type=float)
                
                # Start with all vessels
                vessels = self.fleet.vessels
                
                # Apply filters
                if vessel_type:
                    try:
                        vtype = VesselType(vessel_type.lower())
                        vessels = [v for v in vessels if v.vessel_type == vtype]
                    except ValueError:
                        return jsonify({'error': f'Invalid vessel type: {vessel_type}'}), 400
                
                if status:
                    try:
                        vstatus = VesselStatus(status.lower())
                        vessels = [v for v in vessels if v.current_status == vstatus]
                    except ValueError:
                        return jsonify({'error': f'Invalid status: {status}'}), 400
                
                if country:
                    vessels = [v for v in vessels if v.flag_state.lower() == country.lower()]
                
                if min_age is not None:
                    vessels = [v for v in vessels if v.age_years >= min_age]
                
                if max_age is not None:
                    vessels = [v for v in vessels if v.age_years <= max_age]
                
                # Apply pagination
                total_count = len(vessels)
                vessels_page = vessels[offset:offset + limit]
                
                # Convert to dict format
                vessels_data = [vessel.to_dict() for vessel in vessels_page]
                
                return jsonify({
                    'vessels': vessels_data,
                    'pagination': {
                        'total': total_count,
                        'limit': limit,
                        'offset': offset,
                        'has_next': offset + limit < total_count,
                        'has_prev': offset > 0
                    },
                    'filters_applied': {
                        'vessel_type': vessel_type,
                        'status': status,
                        'country': country,
                        'min_age': min_age,
                        'max_age': max_age
                    }
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/vessels/<imo_number>', methods=['GET'])
        def get_vessel_by_imo(imo_number):
            """Get specific vessel by IMO number"""
            try:
                vessel = next((v for v in self.fleet.vessels if v.imo_number == imo_number), None)
                
                if not vessel:
                    return jsonify({'error': 'Vessel not found'}), 404
                
                # Include detailed dry dock history
                vessel_data = vessel.to_dict()
                vessel_data['dry_dock_history'] = [
                    {
                        'start_date': record.start_date.isoformat(),
                        'end_date': record.end_date.isoformat() if record.end_date else None,
                        'location': str(record.location),
                        'purpose': record.purpose,
                        'cost_estimate': record.cost_estimate,
                        'duration_days': record.duration_days,
                        'completed': record.completed
                    }
                    for record in vessel.dry_dock_history
                ]
                
                return jsonify(vessel_data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/vessels/type/<vessel_type>', methods=['GET'])
        def get_vessels_by_type(vessel_type):
            """Get vessels by type"""
            try:
                vtype = VesselType(vessel_type.lower())
                vessels = self.fleet.get_by_type(vtype)
                
                limit = request.args.get('limit', type=int, default=50)
                offset = request.args.get('offset', type=int, default=0)
                
                total_count = len(vessels)
                vessels_page = vessels[offset:offset + limit]
                vessels_data = [vessel.to_dict() for vessel in vessels_page]
                
                return jsonify({
                    'vessel_type': vessel_type,
                    'total_count': total_count,
                    'vessels': vessels_data,
                    'pagination': {
                        'limit': limit,
                        'offset': offset,
                        'has_next': offset + limit < total_count
                    }
                })
                
            except ValueError:
                return jsonify({'error': f'Invalid vessel type: {vessel_type}'}), 400
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/vessels/status/<status>', methods=['GET'])
        def get_vessels_by_status(status):
            """Get vessels by status"""
            try:
                vstatus = VesselStatus(status.lower())
                vessels = self.fleet.get_by_status(vstatus)
                
                vessels_data = [vessel.to_dict() for vessel in vessels]
                
                return jsonify({
                    'status': status,
                    'count': len(vessels),
                    'vessels': vessels_data
                })
                
            except ValueError:
                return jsonify({'error': f'Invalid status: {status}'}), 400
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/vessels/country/<country>', methods=['GET'])
        def get_vessels_by_country(country):
            """Get vessels by flag state country"""
            try:
                vessels = self.fleet.get_by_flag_state(country)
                vessels_data = [vessel.to_dict() for vessel in vessels]
                
                return jsonify({
                    'country': country,
                    'count': len(vessels),
                    'vessels': vessels_data
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/dry-dock', methods=['GET'])
        def get_dry_dock_info():
            """Get comprehensive dry dock information"""
            try:
                vessels_in_dry_dock = self.fleet.get_vessels_in_dry_dock()
                
                # Get dry dock schedule
                schedule = self.analytics.generate_dry_dock_schedule()
                
                # Dry dock statistics by type
                dry_dock_stats = {}
                for vessel_type in VesselType:
                    type_vessels = self.fleet.get_by_type(vessel_type)
                    type_in_dry_dock = [v for v in type_vessels if v.current_dry_dock is not None]
                    
                    dry_dock_stats[vessel_type.value] = {
                        'total_vessels': len(type_vessels),
                        'in_dry_dock': len(type_in_dry_dock),
                        'percentage': round(len(type_in_dry_dock) / len(type_vessels) * 100, 2) if type_vessels else 0
                    }
                
                return jsonify({
                    'currently_in_dry_dock': {
                        'total_count': len(vessels_in_dry_dock),
                        'vessels': [vessel.to_dict() for vessel in vessels_in_dry_dock]
                    },
                    'statistics_by_type': dry_dock_stats,
                    'upcoming_schedule': schedule[:20],  # Next 20 scheduled
                    'total_fleet_dry_dock_days': sum(v.total_dry_dock_days for v in self.fleet.vessels)
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics', methods=['GET'])
        def get_analytics():
            """Get comprehensive fleet analytics"""
            try:
                overview = self.analytics.get_fleet_overview()
                return jsonify(overview)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics/dashboard', methods=['GET'])
        def get_dashboard_data():
            """Get data formatted for dashboard visualization"""
            try:
                dashboard_data = create_analytics_dashboard_data(self.fleet)
                return jsonify(dashboard_data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/statistics', methods=['GET'])
        def get_statistics():
            """Get fleet statistics summary"""
            try:
                stats = self.fleet.get_vessel_statistics()
                
                # Add some additional computed statistics
                additional_stats = {
                    'fleet_utilization': {
                        'operational_vessels': len([v for v in self.fleet.vessels 
                                                  if v.current_status in [VesselStatus.AT_SEA, VesselStatus.IN_PORT]]),
                        'total_vessels': len(self.fleet.vessels)
                    },
                    'age_distribution': {
                        'under_10_years': len([v for v in self.fleet.vessels if v.age_years < 10]),
                        '10_to_20_years': len([v for v in self.fleet.vessels if 10 <= v.age_years < 20]),
                        'over_20_years': len([v for v in self.fleet.vessels if v.age_years >= 20])
                    }
                }
                
                stats.update(additional_stats)
                return jsonify(stats)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/locations', methods=['GET'])
        def get_vessel_locations():
            """Get vessel locations for mapping"""
            try:
                locations = []
                
                for vessel in self.fleet.vessels:
                    if vessel.current_location:
                        locations.append({
                            'imo_number': vessel.imo_number,
                            'vessel_name': vessel.vessel_name,
                            'vessel_type': vessel.vessel_type.value,
                            'latitude': vessel.current_location.latitude,
                            'longitude': vessel.current_location.longitude,
                            'port_name': vessel.current_location.port_name,
                            'country': vessel.current_location.country,
                            'status': vessel.current_status.value
                        })
                
                return jsonify({
                    'total_locations': len(locations),
                    'locations': locations
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/recommendations', methods=['GET'])
        def get_recommendations():
            """Get fleet management recommendations"""
            try:
                recommendations = self.analytics.get_vessel_recommendations()
                return jsonify(recommendations)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/search', methods=['GET'])
        def search_vessels():
            """Search vessels by name, IMO, or other criteria"""
            try:
                query = request.args.get('q', '').lower()
                search_type = request.args.get('type', 'all')  # name, imo, company, all
                
                if not query:
                    return jsonify({'error': 'Search query required'}), 400
                
                results = []
                
                for vessel in self.fleet.vessels:
                    match = False
                    
                    if search_type in ['name', 'all'] and query in vessel.vessel_name.lower():
                        match = True
                    elif search_type in ['imo', 'all'] and query in vessel.imo_number.lower():
                        match = True
                    elif search_type in ['company', 'all'] and (
                        query in vessel.owner_company.lower() or 
                        query in vessel.operator_company.lower()
                    ):
                        match = True
                    
                    if match:
                        results.append(vessel.to_dict())
                
                return jsonify({
                    'query': query,
                    'search_type': search_type,
                    'results_count': len(results),
                    'results': results[:50]  # Limit to 50 results
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reports/comprehensive', methods=['GET'])
        def get_comprehensive_report():
            """Get comprehensive fleet report with all analyses"""
            try:
                report = self.comprehensive_reports.generate_master_comprehensive_report()
                return jsonify(report)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reports/vessel-types', methods=['GET'])
        def get_vessel_types_report():
            """Get detailed vessel type analysis"""
            try:
                report = self.comprehensive_reports.generate_vessel_type_detailed_report()
                return jsonify(report)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reports/dry-dock', methods=['GET'])
        def get_dry_dock_comprehensive_report():
            """Get comprehensive dry dock analysis"""
            try:
                report = self.comprehensive_reports.generate_dry_dock_comprehensive_report()
                return jsonify(report)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reports/countries', methods=['GET'])
        def get_countries_service_areas_report():
            """Get countries and service areas analysis"""
            try:
                report = self.comprehensive_reports.generate_countries_and_service_areas_report()
                return jsonify(report)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reports/age-analysis', methods=['GET'])
        def get_age_analysis_report():
            """Get vessel age comprehensive analysis"""
            try:
                report = self.comprehensive_reports.generate_vessel_age_comprehensive_report()
                return jsonify(report)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reports/export', methods=['POST'])
        def export_comprehensive_report():
            """Export comprehensive report to file"""
            try:
                filename = request.json.get('filename') if request.json else None
                report_file = self.comprehensive_reports.export_comprehensive_report(filename)
                
                return jsonify({
                    'message': 'Report exported successfully',
                    'filename': report_file,
                    'export_date': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reports/summary', methods=['GET'])
        def get_reports_summary():
            """Get summary of all available reports"""
            try:
                # Generate quick summaries
                vessel_types_summary = self.comprehensive_reports.generate_vessel_type_detailed_report()['summary']
                dry_dock_summary = self.comprehensive_reports.generate_dry_dock_comprehensive_report()['summary']
                countries_summary = self.comprehensive_reports.generate_countries_and_service_areas_report()['summary']
                age_summary = self.comprehensive_reports.generate_vessel_age_comprehensive_report()['summary']
                
                return jsonify({
                    'report_summaries': {
                        'vessel_types': vessel_types_summary,
                        'dry_dock_analysis': dry_dock_summary,
                        'countries_analysis': countries_summary,
                        'age_analysis': age_summary
                    },
                    'available_reports': [
                        'comprehensive',
                        'vessel-types',
                        'dry-dock',
                        'countries',
                        'age-analysis'
                    ],
                    'generation_date': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            """Handle 404 errors"""
            return jsonify({'error': 'Endpoint not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle 500 errors"""
            return jsonify({'error': 'Internal server error'}), 500
    
    def _setup_websocket_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            print(f"WebSocket client connected: {request.sid}")
            
            # Send initial fleet summary
            fleet_summary = self.fleet.get_vessel_statistics()
            emit('fleet_summary', {
                'summary': fleet_summary,
                'timestamp': datetime.now().isoformat(),
                'message': 'Connected to AIS WebSocket stream'
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            print(f"WebSocket client disconnected: {request.sid}")
        
        @self.socketio.on('get_fleet_summary')
        def handle_get_fleet_summary():
            """Handle fleet summary requests"""
            try:
                summary = self.fleet.get_vessel_statistics()
                emit('fleet_summary', {
                    'summary': summary,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                emit('error', {'message': str(e)})
        
        @self.socketio.on('get_vessel_data')
        def handle_get_vessel_data(data):
            """Handle specific vessel data requests"""
            try:
                imo_number = data.get('imo_number')
                vessel = next((v for v in self.fleet.vessels if v.imo_number == imo_number), None)
                
                if vessel:
                    emit('vessel_data', {
                        'vessel': vessel.to_dict(),
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    emit('error', {'message': f'Vessel {imo_number} not found'})
            except Exception as e:
                emit('error', {'message': str(e)})
        
        @self.socketio.on('get_fleet_statistics')
        def handle_get_fleet_statistics():
            """Handle fleet statistics requests"""
            try:
                stats = self.fleet.get_vessel_statistics()
                emit('fleet_statistics', {
                    'statistics': stats,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                emit('error', {'message': str(e)})
        
        @self.socketio.on('get_vessels_by_type')
        def handle_get_vessels_by_type(data):
            """Handle vessels by type requests"""
            try:
                vessel_type = data.get('vessel_type')
                vessels = [v for v in self.fleet.vessels if v.vessel_type.value == vessel_type]
                vessel_data = [v.to_dict() for v in vessels]
                emit('vessels_by_type', {
                    'vessel_type': vessel_type,
                    'data': vessel_data,
                    'count': len(vessel_data),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                emit('error', {'message': str(e)})
        
        @self.socketio.on('get_historical_data')
        def handle_get_historical_data(data):
            """Handle historical data requests using real CSV data"""
            try:
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                
                print(f"📅 Historical data request: {start_date} to {end_date}")
                
                if self.csv_loader:
                    # Use real CSV data
                    csv_vessels = self.csv_loader.load_data_by_date_range(start_date, end_date, max_records=500)
                    print(f"📊 Found {len(csv_vessels)} vessels in CSV for date range")
                    
                    # Convert CSV data to vessel format
                    vessels = []
                    for csv_vessel in csv_vessels:
                        # Map CSV data to vessel format
                        vessel_dict = {
                            'vessel_name': csv_vessel.get('vessel_name', 'Unknown Vessel'),
                            'imo_number': csv_vessel.get('imo_number', f"IMO{csv_vessel.get('mmsi', '0000000')}"),
                            'mmsi': csv_vessel.get('mmsi', '000000000'),
                            'vessel_type': self._map_csv_vessel_type(csv_vessel.get('vessel_type', 0)),
                            'current_status': self._map_csv_status(csv_vessel.get('status', 0)),
                            'position': {
                                'latitude': csv_vessel.get('latitude', 0),
                                'longitude': csv_vessel.get('longitude', 0)
                            },
                            'age_years': 15.0,  # Default age for CSV vessels
                            'timestamp': csv_vessel.get('timestamp', start_date)
                        }
                        vessels.append(vessel_dict)
                else:
                    # Fallback to simulated data
                    print("⚠️ Using simulated data (CSV not available)")
                    vessels = [v.to_dict() for v in self.fleet.vessels[:200]]
                
                historical_data = {
                    'type': 'historical_data',
                    'data': {
                        start_date: {'vessels': vessels}
                    },
                    'date_range': {
                        'start': start_date,
                        'end': end_date
                    },
                    'total_count': len(vessels),
                    'available_dates': [start_date],
                    'data_source': 'csv' if self.csv_loader else 'simulated'
                }
                
                print(f"📈 Sending {len(vessels)} historical vessels")
                emit('historical_data', historical_data)
                
            except Exception as e:
                print(f"❌ Error in historical data: {e}")
                emit('error', {'message': str(e)})
    
    def _map_csv_vessel_type(self, ais_type: int) -> str:
        """Map AIS vessel type codes to our vessel types"""
        type_mapping = {
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
            90: 'container',      # Container
            91: 'container',      # Container
            92: 'container',      # Container
            93: 'container',      # Container
            94: 'container',      # Container
            95: 'container',      # Container
            96: 'container',      # Container
            97: 'container',      # Container
            98: 'container',      # Container
            99: 'container',      # Container
        }
        return type_mapping.get(ais_type, 'general_cargo')
    
    def _map_csv_status(self, ais_status: int) -> str:
        """Map AIS status codes to our status values"""
        status_mapping = {
            0: 'at_sea',      # Under way using engine
            1: 'at_sea',      # At anchor
            2: 'in_port',     # Not under command
            3: 'in_port',     # Restricted manoeuvrability
            4: 'in_port',     # Constrained by her draught
            5: 'in_port',     # Moored
            6: 'in_port',     # Aground
            7: 'in_port',     # Engaged in fishing
            8: 'at_sea',      # Under way sailing
            9: 'dry_dock',    # Reserved for future amendment
            10: 'dry_dock',   # Reserved for future amendment
            11: 'dry_dock',   # Reserved for future amendment
            12: 'dry_dock',   # Reserved for future amendment
            13: 'dry_dock',   # Reserved for future amendment
            14: 'dry_dock',   # Reserved for future amendment
            15: 'dry_dock',   # Reserved for future amendment
        }
        return status_mapping.get(ais_status, 'at_sea')
        
        @self.socketio.on('get_vessel_details')
        def handle_get_vessel_details(data):
            """Handle vessel details requests"""
            try:
                imo_number = data.get('imo_number')
                vessel = next((v for v in self.fleet.vessels if v.imo_number == imo_number), None)
                
                if vessel:
                    emit('vessel_details', {
                        'vessel': vessel.to_dict(),
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    emit('error', {'message': f'Vessel {imo_number} not found'})
            except Exception as e:
                emit('error', {'message': str(e)})
    
    def run(self, host='0.0.0.0', port=5000, debug=True):
        """Run the Flask application"""
        print(f"Starting AIS Flask API server...")
        print(f"Fleet size: {len(self.fleet.vessels)} vessels")
        print(f"API will be available at: http://{host}:{port}")
        print(f"Documentation available at: http://{host}:{port}/")
        
        self.app.run(host=host, port=port, debug=debug)


def create_app(fleet_size: int = 500, use_csv_data: bool = False):
    """Factory function to create Flask app with SocketIO"""
    ais_app = AISFlaskApp(fleet_size=fleet_size, use_csv_data=use_csv_data)
    return ais_app.app, ais_app.socketio


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AIS Marine Vessel System API')
    parser.add_argument('--fleet-size', type=int, default=500, 
                       help='Number of vessels to generate (default: 500)')
    parser.add_argument('--host', default='0.0.0.0', 
                       help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, 
                       help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create and run the application
    ais_app = AISFlaskApp(fleet_size=args.fleet_size)
    ais_app.run(host=args.host, port=args.port, debug=args.debug)
