"""
Vessel Analytics System
Advanced analytics and reporting for marine vessel data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from models.vessel import Vessel, VesselFleet, VesselType, VesselStatus, ServiceLine


class VesselAnalytics:
    """Advanced analytics for vessel fleet management"""
    
    def __init__(self, fleet: VesselFleet):
        """Initialize analytics with vessel fleet"""
        self.fleet = fleet
        self.df = self._create_dataframe()
    
    def _create_dataframe(self) -> pd.DataFrame:
        """Convert vessel fleet to pandas DataFrame for analysis"""
        data = []
        
        for vessel in self.fleet.vessels:
            # Basic vessel data
            row = {
                'imo_number': vessel.imo_number,
                'vessel_name': vessel.vessel_name,
                'vessel_type': vessel.vessel_type.value,
                'service_line': vessel.service_line.value,
                'flag_state': vessel.flag_state,
                'owner_company': vessel.owner_company,
                'operator_company': vessel.operator_company,
                'current_status': vessel.current_status.value,
                'age_years': vessel.age_years,
                'build_year': vessel.build_date.year,
                'total_dry_dock_days': vessel.total_dry_dock_days,
                'dry_dock_visits': len(vessel.dry_dock_history),
                'dry_dock_frequency': vessel.dry_dock_frequency,
                'currently_in_dry_dock': vessel.current_dry_dock is not None,
                'total_voyages': vessel.total_voyages,
                'total_distance_nm': vessel.total_distance_nm,
                'average_speed_knots': vessel.average_speed_knots,
                'fuel_efficiency': vessel.fuel_efficiency
            }
            
            # Current location
            if vessel.current_location:
                row.update({
                    'current_latitude': vessel.current_location.latitude,
                    'current_longitude': vessel.current_location.longitude,
                    'current_port': vessel.current_location.port_name,
                    'current_country': vessel.current_location.country
                })
            else:
                row.update({
                    'current_latitude': None,
                    'current_longitude': None,
                    'current_port': None,
                    'current_country': None
                })
            
            # Specifications
            if vessel.specifications:
                row.update({
                    'length_meters': vessel.specifications.length_meters,
                    'width_meters': vessel.specifications.width_meters,
                    'gross_tonnage': vessel.specifications.gross_tonnage,
                    'deadweight_tonnage': vessel.specifications.deadweight_tonnage,
                    'max_speed_knots': vessel.specifications.max_speed_knots,
                    'engine_power_hp': vessel.specifications.engine_power_hp,
                    'fuel_capacity_tons': vessel.specifications.fuel_capacity_tons,
                    'cargo_capacity': vessel.specifications.cargo_capacity,
                    'size_category': vessel.specifications.size_category
                })
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def get_fleet_overview(self) -> Dict[str, Any]:
        """Generate comprehensive fleet overview"""
        return {
            'total_vessels': len(self.df),
            'vessel_types': self._get_type_distribution(),
            'age_analysis': self._get_age_analysis(),
            'status_distribution': self._get_status_distribution(),
            'geographic_distribution': self._get_geographic_distribution(),
            'dry_dock_analysis': self._get_dry_dock_analysis(),
            'performance_metrics': self._get_performance_metrics(),
            'size_analysis': self._get_size_analysis()
        }
    
    def _get_type_distribution(self) -> Dict[str, Any]:
        """Analyze vessel type distribution"""
        type_counts = self.df['vessel_type'].value_counts()
        total = len(self.df)
        
        return {
            'counts': type_counts.to_dict(),
            'percentages': (type_counts / total * 100).round(2).to_dict(),
            'total': total
        }
    
    def _get_age_analysis(self) -> Dict[str, Any]:
        """Analyze fleet age characteristics"""
        ages = self.df['age_years']
        
        # Age categories
        age_categories = pd.cut(ages, 
                               bins=[0, 5, 10, 15, 20, 25, 100], 
                               labels=['0-5', '6-10', '11-15', '16-20', '21-25', '25+'])
        
        # Age by vessel type
        age_by_type = self.df.groupby('vessel_type')['age_years'].agg(['mean', 'median', 'std']).round(2)
        
        return {
            'overall_stats': {
                'mean_age': ages.mean().round(2),
                'median_age': ages.median().round(2),
                'oldest_vessel': ages.max().round(2),
                'newest_vessel': ages.min().round(2),
                'std_deviation': ages.std().round(2)
            },
            'age_categories': age_categories.value_counts().to_dict(),
            'by_vessel_type': age_by_type.to_dict(),
            'aging_vessels': len(self.df[self.df['age_years'] > 20])  # Vessels over 20 years
        }
    
    def _get_status_distribution(self) -> Dict[str, Any]:
        """Analyze current vessel status distribution"""
        status_counts = self.df['current_status'].value_counts()
        total = len(self.df)
        
        # Status by vessel type
        status_by_type = pd.crosstab(self.df['vessel_type'], self.df['current_status'])
        
        return {
            'overall': {
                'counts': status_counts.to_dict(),
                'percentages': (status_counts / total * 100).round(2).to_dict()
            },
            'by_vessel_type': status_by_type.to_dict(),
            'vessels_in_operation': len(self.df[self.df['current_status'].isin(['at_sea', 'in_port'])]),
            'vessels_out_of_service': len(self.df[self.df['current_status'].isin(['dry_dock', 'under_repair'])])
        }
    
    def _get_geographic_distribution(self) -> Dict[str, Any]:
        """Analyze geographic distribution of vessels"""
        # Flag state distribution
        flag_counts = self.df['flag_state'].value_counts()
        
        # Current location distribution
        current_country_counts = self.df['current_country'].value_counts()
        
        # Vessels by region (simplified)
        region_mapping = {
            'Asia': ['China', 'Japan', 'South Korea', 'Singapore', 'Hong Kong', 'Taiwan'],
            'Europe': ['Netherlands', 'Germany', 'United Kingdom', 'Belgium', 'Spain', 'Italy', 'Greece'],
            'North America': ['United States', 'Canada'],
            'Middle East': ['UAE', 'Saudi Arabia', 'Qatar'],
            'Others': []  # Will be filled dynamically
        }
        
        region_counts = defaultdict(int)
        for country in current_country_counts.index:
            assigned = False
            for region, countries in region_mapping.items():
                if country in countries:
                    region_counts[region] += current_country_counts[country]
                    assigned = True
                    break
            if not assigned:
                region_counts['Others'] += current_country_counts[country]
        
        return {
            'flag_states': {
                'top_10': flag_counts.head(10).to_dict(),
                'total_countries': len(flag_counts)
            },
            'current_locations': {
                'top_10_countries': current_country_counts.head(10).to_dict(),
                'by_region': dict(region_counts)
            }
        }
    
    def _get_dry_dock_analysis(self) -> Dict[str, Any]:
        """Analyze dry dock patterns and maintenance"""
        # Basic dry dock statistics
        vessels_in_dry_dock = self.df[self.df['currently_in_dry_dock'] == True]
        
        # Dry dock frequency by vessel type
        dry_dock_by_type = self.df.groupby('vessel_type')['total_dry_dock_days'].agg(['mean', 'median', 'sum']).round(2)
        
        # Vessels due for dry dock (simplified: if last visit > 3 years ago)
        # This would need more sophisticated logic with actual dates
        high_maintenance_vessels = self.df[self.df['total_dry_dock_days'] > self.df['total_dry_dock_days'].quantile(0.8)]
        
        return {
            'currently_in_dry_dock': {
                'count': len(vessels_in_dry_dock),
                'percentage': (len(vessels_in_dry_dock) / len(self.df) * 100).round(2),
                'by_type': vessels_in_dry_dock['vessel_type'].value_counts().to_dict()
            },
            'maintenance_patterns': {
                'average_dry_dock_days_per_vessel': self.df['total_dry_dock_days'].mean().round(2),
                'total_fleet_dry_dock_days': self.df['total_dry_dock_days'].sum(),
                'by_vessel_type': dry_dock_by_type.to_dict()
            },
            'high_maintenance_vessels': {
                'count': len(high_maintenance_vessels),
                'threshold_days': self.df['total_dry_dock_days'].quantile(0.8).round(2)
            }
        }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Analyze vessel performance metrics"""
        return {
            'operational_efficiency': {
                'average_voyages_per_year': (self.df['total_voyages'] / self.df['age_years']).mean().round(2),
                'average_distance_per_year': (self.df['total_distance_nm'] / self.df['age_years']).mean().round(0),
                'fleet_utilization': (len(self.df[self.df['current_status'].isin(['at_sea', 'in_port'])]) / len(self.df) * 100).round(2)
            },
            'speed_analysis': {
                'average_fleet_speed': self.df['average_speed_knots'].mean().round(2),
                'speed_by_type': self.df.groupby('vessel_type')['average_speed_knots'].mean().round(2).to_dict()
            },
            'fuel_efficiency': {
                'average_efficiency': self.df['fuel_efficiency'].mean().round(3),
                'efficiency_by_type': self.df.groupby('vessel_type')['fuel_efficiency'].mean().round(3).to_dict()
            }
        }
    
    def _get_size_analysis(self) -> Dict[str, Any]:
        """Analyze vessel size distribution"""
        if 'size_category' in self.df.columns:
            size_distribution = self.df['size_category'].value_counts()
            
            # Average specifications by type
            size_metrics = self.df.groupby('vessel_type')[
                ['length_meters', 'deadweight_tonnage', 'gross_tonnage']
            ].mean().round(2)
            
            return {
                'size_categories': size_distribution.to_dict(),
                'average_specs_by_type': size_metrics.to_dict(),
                'largest_vessels': self.df.nlargest(5, 'deadweight_tonnage')[
                    ['vessel_name', 'vessel_type', 'deadweight_tonnage']
                ].to_dict('records')
            }
        return {}
    
    def generate_dry_dock_schedule(self, days_ahead: int = 365) -> List[Dict[str, Any]]:
        """Generate predicted dry dock schedule based on patterns"""
        schedule = []
        
        for _, vessel_data in self.df.iterrows():
            # Simple prediction: if frequency > 0, predict next dry dock
            if vessel_data['dry_dock_frequency'] > 0:
                # Estimate next dry dock date (simplified)
                days_since_last = vessel_data['dry_dock_frequency'] * 0.8  # Assume 80% of frequency has passed
                days_until_next = vessel_data['dry_dock_frequency'] - days_since_last
                
                if days_until_next <= days_ahead:
                    predicted_date = datetime.now() + timedelta(days=int(days_until_next))
                    
                    schedule.append({
                        'vessel_name': vessel_data['vessel_name'],
                        'vessel_type': vessel_data['vessel_type'],
                        'predicted_date': predicted_date.strftime('%Y-%m-%d'),
                        'estimated_duration': random.randint(20, 40),  # Simplified
                        'priority': 'High' if days_until_next < 90 else 'Medium'
                    })
        
        return sorted(schedule, key=lambda x: x['predicted_date'])
    
    def get_vessel_recommendations(self) -> Dict[str, List[Dict]]:
        """Generate recommendations for fleet management"""
        recommendations = {
            'maintenance_urgent': [],
            'performance_issues': [],
            'efficiency_improvements': [],
            'age_concerns': []
        }
        
        # Maintenance urgent (high dry dock days)
        high_maintenance = self.df[self.df['total_dry_dock_days'] > self.df['total_dry_dock_days'].quantile(0.9)]
        for _, vessel in high_maintenance.iterrows():
            recommendations['maintenance_urgent'].append({
                'vessel_name': vessel['vessel_name'],
                'issue': f"High maintenance: {vessel['total_dry_dock_days']} dry dock days",
                'recommendation': 'Review maintenance strategy and consider replacement'
            })
        
        # Performance issues (low speed compared to max)
        if 'max_speed_knots' in self.df.columns:
            poor_performance = self.df[
                (self.df['average_speed_knots'] / self.df['max_speed_knots']) < 0.6
            ]
            for _, vessel in poor_performance.iterrows():
                recommendations['performance_issues'].append({
                    'vessel_name': vessel['vessel_name'],
                    'issue': f"Operating at {(vessel['average_speed_knots']/vessel['max_speed_knots']*100):.1f}% of max speed",
                    'recommendation': 'Investigate engine performance and hull condition'
                })
        
        # Age concerns (very old vessels)
        old_vessels = self.df[self.df['age_years'] > 25]
        for _, vessel in old_vessels.iterrows():
            recommendations['age_concerns'].append({
                'vessel_name': vessel['vessel_name'],
                'issue': f"Vessel age: {vessel['age_years']:.1f} years",
                'recommendation': 'Consider replacement or major refurbishment'
            })
        
        return recommendations
    
    def export_analytics_report(self, filename: str = None) -> str:
        """Export comprehensive analytics to JSON/Excel"""
        if filename is None:
            filename = f"vessel_analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'generation_date': datetime.now().isoformat(),
            'fleet_overview': self.get_fleet_overview(),
            'recommendations': self.get_vessel_recommendations(),
            'dry_dock_schedule': self.generate_dry_dock_schedule(),
            'summary': {
                'total_vessels': len(self.df),
                'operational_vessels': len(self.df[self.df['current_status'].isin(['at_sea', 'in_port'])]),
                'average_age': self.df['age_years'].mean().round(2),
                'vessels_in_dry_dock': len(self.df[self.df['currently_in_dry_dock'] == True])
            }
        }
        
        import json
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return filename


