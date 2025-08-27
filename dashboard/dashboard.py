"""
Interactive Dashboard for AIS Marine Vessel System
Provides comprehensive visualization and monitoring interface
"""

import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.ais_data_generator import generate_sample_fleet
from analytics.vessel_analytics import VesselAnalytics, create_analytics_dashboard_data
from models.vessel import VesselType, VesselStatus


class AISVesselDashboard:
    """Main dashboard application for AIS vessel monitoring"""
    
    def __init__(self, fleet_size: int = 1000):
        """Initialize dashboard with vessel fleet"""
        print(f"Generating fleet with {fleet_size} vessels for dashboard...")
        self.fleet = generate_sample_fleet(fleet_size)
        self.analytics = VesselAnalytics(self.fleet)
        self.dashboard_data = create_analytics_dashboard_data(self.fleet)
        
        # Initialize Dash app
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.app.title = "AIS Marine Vessel Dashboard"
        
        # Setup layout and callbacks
        self._setup_layout()
        self._setup_callbacks()
        
        print("Dashboard initialized successfully!")
    
    def _setup_layout(self):
        """Setup the dashboard layout"""
        
        # Header
        header = dbc.NavbarSimple(
            brand="AIS Marine Vessel Management System",
            brand_href="#",
            color="primary",
            dark=True,
            className="mb-4"
        )
        
        # Summary cards
        summary_cards = self._create_summary_cards()
        
        # Main content tabs
        tabs = dbc.Tabs([
            dbc.Tab(label="Fleet Overview", tab_id="overview"),
            dbc.Tab(label="Vessel Types", tab_id="types"),
            dbc.Tab(label="Dry Dock Analysis", tab_id="drydock"),
            dbc.Tab(label="Geographic Distribution", tab_id="geographic"),
            dbc.Tab(label="Performance Metrics", tab_id="performance"),
            dbc.Tab(label="Vessel Details", tab_id="details"),
        ], id="main-tabs", active_tab="overview")
        
        # Main layout
        self.app.layout = dbc.Container([
            header,
            summary_cards,
            html.Hr(),
            tabs,
            html.Div(id="tab-content", className="mt-4"),
            
            # Store components for data sharing
            dcc.Store(id="fleet-data", data=self.dashboard_data),
            dcc.Store(id="selected-vessel-type", data="all"),
            dcc.Store(id="selected-status", data="all"),
            
        ], fluid=True)
    
    def _create_summary_cards(self):
        """Create summary statistics cards"""
        stats = self.dashboard_data['fleet_overview']
        
        total_vessels = stats['total_vessels']
        vessels_in_dry_dock = stats['dry_dock_analysis']['currently_in_dry_dock']['count']
        avg_age = stats['age_analysis']['overall_stats']['mean_age']
        operational_vessels = stats['status_distribution']['vessels_in_operation']
        
        cards = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{total_vessels:,}", className="card-title text-primary"),
                        html.P("Total Vessels", className="card-text")
                    ])
                ], className="text-center")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{operational_vessels:,}", className="card-title text-success"),
                        html.P("Operational Vessels", className="card-text")
                    ])
                ], className="text-center")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{vessels_in_dry_dock:,}", className="card-title text-warning"),
                        html.P("In Dry Dock", className="card-text")
                    ])
                ], className="text-center")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{avg_age:.1f} yrs", className="card-title text-info"),
                        html.P("Average Fleet Age", className="card-text")
                    ])
                ], className="text-center")
            ], width=3),
        ])
        
        return cards
    
    def _setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            Output("tab-content", "children"),
            [Input("main-tabs", "active_tab"),
             Input("fleet-data", "data")]
        )
        def render_tab_content(active_tab, fleet_data):
            """Render content based on active tab"""
            
            if active_tab == "overview":
                return self._create_overview_tab(fleet_data)
            elif active_tab == "types":
                return self._create_types_tab(fleet_data)
            elif active_tab == "drydock":
                return self._create_drydock_tab(fleet_data)
            elif active_tab == "geographic":
                return self._create_geographic_tab(fleet_data)
            elif active_tab == "performance":
                return self._create_performance_tab(fleet_data)
            elif active_tab == "details":
                return self._create_details_tab(fleet_data)
            
            return html.Div("Select a tab to view content.")
    
    def _create_overview_tab(self, fleet_data):
        """Create fleet overview tab"""
        
        # Vessel type distribution pie chart
        type_fig = px.pie(
            values=fleet_data['vessel_types_chart']['values'],
            names=fleet_data['vessel_types_chart']['labels'],
            title="Fleet Composition by Vessel Type"
        )
        type_fig.update_traces(textposition='inside', textinfo='percent+label')
        
        # Age distribution histogram
        age_fig = px.bar(
            x=fleet_data['age_distribution_chart']['labels'],
            y=fleet_data['age_distribution_chart']['values'],
            title="Fleet Age Distribution",
            labels={'x': 'Age Range (Years)', 'y': 'Number of Vessels'}
        )
        
        # Status distribution
        status_fig = px.bar(
            x=fleet_data['status_distribution_chart']['labels'],
            y=fleet_data['status_distribution_chart']['values'],
            title="Vessel Status Distribution",
            labels={'x': 'Status', 'y': 'Number of Vessels'}
        )
        
        return dbc.Row([
            dbc.Col([
                dcc.Graph(figure=type_fig)
            ], width=6),
            dbc.Col([
                dcc.Graph(figure=age_fig)
            ], width=6),
            dbc.Col([
                dcc.Graph(figure=status_fig)
            ], width=12, className="mt-3")
        ])
    
    def _create_types_tab(self, fleet_data):
        """Create vessel types analysis tab"""
        
        # Create vessel type comparison charts
        type_stats = fleet_data['fleet_overview']['vessel_types']
        
        # Type distribution with counts and percentages
        type_df = pd.DataFrame([
            {'Type': k, 'Count': v['count'], 'Percentage': v['percentage']}
            for k, v in type_stats.items()
        ])
        
        # Count chart
        count_fig = px.bar(
            type_df, x='Type', y='Count',
            title="Vessel Count by Type",
            text='Count'
        )
        count_fig.update_traces(texttemplate='%{text}', textposition='outside')
        
        # Percentage chart
        pct_fig = px.bar(
            type_df, x='Type', y='Percentage',
            title="Vessel Distribution by Type (%)",
            text='Percentage'
        )
        pct_fig.update_traces(texttemplate='%{text}%', textposition='outside')
        
        # Age analysis by type
        vessels_df = pd.DataFrame(fleet_data['vessels_dataframe'])
        if not vessels_df.empty:
            age_by_type_fig = px.box(
                vessels_df, x='vessel_type', y='age_years',
                title="Age Distribution by Vessel Type"
            )
        else:
            age_by_type_fig = go.Figure()
        
        return dbc.Row([
            dbc.Col([
                dcc.Graph(figure=count_fig)
            ], width=6),
            dbc.Col([
                dcc.Graph(figure=pct_fig)
            ], width=6),
            dbc.Col([
                dcc.Graph(figure=age_by_type_fig)
            ], width=12, className="mt-3")
        ])
    
    def _create_drydock_tab(self, fleet_data):
        """Create dry dock analysis tab"""
        
        drydock_data = fleet_data['fleet_overview']['dry_dock_analysis']
        
        # Current dry dock status
        current_data = drydock_data['currently_in_dry_dock']
        
        # Dry dock by type pie chart
        if current_data['by_type']:
            drydock_type_fig = px.pie(
                values=list(current_data['by_type'].values()),
                names=list(current_data['by_type'].keys()),
                title=f"Vessels Currently in Dry Dock by Type (Total: {current_data['count']})"
            )
        else:
            drydock_type_fig = go.Figure()
            drydock_type_fig.add_annotation(text="No vessels currently in dry dock", 
                                          xref="paper", yref="paper", x=0.5, y=0.5)
        
        # Maintenance patterns
        maintenance_data = drydock_data['maintenance_patterns']
        
        # Create maintenance metrics cards
        maintenance_cards = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5(f"{maintenance_data['average_dry_dock_days_per_vessel']:.1f}", 
                               className="text-primary"),
                        html.P("Avg Days/Vessel", className="small text-muted")
                    ])
                ], className="text-center")
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5(f"{maintenance_data['total_fleet_dry_dock_days']:,}", 
                               className="text-warning"),
                        html.P("Total Fleet Days", className="small text-muted")
                    ])
                ], className="text-center")
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5(f"{current_data['percentage']:.1f}%", 
                               className="text-info"),
                        html.P("Currently in Dry Dock", className="small text-muted")
                    ])
                ], className="text-center")
            ], width=4)
        ])
        
        # Dry dock days by vessel type
        vessels_df = pd.DataFrame(fleet_data['vessels_dataframe'])
        if not vessels_df.empty:
            drydock_days_fig = px.box(
                vessels_df, x='vessel_type', y='total_dry_dock_days',
                title="Total Dry Dock Days by Vessel Type"
            )
        else:
            drydock_days_fig = go.Figure()
        
        return html.Div([
            maintenance_cards,
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=drydock_type_fig)
                ], width=6),
                dbc.Col([
                    dcc.Graph(figure=drydock_days_fig)
                ], width=6)
            ])
        ])
    
    def _create_geographic_tab(self, fleet_data):
        """Create geographic distribution tab"""
        
        geo_data = fleet_data['fleet_overview']['geographic_distribution']
        
        # Top flag states
        flag_states = geo_data['flag_states']['top_10']
        flag_fig = px.bar(
            x=list(flag_states.values()),
            y=list(flag_states.keys()),
            orientation='h',
            title="Top 10 Flag States",
            labels={'x': 'Number of Vessels', 'y': 'Country'}
        )
        
        # Current locations by country
        current_locations = geo_data['current_locations']['top_10_countries']
        location_fig = px.bar(
            x=list(current_locations.keys()),
            y=list(current_locations.values()),
            title="Top 10 Current Location Countries",
            labels={'x': 'Country', 'y': 'Number of Vessels'}
        )
        location_fig.update_xaxes(tickangle=45)
        
        # Regional distribution pie chart
        regional_data = geo_data['current_locations']['by_region']
        region_fig = px.pie(
            values=list(regional_data.values()),
            names=list(regional_data.keys()),
            title="Regional Distribution of Current Locations"
        )
        
        # Create world map with vessel locations
        vessels_df = pd.DataFrame(fleet_data['vessels_dataframe'])
        if not vessels_df.empty and 'current_latitude' in vessels_df.columns:
            # Filter out vessels without location data
            map_df = vessels_df.dropna(subset=['current_latitude', 'current_longitude'])
            
            if not map_df.empty:
                map_fig = px.scatter_mapbox(
                    map_df,
                    lat='current_latitude',
                    lon='current_longitude',
                    color='vessel_type',
                    size_max=15,
                    zoom=1,
                    title="Global Vessel Locations"
                )
                map_fig.update_layout(mapbox_style="open-street-map")
            else:
                map_fig = go.Figure()
        else:
            map_fig = go.Figure()
        
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=flag_fig)
                ], width=6),
                dbc.Col([
                    dcc.Graph(figure=location_fig)
                ], width=6)
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=region_fig)
                ], width=6),
                dbc.Col([
                    dcc.Graph(figure=map_fig)
                ], width=6)
            ])
        ])
    
    def _create_performance_tab(self, fleet_data):
        """Create performance metrics tab"""
        
        performance_data = fleet_data['fleet_overview']['performance_metrics']
        
        # Performance metrics cards
        performance_cards = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5(f"{performance_data['operational_efficiency']['fleet_utilization']:.1f}%", 
                               className="text-success"),
                        html.P("Fleet Utilization", className="small text-muted")
                    ])
                ], className="text-center")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5(f"{performance_data['operational_efficiency']['average_voyages_per_year']:.1f}", 
                               className="text-primary"),
                        html.P("Avg Voyages/Year", className="small text-muted")
                    ])
                ], className="text-center")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5(f"{performance_data['speed_analysis']['average_fleet_speed']:.1f} kts", 
                               className="text-info"),
                        html.P("Avg Fleet Speed", className="small text-muted")
                    ])
                ], className="text-center")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5(f"{performance_data['fuel_efficiency']['average_efficiency']:.3f}", 
                               className="text-warning"),
                        html.P("Fuel Efficiency", className="small text-muted")
                    ])
                ], className="text-center")
            ], width=3)
        ])
        
        # Speed by vessel type
        speed_by_type = performance_data['speed_analysis']['speed_by_type']
        speed_fig = px.bar(
            x=list(speed_by_type.keys()),
            y=list(speed_by_type.values()),
            title="Average Speed by Vessel Type",
            labels={'x': 'Vessel Type', 'y': 'Average Speed (knots)'}
        )
        
        # Fuel efficiency by type
        efficiency_by_type = performance_data['fuel_efficiency']['efficiency_by_type']
        efficiency_fig = px.bar(
            x=list(efficiency_by_type.keys()),
            y=list(efficiency_by_type.values()),
            title="Fuel Efficiency by Vessel Type",
            labels={'x': 'Vessel Type', 'y': 'Fuel Efficiency (tons/nm)'}
        )
        
        return html.Div([
            performance_cards,
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=speed_fig)
                ], width=6),
                dbc.Col([
                    dcc.Graph(figure=efficiency_fig)
                ], width=6)
            ])
        ])
    
    def _create_details_tab(self, fleet_data):
        """Create vessel details table tab"""
        
        vessels_df = pd.DataFrame(fleet_data['vessels_dataframe'])
        
        if vessels_df.empty:
            return html.Div("No vessel data available")
        
        # Prepare data for table
        display_columns = [
            'vessel_name', 'vessel_type', 'flag_state', 'age_years',
            'current_status', 'total_dry_dock_days', 'owner_company'
        ]
        
        # Filter available columns
        available_columns = [col for col in display_columns if col in vessels_df.columns]
        table_data = vessels_df[available_columns].to_dict('records')
        
        # Column definitions
        columns = [
            {"name": "Vessel Name", "id": "vessel_name"},
            {"name": "Type", "id": "vessel_type"},
            {"name": "Flag State", "id": "flag_state"},
            {"name": "Age (Years)", "id": "age_years", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Status", "id": "current_status"},
            {"name": "Dry Dock Days", "id": "total_dry_dock_days", "type": "numeric"},
            {"name": "Owner", "id": "owner_company"}
        ]
        
        # Filter columns based on available data
        available_column_ids = [col for col in available_columns]
        filtered_columns = [col for col in columns if col["id"] in available_column_ids]
        
        table = dash_table.DataTable(
            data=table_data,
            columns=filtered_columns,
            page_size=20,
            sort_action="native",
            filter_action="native",
            style_cell={'textAlign': 'left'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{current_status} = dry_dock'},
                    'backgroundColor': '#fff2cc',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{age_years} > 20'},
                    'backgroundColor': '#ffe6e6',
                    'color': 'black',
                }
            ]
        )
        
        return html.Div([
            html.H4("Vessel Details"),
            html.P("Table shows all vessels with filtering and sorting capabilities. "
                  "Vessels in dry dock are highlighted in yellow, vessels over 20 years old in light red."),
            table
        ])
    
    def run(self, host='127.0.0.1', port=8050, debug=True):
        """Run the dashboard application"""
        print(f"Starting AIS Dashboard...")
        print(f"Fleet size: {len(self.fleet.vessels)} vessels")
        print(f"Dashboard will be available at: http://{host}:{port}")
        
        self.app.run_server(host=host, port=port, debug=debug)


def create_dashboard_app(fleet_size: int = 500):
    """Factory function to create dashboard app"""
    dashboard = AISVesselDashboard(fleet_size=fleet_size)
    return dashboard.app


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AIS Marine Vessel Dashboard')
    parser.add_argument('--fleet-size', type=int, default=500, 
                       help='Number of vessels to generate (default: 500)')
    parser.add_argument('--host', default='127.0.0.1', 
                       help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8050, 
                       help='Port to bind to (default: 8050)')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create and run the dashboard
    dashboard = AISVesselDashboard(fleet_size=args.fleet_size)
    dashboard.run(host=args.host, port=args.port, debug=args.debug)
