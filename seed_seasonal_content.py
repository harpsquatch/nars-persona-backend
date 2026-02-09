#!/usr/bin/env python3
"""
Seed script to populate seasonal_content table with sample data
"""

import mysql.connector
import json
from datetime import datetime, date, timedelta
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

def seed_seasonal_content():
    """Seed the seasonal_content table with sample data"""
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("Connected to MySQL database")
        
        # Current date
        today = date.today()
        
        # Sample seasonal content data
        seasonal_data = [
            # Monthly Trend - February 2026
            {
                'title': "Valentine's Romance",
                'description': "Soft pinks, romantic reds, and dewy glows perfect for date nights and celebrations",
                'content_type': 'trend',
                'start_date': date(2026, 2, 1),
                'end_date': date(2026, 2, 28),
                'is_active': True,
                'image_url': 'https://via.placeholder.com/800x400/FFB3BA/FFFFFF?text=Valentine%27s+Romance',
                'related_look_ids': json.dumps([]),
                'related_product_ids': json.dumps([]),
                'metadata': json.dumps({
                    'tags': ['romantic', 'pink', 'red', 'dewy'],
                    'sub_looks': [
                        {'name': 'Rosy Glow Look', 'description': 'Blush-focused, fresh, romantic'},
                        {'name': 'Bold Red Lips', 'description': 'Classic, confident, timeless'}
                    ]
                })
            },
            
            # Holiday - Valentine's Day
            {
                'title': "Valentine's Day - Feb 14",
                'description': "Romantic date night makeup looks ready for you",
                'content_type': 'holiday',
                'start_date': date(2026, 2, 7),
                'end_date': date(2026, 2, 14),
                'is_active': True,
                'image_url': 'https://via.placeholder.com/800x400/E91E63/FFFFFF?text=Valentine%27s+Day',
                'related_look_ids': json.dumps([]),
                'related_product_ids': json.dumps([]),
                'metadata': json.dumps({
                    'icon': '❤️',
                    'cta': 'View Looks'
                })
            },
            
            # Holiday - Spring Fashion Week
            {
                'title': "Spring Fashion Week - Mar 1-7",
                'description': "High fashion editorial looks for the season",
                'content_type': 'holiday',
                'start_date': date(2026, 2, 20),
                'end_date': date(2026, 3, 7),
                'is_active': True,
                'image_url': 'https://via.placeholder.com/800x400/FF9800/FFFFFF?text=Spring+Fashion+Week',
                'related_look_ids': json.dumps([]),
                'related_product_ids': json.dumps([]),
                'metadata': json.dumps({
                    'icon': '⭐',
                    'status': 'Coming Soon'
                })
            },
            
            # Look of the Week - Sunset Glow
            {
                'title': "Sunset Glow",
                'description': "A warm, luminous look featuring NARS's new Light Reflecting Foundation and Orgasm blush. Perfect for winter evenings with a sun-kissed glow.",
                'content_type': 'look_of_week',
                'start_date': today - timedelta(days=3),
                'end_date': today + timedelta(days=4),
                'is_active': True,
                'image_url': 'https://via.placeholder.com/600x400/FCE4EC/000000?text=Sunset+Glow',
                'related_look_ids': json.dumps([]),
                'related_product_ids': json.dumps([]),
                'metadata': json.dumps({
                    'application_time': '15 min',
                    'skill_level': 'Intermediate',
                    'new_products': 4,
                    'tags': ['warm', 'luminous', 'sun-kissed', 'evening']
                })
            },
            
            # Trend Insight
            {
                'title': "Berry Tones & Dewy Skin",
                'description': "This month, berry-toned lips and dewy skin are trending globally. These trends pair perfectly with most archetypes!",
                'content_type': 'trend',
                'start_date': date(2026, 2, 1),
                'end_date': date(2026, 2, 28),
                'is_active': True,
                'image_url': None,
                'related_look_ids': json.dumps([]),
                'related_product_ids': json.dumps([]),
                'metadata': json.dumps({
                    'type': 'insight',
                    'trends': ['berry-toned lips', 'dewy skin']
                })
            }
        ]
        
        # Insert seasonal content
        print("\nInserting seasonal content...")
        insert_query = """
            INSERT INTO seasonal_content 
            (title, description, content_type, start_date, end_date, is_active, image_url, related_look_ids, related_product_ids, extra_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        for content in seasonal_data:
            cursor.execute(insert_query, (
                content['title'],
                content['description'],
                content['content_type'],
                content['start_date'],
                content['end_date'],
                content['is_active'],
                content['image_url'],
                content['related_look_ids'],
                content['related_product_ids'],
                content['metadata']
            ))
            print(f"✓ Added: {content['title']} ({content['content_type']})")
        
        conn.commit()
        
        # Verify data
        print("\n" + "="*60)
        cursor.execute("SELECT COUNT(*) FROM seasonal_content")
        count = cursor.fetchone()[0]
        print(f"Total seasonal content items: {count}")
        
        # Show breakdown by type
        cursor.execute("""
            SELECT content_type, COUNT(*) 
            FROM seasonal_content 
            GROUP BY content_type
        """)
        breakdown = cursor.fetchall()
        print("\nBreakdown by type:")
        for content_type, type_count in breakdown:
            print(f"  - {content_type}: {type_count}")
        
        print("\n✅ Seasonal content seeding completed successfully!")
        
        # Close connection
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"\n❌ Error: {err}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("SEASONAL CONTENT SEEDING")
    print("=" * 60)
    
    success = seed_seasonal_content()
    
    if success:
        print("\n" + "=" * 60)
        print("Seeding completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Seeding failed. Please check the errors above.")
        print("=" * 60)

