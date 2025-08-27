#!/usr/bin/env python3
"""
AIS Marine Vessel System - Comprehensive Demo
Demonstrates all features of the AIS vessel management system
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generators.ais_data_generator import generate_sample_fleet
from analytics.vessel_analytics import VesselAnalytics
from analytics.comprehensive_reports import ComprehensiveVesselReports
from database.models import DatabaseManager
from models.vessel import VesselType, VesselStatus


def print_demo_banner():
    """Print demo banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════╗
║                     AIS MARINE VESSEL SYSTEM                            ║
║                        COMPREHENSIVE DEMO                               ║
║                                                                          ║
║  This demo showcases the complete AIS vessel management system with:    ║
║  • Realistic vessel data generation (Tankers, Bulkers, Containers, etc.)║
║  • Comprehensive dry dock tracking and analysis                         ║
║  • Global vessel distribution and country analysis                      ║
║  • Fleet age analysis and renewal planning                              ║
║  • Performance metrics and operational insights                         ║
║  • REST API and interactive dashboard capabilities                      ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def demo_fleet_generation(fleet_size: int = 1000):
    """Demonstrate fleet generation capabilities"""
    print(f"\n{'='*80}")
    print(f"STEP 1: GENERATING COMPREHENSIVE VESSEL FLEET")
    print(f"{'='*80}")
    
    print(f"Generating {fleet_size:,} vessels with realistic AIS data...")
    print("✓ Creating diverse vessel types (Tankers, Bulkers, Containers, General Cargo)")
    print("✓ Assigning global flag states and operational areas")
    print("✓ Generating realistic vessel specifications and ages")
    print("✓ Creating comprehensive dry dock maintenance histories")
    print("✓ Simulating current operational status and locations")
    
    start_time = time.time()
    fleet = generate_sample_fleet(fleet_size)
    generation_time = time.time() - start_time
    
    print(f"\n✅ Fleet generation completed in {generation_time:.2f} seconds")
    print(f"Generated {len(fleet.vessels):,} vessels")
    
    # Show basic statistics
    stats = fleet.get_vessel_statistics()
    print(f"\nFleet Composition:")
    for vessel_type, data in stats['vessel_types'].items():
        print(f"  {vessel_type.replace('_', ' ').title()}: {data['count']:,} vessels ({data['percentage']:.1f}%)")
    
    print(f"\nGlobal Distribution:")
    print(f"  Flag States: {len(stats['countries'])} countries")
    print(f"  Average Fleet Age: {stats['age_statistics']['average_age']} years")
    print(f"  Vessels in Dry Dock: {stats['dry_dock_statistics']['vessels_currently_in_dry_dock']}")
    
    return fleet


def demo_comprehensive_analytics(fleet):
    """Demonstrate comprehensive analytics capabilities"""
    print(f"\n{'='*80}")
    print(f"STEP 2: COMPREHENSIVE VESSEL ANALYTICS")
    print(f"{'='*80}")
    
    print("Analyzing fleet with advanced analytics engine...")
    analytics = VesselAnalytics(fleet)
    comprehensive_reports = ComprehensiveVesselReports(fleet)
    
    # Vessel Type Analysis
    print(f"\n🚢 VESSEL TYPE DETAILED ANALYSIS")
    type_report = comprehensive_reports.generate_vessel_type_detailed_report()
    
    print(f"Detailed breakdown of {type_report['summary']['total_vessels']:,} vessels:")
    for vessel_type, data in type_report['summary']['type_distribution'].items():
        type_name = vessel_type.replace('_', ' ').title()
        print(f"  {type_name}: {data['count']:,} vessels ({data['percentage']:.1f}%)")
        
        # Show key insights for each type
        if vessel_type in type_report['detailed_analysis_by_type']:
            details = type_report['detailed_analysis_by_type'][vessel_type]
            age_stats = details['age_statistics']
            print(f"    └─ Average Age: {age_stats['average_age']} years")
            print(f"    └─ Top Flag State: {list(details['flag_state_distribution'].keys())[0] if details['flag_state_distribution'] else 'N/A'}")
    
    return analytics, comprehensive_reports


