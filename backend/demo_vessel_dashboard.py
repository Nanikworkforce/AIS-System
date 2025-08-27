#!/usr/bin/env python3
"""
Demo Script for Vessel Categorization Dashboard
Shows the key features and capabilities of the new dashboard system
"""

import json
import time
from datetime import datetime

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_feature(icon, title, description):
    print(f"{icon} {title}")
    print(f"   {description}")
    print()

def demo_vessel_categories():
    print_header("🚢 VESSEL CATEGORIZATION")
    
    categories = {
        "🛢️ Tankers": {
            "description": "Oil, chemical, and liquid cargo transport vessels",
            "features": ["Specialized cargo tanks", "Double hull construction", "Chemical compatibility"],
            "example_specs": "300,000 DWT, 400m length, specialized pumping systems"
        },
        "📦 Container Ships": {
            "description": "Containerized cargo vessels with TEU capacity",
            "features": ["Container guides and locks", "Automated handling", "Modular cargo"],
            "example_specs": "24,000 TEU, 400m length, automated crane systems"
        },
        "⚓ Bulk Carriers": {
            "description": "Dry bulk cargo vessels for grain, ore, coal",
            "features": ["Large cargo holds", "Self-unloading systems", "Weatherproof"],
            "example_specs": "400,000 DWT, 360m length, conveyor systems"
        },
        "🚢 General Cargo": {
            "description": "Multi-purpose cargo vessels for diverse freight",
            "features": ["Flexible cargo spaces", "Multi-deck design", "Versatile handling"],
            "example_specs": "75,000 DWT, 250m length, multipurpose cranes"
        }
    }
    
    for category, info in categories.items():
        print(f"{category}")
        print(f"   Description: {info['description']}")
        print(f"   Key Features: {', '.join(info['features'])}")
        print(f"   Example Specs: {info['example_specs']}")
        print()

def demo_vessel_details():
    print_header("🔧 DETAILED VESSEL INFORMATION")
    
    sample_vessel = {
        "vessel_name": "Nordic Explorer",
        "vessel_type": "tanker",
        "imo_number": "IMO9000001",
        "specifications": {
            "length": 350,
            "beam": 56,
            "gross_tonnage": 180000,
            "deadweight": 320000,
            "cargo_capacity": "320,000 DWT"
        },
        "details": {
            "build_year": 2018,
            "age_years": 5,
            "flag_country": "Norway",
            "operator": "Nordic Shipping Co."
        },
        "dry_dock": {
            "last_dry_dock": "2023-03-15",
            "days_since_dry_dock": 225,
            "next_dry_dock": "2025-03-15",
            "days_to_next_dry_dock": 505,
            "last_duration_days": 35
        },
        "navigation": {
            "speed": 14.2,
            "heading": 180,
            "status": "at_sea"
        }
    }
    
    print(f"🚢 Sample Vessel: {sample_vessel['vessel_name']}")
    print(f"   Type: {sample_vessel['vessel_type'].upper()}")
    print(f"   IMO: {sample_vessel['imo_number']}")
    print()
    
    print("📏 Technical Specifications:")
    specs = sample_vessel['specifications']
    print(f"   • Length: {specs['length']}m")
    print(f"   • Beam: {specs['beam']}m")
    print(f"   • Gross Tonnage: {specs['gross_tonnage']:,}")
    print(f"   • Deadweight: {specs['deadweight']:,}")
    print(f"   • Cargo Capacity: {specs['cargo_capacity']}")
    print()
    
    print("📋 Vessel Details:")
    details = sample_vessel['details']
    print(f"   • Build Year: {details['build_year']}")
    print(f"   • Age: {details['age_years']} years")
    print(f"   • Flag: {details['flag_country']}")
    print(f"   • Operator: {details['operator']}")
    print()
    
    print("🔧 Dry Dock Information:")
    dry_dock = sample_vessel['dry_dock']
    print(f"   • Last Dry Dock: {dry_dock['last_dry_dock']}")
    print(f"   • Days Since: {dry_dock['days_since_dry_dock']} days")
    print(f"   • Duration: {dry_dock['last_duration_days']} days")
    print(f"   • Next Scheduled: {dry_dock['next_dry_dock']}")
    print(f"   • Days Until: {dry_dock['days_to_next_dry_dock']} days")
    print()
    
    print("🧭 Navigation Status:")
    nav = sample_vessel['navigation']
    print(f"   • Speed: {nav['speed']} knots")
    print(f"   • Heading: {nav['heading']}°")
    print(f"   • Status: {nav['status'].replace('_', ' ').upper()}")

