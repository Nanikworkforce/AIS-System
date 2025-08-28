"""
AIS Data Generator for Marine Vessels
Generates realistic vessel data with dry dock history, locations, and specifications
Now integrated with CSV data loading capabilities
"""

import random
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from faker import Faker
from geopy.geocoders import Nominatim
import numpy as np

from models.vessel import (
    Vessel, VesselType, VesselStatus, ServiceLine, Location, 
    DryDockRecord, VesselSpecifications, VesselFleet
)
from data_loaders.csv_loader import AISCSVLoader


class AISDataGenerator:
    """Generates realistic AIS vessel data"""
    
    def __init__(self, seed: int = 42):
        """Initialize generator with optional seed for reproducibility"""
        random.seed(seed)
        np.random.seed(seed)
        self.fake = Faker()
        Faker.seed(seed)
        
        # Major shipping countries
        self.shipping_countries = [
            'Panama', 'Liberia', 'Marshall Islands', 'Hong Kong', 'Singapore',
            'Malta', 'Bahamas', 'Cyprus', 'China', 'Greece', 'Japan', 'Norway',
            'United Kingdom', 'Germany', 'Italy', 'South Korea', 'Netherlands',
            'Denmark', 'United States', 'France', 'Russia', 'Turkey'
        ]
        
        # Major ports with coordinates
        self.major_ports = {
            'Shanghai': {'lat': 31.2304, 'lon': 121.4737, 'country': 'China'},
            'Singapore': {'lat': 1.2966, 'lon': 103.7764, 'country': 'Singapore'},
            'Rotterdam': {'lat': 51.9225, 'lon': 4.4792, 'country': 'Netherlands'},
            'Antwerp': {'lat': 51.2993, 'lon': 4.9407, 'country': 'Belgium'},
            'Hamburg': {'lat': 53.5488, 'lon': 9.9872, 'country': 'Germany'},
            'Los Angeles': {'lat': 33.7701, 'lon': -118.1937, 'country': 'United States'},
            'Long Beach': {'lat': 33.7564, 'lon': -118.1318, 'country': 'United States'},
            'Dubai': {'lat': 25.2769, 'lon': 55.2962, 'country': 'UAE'},
            'Hong Kong': {'lat': 22.3526, 'lon': 114.1417, 'country': 'Hong Kong'},
            'Busan': {'lat': 35.0951, 'lon': 129.0756, 'country': 'South Korea'},
            'Qingdao': {'lat': 36.0986, 'lon': 120.3719, 'country': 'China'},
            'Guangzhou': {'lat': 23.0965, 'lon': 113.3123, 'country': 'China'},
            'Tokyo': {'lat': 35.6528, 'lon': 139.7594, 'country': 'Japan'},
            'Kaohsiung': {'lat': 22.5431, 'lon': 120.2975, 'country': 'Taiwan'},
            'Jebel Ali': {'lat': 25.0269, 'lon': 55.1136, 'country': 'UAE'},
            'Piraeus': {'lat': 37.9364, 'lon': 23.6503, 'country': 'Greece'},
            'Valencia': {'lat': 39.4699, 'lon': -0.3763, 'country': 'Spain'},
            'Algeciras': {'lat': 36.1408, 'lon': -5.4526, 'country': 'Spain'},
            'Felixstowe': {'lat': 51.9542, 'lon': 1.3464, 'country': 'United Kingdom'},
            'Bremen': {'lat': 53.0793, 'lon': 8.8017, 'country': 'Germany'}
        }
        
        # Dry dock facilities
        self.dry_dock_facilities = {
            'Sembcorp Marine': {'lat': 1.2673, 'lon': 103.8014, 'country': 'Singapore'},
            'Keppel FELS': {'lat': 1.2673, 'lon': 103.8014, 'country': 'Singapore'},
            'DSME Shipyard': {'lat': 35.0951, 'lon': 129.0756, 'country': 'South Korea'},
            'Hyundai Heavy': {'lat': 35.5384, 'lon': 129.3114, 'country': 'South Korea'},
            'COSCO Dalian': {'lat': 38.9140, 'lon': 121.6147, 'country': 'China'},
            'Drydocks World Dubai': {'lat': 25.2769, 'lon': 55.2962, 'country': 'UAE'},
            'Newport News': {'lat': 36.9735, 'lon': -76.4951, 'country': 'United States'},
            'Fincantieri Trieste': {'lat': 45.6495, 'lon': 13.7768, 'country': 'Italy'},
            'Navantia Ferrol': {'lat': 43.4823, 'lon': -8.2375, 'country': 'Spain'},
            'Damen Shiprepair': {'lat': 51.9225, 'lon': 4.4792, 'country': 'Netherlands'}
        }
        
        # Service lines by vessel type
        self.service_lines_by_type = {
            VesselType.TANKER: [
                ServiceLine.CRUDE_OIL_TRANSPORT,
                ServiceLine.PRODUCT_TANKER,
                ServiceLine.CHEMICAL_TRANSPORT
            ],
            VesselType.BULKER: [
                ServiceLine.DRY_BULK_CARGO
            ],
            VesselType.CONTAINER: [
                ServiceLine.CONTAINER_SHIPPING
            ],
            VesselType.GENERAL_CARGO: [
                ServiceLine.GENERAL_CARGO,
                ServiceLine.RO_RO_FERRY,
                ServiceLine.OFFSHORE_SUPPLY
            ]
        }
        
        # Company names by vessel type
        self.shipping_companies = {
            VesselType.CONTAINER: [
                'Maersk Line', 'MSC', 'CMA CGM', 'COSCO Shipping', 'Hapag-Lloyd',
                'ONE (Ocean Network Express)', 'Evergreen Line', 'Yang Ming',
                'PIL Pacific International Lines', 'Zim'
            ],
            VesselType.TANKER: [
                'Euronav', 'Frontline', 'International Seaways', 'Teekay Corporation',
                'Stena Bulk', 'Torm', 'Scorpio Tankers', 'Hafnia', 'Nordic American Tankers',
                'DHT Holdings'
            ],
            VesselType.BULKER: [
                'Diana Shipping', 'DryShips', 'Golden Ocean Group', 'Genco Shipping',
                'Eagle Bulk Shipping', 'Star Bulk Carriers', 'Seanergy Maritime',
                'Safe Bulkers', 'Pangaea Logistics', 'Jinhui Shipping'
            ],
            VesselType.GENERAL_CARGO: [
                'Rickmers Group', 'Zeaborn Ship Management', 'BBC Chartering',
                'Beluga Shipping', 'Intermarine', 'Jumbo Shipping', 'SAL Heavy Lift',
                'BigLift Shipping', 'Spliethoff', 'Wagenborg Shipping'
            ]
        }
    
    def generate_vessel_name(self, vessel_type: VesselType) -> str:
        """Generate realistic vessel name based on type"""
        prefixes = {
            VesselType.TANKER: ['MT', 'MV', 'M/T'],
            VesselType.BULKER: ['MV', 'M/V', 'MS'],
            VesselType.CONTAINER: ['MV', 'M/V', 'MSC', 'COSCO'],
            VesselType.GENERAL_CARGO: ['MV', 'M/V', 'MS']
        }
        
        # Generate name components
        prefix = random.choice(prefixes[vessel_type])
        
        # Use mix of real-sounding names and place names
        name_options = [
            self.fake.first_name(),
            self.fake.last_name(),
            self.fake.city().replace(' ', ''),
            f"{self.fake.color_name()} {random.choice(['Star', 'Ocean', 'Wave', 'Wind', 'Dawn'])}"
        ]
        
        base_name = random.choice(name_options)
        return f"{prefix} {base_name}"
    
    def generate_specifications(self, vessel_type: VesselType) -> VesselSpecifications:
        """Generate realistic vessel specifications based on type"""
        specs_ranges = {
            VesselType.TANKER: {
                'length': (150, 400), 'width': (25, 70), 'gt': (50000, 500000),
                'dwt': (80000, 320000), 'speed': (12, 16), 'power': (15000, 35000),
                'fuel': (3000, 8000), 'cargo': (100000, 300000)
            },
            VesselType.BULKER: {
                'length': (180, 350), 'width': (30, 65), 'gt': (40000, 250000),
                'dwt': (75000, 400000), 'speed': (13, 15), 'power': (12000, 25000),
                'fuel': (2500, 6000), 'cargo': (80000, 380000)
            },
            VesselType.CONTAINER: {
                'length': (200, 400), 'width': (32, 60), 'gt': (80000, 230000),
                'dwt': (100000, 220000), 'speed': (18, 25), 'power': (20000, 80000),
                'fuel': (4000, 12000), 'cargo': (8000, 24000)  # TEU
            },
            VesselType.GENERAL_CARGO: {
                'length': (100, 200), 'width': (15, 30), 'gt': (5000, 50000),
                'dwt': (8000, 70000), 'speed': (12, 18), 'power': (3000, 15000),
                'fuel': (500, 3000), 'cargo': (10000, 60000)
            }
        }
        
        ranges = specs_ranges[vessel_type]
        
        return VesselSpecifications(
            length_meters=round(random.uniform(*ranges['length']), 1),
            width_meters=round(random.uniform(*ranges['width']), 1),
            gross_tonnage=round(random.uniform(*ranges['gt'])),
            deadweight_tonnage=round(random.uniform(*ranges['dwt'])),
            max_speed_knots=round(random.uniform(*ranges['speed']), 1),
            engine_power_hp=round(random.uniform(*ranges['power'])),
            fuel_capacity_tons=round(random.uniform(*ranges['fuel'])),
            cargo_capacity=round(random.uniform(*ranges['cargo']))
        )
    
    def generate_location(self, port_name: str = None) -> Location:
        """Generate location, optionally at specific port"""
        if port_name and port_name in self.major_ports:
            port_data = self.major_ports[port_name]
            return Location(
                latitude=port_data['lat'],
                longitude=port_data['lon'],
                port_name=port_name,
                country=port_data['country']
            )
        elif port_name is None:
            # Random port
            port_name = random.choice(list(self.major_ports.keys()))
            return self.generate_location(port_name)
        else:
            # Random ocean location
            return Location(
                latitude=random.uniform(-60, 70),
                longitude=random.uniform(-180, 180)
            )
    
    def generate_dry_dock_history(self, vessel_age_years: float, vessel_type: VesselType) -> List[DryDockRecord]:
        """Generate realistic dry dock maintenance history"""
        dry_dock_records = []
        
        # Typical dry dock frequency: every 2.5-5 years depending on vessel type
        frequency_ranges = {
            VesselType.TANKER: (2.5, 4.0),
            VesselType.BULKER: (3.0, 5.0),
            VesselType.CONTAINER: (2.0, 3.5),
            VesselType.GENERAL_CARGO: (3.0, 5.0)
        }
        
        min_freq, max_freq = frequency_ranges[vessel_type]
        avg_frequency = random.uniform(min_freq, max_freq)
        
        # Calculate number of dry dock visits
        expected_visits = int(vessel_age_years / avg_frequency)
        actual_visits = random.randint(max(0, expected_visits - 1), expected_visits + 1)
        
        # Generate historical dry dock records
        for i in range(actual_visits):
            # Calculate timing
            visit_age = vessel_age_years * (i + 1) / (actual_visits + 1)
            start_date = datetime.now() - timedelta(days=int((vessel_age_years - visit_age) * 365.25))
            
            # Duration: typically 15-45 days
            duration_days = random.randint(15, 45)
            end_date = start_date + timedelta(days=duration_days)
            
            # Location: random dry dock facility
            facility_name = random.choice(list(self.dry_dock_facilities.keys()))
            facility_data = self.dry_dock_facilities[facility_name]
            location = Location(
                latitude=facility_data['lat'],
                longitude=facility_data['lon'],
                port_name=facility_name,
                country=facility_data['country']
            )
            
            # Purpose
            purposes = [
                'Annual Survey and Maintenance',
                'Hull Cleaning and Painting',
                'Engine Overhaul',
                'Safety Equipment Inspection',
                'Classification Society Survey',
                'Propeller Maintenance',
                'Tank Inspection and Repair',
                'Electronics Upgrade'
            ]
            purpose = random.choice(purposes)
            
            # Cost estimate
            cost_estimate = random.uniform(500000, 2500000)  # USD
            
            record = DryDockRecord(
                start_date=start_date,
                end_date=end_date,
                location=location,
                purpose=purpose,
                cost_estimate=cost_estimate,
                completed=True
            )
            
            dry_dock_records.append(record)
        
        # Possibly add current dry dock
        if random.random() < 0.05:  # 5% chance of being in dry dock now
            facility_name = random.choice(list(self.dry_dock_facilities.keys()))
            facility_data = self.dry_dock_facilities[facility_name]
            location = Location(
                latitude=facility_data['lat'],
                longitude=facility_data['lon'],
                port_name=facility_name,
                country=facility_data['country']
            )
            
            current_record = DryDockRecord(
                start_date=datetime.now() - timedelta(days=random.randint(1, 20)),
                end_date=None,
                location=location,
                purpose='Scheduled Maintenance',
                completed=False
            )
            dry_dock_records.append(current_record)
        
        return dry_dock_records
    
    def generate_vessel(self, vessel_type: VesselType = None) -> Vessel:
        """Generate a single realistic vessel"""
        if vessel_type is None:
            vessel_type = random.choice(list(VesselType))
        
        # Basic info
        vessel_name = self.generate_vessel_name(vessel_type)
        call_sign = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
        flag_state = random.choice(self.shipping_countries)
        
        # Build date (age between 1-30 years)
        age_years = random.uniform(1, 30)
        build_date = datetime.now() - timedelta(days=int(age_years * 365.25))
        
        # Company info
        owner_company = random.choice(self.shipping_companies[vessel_type])
        operator_company = owner_company if random.random() < 0.7 else random.choice(self.shipping_companies[vessel_type])
        
        # Service line
        service_line = random.choice(self.service_lines_by_type[vessel_type])
        
        # Current location and status
        if random.random() < 0.7:  # 70% at sea or in port
            if random.random() < 0.6:  # 60% of those at sea
                current_location = self.generate_location()  # Random ocean
                current_status = VesselStatus.AT_SEA
            else:  # 40% in port
                port_name = random.choice(list(self.major_ports.keys()))
                current_location = self.generate_location(port_name)
                current_status = VesselStatus.IN_PORT
        else:  # 30% other statuses
            current_status = random.choice([VesselStatus.ANCHORED, VesselStatus.UNDER_REPAIR])
            current_location = self.generate_location(random.choice(list(self.major_ports.keys())))
        
        # Specifications
        specifications = self.generate_specifications(vessel_type)
        
        # Create vessel
        vessel = Vessel(
            vessel_name=vessel_name,
            call_sign=call_sign,
            vessel_type=vessel_type,
            service_line=service_line,
            flag_state=flag_state,
            home_port=random.choice(list(self.major_ports.keys())),
            owner_company=owner_company,
            operator_company=operator_company,
            build_date=build_date,
            specifications=specifications,
            current_status=current_status,
            current_location=current_location
        )
        
        # Generate dry dock history
        dry_dock_history = self.generate_dry_dock_history(age_years, vessel_type)
        vessel.dry_dock_history = dry_dock_history
        
        # Update status if currently in dry dock
        current_dry_dock = vessel.current_dry_dock
        if current_dry_dock:
            vessel.current_status = VesselStatus.DRY_DOCK
            vessel.current_location = current_dry_dock.location
        
        # Generate performance metrics
        vessel.total_voyages = random.randint(int(age_years * 10), int(age_years * 25))
        vessel.total_distance_nm = random.uniform(age_years * 50000, age_years * 150000)
        vessel.average_speed_knots = random.uniform(
            specifications.max_speed_knots * 0.6,
            specifications.max_speed_knots * 0.9
        )
        vessel.fuel_efficiency = random.uniform(0.1, 0.3)
        
        return vessel
    
    def generate_fleet(self, total_vessels: int = 1000, 
                      type_distribution: dict = None) -> VesselFleet:
        """
        Generate a complete vessel fleet
        
        Args:
            total_vessels: Total number of vessels to generate
            type_distribution: Dict with vessel type percentages (optional)
        """
        if type_distribution is None:
            # Default realistic distribution
            type_distribution = {
                VesselType.CONTAINER: 0.25,  # 25%
                VesselType.TANKER: 0.30,     # 30%
                VesselType.BULKER: 0.25,     # 25%
                VesselType.GENERAL_CARGO: 0.20  # 20%
            }
        
        fleet = VesselFleet()
        
        # Generate vessels by type
        for vessel_type, percentage in type_distribution.items():
            count = int(total_vessels * percentage)
            
            for _ in range(count):
                vessel = self.generate_vessel(vessel_type)
                fleet.add_vessel(vessel)
        
        print(f"Generated fleet with {len(fleet.vessels)} vessels")
        print(f"Distribution: {fleet.get_vessel_statistics()['vessel_types']}")
        
        return fleet
    
    def generate_fleet_from_csv(self, csv_file_path: str, vessels_count: int = 500) -> VesselFleet:
        """
        Generate fleet using real AIS data from CSV file
        
        Args:
            csv_file_path: Path to the CSV file containing AIS data
            vessels_count: Number of vessels to create from CSV data
            
        Returns:
            VesselFleet object with vessels based on real AIS data
        """
        print(f"🚢 Generating fleet from CSV data: {csv_file_path}")
        print(f"Loading {vessels_count} vessel records...")
        
        # Load CSV data
        csv_loader = AISCSVLoader(csv_file_path)
        csv_data = csv_loader.load_sample_data(vessels_count)
        
        print(f"✅ Loaded {len(csv_data)} records from CSV")
        
        vessels = []
        for i, ais_record in enumerate(csv_data):
            vessel = self._create_vessel_from_ais_data(ais_record, i)
            if vessel:
                vessels.append(vessel)
        
        fleet = VesselFleet(vessels)
        
        print(f"✅ Created fleet with {len(vessels)} vessels from CSV data")
        print(f"Distribution: {fleet.get_vessel_statistics()['vessel_types']}")
        
        return fleet
    
    def _create_vessel_from_ais_data(self, ais_data: dict, index: int) -> Optional[Vessel]:
        """
        Create a Vessel object from AIS CSV data
        
        Args:
            ais_data: Dictionary containing AIS data from CSV
            index: Index for generating additional data
            
        Returns:
            Vessel object or None if data is invalid
        """
        try:
            # Extract basic vessel information
            vessel_name = ais_data.get('vessel_name') or f"Vessel-{ais_data.get('mmsi', index)}"
            imo_number = ais_data.get('imo_number') or f"IMO{random.randint(1000000, 9999999)}"
            
            # Map AIS vessel type codes to our enum
            ais_vessel_type = ais_data.get('vessel_type', 0)
            vessel_type = self._map_ais_vessel_type(ais_vessel_type)
            
            # Generate vessel specifications based on AIS data
            length = ais_data.get('length') or self._generate_vessel_length(vessel_type)
            width = ais_data.get('width') or (length * random.uniform(0.12, 0.18))
            draft = ais_data.get('draft') or (length * random.uniform(0.03, 0.07))
            
            specs = VesselSpecifications(
                length_meters=length,
                width_meters=width,
                draft_meters=draft,
                gross_tonnage=int(length * width * draft * random.uniform(0.6, 0.8)),
                deadweight_tonnage=int(length * width * draft * random.uniform(0.4, 0.7)),
                engine_power_kw=int(length * random.uniform(50, 200)),
                max_speed_knots=random.uniform(12, 25),
                fuel_capacity_tons=int(length * random.uniform(5, 20)),
                crew_capacity=random.randint(10, 50)
            )
            
            # Create current location from AIS data
            current_location = Location(
                latitude=ais_data['latitude'],
                longitude=ais_data['longitude'],
                timestamp=ais_data.get('timestamp', datetime.now()),
                speed_knots=ais_data.get('speed_over_ground', 0),
                course_degrees=ais_data.get('course_over_ground', 0),
                country=self._get_country_from_coordinates(ais_data['latitude'], ais_data['longitude'])
            )
            
            # Determine flag state and company
            flag_state = random.choice(self.shipping_countries)
            company_name = self.fake.company()
            
            # Generate age and dry dock history
            age_years = random.uniform(1, 30)
            build_date = datetime.now() - timedelta(days=age_years * 365)
            
            # Generate dry dock history
            dry_dock_history = self._generate_dry_dock_history(age_years, current_location.country)
            
            # Determine current status
            status = VesselStatus.IN_SERVICE
            current_dry_dock = None
            
            # Small chance vessel is currently in dry dock
            if random.random() < 0.05:  # 5% chance
                status = VesselStatus.IN_DRY_DOCK
                current_dry_dock = self._generate_current_dry_dock(current_location.country)
            
            # Create vessel
            vessel = Vessel(
                vessel_name=vessel_name,
                imo_number=imo_number,
                mmsi_number=str(ais_data.get('mmsi', random.randint(100000000, 999999999))),
                call_sign=ais_data.get('call_sign') or self._generate_call_sign(),
                flag_state=flag_state,
                vessel_type=vessel_type,
                build_date=build_date,
                specifications=specs,
                company_name=company_name,
                service_line=self._assign_service_line(vessel_type),
                home_port=self._get_port_name(current_location.country),
                current_location=current_location,
                status=status,
                dry_dock_history=dry_dock_history,
                current_dry_dock=current_dry_dock
            )
            
            return vessel
            
        except Exception as e:
            print(f"Warning: Failed to create vessel from AIS data: {e}")
            return None
    
    def _map_ais_vessel_type(self, ais_type: Optional[int]) -> VesselType:
        """
        Map AIS vessel type codes to our VesselType enum
        
        Args:
            ais_type: AIS vessel type code
            
        Returns:
            Corresponding VesselType enum value
        """
        if ais_type is None:
            return random.choice(list(VesselType))
        
        # AIS vessel type mapping (based on ITU-R M.1371-5)
        type_mapping = {
            # Cargo vessels
            70: VesselType.GENERAL_CARGO, 71: VesselType.GENERAL_CARGO, 72: VesselType.GENERAL_CARGO,
            73: VesselType.GENERAL_CARGO, 74: VesselType.GENERAL_CARGO, 75: VesselType.GENERAL_CARGO,
            76: VesselType.GENERAL_CARGO, 77: VesselType.GENERAL_CARGO, 78: VesselType.GENERAL_CARGO,
            79: VesselType.GENERAL_CARGO,
            
            # Tankers
            80: VesselType.TANKER, 81: VesselType.TANKER, 82: VesselType.TANKER, 83: VesselType.TANKER,
            84: VesselType.TANKER, 85: VesselType.TANKER, 86: VesselType.TANKER, 87: VesselType.TANKER,
            88: VesselType.TANKER, 89: VesselType.TANKER,
            
            # Other vessel types
            30: VesselType.GENERAL_CARGO,  # Fishing
            31: VesselType.GENERAL_CARGO,  # Towing
            32: VesselType.GENERAL_CARGO,  # Towing large
            33: VesselType.GENERAL_CARGO,  # Dredging
            34: VesselType.GENERAL_CARGO,  # Diving ops
            35: VesselType.GENERAL_CARGO,  # Military ops
            36: VesselType.GENERAL_CARGO,  # Sailing
            37: VesselType.GENERAL_CARGO,  # Pleasure craft
            52: VesselType.GENERAL_CARGO,  # Tug
            53: VesselType.GENERAL_CARGO,  # Port tender
            54: VesselType.GENERAL_CARGO,  # Anti-pollution
            55: VesselType.GENERAL_CARGO,  # Law enforcement
            58: VesselType.GENERAL_CARGO,  # Medical transport
        }
        
        # Default mapping for unknown types
        if ais_type in type_mapping:
            return type_mapping[ais_type]
        elif 70 <= ais_type <= 79:
            return VesselType.GENERAL_CARGO
        elif 80 <= ais_type <= 89:
            return VesselType.TANKER
        else:
            # For container ships, we'll randomly assign some cargo vessels as containers
            if random.random() < 0.3:  # 30% chance for container
                return VesselType.CONTAINER
            elif random.random() < 0.5:  # 20% chance for bulker
                return VesselType.BULKER
            else:
                return VesselType.GENERAL_CARGO
    
    def _get_country_from_coordinates(self, lat: float, lon: float) -> str:
        """
        Get country name from coordinates (simplified version)
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Country name
        """
        # Simplified mapping based on coordinate ranges
        # In a real implementation, you might use reverse geocoding
        if -125 <= lon <= -66 and 20 <= lat <= 50:
            return "United States"
        elif -15 <= lon <= 45 and 35 <= lat <= 70:
            return "Europe"
        elif 100 <= lon <= 150 and 10 <= lat <= 50:
            return "Asia"
        elif 95 <= lon <= 140 and -50 <= lat <= 20:
            return "Southeast Asia"
        else:
            return random.choice(self.shipping_countries)


