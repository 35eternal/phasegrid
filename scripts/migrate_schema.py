#!/usr/bin/env python3
"""
Schema migration script for PhaseGrid paper_slips table
Safely adds confidence_score and closing_line columns
"""

import sqlite3
import os
import sys
import logging
from datetime import datetime
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SchemaMigrator:
    """Handles database schema migrations safely"""
    
    def __init__(self, db_path: str = "data/paper_metrics.db"):
        self.db_path = db_path
        self.backup_dir = "backups/migrations"
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def backup_database(self) -> str:
        """Create a backup of the database before migration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.backup_dir, f"paper_metrics_backup_{timestamp}.db")
        
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"✅ Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            raise
    
    def check_table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        """Check if a table exists in the database"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        return cursor.fetchone() is not None
    
    def get_table_columns(self, conn: sqlite3.Connection, table_name: str) -> list:
        """Get list of columns in a table"""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [col[1] for col in cursor.fetchall()]
    
    def create_paper_slips_table(self, conn: sqlite3.Connection):
        """Create paper_slips table if it doesn't exist"""
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_slips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slip_id TEXT UNIQUE NOT NULL,
                date TEXT NOT NULL,
                player TEXT,
                prop_type TEXT,
                line REAL,
                pick TEXT,
                confidence REAL,
                confidence_score REAL,
                closing_line TEXT,
                result TEXT,
                payout REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indices for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_slip_date ON paper_slips(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_slip_id ON paper_slips(slip_id)")
        
        conn.commit()
        logger.info("✅ Created paper_slips table with all columns")
    
    def add_column_if_not_exists(self, conn: sqlite3.Connection, table_name: str, 
                                column_name: str, column_type: str, default_value=None):
        """Add a column to a table if it doesn't already exist"""
        existing_columns = self.get_table_columns(conn, table_name)
        
        if column_name not in existing_columns:
            cursor = conn.cursor()
            
            # Build ALTER TABLE statement
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default_value is not None:
                alter_sql += f" DEFAULT {default_value}"
            
            try:
                cursor.execute(alter_sql)
                conn.commit()
                logger.info(f"✅ Added column '{column_name}' to table '{table_name}'")
                return True
            except Exception as e:
                logger.error(f"Failed to add column '{column_name}': {e}")
                raise
        else:
            logger.info(f"ℹ️  Column '{column_name}' already exists in table '{table_name}'")
            return False
    
    def migrate_database(self):
        """Run the complete migration"""
        logger.info("🚀 Starting database migration...")
        
        # Check if database exists
        if not os.path.exists(self.db_path):
            logger.info("Database doesn't exist, creating new one...")
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        else:
            # Backup existing database
            self.backup_database()
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Check if paper_slips table exists
            if not self.check_table_exists(conn, 'paper_slips'):
                logger.info("paper_slips table doesn't exist, creating it...")
                self.create_paper_slips_table(conn)
            else:
                # Add new columns if they don't exist
                logger.info("Checking for new columns...")
                
                # Add confidence_score column
                self.add_column_if_not_exists(
                    conn, 'paper_slips', 'confidence_score', 'REAL'
                )
                
                # Add closing_line column
                self.add_column_if_not_exists(
                    conn, 'paper_slips', 'closing_line', 'TEXT'
                )
                
                # Add any other useful columns while we're at it
                self.add_column_if_not_exists(
                    conn, 'paper_slips', 'batch_id', 'TEXT'
                )
                
                self.add_column_if_not_exists(
                    conn, 'paper_slips', 'model_variance', 'REAL'
                )
            
            # Verify migration
            final_columns = self.get_table_columns(conn, 'paper_slips')
            logger.info(f"📋 Final table columns: {', '.join(final_columns)}")
            
            # Run integrity check
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            if integrity_result == 'ok':
                logger.info("✅ Database integrity check passed!")
            else:
                logger.error(f"❌ Database integrity check failed: {integrity_result}")
                raise Exception("Database integrity check failed")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            conn.close()
            raise
        
        finally:
            conn.close()
        
        logger.info("🎉 Migration completed successfully!")
    
    def print_table_info(self):
        """Print current table structure"""
        conn = sqlite3.connect(self.db_path)
        
        if self.check_table_exists(conn, 'paper_slips'):
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(paper_slips)")
            
            print("\n📊 Current paper_slips table structure:")
            print("-" * 80)
            print(f"{'Column':<20} {'Type':<15} {'Not Null':<10} {'Default':<15} {'Primary Key':<12}")
            print("-" * 80)
            
            for col in cursor.fetchall():
                cid, name, dtype, notnull, default, pk = col
                print(f"{name:<20} {dtype:<15} {notnull:<10} {default or 'None':<15} {pk:<12}")
            
            # Get row count
            cursor.execute("SELECT COUNT(*) FROM paper_slips")
            row_count = cursor.fetchone()[0]
            print(f"\nTotal rows: {row_count}")
        else:
            print("❌ paper_slips table does not exist")
        
        conn.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PhaseGrid Schema Migration Tool')
    parser.add_argument('--db-path', type=str, 
                       default='data/paper_metrics.db',
                       help='Path to the database file')
    parser.add_argument('--info', action='store_true',
                       help='Show current table structure without migrating')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without actually doing it')
    
    args = parser.parse_args()
    
    migrator = SchemaMigrator(args.db_path)
    
    if args.info:
        migrator.print_table_info()
    elif args.dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
        # Just check what needs to be done
        conn = sqlite3.connect(args.db_path)
        if migrator.check_table_exists(conn, 'paper_slips'):
            columns = migrator.get_table_columns(conn, 'paper_slips')
            logger.info(f"Current columns: {', '.join(columns)}")
            
            missing = []
            if 'confidence_score' not in columns:
                missing.append('confidence_score (REAL)')
            if 'closing_line' not in columns:
                missing.append('closing_line (TEXT)')
            
            if missing:
                logger.info(f"Would add columns: {', '.join(missing)}")
            else:
                logger.info("No changes needed - all columns exist")
        else:
            logger.info("Would create paper_slips table")
        conn.close()
    else:
        # Run the migration
        try:
            migrator.migrate_database()
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()