#!/usr/bin/env python3
"""
Simple CSV Dashboard
Displays AIS data from CSV file without complex dependencies
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template_string, jsonify
from flask_cors import CORS

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loaders.csv_loader import AISCSVLoader

app = Flask(__name__)
CORS(app)

# Global variable to store loaded data
vessel_data = []

def load_csv_data(num_vessels=100):
    """Load AIS data from CSV file"""
    global vessel_data
    
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'files', 'AIS_2023_01_01.csv')
        loader = AISCSVLoader(csv_path)
        vessel_data = loader.load_sample_data(num_vessels)
        print(f"✅ Loaded {len(vessel_data)} vessels from CSV")
        return len(vessel_data)
    except Exception as e:
        print(f"❌ Error loading CSV data: {e}")
        return 0

@app.route('/')
def dashboard():
    """Main dashboard page"""
    
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIS CSV Data Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }

        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 1.5rem 2rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }

        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
        }

        .container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 0.5rem;
        }

        .stat-label {
            font-size: 1rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .vessel-table {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }

        .table-header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 1rem;
            font-size: 1.2rem;
            font-weight: 600;
        }

        .table-content {
            max-height: 600px;
            overflow-y: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #eee;
        }

        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        tr:hover {
            background-color: #f8f9fa;
        }

        .vessel-name {
            font-weight: 600;
            color: #667eea;
        }

        .mmsi {
            font-family: monospace;
            color: #764ba2;
        }

        .coordinates {
            font-family: monospace;
            font-size: 0.9rem;
        }

        .speed {
            color: #28a745;
            font-weight: 500;
        }

        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }

        .refresh-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 1rem;
            transition: transform 0.2s;
        }

        .refresh-btn:hover {
            transform: translateY(-2px);
        }

        .footer {
            text-align: center;
            padding: 2rem;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚢 AIS CSV Data Dashboard</h1>
    </div>

    <div class="container">
        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <div class="stat-number" id="totalVessels">-</div>
                <div class="stat-label">Total Vessels</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="averageSpeed">-</div>
                <div class="stat-label">Avg Speed (knots)</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="activeVessels">-</div>
                <div class="stat-label">Moving Vessels</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="lastUpdate">-</div>
                <div class="stat-label">Data Source</div>
            </div>
        </div>

        <div class="vessel-table">
            <div class="table-header">
                📊 Real AIS Vessel Data from CSV
                <button class="refresh-btn" onclick="loadVesselData()" style="float: right;">🔄 Refresh</button>
            </div>
            <div class="table-content">
                <table>
                    <thead>
                        <tr>
                            <th>Vessel Name</th>
                            <th>MMSI</th>
                            <th>Position (Lat, Lon)</th>
                            <th>Speed (knots)</th>
                            <th>Course</th>
                            <th>IMO</th>
                            <th>Call Sign</th>
                        </tr>
                    </thead>
                    <tbody id="vesselTableBody">
                        <tr>
                            <td colspan="7" class="loading">Loading vessel data...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="footer">
        Data loaded from AIS_2023_01_01.csv • Real vessel tracking information
    </div>

    <script>
        async function loadVesselData() {
            try {
                const response = await fetch('/api/vessels');
                const data = await response.json();
                
                // Update statistics
                document.getElementById('totalVessels').textContent = data.total_vessels;
                document.getElementById('averageSpeed').textContent = data.average_speed.toFixed(1);
                document.getElementById('activeVessels').textContent = data.moving_vessels;
                document.getElementById('lastUpdate').textContent = 'CSV File';
                
                // Update vessel table
                const tbody = document.getElementById('vesselTableBody');
                tbody.innerHTML = '';
                
                data.vessels.forEach(vessel => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td class="vessel-name">${vessel.vessel_name || 'Unknown'}</td>
                        <td class="mmsi">${vessel.mmsi}</td>
                        <td class="coordinates">${vessel.latitude.toFixed(4)}, ${vessel.longitude.toFixed(4)}</td>
                        <td class="speed">${vessel.speed_over_ground || 0}</td>
                        <td>${vessel.course_over_ground || '-'}</td>
                        <td>${vessel.imo_number || '-'}</td>
                        <td>${vessel.call_sign || '-'}</td>
                    `;
                    tbody.appendChild(row);
                });
                
            } catch (error) {
                console.error('Error loading vessel data:', error);
                document.getElementById('vesselTableBody').innerHTML = 
                    '<tr><td colspan="7" class="loading">Error loading data</td></tr>';
            }
        }

        // Load data when page loads
        window.addEventListener('DOMContentLoaded', loadVesselData);

        // Auto-refresh every 30 seconds
        setInterval(loadVesselData, 30000);
    </script>
</body>
</html>
    """
    
    return dashboard_html

@app.route('/api/vessels')
def api_vessels():
    """API endpoint to get vessel data"""
    global vessel_data
    
    if not vessel_data:
        return jsonify({
            'total_vessels': 0,
            'average_speed': 0,
            'moving_vessels': 0,
            'vessels': []
        })
    
    # Calculate statistics
    total_vessels = len(vessel_data)
    speeds = [v.get('speed_over_ground', 0) or 0 for v in vessel_data]
    average_speed = sum(speeds) / len(speeds) if speeds else 0
    moving_vessels = len([v for v in vessel_data if (v.get('speed_over_ground') or 0) > 0.5])
    
    return jsonify({
        'total_vessels': total_vessels,
        'average_speed': average_speed,
        'moving_vessels': moving_vessels,
        'vessels': vessel_data[:50]  # Limit to first 50 for display
    })

@app.route('/api/stats')
def api_stats():
    """API endpoint for detailed statistics"""
    global vessel_data
    
    if not vessel_data:
        return jsonify({'error': 'No data loaded'})
    
    # Calculate detailed statistics
    vessel_types = {}
    for vessel in vessel_data:
        vtype = vessel.get('vessel_type', 'Unknown')
        vessel_types[vtype] = vessel_types.get(vtype, 0) + 1
    
    stats = {
        'total_vessels': len(vessel_data),
        'vessel_types': vessel_types,
        'speed_stats': {
            'max_speed': max((v.get('speed_over_ground') or 0 for v in vessel_data), default=0),
            'min_speed': min((v.get('speed_over_ground') or 0 for v in vessel_data), default=0),
            'average_speed': sum((v.get('speed_over_ground') or 0 for v in vessel_data)) / len(vessel_data)
        },
        'geographic_bounds': {
            'north': max((v.get('latitude') or 0 for v in vessel_data), default=0),
            'south': min((v.get('latitude') or 0 for v in vessel_data), default=0),
            'east': max((v.get('longitude') or 0 for v in vessel_data), default=0),
            'west': min((v.get('longitude') or 0 for v in vessel_data), default=0)
        }
    }
    
    return jsonify(stats)

def main():
    """Main function to run the dashboard"""
    print("🚢 Starting AIS CSV Dashboard...")
    
    # Load CSV data
    num_loaded = load_csv_data(200)  # Load 200 vessels
    
    if num_loaded == 0:
        print("❌ No data loaded. Please check that AIS_2023_01_01.csv exists in the files/ directory")
        return
    
    print(f"✅ Dashboard ready with {num_loaded} vessels from CSV")
    print(f"🌐 Open your browser to: http://127.0.0.1:5001")
    print(f"📊 Real AIS data from CSV file will be displayed")
    print(f"🔄 Data refreshes automatically every 30 seconds")
    
    # Run the Flask app
    app.run(host='127.0.0.1', port=5001, debug=True)

if __name__ == '__main__':
    main()

