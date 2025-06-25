# src/sheet_repair.py - Stub implementation for testing

import pandas as pd
import numpy as np
from typing import Dict


class SheetRepair:
    """Repair and validate spreadsheet data"""
    
    def __init__(self):
        self.repair_count = 0
    
    def detect_missing_values(self, df: pd.DataFrame) -> Dict[str, int]:
        """Detect missing values in each column"""
        return df.isnull().sum().to_dict()
    
    def fill_missing_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing dates with interpolation"""
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Date'] = df['Date'].fillna(method='ffill')
        return df
    
    def fill_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill numeric columns with appropriate methods"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = df[col].fillna(df[col].mean())
        return df
    
    def validate_player_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and expand player names"""
        if 'Player' in df.columns:
            # Simple mock expansion
            df['Player'] = df['Player'].replace({
                'S. Curry': 'Stephen Curry',
                'K Durant': 'Kevin Durant'
            })
        return df
    
    def repair_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Repair data types"""
        for col in df.columns:
            if col.endswith('_ID'):
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            elif col in ['Points', 'Rebounds', 'Assists']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    
    def handle_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows"""
        return df.drop_duplicates()
    
    def repair_sheet(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full sheet repair process"""
        df = self.fill_missing_dates(df)
        df = self.fill_numeric_columns(df)
        df = self.validate_player_names(df)
        df = self.repair_data_types(df)
        df = self.handle_duplicates(df)
        self.repair_count += 1
        return df
    
    def standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names"""
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        # Rename specific columns
        rename_map = {
            'ast': 'assists',
            'reb': 'rebounds',
            'pts': 'points'
        }
        df = df.rename(columns=rename_map)
        return df
    
    def handle_outliers(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Handle outliers in a column"""
        if column in df.columns:
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            upper_bound = Q3 + 3 * IQR
            df.loc[df[column] > upper_bound, column] = upper_bound
        return df
    
    def standardize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize date formats"""
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        return df
