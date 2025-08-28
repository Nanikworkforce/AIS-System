"""
AIS Marine Vessel Management System
Main application launcher with multiple modes
"""

import argparse
import sys
import os
import threading
import time
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generators.ais_data_generator import generate_sample_fleet, generate_fleet_from_csv
from analytics.vessel_analytics import VesselAnalytics
from database.models import DatabaseManager
from api.app import AISFlaskApp
from dashboard.dashboard import AISVesselDashboard


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║              AIS Marine Vessel Management System             ║
║                                                              ║
║  Comprehensive vessel tracking, analytics, and reporting    ║
║  • Tankers, Bulkers, Container Ships, General Cargo        ║
║  • Dry dock tracking and maintenance scheduling            ║
║  • Global fleet analytics and performance metrics          ║
║  • Real-time dashboard and REST API                        ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def generate_fleet_command(args):
    """Generate vessel fleet data"""
    print(f"Generating fleet with {args.vessels} vessels...")
    
    # Use CSV data by default, unless use_generated is specified
    if hasattr(args, 'use_generated') and args.use_generated:
        print("🔄 Using generated vessel data...")
        fleet = generate_sample_fleet(args.vessels)
    else:
        print("🔄 Using real AIS data from CSV file...")
        fleet = generate_fleet_from_csv(vessels_count=args.vessels)
    
    analytics = VesselAnalytics(fleet)
    
    # Display summary
    overview = analytics.get_fleet_overview()
    print(f"\nFleet Generation Complete!")
    print(f"Total Vessels: {overview['total_vessels']:,}")
    print(f"Average Age: {overview['age_analysis']['overall_stats']['mean_age']:.1f} years")
    print(f"Vessels in Dry Dock: {overview['dry_dock_analysis']['currently_in_dry_dock']['count']}")
    
    print(f"\nVessel Type Distribution:")
    for vessel_type, data in overview['vessel_types']['counts'].items():
        percentage = overview['vessel_types']['percentages'][vessel_type]
        print(f"  {vessel_type.title()}: {data:,} ({percentage:.1f}%)")
    
    # Save to database if requested
    if args.save_db:
        print(f"\nSaving fleet to database...")
        db_manager = DatabaseManager(args.database_url)
        saved_vessels = db_manager.save_fleet(fleet)
        print(f"Saved {len(saved_vessels)} vessels to database: {args.database_url}")
    
    # Export analytics report
    if args.export:
        report_file = analytics.export_analytics_report(args.export)
        print(f"Analytics report exported to: {report_file}")


def run_api_command(args):
    """Run the Flask API server"""
    print("Starting AIS Flask API Server...")
    
    if args.load_db:
        print("Loading data from database...")
        # In a real implementation, you'd load from database
        # For now, generate sample data
        fleet_size = args.vessels
    else:
        fleet_size = args.vessels
    
    # Use CSV data by default, unless use_generated is specified
    use_csv = not (hasattr(args, 'use_generated') and args.use_generated)
    api_app = AISFlaskApp(fleet_size=fleet_size, use_csv_data=use_csv)
    
    print(f"API Documentation: http://{args.host}:{args.port}/")
    print(f"Sample Endpoints:")
    print(f"  GET http://{args.host}:{args.port}/api/vessels")
    print(f"  GET http://{args.host}:{args.port}/api/analytics")
    print(f"  GET http://{args.host}:{args.port}/api/dry-dock")
    
    api_app.run(host=args.host, port=args.port, debug=args.debug)


def run_dashboard_command(args):
    """Run the dashboard interface"""
    print("Starting AIS Dashboard...")
    
    # Use CSV data by default, unless use_generated is specified
    use_csv = not (hasattr(args, 'use_generated') and args.use_generated)
    dashboard = AISVesselDashboard(fleet_size=args.vessels, use_csv_data=use_csv)
    
    print(f"Dashboard Features:")
    print(f"  • Fleet Overview and Statistics")
    print(f"  • Vessel Type Analysis")
    print(f"  • Dry Dock Tracking")
    print(f"  • Geographic Distribution")
    print(f"  • Performance Metrics")
    print(f"  • Detailed Vessel Tables")
    
    dashboard.run(host=args.host, port=args.port, debug=args.debug)