def demo_dry_dock_analysis(comprehensive_reports):
    """Demonstrate dry dock analysis capabilities"""
    print(f"\n⚓ DRY DOCK COMPREHENSIVE ANALYSIS")
    dry_dock_report = comprehensive_reports.generate_dry_dock_comprehensive_report()
    
    summary = dry_dock_report['summary']
    print(f"Fleet-wide Dry Dock Statistics:")
    print(f"  Total Dry Dock Days: {summary['total_fleet_dry_dock_days']:,} days")
    print(f"  Average per Vessel: {summary['average_days_per_vessel']} days")
    print(f"  Currently in Dry Dock: {summary['vessels_currently_in_dry_dock']} vessels ({summary['percentage_of_fleet_in_dry_dock']:.1f}%)")
    
    print(f"\nDry Dock Analysis by Vessel Type:")
    for vessel_type, data in dry_dock_report['analysis_by_vessel_type'].items():
        type_name = vessel_type.replace('_', ' ').title()
        print(f"  {type_name}:")
        print(f"    └─ In Dry Dock: {data['currently_in_dry_dock']}/{data['total_vessels']} ({data['percentage_in_dry_dock']:.1f}%)")
        print(f"    └─ Avg Maintenance: {data['average_dry_dock_days']} days")
    
    # Show maintenance patterns
    patterns = dry_dock_report['maintenance_patterns']
    high_maintenance = patterns['high_maintenance_vessels']
    print(f"\nMaintenance Insights:")
    print(f"  High Maintenance Vessels: {high_maintenance['vessel_count']} ({high_maintenance['percentage_of_fleet']:.1f}%)")
    print(f"  Threshold: {high_maintenance['threshold_days']} days")


def demo_geographic_analysis(comprehensive_reports):
    """Demonstrate geographic and service area analysis"""
    print(f"\n🌍 COUNTRIES AND SERVICE AREAS ANALYSIS")
    countries_report = comprehensive_reports.generate_countries_and_service_areas_report()
    
    summary = countries_report['summary']
    print(f"Global Fleet Distribution:")
    print(f"  Flag States Represented: {summary['total_countries_represented']} countries")
    print(f"  Current Operational Areas: {summary['total_current_location_countries']} countries")
    print(f"  Most Common Flag State: {summary['most_common_flag_state']}")
    
    # Top flag states
    flag_analysis = countries_report['flag_state_analysis']
    print(f"\nTop 5 Flag States:")
    top_flags = list(flag_analysis['top_10_flag_states'].items())[:5]
    for country, data in top_flags:
        print(f"  {country}: {data['vessel_count']} vessels ({data['percentage']:.1f}%)")
    
    # Current locations
    location_analysis = countries_report['current_location_analysis']
    print(f"\nTop 5 Current Operational Areas:")
    top_locations = list(location_analysis['top_10_current_locations'].items())[:5]
    for country, data in top_locations:
        print(f"  {country}: {data['vessel_count']} vessels ({data['percentage']:.1f}%)")
    
    # Service area insights
    service_analysis = countries_report['service_area_analysis']
    print(f"\nService Line Distribution:")
    for service_line, data in service_analysis.items():
        service_name = service_line.replace('_', ' ').title()
        print(f"  {service_name}: {data['vessel_count']} vessels")
        if data['primary_flag_states']:
            top_flag = list(data['primary_flag_states'].items())[0]
            print(f"    └─ Primary Flag State: {top_flag[0]} ({top_flag[1]} vessels)")


def demo_age_analysis(comprehensive_reports):
    """Demonstrate fleet age analysis"""
    print(f"\n📅 VESSEL AGE COMPREHENSIVE ANALYSIS")
    age_report = comprehensive_reports.generate_vessel_age_comprehensive_report()
    
    summary = age_report['summary']
    print(f"Fleet Age Statistics:")
    print(f"  Average Age: {summary['fleet_average_age']} years")
    print(f"  Age Range: {summary['newest_vessel_age']} - {summary['oldest_vessel_age']} years")
    print(f"  Median Age: {summary['fleet_median_age']} years")
    
    print(f"\nAge Distribution:")
    for age_range, data in age_report['age_distribution'].items():
        print(f"  {age_range}: {data['count']} vessels ({data['percentage']:.1f}%)")
    
    # Fleet renewal analysis
    renewal = age_report['fleet_renewal_analysis']
    print(f"\nFleet Renewal Assessment:")
    over_20 = renewal['vessels_over_20_years']
    over_25 = renewal['vessels_over_25_years']
    print(f"  Vessels over 20 years: {over_20['count']} ({over_20['percentage']:.1f}%)")
    print(f"  Vessels over 25 years: {over_25['count']} ({over_25['percentage']:.1f}%)")
    print(f"  Renewal Priority Score: {renewal['renewal_priority_score']}/100")
    
    if renewal['renewal_priority_score'] > 60:
        print(f"  ⚠️  Fleet renewal program recommended")
    elif renewal['renewal_priority_score'] > 40:
        print(f"  ⚡ Monitor aging vessels closely")
    else:
        print(f"  ✅ Fleet age profile is healthy")


