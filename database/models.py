"""
Database Models for AIS Marine Vessel System
SQLAlchemy models for data persistence
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
from typing import Dict, Any, List, Optional

Base = declarative_base()


class VesselDB(Base):
    """Database model for vessels"""
    __tablename__ = 'vessels'
    
    id = Column(Integer, primary_key=True)
    imo_number = Column(String(20), unique=True, nullable=False)
    mmsi = Column(String(20), unique=True, nullable=False)
    vessel_name = Column(String(200), nullable=False)
    call_sign = Column(String(20))
    
    # Classification
    vessel_type = Column(String(50), nullable=False)
    service_line = Column(String(100))
    
    # Origin and ownership
    flag_state = Column(String(100))
    home_port = Column(String(200))
    owner_company = Column(String(200))
    operator_company = Column(String(200))
    
    # Dates
    build_date = Column(DateTime)
    last_survey_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Technical specifications (stored as JSON)
    specifications_json = Column(Text)  # JSON string of specifications
    
    # Current status
    current_status = Column(String(50))
    current_latitude = Column(Float)
    current_longitude = Column(Float)
    current_port = Column(String(200))
    current_country = Column(String(100))
    
    # Performance metrics
    total_voyages = Column(Integer, default=0)
    total_distance_nm = Column(Float, default=0.0)
    average_speed_knots = Column(Float, default=0.0)
    fuel_efficiency = Column(Float, default=0.0)
    
    # Relationships
    dry_dock_records = relationship("DryDockRecordDB", back_populates="vessel")
    port_visits = relationship("PortVisitDB", back_populates="vessel")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        specs = {}
        if self.specifications_json:
            try:
                specs = json.loads(self.specifications_json)
            except:
                pass
        
        return {
            'id': self.id,
            'imo_number': self.imo_number,
            'mmsi': self.mmsi,
            'vessel_name': self.vessel_name,
            'call_sign': self.call_sign,
            'vessel_type': self.vessel_type,
            'service_line': self.service_line,
            'flag_state': self.flag_state,
            'home_port': self.home_port,
            'owner_company': self.owner_company,
            'operator_company': self.operator_company,
            'build_date': self.build_date.isoformat() if self.build_date else None,
            'current_status': self.current_status,
            'current_location': {
                'latitude': self.current_latitude,
                'longitude': self.current_longitude,
                'port': self.current_port,
                'country': self.current_country
            } if self.current_latitude and self.current_longitude else None,
            'specifications': specs,
            'performance': {
                'total_voyages': self.total_voyages,
                'total_distance_nm': self.total_distance_nm,
                'average_speed_knots': self.average_speed_knots,
                'fuel_efficiency': self.fuel_efficiency
            },
            'age_years': (datetime.now() - self.build_date).days / 365.25 if self.build_date else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DryDockRecordDB(Base):
    """Database model for dry dock records"""
    __tablename__ = 'dry_dock_records'
    
    id = Column(Integer, primary_key=True)
    vessel_id = Column(Integer, ForeignKey('vessels.id'), nullable=False)
    
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    
    facility_name = Column(String(200))
    facility_country = Column(String(100))
    facility_latitude = Column(Float)
    facility_longitude = Column(Float)
    
    purpose = Column(String(500))
    cost_estimate = Column(Float)
    completed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vessel = relationship("VesselDB", back_populates="dry_dock_records")
    
    @property
    def duration_days(self) -> Optional[int]:
        """Calculate duration in days"""
        if self.end_date:
            return (self.end_date - self.start_date).days
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'vessel_id': self.vessel_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'facility': {
                'name': self.facility_name,
                'country': self.facility_country,
                'latitude': self.facility_latitude,
                'longitude': self.facility_longitude
            },
            'purpose': self.purpose,
            'cost_estimate': self.cost_estimate,
            'duration_days': self.duration_days,
            'completed': self.completed,
            'created_at': self.created_at.isoformat()
        }


class PortVisitDB(Base):
    """Database model for port visits"""
    __tablename__ = 'port_visits'
    
    id = Column(Integer, primary_key=True)
    vessel_id = Column(Integer, ForeignKey('vessels.id'), nullable=False)
    
    port_name = Column(String(200), nullable=False)
    country = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    
    arrival_time = Column(DateTime)
    departure_time = Column(DateTime)
    
    purpose = Column(String(200))  # Loading, Unloading, Bunkering, etc.
    cargo_operations = Column(Text)  # JSON string of cargo details
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vessel = relationship("VesselDB", back_populates="port_visits")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        cargo_ops = {}
        if self.cargo_operations:
            try:
                cargo_ops = json.loads(self.cargo_operations)
            except:
                pass
        
        return {
            'id': self.id,
            'vessel_id': self.vessel_id,
            'port': {
                'name': self.port_name,
                'country': self.country,
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            'arrival_time': self.arrival_time.isoformat() if self.arrival_time else None,
            'departure_time': self.departure_time.isoformat() if self.departure_time else None,
            'purpose': self.purpose,
            'cargo_operations': cargo_ops,
            'created_at': self.created_at.isoformat()
        }


class DatabaseManager:
    """Database connection and operations manager"""
    
    def __init__(self, database_url: str = "sqlite:///ais_vessels.db"):
        """Initialize database manager"""
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def save_vessel(self, vessel) -> VesselDB:
        """Save vessel to database"""
        session = self.get_session()
        try:
            # Check if vessel already exists
            existing = session.query(VesselDB).filter_by(imo_number=vessel.imo_number).first()
            
            if existing:
                # Update existing vessel
                self._update_vessel_from_model(existing, vessel)
                vessel_db = existing
            else:
                # Create new vessel
                vessel_db = self._create_vessel_from_model(vessel)
                session.add(vessel_db)
            
            session.commit()
            return vessel_db
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def save_fleet(self, fleet) -> List[VesselDB]:
        """Save entire fleet to database"""
        session = self.get_session()
        try:
            saved_vessels = []
            
            for vessel in fleet.vessels:
                # Check if vessel already exists
                existing = session.query(VesselDB).filter_by(imo_number=vessel.imo_number).first()
                
                if existing:
                    self._update_vessel_from_model(existing, vessel)
                    vessel_db = existing
                else:
                    vessel_db = self._create_vessel_from_model(vessel)
                    session.add(vessel_db)
                
                # Save dry dock records
                for record in vessel.dry_dock_history:
                    dry_dock_db = DryDockRecordDB(
                        vessel_id=vessel_db.id if existing else None,  # Will be set after commit
                        start_date=record.start_date,
                        end_date=record.end_date,
                        facility_name=record.location.port_name,
                        facility_country=record.location.country,
                        facility_latitude=record.location.latitude,
                        facility_longitude=record.location.longitude,
                        purpose=record.purpose,
                        cost_estimate=record.cost_estimate,
                        completed=record.completed
                    )
                    if not existing:
                        vessel_db.dry_dock_records.append(dry_dock_db)
                
                saved_vessels.append(vessel_db)
                
                # Commit in batches to avoid memory issues
                if len(saved_vessels) % 100 == 0:
                    session.commit()
            
            session.commit()
            return saved_vessels
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _create_vessel_from_model(self, vessel) -> VesselDB:
        """Create VesselDB from vessel model"""
        # Prepare specifications JSON
        specs_json = None
        if vessel.specifications:
            specs_json = json.dumps({
                'length_meters': vessel.specifications.length_meters,
                'width_meters': vessel.specifications.width_meters,
                'gross_tonnage': vessel.specifications.gross_tonnage,
                'deadweight_tonnage': vessel.specifications.deadweight_tonnage,
                'max_speed_knots': vessel.specifications.max_speed_knots,
                'engine_power_hp': vessel.specifications.engine_power_hp,
                'fuel_capacity_tons': vessel.specifications.fuel_capacity_tons,
                'cargo_capacity': vessel.specifications.cargo_capacity
            })
        
        vessel_db = VesselDB(
            imo_number=vessel.imo_number,
            mmsi=vessel.mmsi,
            vessel_name=vessel.vessel_name,
            call_sign=vessel.call_sign,
            vessel_type=vessel.vessel_type.value,
            service_line=vessel.service_line.value,
            flag_state=vessel.flag_state,
            home_port=vessel.home_port,
            owner_company=vessel.owner_company,
            operator_company=vessel.operator_company,
            build_date=vessel.build_date,
            last_survey_date=vessel.last_survey_date,
            specifications_json=specs_json,
            current_status=vessel.current_status.value,
            current_latitude=vessel.current_location.latitude if vessel.current_location else None,
            current_longitude=vessel.current_location.longitude if vessel.current_location else None,
            current_port=vessel.current_location.port_name if vessel.current_location else None,
            current_country=vessel.current_location.country if vessel.current_location else None,
            total_voyages=vessel.total_voyages,
            total_distance_nm=vessel.total_distance_nm,
            average_speed_knots=vessel.average_speed_knots,
            fuel_efficiency=vessel.fuel_efficiency
        )
        
        return vessel_db
    
    def _update_vessel_from_model(self, vessel_db: VesselDB, vessel):
        """Update VesselDB from vessel model"""
        vessel_db.vessel_name = vessel.vessel_name
        vessel_db.current_status = vessel.current_status.value
        vessel_db.current_latitude = vessel.current_location.latitude if vessel.current_location else None
        vessel_db.current_longitude = vessel.current_location.longitude if vessel.current_location else None
        vessel_db.current_port = vessel.current_location.port_name if vessel.current_location else None
        vessel_db.current_country = vessel.current_location.country if vessel.current_location else None
        vessel_db.total_voyages = vessel.total_voyages
        vessel_db.total_distance_nm = vessel.total_distance_nm
        vessel_db.average_speed_knots = vessel.average_speed_knots
        vessel_db.fuel_efficiency = vessel.fuel_efficiency
        vessel_db.updated_at = datetime.utcnow()
    
    def get_all_vessels(self, limit: int = None, offset: int = 0) -> List[VesselDB]:
        """Get all vessels from database"""
        session = self.get_session()
        try:
            query = session.query(VesselDB)
            if limit:
                query = query.offset(offset).limit(limit)
            return query.all()
        finally:
            session.close()
    
    def get_vessel_by_imo(self, imo_number: str) -> Optional[VesselDB]:
        """Get vessel by IMO number"""
        session = self.get_session()
        try:
            return session.query(VesselDB).filter_by(imo_number=imo_number).first()
        finally:
            session.close()
    
    def get_vessels_by_type(self, vessel_type: str) -> List[VesselDB]:
        """Get vessels by type"""
        session = self.get_session()
        try:
            return session.query(VesselDB).filter_by(vessel_type=vessel_type).all()
        finally:
            session.close()
    
    def get_vessels_by_status(self, status: str) -> List[VesselDB]:
        """Get vessels by status"""
        session = self.get_session()
        try:
            return session.query(VesselDB).filter_by(current_status=status).all()
        finally:
            session.close()
    
    def get_vessels_in_dry_dock(self) -> List[VesselDB]:
        """Get vessels currently in dry dock"""
        session = self.get_session()
        try:
            return session.query(VesselDB).filter_by(current_status='dry_dock').all()
        finally:
            session.close()
    
    def get_dry_dock_records(self, vessel_id: int = None) -> List[DryDockRecordDB]:
        """Get dry dock records"""
        session = self.get_session()
        try:
            query = session.query(DryDockRecordDB)
            if vessel_id:
                query = query.filter_by(vessel_id=vessel_id)
            return query.all()
        finally:
            session.close()
    
    def get_fleet_statistics(self) -> Dict[str, Any]:
        """Get fleet statistics from database"""
        session = self.get_session()
        try:
            total_vessels = session.query(VesselDB).count()
            
            # Count by type
            type_counts = session.query(VesselDB.vessel_type, session.query(VesselDB).filter_by(vessel_type=VesselDB.vessel_type).count()).distinct().all()
            
            # Count by status
            status_counts = session.query(VesselDB.current_status, session.query(VesselDB).filter_by(current_status=VesselDB.current_status).count()).distinct().all()
            
            return {
                'total_vessels': total_vessels,
                'by_type': dict(type_counts),
                'by_status': dict(status_counts)
            }
        finally:
            session.close()


if __name__ == "__main__":
    # Example usage
    db_manager = DatabaseManager()
    
    # Generate sample data and save to database
    from generators.ais_data_generator import generate_sample_fleet
    
    print("Generating sample fleet...")
    fleet = generate_sample_fleet(100)
    
    print("Saving fleet to database...")
    saved_vessels = db_manager.save_fleet(fleet)
    
    print(f"Saved {len(saved_vessels)} vessels to database")
    
    # Test queries
    print(f"Total vessels in DB: {len(db_manager.get_all_vessels())}")
    print(f"Tankers in DB: {len(db_manager.get_vessels_by_type('tanker'))}")
    print(f"Vessels in dry dock: {len(db_manager.get_vessels_in_dry_dock())}")
