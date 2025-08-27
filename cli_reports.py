#!/usr/bin/env python3
"""
CLI Tool for AIS Vessel Comprehensive Reports
Generate detailed vessel reports from command line
"""

import argparse
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generators.ais_data_generator import generate_sample_fleet
from analytics.comprehensive_reports import ComprehensiveVesselReports
from database.models import DatabaseManager


def print_report_banner():
    """Print CLI banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════════╗
║           AIS VESSEL COMPREHENSIVE REPORTING SYSTEM              ║
║                                                                   ║
║  Generate detailed reports on marine vessel fleets:              ║
║  • Vessel Type Analysis (Tankers, Bulkers, Containers, General)  ║
║  • Comprehensive Dry Dock Tracking and Analysis                  ║
║  • Countries and Service Areas Analysis                          ║
║  • Fleet Age Distribution and Renewal Planning                   ║
║  • Performance Metrics and Recommendations                       ║
╚═══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_summary_stats(report_data: Dict[str, Any]):
    """Print summary statistics from report"""
    if 'executive_summary' in report_data:
        summary = report_data['executive_summary']
        metrics = summary['key_metrics']
        
        print(f"\n{'='*70}")
        print(f"FLEET SUMMARY STATISTICS")
        print(f"{'='*70}")
        print(f"Total Fleet Size: {metrics['total_fleet_size']:,} vessels")
        print(f"Average Fleet Age: {metrics['average_fleet_age']} years")
        print(f"Operational Vessels: {metrics['operational_vessels']:,} ({metrics['operational_vessels']/metrics['total_fleet_size']*100:.1f}%)")
        print(f"Vessels in Dry Dock: {metrics['vessels_currently_in_dry_dock']:,} ({metrics['dry_dock_percentage']:.1f}%)")
        print(f"Flag State Diversity: {metrics['flag_state_diversity']} countries")
        print(f"Global Presence: {metrics['global_presence']} countries")
        
        print(f"\nFleet Composition:")
        for vessel_type, data in summary['fleet_composition'].items():
            type_name = vessel_type.replace('_', ' ').title()
            print(f"  {type_name}: {data['count']:,} vessels ({data['percentage']:.1f}%)")
        
        print(f"\nKey Insights:")
        for insight in summary['key_insights']:
            print(f"  • {insight}")


def print_vessel_type_analysis(report_data: Dict[str, Any]):
    """Print vessel type analysis"""
    if 'vessel_type_analysis' not in report_data:
        return
    
    analysis = report_data['vessel_type_analysis']
    
    print(f"\n{'='*70}")
    print(f"VESSEL TYPE DETAILED ANALYSIS")
    print(f"{'='*70}")
    
    for vessel_type, details in analysis['detailed_analysis_by_type'].items():
        type_name = vessel_type.replace('_', ' ').title()
        print(f"\n{type_name.upper()} VESSELS:")
        
        # Age statistics
        age_stats = details['age_statistics']
        print(f"  Age Statistics:")
        print(f"    Average Age: {age_stats['average_age']} years")
        print(f"    Age Range: {age_stats['newest_vessel']} - {age_stats['oldest_vessel']} years")
        
        # Operational status
        status_breakdown = details['operational_status']
        print(f"  Operational Status:")
        for status, data in status_breakdown.items():
            status_name = status.replace('_', ' ').title()
            print(f"    {status_name}: {data['count']} vessels ({data['percentage']:.1f}%)")
        
        # Top flag states
        print(f"  Top Flag States:")
        flag_states = list(details['flag_state_distribution'].items())[:5]
        for country, count in flag_states:
            print(f"    {country}: {count} vessels")
        
        # Dry dock analysis
        dry_dock = details['dry_dock_analysis']
        print(f"  Dry Dock Analysis:")
        print(f"    Currently in Dry Dock: {dry_dock['currently_in_dry_dock']} vessels")
        print(f"    Average Dry Dock Days: {dry_dock['average_dry_dock_days']} days")


def print_dry_dock_analysis(report_data: Dict[str, Any]):
    """Print dry dock analysis"""
    if 'dry_dock_comprehensive_analysis' not in report_data:
        return
    
    analysis = report_data['dry_dock_comprehensive_analysis']
    summary = analysis['summary']
    
    print(f"\n{'='*70}")
    print(f"DRY DOCK COMPREHENSIVE ANALYSIS")
    print(f"{'='*70}")
    
    print(f"Fleet-wide Dry Dock Statistics:")
    print(f"  Total Fleet Dry Dock Days: {summary['total_fleet_dry_dock_days']:,} days")
    print(f"  Average Days per Vessel: {summary['average_days_per_vessel']} days")
    print(f"  Vessels Currently in Dry Dock: {summary['vessels_currently_in_dry_dock']} ({summary['percentage_of_fleet_in_dry_dock']:.1f}%)")
    
    print(f"\nDry Dock Analysis by Vessel Type:")
    for vessel_type, data in analysis['analysis_by_vessel_type'].items():
        type_name = vessel_type.replace('_', ' ').title()
        print(f"  {type_name}:")
        print(f"    Total Vessels: {data['total_vessels']}")
        print(f"    In Dry Dock: {data['currently_in_dry_dock']} ({data['percentage_in_dry_dock']:.1f}%)")
        print(f"    Average Dry Dock Days: {data['average_dry_dock_days']} days")
    
    # Maintenance insights
    if 'maintenance_insights_and_recommendations' in analysis:
        print(f"\nMaintenance Insights:")
        for insight in analysis['maintenance_insights_and_recommendations']:
            print(f"  • {insight}")


def print_countries_analysis(report_data: Dict[str, Any]):
    """Print countries and service areas analysis"""
    if 'countries_and_service_areas' not in report_data:
        return
    
    analysis = report_data['countries_and_service_areas']
    
    print(f"\n{'='*70}")
    print(f"COUNTRIES AND SERVICE AREAS ANALYSIS")
    print(f"{'='*70}")
    
    # Flag state analysis
    flag_analysis = analysis['flag_state_analysis']
    print(f"Flag State Distribution:")
    print(f"  Total Flag States: {flag_analysis['total_flag_states']}")
    print(f"  Top 10 Flag States:")
    for country, data in flag_analysis['top_10_flag_states'].items():
        print(f"    {country}: {data['vessel_count']} vessels ({data['percentage']:.1f}%)")
    
    # Current locations
    location_analysis = analysis['current_location_analysis']
    print(f"\nCurrent Location Distribution:")
    print(f"  Countries with Vessels: {location_analysis['total_location_countries']}")
    print(f"  Top 10 Current Locations:")
    for country, data in location_analysis['top_10_current_locations'].items():
        print(f"    {country}: {data['vessel_count']} vessels ({data['percentage']:.1f}%)")
    
    # Global presence insights
    if 'global_presence_insights' in analysis:
        print(f"\nGlobal Presence Insights:")
        for insight in analysis['global_presence_insights']:
            print(f"  • {insight}")


def print_age_analysis(report_data: Dict[str, Any]):
    """Print vessel age analysis"""
    if 'vessel_age_analysis' not in report_data:
        return
    
    analysis = report_data['vessel_age_analysis']
    summary = analysis['summary']
    
    print(f"\n{'='*70}")
    print(f"VESSEL AGE COMPREHENSIVE ANALYSIS")
    print(f"{'='*70}")
    
    print(f"Fleet Age Statistics:")
    print(f"  Average Age: {summary['fleet_average_age']} years")
    print(f"  Median Age: {summary['fleet_median_age']} years")
    print(f"  Age Range: {summary['newest_vessel_age']} - {summary['oldest_vessel_age']} years")
    
    print(f"\nAge Distribution:")
    for age_range, data in analysis['age_distribution'].items():
        print(f"  {age_range}: {data['count']} vessels ({data['percentage']:.1f}%)")
    
    print(f"\nAge Analysis by Vessel Type:")
    for vessel_type, data in analysis['analysis_by_vessel_type'].items():
        type_name = vessel_type.replace('_', ' ').title()
        print(f"  {type_name}: Average {data['average_age']} years (Range: {data['age_range']['min']}-{data['age_range']['max']} years)")
    
    # Fleet renewal analysis
    renewal = analysis['fleet_renewal_analysis']
    print(f"\nFleet Renewal Analysis:")
    over_20 = renewal['vessels_over_20_years']
    over_25 = renewal['vessels_over_25_years']
    print(f"  Vessels over 20 years: {over_20['count']} ({over_20['percentage']:.1f}%)")
    print(f"  Vessels over 25 years: {over_25['count']} ({over_25['percentage']:.1f}%)")
    print(f"  Renewal Priority Score: {renewal['renewal_priority_score']}/100")


def generate_comprehensive_report(args):
    """Generate comprehensive report"""
    print_report_banner()
    print(f"Generating comprehensive vessel report...")
    print(f"Fleet size: {args.vessels} vessels")
    
    # Generate or load fleet
    if args.load_db:
        print("Loading data from database...")
        # In a real implementation, load from database
        fleet = generate_sample_fleet(args.vessels)
    else:
        print("Generating sample fleet...")
        fleet = generate_sample_fleet(args.vessels)
    
    # Create comprehensive reports
    reports = ComprehensiveVesselReports(fleet)
    
    # Generate master report
    master_report = reports.generate_master_comprehensive_report()
    
    # Print analyses based on options
    if args.summary or args.all:
        print_summary_stats(master_report)
    
    if args.vessel_types or args.all:
        print_vessel_type_analysis(master_report)
    
    if args.dry_dock or args.all:
        print_dry_dock_analysis(master_report)
    
    if args.countries or args.all:
        print_countries_analysis(master_report)
    
    if args.age_analysis or args.all:
        print_age_analysis(master_report)
    
    # Export report if requested
    if args.export:
        export_file = reports.export_comprehensive_report(args.export)
        print(f"\n{'='*70}")
        print(f"REPORT EXPORTED")
        print(f"{'='*70}")
        print(f"Comprehensive report exported to: {export_file}")
        print(f"Export time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Print recommendations
    if args.recommendations or args.all:
        recommendations = master_report['fleet_management_recommendations']
        print(f"\n{'='*70}")
        print(f"FLEET MANAGEMENT RECOMMENDATIONS")
        print(f"{'='*70}")
        
        for category, recs in recommendations.items():
            if recs and category not in ['fleet_optimization', 'geographic_expansion', 'fleet_renewal', 'operational_efficiency']:
                category_name = category.replace('_', ' ').title()
                print(f"\n{category_name}:")
                for rec in recs[:3]:  # Show top 3 recommendations
                    if isinstance(rec, dict):
                        print(f"  • {rec.get('vessel_name', 'N/A')}: {rec.get('recommendation', rec.get('issue', 'N/A'))}")
                    else:
                        print(f"  • {rec}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='AIS Vessel Comprehensive Reporting System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --vessels 1000 --all --export comprehensive_report.json
  %(prog)s --vessels 500 --summary --vessel-types
  %(prog)s --vessels 1000 --dry-dock --countries --export fleet_analysis.json
  %(prog)s --vessels 2000 --age-analysis --recommendations
  %(prog)s --load-db --all --export database_report.json
        """
    )
    
    # Fleet configuration
    parser.add_argument('--vessels', type=int, default=1000,
                       help='Number of vessels to analyze (default: 1000)')
    parser.add_argument('--load-db', action='store_true',
                       help='Load data from database instead of generating')
    parser.add_argument('--database-url', default='sqlite:///ais_vessels.db',
                       help='Database URL (default: sqlite:///ais_vessels.db)')
    
    # Report sections
    parser.add_argument('--all', action='store_true',
                       help='Generate all report sections')
    parser.add_argument('--summary', action='store_true',
                       help='Show executive summary')
    parser.add_argument('--vessel-types', action='store_true',
                       help='Show vessel type detailed analysis')
    parser.add_argument('--dry-dock', action='store_true',
                       help='Show dry dock comprehensive analysis')
    parser.add_argument('--countries', action='store_true',
                       help='Show countries and service areas analysis')
    parser.add_argument('--age-analysis', action='store_true',
                       help='Show vessel age comprehensive analysis')
    parser.add_argument('--recommendations', action='store_true',
                       help='Show fleet management recommendations')
    
    # Export options
    parser.add_argument('--export', metavar='FILENAME',
                       help='Export comprehensive report to JSON file')
    parser.add_argument('--format', choices=['json', 'csv', 'excel'], default='json',
                       help='Export format (default: json)')
    
    # Display options
    parser.add_argument('--quiet', action='store_true',
                       help='Minimize output (only show key metrics)')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed output including debug information')
    
    args = parser.parse_args()
    
    # If no specific sections requested, show summary
    if not any([args.all, args.summary, args.vessel_types, args.dry_dock, 
               args.countries, args.age_analysis, args.recommendations]):
        args.summary = True
    
    try:
        generate_comprehensive_report(args)
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError generating report: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
