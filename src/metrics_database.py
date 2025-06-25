# src/metrics_database.py - Historical Metrics Storage

import sqlite3
import pandas as pd
from datetime import datetime
import logging
import os
from typing import Dict, List, Optional
import json


class MetricsDatabase:
    """Handle storage and retrieval of paper trading metrics"""
    
    def __init__(self, db_path: str = "data/paper_metrics.db"):
        self.db_path = db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_metrics (
                    date TEXT PRIMARY KEY,
                    total_trades INTEGER,
                    winners INTEGER,
                    losers INTEGER,
                    win_rate REAL,
                    total_stake REAL,
                    total_profit REAL,
                    roi REAL,
                    average_odds REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Individual trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    player TEXT,
                    stat_type TEXT,
                    projection REAL,
                    line REAL,
                    actual REAL,
                    direction TEXT,
                    payout_odds REAL,
                    won BOOLEAN,
                    stake REAL,
                    profit REAL,
                    roi REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, player, stat_type)
                )
            """)
            
            # Weekly summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weekly_summary (
                    week_start TEXT PRIMARY KEY,
                    week_end TEXT,
                    total_trades INTEGER,
                    win_rate REAL,
                    total_profit REAL,
                    roi REAL,
                    best_day TEXT,
                    worst_day TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indices for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_player ON trades(player)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_won ON trades(won)")
            
            conn.commit()
    
    def insert_daily_metrics(self, metrics: Dict) -> bool:
        """
        Insert or update daily metrics
        
        Args:
            metrics: Dictionary containing daily metrics
            
        Returns:
            bool: Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_metrics 
                    (date, total_trades, winners, losers, win_rate, 
                     total_stake, total_profit, roi, average_odds, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    metrics['date'],
                    metrics['total_trades'],
                    metrics['winners'],
                    metrics['losers'],
                    metrics['win_rate'],
                    metrics['total_stake'],
                    metrics['total_profit'],
                    metrics['roi'],
                    metrics.get('average_odds', 0)
                ))
                
                conn.commit()
                logging.info(f"Inserted metrics for {metrics['date']}")
                return True
                
        except Exception as e:
            logging.error(f"Error inserting daily metrics: {e}")
            return False
    
    def insert_trades(self, trades_df: pd.DataFrame) -> bool:
        """
        Insert individual trades
        
        Args:
            trades_df: DataFrame containing trade data
            
        Returns:
            bool: Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Use pandas to_sql with if_exists='append'
                trades_df.to_sql('trades', conn, if_exists='append', index=False)
                logging.info(f"Inserted {len(trades_df)} trades")
                return True
                
        except sqlite3.IntegrityError:
            # Handle duplicates by updating existing records
            logging.info("Updating existing trades...")
            return self._update_trades(trades_df)
            
        except Exception as e:
            logging.error(f"Error inserting trades: {e}")
            return False
    
    def _update_trades(self, trades_df: pd.DataFrame) -> bool:
        """Update existing trades"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for _, trade in trades_df.iterrows():
                    cursor.execute("""
                        UPDATE trades 
                        SET projection=?, line=?, actual=?, direction=?, 
                            payout_odds=?, won=?, stake=?, profit=?, roi=?
                        WHERE date=? AND player=? AND stat_type=?
                    """, (
                        trade['projection'], trade['line'], trade['actual'],
                        trade['direction'], trade['payout_odds'], trade['won'],
                        trade['stake'], trade['profit'], trade['roi'],
                        trade['date'], trade['player'], trade['stat_type']
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logging.error(f"Error updating trades: {e}")
            return False
    
    def get_metrics_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get metrics for a date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Metrics data
        """
        query = """
            SELECT * FROM daily_metrics 
            WHERE date BETWEEN ? AND ?
            ORDER BY date
        """
        
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=(start_date, end_date))
    
    def get_player_stats(self, player: str) -> pd.DataFrame:
        """Get all trades for a specific player"""
        query = """
            SELECT * FROM trades 
            WHERE player = ?
            ORDER BY date DESC
        """
        
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=(player,))
    
    def calculate_rolling_metrics(self, days: int = 7) -> pd.DataFrame:
        """Calculate rolling average metrics"""
        query = f"""
            SELECT 
                date,
                AVG(win_rate) OVER (ORDER BY date ROWS BETWEEN {days-1} PRECEDING AND CURRENT ROW) as rolling_win_rate,
                AVG(roi) OVER (ORDER BY date ROWS BETWEEN {days-1} PRECEDING AND CURRENT ROW) as rolling_roi,
                SUM(total_profit) OVER (ORDER BY date ROWS BETWEEN {days-1} PRECEDING AND CURRENT ROW) as rolling_profit
            FROM daily_metrics
            ORDER BY date
        """
        
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn)
    
    def get_best_worst_days(self, limit: int = 5) -> Dict[str, pd.DataFrame]:
        """Get best and worst performing days"""
        with sqlite3.connect(self.db_path) as conn:
            best_query = "SELECT * FROM daily_metrics ORDER BY roi DESC LIMIT ?"
            worst_query = "SELECT * FROM daily_metrics ORDER BY roi ASC LIMIT ?"
            
            best_days = pd.read_sql_query(best_query, conn, params=(limit,))
            worst_days = pd.read_sql_query(worst_query, conn, params=(limit,))
            
            return {'best': best_days, 'worst': worst_days}
    
    def migrate_csv_data(self, csv_path: str = "data/paper_metrics.csv") -> bool:
        """
        Migrate existing CSV data to database
        
        Args:
            csv_path: Path to existing CSV file
            
        Returns:
            bool: Success status
        """
        if not os.path.exists(csv_path):
            logging.info(f"No CSV file found at {csv_path}")
            return False
        
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            
            # Ensure required columns exist
            required_cols = ['date', 'total_trades', 'win_rate', 'roi']
            if not all(col in df.columns for col in required_cols):
                logging.error("CSV missing required columns")
                return False
            
            # Add missing columns with defaults
            df['winners'] = df.get('winners', (df['total_trades'] * df['win_rate'] / 100).astype(int))
            df['losers'] = df['total_trades'] - df['winners']
            df['total_stake'] = df.get('total_stake', df['total_trades'] * 10)  # Assume $10 per trade
            df['total_profit'] = df.get('total_profit', df['total_stake'] * df['roi'] / 100)
            df['average_odds'] = df.get('average_odds', 1.91)  # Default odds
            
            # Insert each row
            for _, row in df.iterrows():
                self.insert_daily_metrics(row.to_dict())
            
            logging.info(f"Successfully migrated {len(df)} rows from CSV")
            
            # Backup CSV
            backup_path = csv_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d")}.csv')
            os.rename(csv_path, backup_path)
            logging.info(f"CSV backed up to {backup_path}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error migrating CSV data: {e}")
            return False
    
    def generate_weekly_summary(self):
        """Generate and store weekly summaries"""
        query = """
            SELECT 
                DATE(date, 'weekday 0', '-6 days') as week_start,
                DATE(date, 'weekday 0') as week_end,
                COUNT(*) as total_trades,
                AVG(win_rate) as win_rate,
                SUM(total_profit) as total_profit,
                AVG(roi) as roi
            FROM daily_metrics
            GROUP BY week_start
        """
        
        with sqlite3.connect(self.db_path) as conn:
            weekly_data = pd.read_sql_query(query, conn)
            
            for _, week in weekly_data.iterrows():
                # Find best and worst days in the week
                week_metrics = self.get_metrics_range(week['week_start'], week['week_end'])
                
                if not week_metrics.empty:
                    best_day = week_metrics.loc[week_metrics['roi'].idxmax(), 'date']
                    worst_day = week_metrics.loc[week_metrics['roi'].idxmin(), 'date']
                else:
                    best_day = worst_day = None
                
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO weekly_summary 
                    (week_start, week_end, total_trades, win_rate, total_profit, roi, best_day, worst_day)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    week['week_start'], week['week_end'], week['total_trades'],
                    week['win_rate'], week['total_profit'], week['roi'],
                    best_day, worst_day
                ))
            
            conn.commit()


# Example usage script
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    db = MetricsDatabase()
    
    # Migrate existing CSV data
    db.migrate_csv_data()
    
    # Example: Insert new metrics
    sample_metrics = {
        'date': '2024-01-15',
        'total_trades': 10,
        'winners': 6,
        'losers': 4,
        'win_rate': 60.0,
        'total_stake': 100.0,
        'total_profit': 15.5,
        'roi': 15.5,
        'average_odds': 1.91
    }
    
    db.insert_daily_metrics(sample_metrics)
    
    # Query recent metrics
    recent = db.get_metrics_range('2024-01-01', '2024-01-31')
    print("\nRecent metrics:")
    print(recent)
    
    # Generate weekly summaries
    db.generate_weekly_summary()
