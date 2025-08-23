import os
import sqlite3
from datetime import datetime

def migrate_database():
    """
    Migration script to add DA verification fields to disputes table
    """
    print("Starting database migration for dispute verification...")
    
    # Path to SQLite database
    db_path = os.path.join('instance', 'collections.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return
    
    # Create backup before migration
    backup_path = os.path.join('instance', f'collections_backup_disputes_{datetime.now().strftime("%Y%m%d%H%M%S")}.db')
    print(f"Creating backup at {backup_path}")
    
    # Copy the database file as backup
    with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
        dst.write(src.read())
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Beginning migration transaction...")
        cursor.execute("BEGIN TRANSACTION")
        
        # Add new columns to dispute table
        print("Adding DA verification columns to disputes table...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(dispute)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add columns if they don't exist
        if 'da_verified_by' not in columns:
            cursor.execute("ALTER TABLE dispute ADD COLUMN da_verified_by VARCHAR(100)")
            print("Added da_verified_by column")
        
        if 'da_verified_at' not in columns:
            cursor.execute("ALTER TABLE dispute ADD COLUMN da_verified_at DATETIME")
            print("Added da_verified_at column")
        
        if 'da_comments' not in columns:
            cursor.execute("ALTER TABLE dispute ADD COLUMN da_comments TEXT")
            print("Added da_comments column")
            
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {str(e)}")
        print("Migration failed. Database rolled back to previous state.")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()