def demo_dashboard_features():
    print_header("🎯 DASHBOARD FEATURES")
    
    features = [
        ("📊", "Real-time Fleet Statistics", "Live updates of vessel counts, status distribution, and fleet metrics"),
        ("🔍", "Interactive Category Cards", "Click to expand vessel lists, view detailed breakdowns by type"),
        ("📱", "Responsive Design", "Works seamlessly on desktop, tablet, and mobile devices"),
        ("🔄", "Live Data Streaming", "WebSocket-based real-time vessel position and status updates"),
        ("📅", "Date-Based Queries", "Historical data analysis with customizable date ranges"),
        ("🔧", "Detailed Vessel Modals", "Comprehensive vessel information including specs and maintenance"),
        ("🎨", "Modern UI Design", "Glass-morphism effects, smooth animations, and intuitive interface"),
        ("⚡", "High Performance", "Optimized for large fleet management with minimal latency")
    ]
    
    for icon, title, description in features:
        print_feature(icon, title, description)

def demo_query_system():
    print_header("📅 DATE-BASED QUERY SYSTEM")
    
    print("🔍 Query Capabilities:")
    print("   • Historical vessel positions over selected date ranges")
    print("   • Fleet movement pattern analysis")
    print("   • Status change tracking over time")
    print("   • Port visit history and frequency")
    print("   • Maintenance schedule compliance monitoring")
    print()
    
    print("📊 Example Query Results:")
    print("   Date Range: 2024-01-01 to 2024-01-31")
    print("   • 25 vessels tracked")
    print("   • 1,240 position updates")
    print("   • 67 port visits")
    print("   • 3 dry dock entries")
    print("   • Average speed: 12.8 knots")

def demo_technical_specs():
    print_header("🛠️ TECHNICAL ARCHITECTURE")
    
    print("🔗 WebSocket Communication:")
    print("   • Enhanced Server: ws://localhost:8766")
    print("   • Simple Server: ws://localhost:8765")
    print("   • Real-time bidirectional communication")
    print("   • Automatic reconnection handling")
    print()
    
    print("📊 Data Management:")
    print("   • 25 diverse vessel fleet simulation")
    print("   • 30 days of historical position data")
    print("   • Comprehensive vessel specifications")
    print("   • Realistic dry dock scheduling")
    print()
    
    print("🎨 Frontend Technology:")
    print("   • Vanilla JavaScript (no frameworks)")
    print("   • Modern CSS with advanced features")
    print("   • Responsive grid layouts")
    print("   • Modal-based detail views")

def demo_usage_instructions():
    print_header("🚀 GETTING STARTED")
    
    print("1️⃣ Launch the System:")
    print("   python run_vessel_dashboard.py")
    print()
    
    print("2️⃣ Dashboard Navigation:")
    print("   • View fleet overview statistics")
    print("   • Click category cards to explore vessel types")
    print("   • Click individual vessels for detailed information")
    print("   • Use date picker for historical queries")
    print()
    
    print("3️⃣ Key Interactions:")
    print("   • Category expansion: Click any vessel type card")
    print("   • Vessel details: Click any vessel in the list")
    print("   • Date queries: Select date range and click query")
    print("   • Live updates: Data refreshes automatically")
    print()
    
    print("🎯 Dashboard URL:")
    print("   vessel_categorization_dashboard.html")
    print("   (Opens automatically with the launcher)")

def main():
    print("🌊" + "="*60 + "🌊")
    print("    VESSEL CATEGORIZATION DASHBOARD - DEMO")
    print("="*64)
    print("    Advanced Fleet Management System")
    print("    Real-time Tracking • Categorization • Analytics")
    print("="*64)
    
    demo_vessel_categories()
    demo_vessel_details()
    demo_dashboard_features()
    demo_query_system()
    demo_technical_specs()
    demo_usage_instructions()
    
    print_header("✨ READY TO LAUNCH")
    print("The vessel categorization dashboard is ready to use!")
    print("Run 'python run_vessel_dashboard.py' to start the system.")
    print()
    print("📚 For detailed documentation, see: VESSEL_DASHBOARD_README.md")
    print("🔧 For basic WebSocket testing, see: simple_live_websocket_server.py")

if __name__ == "__main__":
    main()
