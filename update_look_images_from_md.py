#!/usr/bin/env python3
"""
Update look images in the database from LOOKS_LIST_FOR_S3.md
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

# Look name to image URLs mapping from LOOKS_LIST_FOR_S3.md
LOOK_UPDATES = {
    "Natural Everyday Glow": [
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/13914926a6a4d3356bba7d58a154e3c8.jpg",
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/399ff3c93d8a992a847e436d3d0b27c0.jpg"
    ],
    "Bold Red Lip": [
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/65dde589543309e67267094f15a3dcdd.jpg",
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/713fbe6ed995f9d882508ef6819aeb3b.jpg"
    ],
    "Smokey Eye": [
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/15de99e030251fce5cf31224678fb758.jpg",
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/384b97256684b660fca7f374e4a9b69e.jpg"
    ],
    "Fresh Dewy Skin": [
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/83fc0432ef91b53cbe8b2ba534c36856.jpg",
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/7fd4e5e76e6aa46f29254b31f50f7c02.jpg"
    ],
    "Defined Brows & Lashes": [
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/9f23dab271821061f36024ea95350a6a.jpg",
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/a41cce1a05ff37c7e93102dd9d9d7c5e.jpg"
    ],
    "Bronzed Goddess": [
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Light%20Smokey%20-%20occhi-sera.png",
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Louminos%20Look%20-%20Labra-giorno.png"
    ],
    "Colorful Eye Statement": [
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/c2be61f3d6bcd004979ea51b1f61a72c.jpg",
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/f06e1c90ac8722892dd31c9ef126c3d9.jpg"
    ],
    "Soft Romantic": [
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/f3d0fbdbaa122760f04239395d37520f.jpg",
        "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/5509766f914628cc4ef465d45148aeb1.jpg"
    ]
}

def update_look_images():
    """Update look images in the database"""
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("Connected to MySQL database")
        print("=" * 80)
        
        # First, show all current looks
        cursor.execute("SELECT id, name, image_url FROM looks ORDER BY name")
        current_looks = cursor.fetchall()
        
        print("\n📋 Current looks in database:")
        for look_id, name, image_url in current_looks:
            print(f"  - ID: {look_id}, Name: '{name}'")
            if image_url:
                print(f"    Current Image: {image_url[:80]}...")
        
        print("\n" + "=" * 80)
        print("\n🔄 Starting image updates...")
        
        updated_count = 0
        not_found_count = 0
        
        # Update each look
        for look_name, image_urls in LOOK_UPDATES.items():
            # Join URLs with comma
            image_url_string = ",".join(image_urls)
            
            # Try to find and update the look
            cursor.execute(
                "SELECT id FROM looks WHERE name = %s",
                (look_name,)
            )
            result = cursor.fetchone()
            
            if result:
                look_id = result[0]
                cursor.execute(
                    "UPDATE looks SET image_url = %s WHERE id = %s",
                    (image_url_string, look_id)
                )
                print(f"\n✅ Updated: '{look_name}' (ID: {look_id})")
                print(f"   Images: {len(image_urls)} URLs")
                for i, url in enumerate(image_urls, 1):
                    print(f"   {i}. {url}")
                updated_count += 1
            else:
                print(f"\n❌ Not found: '{look_name}'")
                not_found_count += 1
        
        # Commit the changes
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"\n✨ Update complete!")
        print(f"   ✅ Updated: {updated_count} looks")
        print(f"   ❌ Not found: {not_found_count} looks")
        
        # Show updated looks
        if updated_count > 0:
            print("\n📸 Verification - Updated looks:")
            cursor.execute(
                "SELECT id, name, image_url FROM looks WHERE name IN (%s)" % 
                ','.join(['%s'] * len(LOOK_UPDATES)),
                tuple(LOOK_UPDATES.keys())
            )
            for look_id, name, image_url in cursor.fetchall():
                print(f"\n  - '{name}' (ID: {look_id})")
                if image_url:
                    urls = image_url.split(',')
                    print(f"    Images: {len(urls)}")
                    for i, url in enumerate(urls, 1):
                        print(f"    {i}. {url}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        
    except mysql.connector.Error as err:
        print(f"\n❌ Database error: {err}")
        raise
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    update_look_images()