def demo_performance_metrics(analytics):
    """Demonstrate performance metrics analysis"""
    print(f"\n📊 PERFORMANCE METRICS AND OPERATIONAL EFFICIENCY")
    overview = analytics.get_fleet_overview()
    performance = overview['performance_metrics']
    
    # Operational efficiency
    efficiency = performance['operational_efficiency']
    print(f"Operational Efficiency:")
    print(f"  Fleet Utilization: {efficiency['fleet_utilization']:.1f}%")
    print(f"  Average Voyages/Year: {efficiency['average_voyages_per_year']:.1f}")
    print(f"  Average Distance/Year: {efficiency['average_distance_per_year']:,.0f} nautical miles")
    
    # Speed analysis
    speed = performance['speed_analysis']
    print(f"\nSpeed Performance:")
    print(f"  Average Fleet Speed: {speed['average_fleet_speed']:.1f} knots")
    print(f"  Speed by Vessel Type:")
    for vessel_type, avg_speed in speed['speed_by_type'].items():
        type_name = vessel_type.replace('_', ' ').title()
        print(f"    {type_name}: {avg_speed:.1f} knots")
    
    # Fuel efficiency
    fuel = performance['fuel_efficiency']
    print(f"\nFuel Efficiency:")
    print(f"  Average Efficiency: {fuel['average_efficiency']:.3f} tons/nm")
    print(f"  Efficiency by Type:")
    for vessel_type, efficiency in fuel['efficiency_by_type'].items():
        type_name = vessel_type.replace('_', ' ').title()
        print(f"    {type_name}: {efficiency:.3f} tons/nm")


def demo_recommendations(comprehensive_reports):
    """Demonstrate fleet management recommendations"""
    print(f"\n💡 FLEET MANAGEMENT RECOMMENDATIONS")
    
    # Get comprehensive recommendations
    master_report = comprehensive_reports.generate_master_comprehensive_report()
    recommendations = master_report['fleet_management_recommendations']
    
    # Show urgent maintenance recommendations
    if recommendations.get('maintenance_urgent'):
        print(f"Urgent Maintenance Required ({len(recommendations['maintenance_urgent'])} vessels):")
        for rec in recommendations['maintenance_urgent'][:3]:
            if isinstance(rec, dict):
                print(f"  ⚠️  {rec.get('vessel_name', 'N/A')}: {rec.get('recommendation', rec.get('issue', 'N/A'))}")
    
    # Show age concerns
    if recommendations.get('age_concerns'):
        print(f"\nAge-Related Concerns ({len(recommendations['age_concerns'])} vessels):")
        for rec in recommendations['age_concerns'][:3]:
            if isinstance(rec, dict):
                print(f"  📅 {rec.get('vessel_name', 'N/A')}: {rec.get('recommendation', rec.get('issue', 'N/A'))}")
    
    # Show performance issues
    if recommendations.get('performance_issues'):
        print(f"\nPerformance Issues ({len(recommendations['performance_issues'])} vessels):")
        for rec in recommendations['performance_issues'][:3]:
            if isinstance(rec, dict):
                print(f"  🔧 {rec.get('vessel_name', 'N/A')}: {rec.get('recommendation', rec.get('issue', 'N/A'))}")


