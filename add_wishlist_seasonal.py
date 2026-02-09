#!/usr/bin/env python3
"""
Migration script to add user_wishlist and seasonal_content tables
"""

import mysql.connector
from datetime import datetime
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
    """Run the migration to add wishlist and seasonal content tables"""
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("Connected to MySQL database")
        
        # Create user_wishlist table
        print("\n1. Creating user_wishlist table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_wishlist (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                product_id INT NOT NULL,
                occasion VARCHAR(50) DEFAULT 'general',
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                priority INT DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                UNIQUE KEY unique_user_product (user_id, product_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        conn.commit()
        print("✓ user_wishlist table created successfully")
        
        # Create seasonal_content table
        print("\n2. Creating seasonal_content table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seasonal_content (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                content_type VARCHAR(50) NOT NULL,
                start_date DATE,
                end_date DATE,
                is_active BOOLEAN DEFAULT TRUE,
                image_url VARCHAR(500),
                related_look_ids TEXT,
                related_product_ids TEXT,
                extra_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_content_type (content_type),
                INDEX idx_is_active (is_active),
                INDEX idx_date_range (start_date, end_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        conn.commit()
        print("✓ seasonal_content table created successfully")
        
        # Check if tables exist
        print("\n3. Verifying tables...")
        cursor.execute("SHOW TABLES LIKE 'user_wishlist'")
        if cursor.fetchone():
            print("✓ user_wishlist table exists")
        
        cursor.execute("SHOW TABLES LIKE 'seasonal_content'")
        if cursor.fetchone():
            print("✓ seasonal_content table exists")
        
        print("\n✅ Migration completed successfully!")
        
        # Close connection
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"\n❌ Error: {err}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("WISHLIST & SEASONAL CONTENT MIGRATION")
    print("=" * 60)
    
    success = run_migration()
    
    if success:
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Migration failed. Please check the errors above.")
        print("=" * 60)

