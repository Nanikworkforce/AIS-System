#!/usr/bin/env python3
"""
Simple AIS Vessel System Demo - No external dependencies
Demonstrates core functionality without requiring additional packages
"""

from datetime import datetime, timedelta
import json
import random

# Simple vessel models without external dependencies
class SimpleVessel:
    def __init__(self, name, vessel_type, age, flag_state, dry_dock_days):
        self.name = name
        self.vessel_type = vessel_type
        self.age = age
        self.flag_state = flag_state
        self.dry_dock_days = dry_dock_days
        self.imo_number = f"IMO{random.randint(1000000, 9999999)}"

def generate_simple_fleet(size=100):
    """Generate simple fleet for demonstration"""
    vessel_types = ['tanker', 'bulker', 'container', 'general_cargo']
    flag_states = ['Panama', 'Liberia', 'Marshall Islands', 'Singapore', 'Malta', 'China', 'Greece']
    
    fleet = []
    for i in range(size):
        vessel = SimpleVessel(
            name=f"MV Vessel {i+1}",
            vessel_type=random.choice(vessel_types),
            age=random.uniform(1, 30),
            flag_state=random.choice(flag_states),
            dry_dock_days=random.randint(0, 150)
        )
        fleet.append(vessel)
    
    return fleet

def analyze_fleet(fleet):
    """Analyze fleet and return comprehensive statistics"""
    total_vessels = len(fleet)
    
    # Vessel type analysis
    type_counts = {}
    for vessel in fleet:
        if vessel.vessel_type in type_counts:
            type_counts[vessel.vessel_type] += 1
        else:
            type_counts[vessel.vessel_type] = 1
    
    # Convert to percentages
    type_percentages = {}
    for vessel_type, count in type_counts.items():
        type_percentages[vessel_type] = round(count / total_vessels * 100, 2)
    
    # Age analysis
    ages = [vessel.age for vessel in fleet]
    avg_age = sum(ages) / len(ages)
    old_vessels = len([v for v in fleet if v.age > 20])
    very_old_vessels = len([v for v in fleet if v.age > 25])
    
    # Flag state analysis
    flag_counts = {}
    for vessel in fleet:
        if vessel.flag_state in flag_counts:
            flag_counts[vessel.flag_state] += 1
        else:
            flag_counts[vessel.flag_state] = 1
    
    # Dry dock analysis
    dry_dock_days = [vessel.dry_dock_days for vessel in fleet]
    total_dry_dock_days = sum(dry_dock_days)
    avg_dry_dock_days = total_dry_dock_days / len(dry_dock_days)
    high_maintenance = len([v for v in fleet if v.dry_dock_days > 100])
    
    return {
        'fleet_summary': {
            'total_vessels': total_vessels,
            'average_age': round(avg_age, 2),
            'vessels_over_20_years': old_vessels,
            'vessels_over_25_years': very_old_vessels
        },
        'vessel_types': {
            'counts': type_counts,
            'percentages': type_percentages
        },
        'flag_states': flag_counts,
        'dry_dock_analysis': {
            'total_dry_dock_days': total_dry_dock_days,
            'average_days_per_vessel': round(avg_dry_dock_days, 2),
            'high_maintenance_vessels': high_maintenance
        }
    }