def demo_database_operations(fleet):
    """Demonstrate database operations"""
    print(f"\n{'='*80}")
    print(f"STEP 3: DATABASE OPERATIONS")
    print(f"{'='*80}")
    
    print("Demonstrating database persistence...")
    
    # Initialize database
    db_manager = DatabaseManager("sqlite:///demo_ais_vessels.db")
    print("✓ Database initialized with SQLAlchemy ORM")
    
    # Save fleet to database
    print(f"Saving {len(fleet.vessels)} vessels to database...")
    start_time = time.time()
    saved_vessels = db_manager.save_fleet(fleet)
    save_time = time.time() - start_time
    
    print(f"✅ Saved {len(saved_vessels)} vessels in {save_time:.2f} seconds")
    
    # Demonstrate queries
    print(f"\nDatabase Query Examples:")
    tankers = db_manager.get_vessels_by_type('tanker')
    print(f"  Tankers in database: {len(tankers)}")
    
    dry_dock_vessels = db_manager.get_vessels_in_dry_dock()
    print(f"  Vessels in dry dock: {len(dry_dock_vessels)}")
    
    fleet_stats = db_manager.get_fleet_statistics()
    print(f"  Database fleet statistics: {fleet_stats['total_vessels']} total vessels")


def demo_export_capabilities(comprehensive_reports):
    """Demonstrate export capabilities"""
    print(f"\n{'='*80}")
    print(f"STEP 4: REPORT EXPORT CAPABILITIES")
    print(f"{'='*80}")
    
    print("Generating comprehensive report export...")
    
    # Export comprehensive report
    export_filename = f"demo_comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file = comprehensive_reports.export_comprehensive_report(export_filename)
    
    print(f"✅ Comprehensive report exported to: {report_file}")
    
    # Show file size and contents summary
    if os.path.exists(report_file):
        file_size = os.path.getsize(report_file) / 1024  # KB
        print(f"  File size: {file_size:.1f} KB")
        
        # Load and show structure
        with open(report_file, 'r') as f:
            report_data = json.load(f)
        
        print(f"  Report sections included:")
        for section in report_data.keys():
            if section != 'report_metadata':
                section_name = section.replace('_', ' ').title()
                print(f"    ✓ {section_name}")
    
    return report_file


def demo_api_capabilities():
    """Demonstrate API capabilities"""
    print(f"\n{'='*80}")
    print(f"STEP 5: REST API CAPABILITIES")
    print(f"{'='*80}")
    
    print("AIS System provides comprehensive REST API with endpoints:")
    
    api_endpoints = [
        ("GET /api/vessels", "Retrieve all vessels with filtering"),
        ("GET /api/vessels/{imo}", "Get specific vessel details"),
        ("GET /api/vessels/type/{type}", "Get vessels by type"),
        ("GET /api/dry-dock", "Get dry dock information"),
        ("GET /api/analytics", "Get fleet analytics"),
        ("GET /api/reports/comprehensive", "Get comprehensive report"),
        ("GET /api/reports/vessel-types", "Get vessel type analysis"),
        ("GET /api/reports/dry-dock", "Get dry dock analysis"),
        ("GET /api/reports/countries", "Get countries analysis"),
        ("GET /api/reports/age-analysis", "Get age analysis"),
        ("GET /api/locations", "Get vessel locations for mapping"),
        ("GET /api/search", "Search vessels by name/IMO/company"),
        ("POST /api/reports/export", "Export reports to files")
    ]
    
    print(f"Available API Endpoints ({len(api_endpoints)} total):")
    for endpoint, description in api_endpoints:
        print(f"  {endpoint}")
        print(f"    └─ {description}")
    
    print(f"\nAPI Features:")
    print(f"  ✓ RESTful design with JSON responses")
    print(f"  ✓ Comprehensive filtering and pagination")
    print(f"  ✓ Real-time analytics and reporting")
    print(f"  ✓ Cross-origin resource sharing (CORS) enabled")
    print(f"  ✓ Error handling and validation")
    print(f"  ✓ Interactive documentation")


