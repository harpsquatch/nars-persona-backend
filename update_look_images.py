"""
Update look image URLs in the database with Supabase storage URLs
"""

from app import app, db
from models import Look

# Updated image URLs from Supabase
UPDATED_LOOK_IMAGES = {
    "Natural Everyday Glow": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Alluring%20Look%20-%20base-giorno.png,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Basic%20Eye%20-%20Labbra-giorno.png",
    
    "Bold Red Lip": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Basic%20Eye%20-%20Labbra-giorno(1).png,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/beauty-portrait-young-brunette-woman-with-evening-makeup-perfect-clean-skin-sexy-model-with-curly-hair-posing-studio-with-red-bright-natural-lips.jpg",
    
    "Smokey Eye": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/beauty-portrait-young-brunette-woman-with-evening-makeup-perfect-clean-skin-sexy-model-with-curly-hair-posing-studio-with-red-bright-natural-lips.jpg,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/beauty-portrait-young-brunette-woman-with-evening-makeup-perfect-clean-skin-sexy-model-with-curly-hair-posing-studio-with-red-bright-natural-lips.jpg",
    
    "Fresh Dewy Skin": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Dark%20Bold%20Lip%20-%20labbra-speciale.png,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Defined%20Eye%20-%20occhi-giorno(1).png",
    
    "Defined Brows & Lashes": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Ethereal%20Glow%20-%20base-speciale.png,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Femme%20&%20Feathery%20-%20occhi-speciale.png",
    
    "Bronzed Goddess": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Light%20Smokey%20-%20occhi-sera.png,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Louminos%20Look%20-%20Labra-giorno.png",
    
    "Colorful Eye Statement": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Passionate%20Look%20-%20base-sera.png,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Playful%20Look%20-%20base-speciale.png",
    
    "Soft Romantic": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/portrait-beautiful-asian-woman-holding-makeup-blusher-brush.jpg,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/young-brunette-woman-wearing-white-poloneck-attractive-girl-model-fashion.jpg"
}

def update_look_images():
    """Update all look image URLs with Supabase storage URLs"""
    with app.app_context():
        print("Starting to update look image URLs...")
        print(f"Total looks to update: {len(UPDATED_LOOK_IMAGES)}")
        
        updated_count = 0
        not_found = []
        
        for look_name, new_image_url in UPDATED_LOOK_IMAGES.items():
            # Find the look by name
            look = Look.query.filter_by(name=look_name).first()
            
            if look:
                old_url = look.image_url
                look.image_url = new_image_url
                db.session.commit()
                
                print(f"\n✓ Updated: {look_name}")
                print(f"  Old: {old_url[:80]}...")
                print(f"  New: {new_image_url[:80]}...")
                updated_count += 1
            else:
                print(f"\n✗ Not found: {look_name}")
                not_found.append(look_name)
        
        print("\n" + "="*60)
        print(f"Update Summary:")
        print(f"  - Successfully updated: {updated_count}/{len(UPDATED_LOOK_IMAGES)}")
        
        if not_found:
            print(f"  - Not found in database: {len(not_found)}")
            for name in not_found:
                print(f"    • {name}")
        
        print("="*60)
        print("\n✅ Look image URLs update completed!")

if __name__ == "__main__":
    update_look_images()

