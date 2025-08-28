#!/usr/bin/env python3
"""
AIS CSV Data Loader
Loads and processes AIS data from CSV files instead of iostream
"""

import csv
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AISCSVLoader:
    """Loads AIS data from CSV files"""
    
    def __init__(self, csv_file_path: str):
        """
        Initialize CSV loader
        
        Args:
            csv_file_path: Path to the CSV file containing AIS data
        """
        self.csv_file_path = Path(csv_file_path)
        self.columns = [
            'MMSI', 'BaseDateTime', 'LAT', 'LON', 'SOG', 'COG', 'Heading',
            'VesselName', 'IMO', 'CallSign', 'VesselType', 'Status', 'Length',
            'Width', 'Draft', 'Cargo', 'TransceiverClass'
        ]
        
        if not self.csv_file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    
    def load_sample_data(self, num_records: int = 1000) -> List[Dict[str, Any]]:
        """
        Load a sample of AIS data from CSV
        
        Args:
            num_records: Number of records to load
            
        Returns:
            List of dictionaries containing AIS vessel data
        """
        logger.info(f"Loading {num_records} records from {self.csv_file_path}")
        
        vessels = []
        
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                # Skip the header if it exists
                reader = csv.DictReader(file)
                
                for i, row in enumerate(reader):
                    if i >= num_records:
                        break
                    
                    # Parse and clean the data
                    vessel_data = self._parse_vessel_record(row)
                    if vessel_data:
                        vessels.append(vessel_data)
                        
        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            raise
        
        logger.info(f"Successfully loaded {len(vessels)} vessel records")
        return vessels
    
    def load_data_with_pandas(self, num_records: int = 1000, chunk_size: int = 10000) -> pd.DataFrame:
        """
        Load AIS data using pandas for better performance
        
        Args:
            num_records: Number of records to load
            chunk_size: Size of chunks to read
            
        Returns:
            Pandas DataFrame with AIS data
        """
        logger.info(f"Loading {num_records} records using pandas from {self.csv_file_path}")
        
        try:
            # Read the CSV in chunks to handle large files
            df = pd.read_csv(self.csv_file_path, nrows=num_records)
            
            # Clean and process the data
            df = self._clean_dataframe(df)
            
            logger.info(f"Successfully loaded {len(df)} records with pandas")
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV with pandas: {e}")
            raise
    
    def load_data_by_date_range(self, start_date: str, end_date: str, max_records: int = 1000) -> List[Dict[str, Any]]:
        """
        Load AIS data filtered by date range
        
        Args:
            start_date: Start date in format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM'
            end_date: End date in format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM'
            max_records: Maximum number of records to return
            
        Returns:
            List of vessel data dictionaries within the date range
        """
        logger.info(f"Loading data from {start_date} to {end_date}")
        
        try:
            # Parse date strings
            start_dt = self._parse_datetime(start_date)
            end_dt = self._parse_datetime(end_date)
            
            if not start_dt or not end_dt:
                logger.error("Invalid date format")
                return []
            
            vessels = []
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for i, row in enumerate(reader):
                    if i >= max_records:
                        break
                    
                    # Parse the timestamp from the record
                    record_time = self._parse_datetime(row.get('BaseDateTime', ''))
                    if not record_time:
                        continue
                    
                    # Check if record is within date range
                    if start_dt <= record_time <= end_dt:
                        vessel_data = self._parse_vessel_record(row)
                        if vessel_data:
                            vessels.append(vessel_data)
            
            logger.info(f"Found {len(vessels)} vessels in date range {start_date} to {end_date}")
            return vessels
            
        except Exception as e:
            logger.error(f"Error loading data by date range: {e}")
            return []
    
    def stream_data(self, chunk_size: int = 1000) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Stream AIS data in chunks to handle large files
        
        Args:
            chunk_size: Number of records per chunk
            
        Yields:
            Chunks of vessel data as lists of dictionaries
        """
        logger.info(f"Streaming data from {self.csv_file_path} in chunks of {chunk_size}")
        
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                chunk = []
                for row in reader:
                    vessel_data = self._parse_vessel_record(row)
                    if vessel_data:
                        chunk.append(vessel_data)
                    
                    if len(chunk) >= chunk_size:
                        yield chunk
                        chunk = []
                
                # Yield any remaining data
                if chunk:
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Error streaming CSV data: {e}")
            raise
    
    def _parse_vessel_record(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Parse a single vessel record from CSV row
        
        Args:
            row: Raw CSV row as dictionary
            
        Returns:
            Parsed vessel data or None if invalid
        """
        try:
            # Handle missing or empty values
            vessel_data = {
                'mmsi': self._safe_int(row.get('MMSI', '')),
                'timestamp': self._parse_datetime(row.get('BaseDateTime', '')),
                'latitude': self._safe_float(row.get('LAT', '')),
                'longitude': self._safe_float(row.get('LON', '')),
                'speed_over_ground': self._safe_float(row.get('SOG', '')),
                'course_over_ground': self._safe_float(row.get('COG', '')),
                'heading': self._safe_float(row.get('Heading', '')),
                'vessel_name': row.get('VesselName', '').strip(),
                'imo_number': row.get('IMO', '').strip(),
                'call_sign': row.get('CallSign', '').strip(),
                'vessel_type': self._safe_int(row.get('VesselType', '')),
                'status': self._safe_int(row.get('Status', '')),
                'length': self._safe_float(row.get('Length', '')),
                'width': self._safe_float(row.get('Width', '')),
                'draft': self._safe_float(row.get('Draft', '')),
                'cargo': self._safe_int(row.get('Cargo', '')),
                'transceiver_class': row.get('TransceiverClass', '').strip()
            }
            
            # Validate essential fields
            if not vessel_data['mmsi'] or not vessel_data['latitude'] or not vessel_data['longitude']:
                return None
            
            return vessel_data
            
        except Exception as e:
            logger.warning(f"Error parsing vessel record: {e}")
            return None
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and process the dataframe
        
        Args:
            df: Raw dataframe
            
        Returns:
            Cleaned dataframe
        """
        # Convert data types
        numeric_columns = ['LAT', 'LON', 'SOG', 'COG', 'Heading', 'Length', 'Width', 'Draft']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert integer columns
        int_columns = ['MMSI', 'VesselType', 'Status', 'Cargo']
        for col in int_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce', downcast='integer')
        
        # Parse datetime
        if 'BaseDateTime' in df.columns:
            df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime'], errors='coerce')
        
        # Drop rows with missing essential data
        df = df.dropna(subset=['MMSI', 'LAT', 'LON'])
        
        return df
    
    def _safe_int(self, value: str) -> Optional[int]:
        """Safely convert string to int"""
        try:
            if value and value.strip():
                return int(float(value))
            return None
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value: str) -> Optional[float]:
        """Safely convert string to float"""
        try:
            if value and value.strip():
                # Handle special values like 511.0 (no data indicator)
                float_val = float(value)
                if float_val == 511.0:  # Common AIS "no data" indicator
                    return None
                return float_val
            return None
        except (ValueError, TypeError):
            return None
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse datetime string"""
        try:
            if datetime_str and datetime_str.strip():
                return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return None
        except (ValueError, TypeError):
            return None
    
    def get_file_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the CSV file
        
        Returns:
            Dictionary with file statistics
        """
        logger.info(f"Getting file statistics for {self.csv_file_path}")
        
        file_size = self.csv_file_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        # Count lines
        line_count = 0
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line_count += 1
        except Exception as e:
            logger.error(f"Error counting lines: {e}")
            line_count = -1
        
        return {
            'file_path': str(self.csv_file_path),
            'file_size_bytes': file_size,
            'file_size_mb': round(file_size_mb, 2),
            'estimated_lines': line_count,
            'estimated_records': max(0, line_count - 1) if line_count > 0 else 0  # Subtract header
        }


def load_ais_data_from_csv(csv_file_path: str, num_records: int = 1000) -> List[Dict[str, Any]]:
    """
    Convenience function to load AIS data from CSV
    
    Args:
        csv_file_path: Path to CSV file
        num_records: Number of records to load
        
    Returns:
        List of vessel data dictionaries
    """
    loader = AISCSVLoader(csv_file_path)
    return loader.load_sample_data(num_records)


def main():
    """Demo function showing CSV loader usage"""
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'files', 'AIS_2023_01_01.csv')
    
    print("🚢 AIS CSV Data Loader Demo")
    print("=" * 40)
    
    try:
        # Initialize loader
        loader = AISCSVLoader(csv_path)
        
        # Show file stats
        stats = loader.get_file_stats()
        print(f"📁 File: {stats['file_path']}")
        print(f"📊 Size: {stats['file_size_mb']} MB")
        print(f"📄 Estimated records: {stats['estimated_records']:,}")
        print()
        
        # Load sample data
        print("Loading sample data...")
        vessels = loader.load_sample_data(100)
        
        print(f"✅ Loaded {len(vessels)} vessel records")
        
        # Show sample vessels
        print("\n🚢 Sample Vessels:")
        for i, vessel in enumerate(vessels[:5]):
            print(f"  {i+1}. {vessel['vessel_name'] or 'Unknown'} (MMSI: {vessel['mmsi']})")
            print(f"     Position: {vessel['latitude']:.4f}, {vessel['longitude']:.4f}")
            print(f"     Speed: {vessel['speed_over_ground']} knots")
        
        # Demo pandas loading
        print("\n📊 Loading with pandas...")
        df = loader.load_data_with_pandas(500)
        print(f"✅ Loaded {len(df)} records with pandas")
        print(f"   Columns: {list(df.columns)}")
        
        print("\n✨ CSV loader ready for use!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    main()

