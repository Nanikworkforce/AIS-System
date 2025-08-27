# 🚢 Vessel Categorization Dashboard

An advanced vessel fleet management dashboard with comprehensive categorization, detailed vessel information, and date-based query capabilities.

## 🌟 Features

### 📊 Vessel Categorization
- **Tankers** - Oil, chemical, and liquid cargo transport vessels
- **Container Ships** - Containerized cargo vessels (TEU capacity)
- **Bulk Carriers** - Dry bulk cargo vessels (grain, ore, coal)
- **General Cargo** - Multi-purpose cargo vessels

### 🔍 Detailed Vessel Information
- **Technical Specifications**: Length, beam, gross tonnage, deadweight, cargo capacity
- **Vessel Details**: IMO number, MMSI, build year, age, flag country, operator
- **Dry Dock History**: Last maintenance, duration, next scheduled maintenance
- **Real-time Location**: Current position, speed, heading, navigation status
- **Port Information**: Current port, destination, estimated time of arrival

### 📅 Date-Based Query System
- Historical vessel position data
- Date range filtering for fleet analysis
- Movement pattern tracking
- Status history over time

### 🎛️ Interactive Dashboard
- Click category cards to expand vessel lists
- Click individual vessels for detailed modal view
- Real-time fleet statistics
- Responsive design for all devices

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install websockets
```

### 2. Run the Dashboard
```bash
python run_vessel_dashboard.py
```

This will:
- Start the enhanced WebSocket server on port 8766
- Open the dashboard in your default browser
- Display real-time vessel data

### 3. Manual Start (Alternative)

**Start Server:**
```bash
python enhanced_vessel_dashboard_server.py
```

**Open Dashboard:**
Open `vessel_categorization_dashboard.html` in your browser

## 📋 Dashboard Components

### Fleet Overview
- Total vessel count
- Vessels at sea
- Vessels in port  
- Vessels in dry dock

### Category Cards
Each vessel type displays:
- Vessel count in category
- Number at sea vs in port
- Average fleet age
- Expandable vessel list

### Vessel Details Modal
Comprehensive information including:
- Technical specifications
- Vessel identification
- Dry dock maintenance history
- Current location and navigation
- Port and destination information

### Date Query System
- Select start and end dates
- Query historical vessel data
- Analyze fleet movements over time

## 🛠️ Technical Architecture

### Backend Server (`enhanced_vessel_dashboard_server.py`)
- **Port**: 8766
- **Protocol**: WebSocket
- **Features**:
  - Real-time vessel data streaming
  - Categorized vessel management
  - Historical data simulation
  - Date range queries
  - Detailed vessel specifications

### Frontend Dashboard (`vessel_categorization_dashboard.html`)
- **Framework**: Vanilla JavaScript
- **Styling**: Modern CSS with gradients and animations
- **Features**:
  - Responsive grid layout
  - Interactive category cards
  - Modal-based detail views
  - Real-time WebSocket communication

## 📊 Data Model

### Vessel Categories
```javascript
{
  tanker: "Oil and chemical transport",
  container: "Containerized cargo",
  bulker: "Dry bulk cargo", 
  general_cargo: "Multi-purpose cargo"
}
```

### Vessel Data Structure
```javascript
{
  imo_number: "IMO9000001",
  vessel_name: "Example Vessel",
  vessel_type: "tanker",
  specifications: {
    length: 300,
    beam: 50,
    gross_tonnage: 150000,
    deadweight: 250000,
    cargo_capacity: "250,000 DWT"
  },
  details: {
    build_year: 2015,
    age_years: 8,
    flag_country: "Norway",
    operator: "Example Shipping Co."
  },
  dry_dock: {
    last_dry_dock: "2023-06-15",
    days_since_dry_dock: 180,
    next_dry_dock: "2025-06-15",
    days_to_next_dry_dock: 545,
    last_duration_days: 45
  },
  position: {
    latitude: 59.9139,
    longitude: 10.7522
  },
  navigation: {
    speed: 12.5,
    heading: 045,
    status: "at_sea"
  }
}
```

## 🔧 Configuration

### Server Configuration
- **Host**: localhost
- **Port**: 8766 (enhanced server) / 8765 (simple server)
- **Update Interval**: 15 seconds
- **Fleet Size**: 25 diverse vessels

### Dashboard Configuration
- **Connection**: Automatic WebSocket connection
- **Reconnection**: Automatic with 5-second intervals
- **Categories**: 4 vessel types with detailed breakdowns
- **History**: 30 days of simulated historical data

## 🎯 Use Cases

### Fleet Management
- Monitor vessel distribution by type
- Track dry dock maintenance schedules
- Analyze vessel age and replacement needs
- Oversee port operations and vessel status

### Operations Monitoring
- Real-time fleet positioning
- Navigation status tracking
- Port arrival/departure monitoring
- Emergency response coordination

### Historical Analysis
- Fleet movement patterns
- Seasonal operation analysis
- Performance metrics over time
- Maintenance scheduling optimization

## 🔄 Real-time Updates

The dashboard receives real-time updates for:
- Vessel position changes
- Navigation status updates
- Port arrivals and departures
- Fleet statistics refresh

## 📱 Responsive Design

The dashboard is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones
- Large displays/monitors

## 🎨 Visual Features

- **Modern Design**: Glass-morphism effects and gradients
- **Color Coding**: Different colors for each vessel type
- **Animations**: Smooth transitions and hover effects
- **Icons**: Intuitive vessel type icons
- **Typography**: Clean, readable fonts with proper hierarchy

## 🔗 Related Files

- `simple_live_websocket_server.py` - Basic WebSocket server (port 8765)
- `realtime_dashboard.html` - Basic real-time dashboard
- `models/vessel.py` - Vessel data models
- `requirements.txt` - Python dependencies

## 🆘 Troubleshooting

### Connection Issues
- Ensure server is running on correct port
- Check firewall settings
- Verify WebSocket support in browser

### Data Issues
- Refresh browser cache
- Restart the server
- Check console for error messages

### Performance Issues
- Close other browser tabs
- Reduce update frequency
- Check system resources

## 📈 Future Enhancements

- Map visualization integration
- Advanced filtering and search
- Export functionality for reports
- Integration with external AIS data sources
- Maintenance scheduling system
- Performance analytics dashboard