def demo_dashboard_capabilities():
    """Demonstrate dashboard capabilities"""
    print(f"\n{'='*80}")
    print(f"STEP 6: INTERACTIVE DASHBOARD CAPABILITIES")
    print(f"{'='*80}")
    
    print("AIS System includes comprehensive dashboard with features:")
    
    dashboard_features = [
        "Fleet Overview with real-time statistics",
        "Vessel Type Analysis with interactive charts",
        "Dry Dock Tracking and scheduling",
        "Geographic Distribution with world map",
        "Performance Metrics and trends",
        "Detailed Vessel Tables with filtering",
        "Maintenance Recommendations",
        "Export capabilities for reports"
    ]
    
    print(f"Dashboard Features:")
    for i, feature in enumerate(dashboard_features, 1):
        print(f"  {i}. {feature}")
    
    print(f"\nTechnical Features:")
    print(f"  ✓ Built with Plotly Dash for interactive visualizations")
    print(f"  ✓ Responsive design with Bootstrap components")
    print(f"  ✓ Real-time data updates")
    print(f"  ✓ Multi-tab interface for organized navigation")
    print(f"  ✓ Downloadable charts and data tables")
    print(f"  ✓ Mobile-friendly responsive design")


def demo_system_architecture():
    """Demonstrate system architecture"""
    print(f"\n{'='*80}")
    print(f"STEP 7: SYSTEM ARCHITECTURE OVERVIEW")
    print(f"{'='*80}")
    
    print("AIS Marine Vessel System Architecture:")
    
    architecture_components = [
        ("Data Models", "Comprehensive vessel, dry dock, and location models"),
        ("Data Generation", "Realistic AIS data generation with faker integration"),
        ("Analytics Engine", "Advanced analytics with pandas and numpy"),
        ("Database Layer", "SQLAlchemy ORM with multiple database support"),
        ("REST API", "Flask-based RESTful API with comprehensive endpoints"),
        ("Dashboard", "Interactive Plotly Dash dashboard"),
        ("Reporting System", "Comprehensive reporting with JSON/CSV/Excel export"),
        ("CLI Tools", "Command-line interface for batch operations")
    ]
    
    print(f"System Components:")
    for component, description in architecture_components:
        print(f"  📦 {component}")
        print(f"     └─ {description}")
    
    print(f"\nKey Technologies:")
    tech_stack = [
        "Python 3.8+ (Core language)",
        "Flask (REST API framework)",
        "Plotly Dash (Interactive dashboard)",
        "SQLAlchemy (Database ORM)",
        "Pandas/NumPy (Data analysis)",
        "Faker (Realistic data generation)",
        "Geopy (Geographic operations)"
    ]
    
    for tech in tech_stack:
        print(f"  ⚙️  {tech}")


def main():
    """Main demo function"""
    print_demo_banner()
    
    print(f"\nStarting comprehensive AIS vessel system demonstration...")
    print(f"Demo timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_start_time = time.time()
    
    try:
        # Step 1: Fleet Generation
        fleet = demo_fleet_generation(1000)
        
        # Step 2: Comprehensive Analytics
        analytics, comprehensive_reports = demo_comprehensive_analytics(fleet)
        
        # Detailed analysis sections
        demo_dry_dock_analysis(comprehensive_reports)
        demo_geographic_analysis(comprehensive_reports)
        demo_age_analysis(comprehensive_reports)
        demo_performance_metrics(analytics)
        demo_recommendations(comprehensive_reports)
        
        # Step 3: Database Operations
        demo_database_operations(fleet)
        
        # Step 4: Export Capabilities
        export_file = demo_export_capabilities(comprehensive_reports)
        
        # Step 5: API Capabilities
        demo_api_capabilities()
        
        # Step 6: Dashboard Capabilities
        demo_dashboard_capabilities()
        
        # Step 7: System Architecture
        demo_system_architecture()
        
        # Demo completion
        total_time = time.time() - total_start_time
        
        print(f"\n{'='*80}")
        print(f"DEMO COMPLETED SUCCESSFULLY")
        print(f"{'='*80}")
        print(f"Total demo time: {total_time:.2f} seconds")
        print(f"Fleet analyzed: {len(fleet.vessels):,} vessels")
        print(f"Report exported: {export_file}")
        print(f"Database created: demo_ais_vessels.db")
        
        print(f"\nNext Steps:")
        print(f"  1. Run API server: python api/app.py --vessels 1000")
        print(f"  2. Run dashboard: python dashboard/dashboard.py --vessels 1000")
        print(f"  3. Generate reports: python cli_reports.py --vessels 1000 --all")
        print(f"  4. View exported report: {export_file}")
        
        print(f"\nThank you for exploring the AIS Marine Vessel Management System! 🚢")
        
    except KeyboardInterrupt:
        print(f"\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
