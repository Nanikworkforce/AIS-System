"""
Marine Vessel Data Models for AIS System
Defines vessel types, properties, and data structures
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid
from dataclasses import dataclass, field


class VesselType(Enum):
    """Vessel type categories"""
    TANKER = "tanker"
    BULKER = "bulker"
    CONTAINER = "container"
    GENERAL_CARGO = "general_cargo"


class VesselStatus(Enum):
    """Current vessel status"""
    AT_SEA = "at_sea"
    IN_PORT = "in_port"
    DRY_DOCK = "dry_dock"
    ANCHORED = "anchored"
    UNDER_REPAIR = "under_repair"


class ServiceLine(Enum):
    """Main service lines for vessels"""
    CRUDE_OIL_TRANSPORT = "crude_oil_transport"
    PRODUCT_TANKER = "product_tanker"
    CHEMICAL_TRANSPORT = "chemical_transport"
    DRY_BULK_CARGO = "dry_bulk_cargo"
    CONTAINER_SHIPPING = "container_shipping"
    GENERAL_CARGO = "general_cargo"
    RO_RO_FERRY = "ro_ro_ferry"
    OFFSHORE_SUPPLY = "offshore_supply"


@dataclass
class Location:
    """Geographical location with port information"""
    latitude: float
    longitude: float
    port_name: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    
    def __str__(self):
        if self.port_name:
            return f"{self.port_name}, {self.country}"
        return f"({self.latitude:.4f}, {self.longitude:.4f})"


@dataclass
class DryDockRecord:
    """Record of dry dock maintenance periods"""
    start_date: datetime
    end_date: Optional[datetime]
    location: Location
    purpose: str
    cost_estimate: Optional[float] = None
    completed: bool = False
    
    @property
    def duration_days(self) -> Optional[int]:
        """Calculate duration in days"""
        if self.end_date:
            return (self.end_date - self.start_date).days
        return None
    
    @property
    def is_current(self) -> bool:
        """Check if currently in dry dock"""
        return not self.completed and (self.end_date is None or self.end_date > datetime.now())


@dataclass
class VesselSpecifications:
    """Technical specifications of the vessel"""
    length_meters: float
    width_meters: float
    gross_tonnage: float
    deadweight_tonnage: float
    max_speed_knots: float
    engine_power_hp: float
    fuel_capacity_tons: float
    cargo_capacity: float  # TEU for containers, tons for others
    
    @property
    def size_category(self) -> str:
        """Categorize vessel by size"""
        if self.deadweight_tonnage < 10000:
            return "Small"
        elif self.deadweight_tonnage < 50000:
            return "Medium"
        elif self.deadweight_tonnage < 150000:
            return "Large"
        else:
            return "Very Large"


@dataclass
class Vessel:
    """Main vessel data model"""
    # Basic identification
    imo_number: str = field(default_factory=lambda: str(uuid.uuid4())[:9])
    mmsi: str = field(default_factory=lambda: str(uuid.uuid4().int)[:9])
    vessel_name: str = ""
    call_sign: str = ""
    
    # Classification
    vessel_type: VesselType = VesselType.GENERAL_CARGO
    service_line: ServiceLine = ServiceLine.GENERAL_CARGO
    
    # Origin and ownership
    flag_state: str = ""
    home_port: str = ""
    owner_company: str = ""
    operator_company: str = ""
    
    # Dates
    build_date: datetime = field(default_factory=lambda: datetime.now() - timedelta(days=365*10))
    last_survey_date: Optional[datetime] = None
    
    # Technical specs
    specifications: Optional[VesselSpecifications] = None
    
    # Current status
    current_status: VesselStatus = VesselStatus.AT_SEA
    current_location: Optional[Location] = None
    destination: Optional[Location] = None
    estimated_arrival: Optional[datetime] = None
    
    # History
    dry_dock_history: List[DryDockRecord] = field(default_factory=list)
    port_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Performance metrics
    total_voyages: int = 0
    total_distance_nm: float = 0.0
    average_speed_knots: float = 0.0
    fuel_efficiency: float = 0.0  # tons per nautical mile
    
    @property
    def age_years(self) -> float:
        """Calculate vessel age in years"""
        return (datetime.now() - self.build_date).days / 365.25
    
    @property
    def current_dry_dock(self) -> Optional[DryDockRecord]:
        """Get current dry dock record if vessel is in dry dock"""
        for record in self.dry_dock_history:
            if record.is_current:
                return record
        return None
    
    @property
    def total_dry_dock_days(self) -> int:
        """Calculate total days spent in dry dock"""
        total = 0
        for record in self.dry_dock_history:
            if record.duration_days:
                total += record.duration_days
        return total
    
    @property
    def dry_dock_frequency(self) -> float:
        """Calculate average days between dry dock visits"""
        if len(self.dry_dock_history) < 2:
            return 0.0
        
        completed_records = [r for r in self.dry_dock_history if r.completed]
        if len(completed_records) < 2:
            return 0.0
        
        total_period = (completed_records[-1].end_date - completed_records[0].start_date).days
        return total_period / len(completed_records)
    
    def add_dry_dock_record(self, record: DryDockRecord):
        """Add a new dry dock record"""
        self.dry_dock_history.append(record)
        if record.is_current:
            self.current_status = VesselStatus.DRY_DOCK
            self.current_location = record.location
    
    def complete_current_dry_dock(self, end_date: datetime):
        """Mark current dry dock as completed"""
        current = self.current_dry_dock
        if current:
            current.end_date = end_date
            current.completed = True
            self.current_status = VesselStatus.IN_PORT
    
    def update_location(self, location: Location, status: VesselStatus = VesselStatus.AT_SEA):
        """Update current vessel location and status"""
        self.current_location = location
        self.current_status = status
        
        # Add to port history if in port
        if status == VesselStatus.IN_PORT and location.port_name:
            self.port_history.append({
                'port_name': location.port_name,
                'country': location.country,
                'arrival_time': datetime.now(),
                'coordinates': (location.latitude, location.longitude)
            })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert vessel to dictionary for API responses"""
        return {
            'imo_number': self.imo_number,
            'mmsi': self.mmsi,
            'vessel_name': self.vessel_name,
            'vessel_type': self.vessel_type.value,
            'service_line': self.service_line.value,
            'flag_state': self.flag_state,
            'owner_company': self.owner_company,
            'age_years': round(self.age_years, 1),
            'current_status': self.current_status.value,
            'current_location': str(self.current_location) if self.current_location else None,
            'total_dry_dock_days': self.total_dry_dock_days,
            'dry_dock_frequency': round(self.dry_dock_frequency, 1),
            'specifications': {
                'length_meters': self.specifications.length_meters,
                'deadweight_tonnage': self.specifications.deadweight_tonnage,
                'size_category': self.specifications.size_category
            } if self.specifications else None
        }