def create_analytics_dashboard_data(fleet: VesselFleet) -> Dict[str, Any]:
    """Create data structure for dashboard visualization"""
    analytics = VesselAnalytics(fleet)
    overview = analytics.get_fleet_overview()
    
    # Prepare data for various charts
    dashboard_data = {
        'fleet_overview': overview,
        'vessel_types_chart': {
            'labels': list(overview['vessel_types']['counts'].keys()),
            'values': list(overview['vessel_types']['counts'].values())
        },
        'age_distribution_chart': {
            'labels': list(overview['age_analysis']['age_categories'].keys()),
            'values': list(overview['age_analysis']['age_categories'].values())
        },
        'status_distribution_chart': {
            'labels': list(overview['status_distribution']['overall']['counts'].keys()),
            'values': list(overview['status_distribution']['overall']['counts'].values())
        },
        'geographic_distribution': overview['geographic_distribution'],
        'dry_dock_analysis': overview['dry_dock_analysis'],
        'recommendations': analytics.get_vessel_recommendations(),
        'vessels_dataframe': analytics.df.to_dict('records')  # For detailed tables
    }
    
    return dashboard_data


if __name__ == "__main__":
    # Example usage
    from generators.ais_data_generator import generate_sample_fleet
    
    # Generate sample fleet
    fleet = generate_sample_fleet(200)
    
    # Create analytics
    analytics = VesselAnalytics(fleet)
    
    # Get overview
    overview = analytics.get_fleet_overview()
    print("Fleet Overview:")
    print(f"Total vessels: {overview['total_vessels']}")
    print(f"Average age: {overview['age_analysis']['overall_stats']['mean_age']} years")
    print(f"Vessels in dry dock: {overview['dry_dock_analysis']['currently_in_dry_dock']['count']}")
    
    # Export report
    report_file = analytics.export_analytics_report()
    print(f"Report exported to: {report_file}")
