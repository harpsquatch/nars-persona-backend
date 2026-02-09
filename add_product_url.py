#!/usr/bin/env python3
"""
Migration script to add product_url column to products table
"""

import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
db_config = {
    'host': os.getenv('MYSQLHOST', 'localhost'),
    'user': os.getenv('MYSQLUSER', 'root'),
    'password': os.getenv('MYSQLPASSWORD', 'mysql'),
    'database': os.getenv('MYSQLDATABASE', 'narsbeauty')
}

def run_migration():
    """Add product_url column to products table"""
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("Connected to MySQL database")
        print("=" * 80)
        
        # Check if column already exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'products' 
            AND COLUMN_NAME = 'product_url'
        """, (db_config['database'],))
        
        exists = cursor.fetchone()[0]
        
        if exists:
            print("\n✅ Column 'product_url' already exists in products table")
        else:
            print("\n🔄 Adding 'product_url' column to products table...")
            
            # Add product_url column
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN product_url VARCHAR(500) NULL
            """)
            
            print("✅ Successfully added 'product_url' column")
        
        # Commit changes
        conn.commit()
        
        # Show current table structure
        cursor.execute("DESCRIBE products")
        columns = cursor.fetchall()
        
        print("\n" + "=" * 80)
        print("\n📋 Current 'products' table structure:")
        print(f"{'Field':<20} {'Type':<30} {'Null':<10} {'Key':<10} {'Default':<20}")
        print("-" * 90)
        for col in columns:
            field, type_, null, key, default = col[:5]
            print(f"{field:<20} {type_:<30} {null:<10} {key:<10} {str(default):<20}")
        
        print("\n" + "=" * 80)
        print("\n✨ Migration complete!")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"\n❌ Database error: {err}")
        raise
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    run_migration()

