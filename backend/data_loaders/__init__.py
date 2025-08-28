"""
Data Loaders Package
Handles loading data from various sources including CSV files
"""

from .csv_loader import AISCSVLoader, load_ais_data_from_csv

__all__ = ['AISCSVLoader', 'load_ais_data_from_csv']

