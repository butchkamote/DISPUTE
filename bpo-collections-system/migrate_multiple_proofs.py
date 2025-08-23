import sqlite3
import os
from datetime import datetime

def migrate_database():
    """
    Migration script to add support for multiple payment proofs
    """
    print("Starting database migration for multiple proofs...")
    
    # Path to SQLite database
    db_path = os.path.join('instance', 'collections.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return
    
    # Create backup before migration
    backup_path = os.path.join('instance', f'collections_backup_multi_{datetime.now().strftime("%Y%m%d%H%M%S")}.db')
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
        
        # Get all table names 
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        # Step 1: Check if payment_proof table exists, create if not
        if 'payment_proof' not in tables:
            print("Creating new payment_proof table...")
            cursor.execute("""
            CREATE TABLE payment_proof (
                id INTEGER PRIMARY KEY,
                payment_id INTEGER NOT NULL,
                file_path VARCHAR(255) NOT NULL,
                file_type VARCHAR(50) NOT NULL,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (payment_id) REFERENCES payment_record (id) ON DELETE CASCADE
            )
            """)
        
        # Step 2: Transfer existing proof data if payment_record has proof_image_path
        if 'payment_record' in tables:
            # Check if payment_record has proof_image_path column
            cursor.execute("PRAGMA table_info(payment_record)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'proof_image_path' in columns:
                print("Transferring existing proof data...")
                cursor.execute("""
                INSERT INTO payment_proof (payment_id, file_path, file_type)
                SELECT id, proof_image_path, 'receipt' FROM payment_record 
                WHERE proof_image_path IS NOT NULL AND proof_image_path != ''
                """)
                
                # Step 3: Create new payment_record table without proof_image_path
                print("Creating updated payment_record table...")
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
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Step 4: Copy data to new payment_record table
                print("Copying data to new payment_record table...")
                cursor.execute("""
                INSERT INTO payment_record_new (id, campaign, dpd, loan_id, amount, date_paid, operator_name, customer_name, created_at)
                SELECT id, campaign, dpd, loan_id, amount, date_paid, operator_name, customer_name, created_at FROM payment_record
                """)
                
                # Step 5: Drop old table and rename new one
                print("Replacing payment_record table...")
                cursor.execute("DROP TABLE payment_record")
                cursor.execute("ALTER TABLE payment_record_new RENAME TO payment_record")
            else:
                print("payment_record table doesn't have proof_image_path column, skipping transfer")
        
        # Commit all changes
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