def print_analysis_report(analysis):
    """Print formatted analysis report"""
    print("=" * 80)
    print("AIS MARINE VESSEL SYSTEM - ANALYSIS REPORT")
    print("=" * 80)
    
    # Fleet Summary
    summary = analysis['fleet_summary']
    print(f"\nFLEET SUMMARY:")
    print(f"  Total Vessels: {summary['total_vessels']:,}")
    print(f"  Average Age: {summary['average_age']} years")
    print(f"  Vessels over 20 years: {summary['vessels_over_20_years']} ({summary['vessels_over_20_years']/summary['total_vessels']*100:.1f}%)")
    print(f"  Vessels over 25 years: {summary['vessels_over_25_years']} ({summary['vessels_over_25_years']/summary['total_vessels']*100:.1f}%)")
    
    # Vessel Type Distribution
    types = analysis['vessel_types']
    print(f"\nVESSEL TYPE DISTRIBUTION:")
    for vessel_type, count in types['counts'].items():
        percentage = types['percentages'][vessel_type]
        type_name = vessel_type.replace('_', ' ').title()
        print(f"  {type_name}: {count} vessels ({percentage}%)")
    
    # Flag State Analysis
    flags = analysis['flag_states']
    print(f"\nTOP FLAG STATES:")
    sorted_flags = sorted(flags.items(), key=lambda x: x[1], reverse=True)
    for country, count in sorted_flags[:5]:
        percentage = count / summary['total_vessels'] * 100
        print(f"  {country}: {count} vessels ({percentage:.1f}%)")
    
    # Dry Dock Analysis
    dry_dock = analysis['dry_dock_analysis']
    print(f"\nDRY DOCK ANALYSIS:")
    print(f"  Total Fleet Dry Dock Days: {dry_dock['total_dry_dock_days']:,}")
    print(f"  Average Days per Vessel: {dry_dock['average_days_per_vessel']}")
    print(f"  High Maintenance Vessels: {dry_dock['high_maintenance_vessels']} ({dry_dock['high_maintenance_vessels']/summary['total_vessels']*100:.1f}%)")

def demonstrate_comprehensive_features():
    """Demonstrate comprehensive AIS system features"""
    print("🚢 AIS MARINE VESSEL MANAGEMENT SYSTEM")
    print("   Comprehensive Demo - Core Features")
    print()
    
    # Generate fleet
    print("📊 GENERATING VESSEL FLEET...")
    fleet = generate_simple_fleet(1000)
    print(f"✅ Generated {len(fleet)} vessels successfully")
    print()
    
    # Analyze fleet
    print("🔍 ANALYZING FLEET COMPOSITION...")
    analysis = analyze_fleet(fleet)
    print("✅ Analysis completed")
    print()
    
    # Print comprehensive report
    print_analysis_report(analysis)
    
    # Show vessel examples
    print(f"\nSAMPLE VESSELS:")
    for i, vessel in enumerate(fleet[:5]):
        print(f"  {i+1}. {vessel.name} ({vessel.vessel_type.title()})")
        print(f"     Age: {vessel.age:.1f} years | Flag: {vessel.flag_state} | Dry Dock: {vessel.dry_dock_days} days")
    
    # Export sample data
    export_filename = f"simple_fleet_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(export_filename, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n📁 REPORT EXPORTED:")
    print(f"   Filename: {export_filename}")
    print(f"   Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n✨ SYSTEM CAPABILITIES DEMONSTRATED:")
    print(f"   ✓ Realistic vessel data generation")
    print(f"   ✓ Comprehensive fleet analysis")
    print(f"   ✓ Vessel type categorization (Tankers, Bulkers, Containers, General)")
    print(f"   ✓ Geographic distribution analysis")
    print(f"   ✓ Age-based fleet assessment")
    print(f"   ✓ Dry dock maintenance tracking")
    print(f"   ✓ Report generation and export")
    
    print(f"\n🚀 FULL SYSTEM FEATURES:")
    print(f"   • Advanced analytics with pandas/numpy")
    print(f"   • Interactive dashboard with Plotly/Dash")
    print(f"   • REST API with comprehensive endpoints")
    print(f"   • Database integration with SQLAlchemy")
    print(f"   • Realistic data generation with Faker")
    print(f"   • Command-line reporting tools")
    print(f"   • Export to JSON, CSV, and Excel formats")
    
    print(f"\n📚 TO EXPLORE THE FULL SYSTEM:")
    print(f"   1. Install dependencies: pip install -r requirements.txt")
    print(f"   2. Run full demo: python demo_comprehensive_ais.py")
    print(f"   3. Start API server: python main.py api --vessels 1000")
    print(f"   4. Launch dashboard: python main.py dashboard --vessels 1000")
    print(f"   5. Generate reports: python cli_reports.py --vessels 1000 --all")
    
    print(f"\nThank you for exploring the AIS Marine Vessel Management System! 🌊")

if __name__ == '__main__':
    demonstrate_comprehensive_features()
