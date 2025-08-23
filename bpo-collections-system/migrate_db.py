import sqlite3
import os
from datetime import datetime

def migrate_database():
    """
    Migration script to add proof_image_path column to payment_record table
    while preserving all existing data.
    """
    print("Starting database migration...")
    
    # Path to SQLite database
    db_path = os.path.join('instance', 'collections.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return
    
    # Create backup before migration
    backup_path = os.path.join('instance', f'collections_backup_{datetime.now().strftime("%Y%m%d%H%M%S")}.db')
    print(f"Creating backup at {backup_path}")
    
    # Copy the database file as backup
    with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
        dst.write(src.read())
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Beginning migration transaction...")
        # Start a transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Get all table names to check if payment_record exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        if 'payment_record' not in tables:
            raise Exception("payment_record table not found in the database")
        
        # Step 1: Create new table with the updated schema
        print("Creating new table with updated schema...")
        cursor.execute("""
        CREATE TABLE payment_record_new (
            id INTEGER PRIMARY KEY,
            campaign VARCHAR(50) NOT NULL,
            dpd INTEGER NOT NULL,
            loan_id VARCHAR(100) NOT NULL,
            amount FLOAT NOT NULL,
            date_paid DATE NOT NULL,
            operator_name VARCHAR(100) NOT NULL,
            customer_name VARCHAR(100) NOT NULL,
            created_at DATETIME,
            proof_image_path VARCHAR(255)
        )
        """)
        
        # Step 2: Copy data from old table to new table
        print("Copying existing data to new table...")
        cursor.execute("""
        INSERT INTO payment_record_new (id, campaign, dpd, loan_id, amount, date_paid, operator_name, customer_name, created_at)
        SELECT id, campaign, dpd, loan_id, amount, date_paid, operator_name, customer_name, created_at FROM payment_record
        """)
        
        # Step 3: Drop the old table
        print("Dropping old table...")
        cursor.execute("DROP TABLE payment_record")
        
        # Step 4: Rename the new table to the original name
        print("Renaming new table...")
        cursor.execute("ALTER TABLE payment_record_new RENAME TO payment_record")
        
        # Commit the transaction
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        print(f"Error during migration: {str(e)}")
        print("Migration failed. Database rolled back to previous state.")
    finally:
        # Close connection
        conn.close()

if __name__ == "__main__":
    migrate_database()