# Convenience function for quick generation
def generate_sample_fleet(vessels_count: int = 500) -> VesselFleet:
    """Generate a sample fleet for testing"""
    generator = AISDataGenerator()
    return generator.generate_fleet(vessels_count)


def generate_fleet_from_csv(csv_file_path: Optional[str] = None, vessels_count: int = 500) -> VesselFleet:
    """
    Generate a fleet using real AIS data from CSV file
    
    Args:
        csv_file_path: Path to CSV file. If None, uses default AIS_2023_01_01.csv
        vessels_count: Number of vessels to load from CSV
        
    Returns:
        VesselFleet object with real AIS data
    """
    if csv_file_path is None:
        # Default to the CSV file in backend/files
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(current_dir, '..', 'files', 'AIS_2023_01_01.csv')
    
    generator = AISDataGenerator()
    return generator.generate_fleet_from_csv(csv_file_path, vessels_count)


if __name__ == "__main__":
    # Example usage
    generator = AISDataGenerator()
    
    # Generate a single vessel
    vessel = generator.generate_vessel(VesselType.CONTAINER)
    print(f"Generated vessel: {vessel.vessel_name}")
    print(f"Type: {vessel.vessel_type.value}")
    print(f"Age: {vessel.age_years:.1f} years")
    print(f"Dry dock visits: {len(vessel.dry_dock_history)}")
    print(f"Currently in dry dock: {vessel.current_dry_dock is not None}")
    
    # Generate a small fleet
    fleet = generator.generate_fleet(100)
    stats = fleet.get_vessel_statistics()
    print(f"\nFleet statistics:")
    print(f"Total vessels: {stats['total_vessels']}")
    print(f"Vessel types: {stats['vessel_types']}")
