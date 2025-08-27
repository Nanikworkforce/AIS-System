"""
Comprehensive AIS Vessel Reporting System
Detailed analysis for marine vessels including dry dock analysis,
service areas, countries analysis, and age distribution
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict, Counter
import json
import random

from models.vessel import Vessel, VesselFleet, VesselType, VesselStatus, ServiceLine


class ComprehensiveVesselReports:
    """Advanced comprehensive reporting for marine vessel fleets"""
    
    def __init__(self, fleet: VesselFleet):
        """Initialize comprehensive reports with vessel fleet"""
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
    
    def generate_vessel_type_detailed_report(self) -> Dict[str, Any]:
        """
        Generate detailed vessel type analysis with subcategories and percentages
        Focuses on: Tankers, Bulkers, Container Ships, General Cargo
        """
        total_vessels = len(self.df)
        
        # Main vessel type distribution
        type_distribution = {}
        detailed_analysis = {}
        
        for vessel_type in VesselType:
            type_vessels = self.df[self.df['vessel_type'] == vessel_type.value]
            count = len(type_vessels)
            percentage = (count / total_vessels * 100) if total_vessels > 0 else 0
            
            type_distribution[vessel_type.value] = {
                'count': count,
                'percentage': round(percentage, 2),
                'total_fleet_percentage': round(percentage, 2)
            }
            
            # Detailed analysis for each type
            if count > 0:
                detailed_analysis[vessel_type.value] = {
                    'age_statistics': {
                        'average_age': round(type_vessels['age_years'].mean(), 2),
                        'median_age': round(type_vessels['age_years'].median(), 2),
                        'oldest_vessel': round(type_vessels['age_years'].max(), 2),
                        'newest_vessel': round(type_vessels['age_years'].min(), 2)
                    },
                    'size_statistics': self._get_size_stats_for_type(type_vessels),
                    'operational_status': self._get_status_breakdown(type_vessels),
                    'flag_state_distribution': self._get_top_countries(type_vessels, 'flag_state', 10),
                    'current_location_distribution': self._get_top_countries(type_vessels, 'current_country', 10),
                    'service_line_breakdown': self._get_service_line_breakdown(type_vessels),
                    'dry_dock_analysis': self._get_dry_dock_analysis_for_type(type_vessels),
                    'performance_metrics': self._get_performance_metrics_for_type(type_vessels)
                }
        
        return {
            'summary': {
                'total_vessels': total_vessels,
                'type_distribution': type_distribution,
                'analysis_date': datetime.now().isoformat()
            },
            'detailed_analysis_by_type': detailed_analysis,
            'fleet_composition_insights': self._generate_fleet_insights(type_distribution)
        }
    
    def generate_dry_dock_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive dry dock analysis including:
        - Time spent in dry docks by vessel type
        - Dry dock facilities analysis
        - Maintenance patterns and costs
        """
        dry_dock_vessels = self.df[self.df['currently_in_dry_dock'] == True]
        
        # Overall dry dock statistics
        total_dry_dock_days = self.df['total_dry_dock_days'].sum()
        average_days_per_vessel = self.df['total_dry_dock_days'].mean()
        
        # Dry dock analysis by vessel type
        type_analysis = {}
        for vessel_type in VesselType:
            type_vessels = self.df[self.df['vessel_type'] == vessel_type.value]
            if len(type_vessels) > 0:
                type_analysis[vessel_type.value] = {
                    'total_vessels': len(type_vessels),
                    'currently_in_dry_dock': len(type_vessels[type_vessels['currently_in_dry_dock'] == True]),
                    'percentage_in_dry_dock': round(
                        len(type_vessels[type_vessels['currently_in_dry_dock'] == True]) / len(type_vessels) * 100, 2
                    ),
                    'average_dry_dock_days': round(type_vessels['total_dry_dock_days'].mean(), 2),
                    'total_dry_dock_days': type_vessels['total_dry_dock_days'].sum(),
                    'max_dry_dock_days': type_vessels['total_dry_dock_days'].max(),
                    'vessels_with_high_maintenance': len(
                        type_vessels[type_vessels['total_dry_dock_days'] > type_vessels['total_dry_dock_days'].quantile(0.8)]
                    )
                }
        
        # Dry dock patterns by age
        age_groups = pd.cut(self.df['age_years'], 
                           bins=[0, 5, 10, 15, 20, 25, 100], 
                           labels=['0-5 years', '6-10 years', '11-15 years', '16-20 years', '21-25 years', '25+ years'])
        
        age_dry_dock_analysis = {}
        for age_group in age_groups.cat.categories:
            age_vessels = self.df[age_groups == age_group]
            if len(age_vessels) > 0:
                age_dry_dock_analysis[age_group] = {
                    'vessel_count': len(age_vessels),
                    'average_dry_dock_days': round(age_vessels['total_dry_dock_days'].mean(), 2),
                    'percentage_currently_in_dry_dock': round(
                        len(age_vessels[age_vessels['currently_in_dry_dock'] == True]) / len(age_vessels) * 100, 2
                    )
                }
        
        # Generate maintenance recommendations
        maintenance_insights = self._generate_maintenance_insights()
        
        return {
            'summary': {
                'total_fleet_dry_dock_days': int(total_dry_dock_days),
                'average_days_per_vessel': round(average_days_per_vessel, 2),
                'vessels_currently_in_dry_dock': len(dry_dock_vessels),
                'percentage_of_fleet_in_dry_dock': round(len(dry_dock_vessels) / len(self.df) * 100, 2),
                'analysis_date': datetime.now().isoformat()
            },
            'analysis_by_vessel_type': type_analysis,
            'analysis_by_age_group': age_dry_dock_analysis,
            'maintenance_patterns': {
                'high_maintenance_vessels': self._identify_high_maintenance_vessels(),
                'maintenance_efficiency_by_type': self._calculate_maintenance_efficiency(),
                'projected_dry_dock_schedule': self._project_dry_dock_schedule()
            },
            'maintenance_insights_and_recommendations': maintenance_insights
        }
    
    def generate_countries_and_service_areas_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive analysis of vessel countries and service areas
        """
        # Flag state analysis
        flag_state_analysis = self._analyze_flag_states()
        
        # Current location analysis
        current_location_analysis = self._analyze_current_locations()
        
        # Service area analysis
        service_area_analysis = self._analyze_service_areas()
        
        # Cross-analysis: vessel types by countries
        cross_analysis = self._cross_analyze_types_and_countries()
        
        return {
            'summary': {
                'total_countries_represented': len(self.df['flag_state'].unique()),
                'total_current_location_countries': len(self.df['current_country'].dropna().unique()),
                'most_common_flag_state': self.df['flag_state'].mode().iloc[0] if not self.df['flag_state'].empty else 'N/A',
                'analysis_date': datetime.now().isoformat()
            },
            'flag_state_analysis': flag_state_analysis,
            'current_location_analysis': current_location_analysis,
            'service_area_analysis': service_area_analysis,
            'cross_analysis': cross_analysis,
            'global_presence_insights': self._generate_global_presence_insights()
        }
    
    def generate_vessel_age_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate detailed vessel age analysis by type and country
        """
        # Overall age statistics
        overall_stats = {
            'fleet_average_age': round(self.df['age_years'].mean(), 2),
            'fleet_median_age': round(self.df['age_years'].median(), 2),
            'oldest_vessel_age': round(self.df['age_years'].max(), 2),
            'newest_vessel_age': round(self.df['age_years'].min(), 2),
            'age_standard_deviation': round(self.df['age_years'].std(), 2)
        }
        
        # Age distribution categories
        age_categories = pd.cut(self.df['age_years'], 
                               bins=[0, 5, 10, 15, 20, 25, 100], 
                               labels=['0-5 years', '6-10 years', '11-15 years', '16-20 years', '21-25 years', '25+ years'])
        
        age_distribution = {}
        total_vessels = len(self.df)
        
        for category in age_categories.cat.categories:
            count = (age_categories == category).sum()
            percentage = (count / total_vessels * 100) if total_vessels > 0 else 0
            age_distribution[category] = {
                'count': int(count),
                'percentage': round(percentage, 2)
            }
        
        # Age analysis by vessel type
        age_by_type = {}
        for vessel_type in VesselType:
            type_vessels = self.df[self.df['vessel_type'] == vessel_type.value]
            if len(type_vessels) > 0:
                age_by_type[vessel_type.value] = {
                    'average_age': round(type_vessels['age_years'].mean(), 2),
                    'median_age': round(type_vessels['age_years'].median(), 2),
                    'age_range': {
                        'min': round(type_vessels['age_years'].min(), 2),
                        'max': round(type_vessels['age_years'].max(), 2)
                    },
                    'age_distribution': self._get_age_distribution_for_type(type_vessels)
                }
        
        # Age analysis by country (top 10 flag states)
        top_countries = self.df['flag_state'].value_counts().head(10).index
        age_by_country = {}
        
        for country in top_countries:
            country_vessels = self.df[self.df['flag_state'] == country]
            age_by_country[country] = {
                'vessel_count': len(country_vessels),
                'average_age': round(country_vessels['age_years'].mean(), 2),
                'median_age': round(country_vessels['age_years'].median(), 2),
                'oldest_vessel': round(country_vessels['age_years'].max(), 2),
                'newest_vessel': round(country_vessels['age_years'].min(), 2)
            }
        
        # Fleet renewal analysis
        fleet_renewal = self._analyze_fleet_renewal_needs()
        
        return {
            'summary': overall_stats,
            'age_distribution': age_distribution,
            'analysis_by_vessel_type': age_by_type,
            'analysis_by_country': age_by_country,
            'fleet_renewal_analysis': fleet_renewal,
            'aging_fleet_insights': self._generate_aging_fleet_insights(),
            'analysis_date': datetime.now().isoformat()
        }
    
    def generate_master_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate the master comprehensive report combining all analyses
        """
        return {
            'executive_summary': self._generate_executive_summary(),
            'vessel_type_analysis': self.generate_vessel_type_detailed_report(),
            'dry_dock_comprehensive_analysis': self.generate_dry_dock_comprehensive_report(),
            'countries_and_service_areas': self.generate_countries_and_service_areas_report(),
            'vessel_age_analysis': self.generate_vessel_age_comprehensive_report(),
            'performance_and_efficiency': self._generate_performance_report(),
            'fleet_management_recommendations': self._generate_comprehensive_recommendations(),
            'report_metadata': {
                'generation_date': datetime.now().isoformat(),
                'total_vessels_analyzed': len(self.df),
                'analysis_scope': 'Global Marine Fleet',
                'report_version': '1.0'
            }
        }
    
    # Helper methods
    def _get_size_stats_for_type(self, type_vessels: pd.DataFrame) -> Dict[str, Any]:
        """Get size statistics for vessel type"""
        stats = {}
        if 'deadweight_tonnage' in type_vessels.columns:
            stats['average_dwt'] = round(type_vessels['deadweight_tonnage'].mean(), 2)
            stats['median_dwt'] = round(type_vessels['deadweight_tonnage'].median(), 2)
            stats['largest_vessel_dwt'] = round(type_vessels['deadweight_tonnage'].max(), 2)
        
        if 'length_meters' in type_vessels.columns:
            stats['average_length'] = round(type_vessels['length_meters'].mean(), 2)
            stats['longest_vessel'] = round(type_vessels['length_meters'].max(), 2)
        
        if 'size_category' in type_vessels.columns:
            stats['size_distribution'] = type_vessels['size_category'].value_counts().to_dict()
        
        return stats
    
    def _get_status_breakdown(self, vessels: pd.DataFrame) -> Dict[str, Any]:
        """Get operational status breakdown for vessels"""
        status_counts = vessels['current_status'].value_counts()
        total = len(vessels)
        
        return {
            status: {
                'count': int(count),
                'percentage': round(count / total * 100, 2)
            }
            for status, count in status_counts.items()
        }
    
    def _get_top_countries(self, vessels: pd.DataFrame, column: str, limit: int) -> Dict[str, int]:
        """Get top countries for specified column"""
        return vessels[column].value_counts().head(limit).to_dict()
    
    def _get_service_line_breakdown(self, vessels: pd.DataFrame) -> Dict[str, Any]:
        """Get service line breakdown for vessels"""
        service_counts = vessels['service_line'].value_counts()
        total = len(vessels)
        
        return {
            service: {
                'count': int(count),
                'percentage': round(count / total * 100, 2)
            }
            for service, count in service_counts.items()
        }
    
    def _get_dry_dock_analysis_for_type(self, vessels: pd.DataFrame) -> Dict[str, Any]:
        """Get dry dock analysis for specific vessel type"""
        return {
            'currently_in_dry_dock': int((vessels['currently_in_dry_dock'] == True).sum()),
            'average_dry_dock_days': round(vessels['total_dry_dock_days'].mean(), 2),
            'total_dry_dock_days': int(vessels['total_dry_dock_days'].sum()),
            'high_maintenance_vessels': int((vessels['total_dry_dock_days'] > vessels['total_dry_dock_days'].quantile(0.8)).sum())
        }
    
    def _get_performance_metrics_for_type(self, vessels: pd.DataFrame) -> Dict[str, Any]:
        """Get performance metrics for specific vessel type"""
        metrics = {}
        
        if 'average_speed_knots' in vessels.columns:
            metrics['average_speed'] = round(vessels['average_speed_knots'].mean(), 2)
        
        if 'fuel_efficiency' in vessels.columns:
            metrics['average_fuel_efficiency'] = round(vessels['fuel_efficiency'].mean(), 3)
        
        if 'total_voyages' in vessels.columns and 'age_years' in vessels.columns:
            metrics['average_voyages_per_year'] = round((vessels['total_voyages'] / vessels['age_years']).mean(), 2)
        
        return metrics
    
    def _generate_fleet_insights(self, type_distribution: Dict[str, Any]) -> List[str]:
        """Generate insights about fleet composition"""
        insights = []
        
        # Find dominant vessel type
        max_type = max(type_distribution.items(), key=lambda x: x[1]['percentage'])
        insights.append(f"Fleet is dominated by {max_type[0].replace('_', ' ').title()} vessels ({max_type[1]['percentage']:.1f}%)")
        
        # Check for balanced fleet
        percentages = [v['percentage'] for v in type_distribution.values()]
        if max(percentages) - min(percentages) < 15:
            insights.append("Fleet composition is well-balanced across vessel types")
        
        # Check for specialization
        if max_type[1]['percentage'] > 50:
            insights.append(f"Fleet is highly specialized in {max_type[0].replace('_', ' ').title()} operations")
        
        return insights
    
    def _generate_maintenance_insights(self) -> List[str]:
        """Generate maintenance insights and recommendations"""
        insights = []
        
        avg_dry_dock_days = self.df['total_dry_dock_days'].mean()
        high_maintenance_threshold = self.df['total_dry_dock_days'].quantile(0.8)
        
        insights.append(f"Fleet average dry dock time: {avg_dry_dock_days:.1f} days per vessel")
        
        high_maintenance_count = (self.df['total_dry_dock_days'] > high_maintenance_threshold).sum()
        insights.append(f"{high_maintenance_count} vessels require high maintenance attention")
        
        # Age-based insights
        old_vessels = self.df[self.df['age_years'] > 20]
        if len(old_vessels) > 0:
            insights.append(f"{len(old_vessels)} vessels over 20 years old may need increased maintenance")
        
        return insights
    
    def _identify_high_maintenance_vessels(self) -> Dict[str, Any]:
        """Identify vessels requiring high maintenance"""
        threshold = self.df['total_dry_dock_days'].quantile(0.9)
        high_maintenance = self.df[self.df['total_dry_dock_days'] > threshold]
        
        return {
            'threshold_days': round(threshold, 2),
            'vessel_count': len(high_maintenance),
            'percentage_of_fleet': round(len(high_maintenance) / len(self.df) * 100, 2),
            'vessel_types_affected': high_maintenance['vessel_type'].value_counts().to_dict()
        }
    
    def _calculate_maintenance_efficiency(self) -> Dict[str, float]:
        """Calculate maintenance efficiency by vessel type"""
        efficiency = {}
        
        for vessel_type in VesselType:
            type_vessels = self.df[self.df['vessel_type'] == vessel_type.value]
            if len(type_vessels) > 0:
                # Lower dry dock days per year = higher efficiency
                avg_annual_dry_dock = (type_vessels['total_dry_dock_days'] / type_vessels['age_years']).mean()
                efficiency[vessel_type.value] = round(avg_annual_dry_dock, 2)
        
        return efficiency
    
    def _project_dry_dock_schedule(self) -> List[Dict[str, Any]]:
        """Project upcoming dry dock requirements"""
        schedule = []
        
        # Simple projection based on average dry dock frequency
        for _, vessel in self.df.iterrows():
            if vessel['dry_dock_frequency'] > 0:
                # Estimate next dry dock (simplified)
                days_until_next = vessel['dry_dock_frequency'] * 0.5  # Rough estimate
                
                if days_until_next <= 365:  # Within next year
                    schedule.append({
                        'vessel_name': vessel.get('vessel_name', 'Unknown'),
                        'vessel_type': vessel['vessel_type'],
                        'estimated_days_until_dry_dock': int(days_until_next),
                        'priority': 'High' if days_until_next < 90 else 'Medium'
                    })
        
        return sorted(schedule, key=lambda x: x['estimated_days_until_dry_dock'])[:20]
    
    def _analyze_flag_states(self) -> Dict[str, Any]:
        """Analyze flag state distribution"""
        flag_counts = self.df['flag_state'].value_counts()
        total_vessels = len(self.df)
        
        return {
            'total_flag_states': len(flag_counts),
            'top_10_flag_states': {
                country: {
                    'vessel_count': int(count),
                    'percentage': round(count / total_vessels * 100, 2)
                }
                for country, count in flag_counts.head(10).items()
            },
            'flag_state_concentration': {
                'top_5_percentage': round(flag_counts.head(5).sum() / total_vessels * 100, 2),
                'top_10_percentage': round(flag_counts.head(10).sum() / total_vessels * 100, 2)
            }
        }
    
    def _analyze_current_locations(self) -> Dict[str, Any]:
        """Analyze current location distribution"""
        location_counts = self.df['current_country'].value_counts()
        total_with_location = len(self.df.dropna(subset=['current_country']))
        
        return {
            'total_location_countries': len(location_counts),
            'vessels_with_known_location': total_with_location,
            'top_10_current_locations': {
                country: {
                    'vessel_count': int(count),
                    'percentage': round(count / total_with_location * 100, 2)
                }
                for country, count in location_counts.head(10).items()
            }
        }
    
    def _analyze_service_areas(self) -> Dict[str, Any]:
        """Analyze service areas and operational regions"""
        service_analysis = {}
        
        for service_line in ServiceLine:
            service_vessels = self.df[self.df['service_line'] == service_line.value]
            if len(service_vessels) > 0:
                service_analysis[service_line.value] = {
                    'vessel_count': len(service_vessels),
                    'primary_flag_states': service_vessels['flag_state'].value_counts().head(5).to_dict(),
                    'current_operational_areas': service_vessels['current_country'].value_counts().head(5).to_dict(),
                    'average_vessel_age': round(service_vessels['age_years'].mean(), 2)
                }
        
        return service_analysis
    
    def _cross_analyze_types_and_countries(self) -> Dict[str, Any]:
        """Cross-analyze vessel types and countries"""
        # Vessel types by flag state
        type_country_matrix = pd.crosstab(self.df['vessel_type'], self.df['flag_state'])
        
        # Find specializations
        specializations = {}
        for country in type_country_matrix.columns:
            country_vessels = type_country_matrix[country]
            if country_vessels.sum() > 0:
                dominant_type = country_vessels.idxmax()
                percentage = (country_vessels.max() / country_vessels.sum() * 100)
                
                if percentage > 40:  # If more than 40% of country's fleet is one type
                    specializations[country] = {
                        'dominant_type': dominant_type,
                        'percentage': round(percentage, 2),
                        'vessel_count': int(country_vessels.max())
                    }
        
        return {
            'country_specializations': specializations,
            'most_diverse_flags': self._find_most_diverse_flags(type_country_matrix)
        }
    
    def _find_most_diverse_flags(self, matrix: pd.DataFrame) -> Dict[str, float]:
        """Find most diverse flag states in terms of vessel types"""
        diversity_scores = {}
        
        for country in matrix.columns:
            country_vessels = matrix[country]
            if country_vessels.sum() >= 10:  # Only consider countries with 10+ vessels
                # Calculate diversity using Simpson's diversity index
                proportions = country_vessels / country_vessels.sum()
                diversity = 1 - (proportions ** 2).sum()
                diversity_scores[country] = round(diversity, 3)
        
        # Return top 5 most diverse
        return dict(sorted(diversity_scores.items(), key=lambda x: x[1], reverse=True)[:5])
    
    def _generate_global_presence_insights(self) -> List[str]:
        """Generate insights about global presence"""
        insights = []
        
        flag_state_count = len(self.df['flag_state'].unique())
        location_count = len(self.df['current_country'].dropna().unique())
        
        insights.append(f"Fleet operates under {flag_state_count} different flag states")
        insights.append(f"Vessels currently present in {location_count} countries")
        
        # Check for global vs regional operations
        if flag_state_count > 20:
            insights.append("Fleet demonstrates truly global operations")
        elif flag_state_count > 10:
            insights.append("Fleet has strong international presence")
        else:
            insights.append("Fleet operations are more regionally focused")
        
        return insights
    
    def _get_age_distribution_for_type(self, vessels: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Get age distribution for specific vessel type"""
        age_categories = pd.cut(vessels['age_years'], 
                               bins=[0, 5, 10, 15, 20, 25, 100], 
                               labels=['0-5 years', '6-10 years', '11-15 years', '16-20 years', '21-25 years', '25+ years'])
        
        distribution = {}
        total = len(vessels)
        
        for category in age_categories.cat.categories:
            count = (age_categories == category).sum()
            distribution[category] = {
                'count': int(count),
                'percentage': round(count / total * 100, 2) if total > 0 else 0
            }
        
        return distribution
    
    def _analyze_fleet_renewal_needs(self) -> Dict[str, Any]:
        """Analyze fleet renewal needs"""
        old_vessels = self.df[self.df['age_years'] > 20]
        very_old_vessels = self.df[self.df['age_years'] > 25]
        
        return {
            'vessels_over_20_years': {
                'count': len(old_vessels),
                'percentage': round(len(old_vessels) / len(self.df) * 100, 2),
                'by_type': old_vessels['vessel_type'].value_counts().to_dict()
            },
            'vessels_over_25_years': {
                'count': len(very_old_vessels),
                'percentage': round(len(very_old_vessels) / len(self.df) * 100, 2),
                'by_type': very_old_vessels['vessel_type'].value_counts().to_dict()
            },
            'renewal_priority_score': self._calculate_renewal_priority_score()
        }
    
    def _calculate_renewal_priority_score(self) -> float:
        """Calculate fleet renewal priority score (0-100)"""
        # Higher score means more urgent renewal needed
        old_vessel_weight = (self.df['age_years'] > 20).sum() / len(self.df) * 40
        very_old_weight = (self.df['age_years'] > 25).sum() / len(self.df) * 30
        avg_age_weight = min(self.df['age_years'].mean() / 25 * 30, 30)
        
        return round(old_vessel_weight + very_old_weight + avg_age_weight, 2)
    
    def _generate_aging_fleet_insights(self) -> List[str]:
        """Generate insights about fleet aging"""
        insights = []
        
        avg_age = self.df['age_years'].mean()
        old_vessels = len(self.df[self.df['age_years'] > 20])
        
        if avg_age > 15:
            insights.append(f"Fleet is aging with average age of {avg_age:.1f} years")
        
        if old_vessels > len(self.df) * 0.3:
            insights.append(f"{old_vessels} vessels over 20 years old may need replacement planning")
        
        # Type-specific aging analysis
        for vessel_type in VesselType:
            type_vessels = self.df[self.df['vessel_type'] == vessel_type.value]
            if len(type_vessels) > 0:
                type_avg_age = type_vessels['age_years'].mean()
                if type_avg_age > 18:
                    insights.append(f"{vessel_type.value.replace('_', ' ').title()} fleet shows signs of aging (avg: {type_avg_age:.1f} years)")
        
        return insights
    
    def _generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary of the fleet"""
        total_vessels = len(self.df)
        avg_age = self.df['age_years'].mean()
        vessels_in_dry_dock = (self.df['currently_in_dry_dock'] == True).sum()
        
        # Key metrics
        key_metrics = {
            'total_fleet_size': total_vessels,
            'average_fleet_age': round(avg_age, 1),
            'vessels_currently_in_dry_dock': int(vessels_in_dry_dock),
            'dry_dock_percentage': round(vessels_in_dry_dock / total_vessels * 100, 2),
            'operational_vessels': int((self.df['current_status'].isin(['at_sea', 'in_port'])).sum()),
            'flag_state_diversity': len(self.df['flag_state'].unique()),
            'global_presence': len(self.df['current_country'].dropna().unique())
        }
        
        # Fleet composition
        fleet_composition = {}
        for vessel_type in VesselType:
            count = (self.df['vessel_type'] == vessel_type.value).sum()
            fleet_composition[vessel_type.value] = {
                'count': int(count),
                'percentage': round(count / total_vessels * 100, 2)
            }
        
        # Key insights
        insights = []
        
        # Dominant vessel type
        dominant_type = max(fleet_composition.items(), key=lambda x: x[1]['percentage'])
        insights.append(f"Fleet is primarily composed of {dominant_type[0].replace('_', ' ').title()} vessels ({dominant_type[1]['percentage']:.1f}%)")
        
        # Age insight
        if avg_age > 15:
            insights.append(f"Fleet shows moderate aging with average age of {avg_age:.1f} years")
        else:
            insights.append(f"Fleet is relatively young with average age of {avg_age:.1f} years")
        
        # Operational efficiency
        operational_pct = key_metrics['operational_vessels'] / total_vessels * 100
        insights.append(f"Fleet operates at {operational_pct:.1f}% capacity with {key_metrics['operational_vessels']} vessels active")
        
        # Global presence
        if key_metrics['global_presence'] > 20:
            insights.append(f"Strong global presence with operations in {key_metrics['global_presence']} countries")
        
        return {
            'key_metrics': key_metrics,
            'fleet_composition': fleet_composition,
            'key_insights': insights,
            'summary_date': datetime.now().isoformat()
        }
    
    def _generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
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
    
    def _generate_comprehensive_recommendations(self) -> Dict[str, Any]:
        """Generate comprehensive fleet management recommendations"""
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
        
        # Age concerns (very old vessels)
        old_vessels = self.df[self.df['age_years'] > 25]
        for _, vessel in old_vessels.iterrows():
            recommendations['age_concerns'].append({
                'vessel_name': vessel['vessel_name'],
                'issue': f"Vessel age: {vessel['age_years']:.1f} years",
                'recommendation': 'Consider replacement or major refurbishment'
            })
        
        # Add additional recommendations based on comprehensive analysis
        additional_recommendations = {
            'fleet_optimization': [],
            'geographic_expansion': [],
            'fleet_renewal': [],
            'operational_efficiency': []
        }
        
        # Fleet renewal recommendations
        old_vessels_pct = len(self.df[self.df['age_years'] > 20]) / len(self.df) * 100
        if old_vessels_pct > 30:
            additional_recommendations['fleet_renewal'].append({
                'priority': 'High',
                'recommendation': f'Consider fleet renewal program as {old_vessels_pct:.1f}% of vessels are over 20 years old',
                'estimated_impact': 'Reduced maintenance costs and improved efficiency'
            })
        
        # Geographic optimization
        flag_concentration = self.df['flag_state'].value_counts()
        if flag_concentration.iloc[0] / len(self.df) > 0.6:
            additional_recommendations['geographic_expansion'].append({
                'priority': 'Medium',
                'recommendation': 'Consider diversifying flag state registration for operational flexibility',
                'estimated_impact': 'Improved regulatory compliance and operational options'
            })
        
        recommendations.update(additional_recommendations)
        return recommendations
    
    def export_comprehensive_report(self, filename: str = None) -> str:
        """Export comprehensive report to JSON file"""
        if filename is None:
            filename = f"comprehensive_vessel_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.generate_master_comprehensive_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return filename


if __name__ == "__main__":
    # Example usage
    from generators.ais_data_generator import generate_sample_fleet
    
    # Generate sample fleet
    fleet = generate_sample_fleet(1000)
    
    # Create comprehensive reports
    reports = ComprehensiveVesselReports(fleet)
    
    # Generate and export master report
    report_file = reports.export_comprehensive_report()
    print(f"Comprehensive report exported to: {report_file}")
    
    # Display key insights
    master_report = reports.generate_master_comprehensive_report()
    exec_summary = master_report['executive_summary']
    
    print(f"\nExecutive Summary:")
    print(f"Total Fleet Size: {exec_summary['key_metrics']['total_fleet_size']:,} vessels")
    print(f"Average Age: {exec_summary['key_metrics']['average_fleet_age']} years")
    print(f"Global Presence: {exec_summary['key_metrics']['global_presence']} countries")
    
    print(f"\nKey Insights:")
    for insight in exec_summary['key_insights']:
        print(f"• {insight}")