def run_both_command(args):
    """Run both API and Dashboard simultaneously"""
    print("Starting both API and Dashboard servers...")
    
    # Start API in a separate thread
    def run_api():
        api_app = AISFlaskApp(fleet_size=args.vessels)
        api_app.run(host=args.api_host, port=args.api_port, debug=False)
    
    # Start Dashboard in a separate thread
    def run_dashboard():
        dashboard = AISVesselDashboard(fleet_size=args.vessels)
        dashboard.run(host=args.dashboard_host, port=args.dashboard_port, debug=False)
    
    api_thread = threading.Thread(target=run_api, daemon=True)
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    
    print(f"Starting API server on http://{args.api_host}:{args.api_port}")
    api_thread.start()
    
    # Wait a moment for API to start
    time.sleep(2)
    
    print(f"Starting Dashboard on http://{args.dashboard_host}:{args.dashboard_port}")
    dashboard_thread.start()
    
    print(f"\nServices Running:")
    print(f"  API: http://{args.api_host}:{args.api_port}")
    print(f"  Dashboard: http://{args.dashboard_host}:{args.dashboard_port}")
    print(f"\nPress Ctrl+C to stop both services")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down services...")


def analytics_command(args):
    """Run analytics and generate reports"""
    print(f"Generating analytics for {args.vessels} vessels...")
    
    # Load or generate fleet
    if args.load_db:
        print("Loading data from database...")
        db_manager = DatabaseManager(args.database_url)
        # In real implementation, would convert DB vessels back to fleet
        fleet = generate_sample_fleet(args.vessels)  # Simplified for now
    else:
        fleet = generate_sample_fleet(args.vessels)
    
    analytics = VesselAnalytics(fleet)
    
    # Generate comprehensive report
    overview = analytics.get_fleet_overview()
    recommendations = analytics.get_vessel_recommendations()
    
    print(f"\n{'='*60}")
    print(f"FLEET ANALYTICS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Fleet Summary
    print(f"\nFLEET SUMMARY:")
    print(f"  Total Vessels: {overview['total_vessels']:,}")
    print(f"  Average Age: {overview['age_analysis']['overall_stats']['mean_age']:.1f} years")
    print(f"  Operational Vessels: {overview['status_distribution']['vessels_in_operation']:,}")
    print(f"  Vessels in Dry Dock: {overview['dry_dock_analysis']['currently_in_dry_dock']['count']:,}")
    
    # Vessel Types
    print(f"\nVESSEL TYPE DISTRIBUTION:")
    for vessel_type, data in overview['vessel_types']['counts'].items():
        percentage = overview['vessel_types']['percentages'][vessel_type]
        print(f"  {vessel_type.replace('_', ' ').title()}: {data:,} ({percentage:.1f}%)")
    
    # Geographic Distribution
    print(f"\nTOP FLAG STATES:")
    for country, count in list(overview['geographic_distribution']['flag_states']['top_10'].items())[:5]:
        print(f"  {country}: {count:,} vessels")
    
    # Performance Metrics
    perf = overview['performance_metrics']
    print(f"\nPERFORMANCE METRICS:")
    print(f"  Fleet Utilization: {perf['operational_efficiency']['fleet_utilization']:.1f}%")
    print(f"  Average Speed: {perf['speed_analysis']['average_fleet_speed']:.1f} knots")
    print(f"  Average Voyages/Year: {perf['operational_efficiency']['average_voyages_per_year']:.1f}")
    
    # Recommendations
    print(f"\nFLEET MANAGEMENT RECOMMENDATIONS:")
    
    if recommendations['maintenance_urgent']:
        print(f"  URGENT MAINTENANCE ({len(recommendations['maintenance_urgent'])} vessels):")
        for rec in recommendations['maintenance_urgent'][:3]:
            print(f"    • {rec['vessel_name']}: {rec['recommendation']}")
    
    if recommendations['age_concerns']:
        print(f"  AGE CONCERNS ({len(recommendations['age_concerns'])} vessels):")
        for rec in recommendations['age_concerns'][:3]:
            print(f"    • {rec['vessel_name']}: {rec['recommendation']}")
    
    # Export detailed report
    if args.export:
        report_file = analytics.export_analytics_report(args.export)
        print(f"\nDetailed report exported to: {report_file}")


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description='AIS Marine Vessel Management System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s generate --vessels 1000 --save-db --export fleet_report.json
  %(prog)s api --vessels 500 --port 5000
  %(prog)s dashboard --vessels 500 --port 8050
  %(prog)s both --vessels 1000
  %(prog)s analytics --vessels 500 --export analytics_report.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate vessel fleet data')
    generate_parser.add_argument('--vessels', type=int, default=1000, 
                               help='Number of vessels to generate (default: 1000)')
    generate_parser.add_argument('--save-db', action='store_true', 
                               help='Save generated fleet to database')
    generate_parser.add_argument('--database-url', default='sqlite:///ais_vessels.db',
                               help='Database URL (default: sqlite:///ais_vessels.db)')
    generate_parser.add_argument('--export', 
                               help='Export analytics report to file')
    generate_parser.add_argument('--use-csv', action='store_true', default=True,
                               help='Use real AIS data from CSV file (default: True)')
    generate_parser.add_argument('--use-generated', action='store_true', 
                               help='Use generated data instead of CSV')
    
    # API command
    api_parser = subparsers.add_parser('api', help='Run Flask API server')
    api_parser.add_argument('--vessels', type=int, default=500,
                          help='Number of vessels to generate (default: 500)')
    api_parser.add_argument('--host', default='0.0.0.0',
                          help='Host to bind to (default: 0.0.0.0)')
    api_parser.add_argument('--port', type=int, default=5000,
                          help='Port to bind to (default: 5000)')
    api_parser.add_argument('--debug', action='store_true',
                          help='Enable debug mode')
    api_parser.add_argument('--load-db', action='store_true',
                          help='Load data from database instead of generating')
    api_parser.add_argument('--use-csv', action='store_true', default=True,
                          help='Use real AIS data from CSV file (default: True)')
    api_parser.add_argument('--use-generated', action='store_true', 
                          help='Use generated data instead of CSV')
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Run dashboard interface')
    dashboard_parser.add_argument('--vessels', type=int, default=500,
                                help='Number of vessels to generate (default: 500)')
    dashboard_parser.add_argument('--host', default='127.0.0.1',
                                help='Host to bind to (default: 127.0.0.1)')
    dashboard_parser.add_argument('--port', type=int, default=8050,
                                help='Port to bind to (default: 8050)')
    dashboard_parser.add_argument('--debug', action='store_true',
                                help='Enable debug mode')
    dashboard_parser.add_argument('--use-csv', action='store_true', default=True,
                                help='Use real AIS data from CSV file (default: True)')
    dashboard_parser.add_argument('--use-generated', action='store_true', 
                                help='Use generated data instead of CSV')
    
    # Both command
    both_parser = subparsers.add_parser('both', help='Run both API and Dashboard')
    both_parser.add_argument('--vessels', type=int, default=1000,
                           help='Number of vessels to generate (default: 1000)')
    both_parser.add_argument('--api-host', default='0.0.0.0',
                           help='API host (default: 0.0.0.0)')
    both_parser.add_argument('--api-port', type=int, default=5000,
                           help='API port (default: 5000)')
    both_parser.add_argument('--dashboard-host', default='127.0.0.1',
                           help='Dashboard host (default: 127.0.0.1)')
    both_parser.add_argument('--dashboard-port', type=int, default=8050,
                           help='Dashboard port (default: 8050)')
    
    # Analytics command
    analytics_parser = subparsers.add_parser('analytics', help='Generate analytics report')
    analytics_parser.add_argument('--vessels', type=int, default=500,
                                help='Number of vessels to analyze (default: 500)')
    analytics_parser.add_argument('--load-db', action='store_true',
                                help='Load data from database')
    analytics_parser.add_argument('--database-url', default='sqlite:///ais_vessels.db',
                                help='Database URL')
    analytics_parser.add_argument('--export',
                                help='Export detailed report to file')
    
    args = parser.parse_args()
    
    print_banner()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'generate':
            generate_fleet_command(args)
        elif args.command == 'api':
            run_api_command(args)
        elif args.command == 'dashboard':
            run_dashboard_command(args)
        elif args.command == 'both':
            run_both_command(args)
        elif args.command == 'analytics':
            analytics_command(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error: {e}")
        if args.command in ['api', 'dashboard'] and hasattr(args, 'debug') and args.debug:
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