class VesselFleet:
    """Manages a collection of vessels"""
    
    def __init__(self):
        self.vessels: List[Vessel] = []
    
    def add_vessel(self, vessel: Vessel):
        """Add vessel to fleet"""
        self.vessels.append(vessel)
    
    def get_by_type(self, vessel_type: VesselType) -> List[Vessel]:
        """Get all vessels of specific type"""
        return [v for v in self.vessels if v.vessel_type == vessel_type]
    
    def get_by_status(self, status: VesselStatus) -> List[Vessel]:
        """Get all vessels with specific status"""
        return [v for v in self.vessels if v.current_status == status]
    
    def get_by_flag_state(self, flag_state: str) -> List[Vessel]:
        """Get all vessels from specific country"""
        return [v for v in self.vessels if v.flag_state.lower() == flag_state.lower()]
    
    def get_vessels_in_dry_dock(self) -> List[Vessel]:
        """Get all vessels currently in dry dock"""
        return [v for v in self.vessels if v.current_dry_dock is not None]
    
    def get_vessel_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive fleet statistics"""
        total_vessels = len(self.vessels)
        if total_vessels == 0:
            return {}
        
        # Type distribution
        type_counts = {}
        for vessel_type in VesselType:
            count = len(self.get_by_type(vessel_type))
            type_counts[vessel_type.value] = {
                'count': count,
                'percentage': round(count / total_vessels * 100, 2)
            }
        
        # Status distribution
        status_counts = {}
        for status in VesselStatus:
            count = len(self.get_by_status(status))
            status_counts[status.value] = {
                'count': count,
                'percentage': round(count / total_vessels * 100, 2)
            }
        
        # Country distribution
        countries = {}
        for vessel in self.vessels:
            country = vessel.flag_state
            if country in countries:
                countries[country] += 1
            else:
                countries[country] = 1
        
        # Age statistics
        ages = [v.age_years for v in self.vessels]
        
        # Dry dock statistics
        vessels_in_dry_dock = self.get_vessels_in_dry_dock()
        total_dry_dock_days = sum(v.total_dry_dock_days for v in self.vessels)
        
        return {
            'total_vessels': total_vessels,
            'vessel_types': type_counts,
            'vessel_status': status_counts,
            'countries': countries,
            'age_statistics': {
                'average_age': round(sum(ages) / len(ages), 1) if ages else 0,
                'oldest_vessel': round(max(ages), 1) if ages else 0,
                'newest_vessel': round(min(ages), 1) if ages else 0
            },
            'dry_dock_statistics': {
                'vessels_currently_in_dry_dock': len(vessels_in_dry_dock),
                'total_dry_dock_days_fleet': total_dry_dock_days,
                'average_dry_dock_days_per_vessel': round(total_dry_dock_days / total_vessels, 1) if total_vessels > 0 else 0
            }
        }
