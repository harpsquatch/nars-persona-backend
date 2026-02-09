"""
Assign all looks to all archetypes with appropriate categories
"""

from app import app, db
from models import Archetype, Look, ArchetypeLookAssociation

# Define which category each look should fall into
LOOK_CATEGORY_MAPPING = {
    "Natural Everyday Glow": "MORNING",
    "Bold Red Lip": "EVENING",
    "Smokey Eye": "EVENING",
    "Fresh Dewy Skin": "MORNING",
    "Defined Brows & Lashes": "MORNING",
    "Bronzed Goddess": "SPECIAL_OCCASION",
    "Colorful Eye Statement": "SPECIAL_OCCASION",
    "Soft Romantic": "MORNING"
}

def assign_all_looks_to_all_archetypes():
    """Assign all looks to all archetypes with appropriate categories"""
    with app.app_context():
        print("Starting to assign all looks to all archetypes...")
        
        # Get all archetypes and looks
        archetypes = Archetype.query.all()
        looks = Look.query.all()
        
        print(f"\nFound {len(archetypes)} archetypes and {len(looks)} looks")
        print(f"This will create {len(archetypes) * len(looks)} associations")
        
        # Clear existing associations
        print("\nClearing existing archetype-look associations...")
        ArchetypeLookAssociation.query.delete()
        db.session.commit()
        print("✓ Cleared existing associations")
        
        # Create new associations
        print("\nCreating new associations...")
        created_count = 0
        
        for archetype in archetypes:
            print(f"\n{archetype.name} ({archetype.binary_representation}):")
            
            for look in looks:
                # Get the category for this look
                category = LOOK_CATEGORY_MAPPING.get(look.name, "MORNING")
                
                # Create the association
                association = ArchetypeLookAssociation(
                    archetype_id=archetype.id,
                    look_id=look.id,
                    category=category
                )
                db.session.add(association)
                created_count += 1
                
                print(f"  ✓ {look.name} → {category}")
            
            db.session.commit()
        
        print("\n" + "="*60)
        print(f"Assignment Summary:")
        print(f"  - Archetypes: {len(archetypes)}")
        print(f"  - Looks: {len(looks)}")
        print(f"  - Total associations created: {created_count}")
        print(f"  - Expected: {len(archetypes) * len(looks)}")
        print("="*60)
        
        # Verify the assignments
        print("\nVerifying assignments...")
        for archetype in archetypes:
            morning_count = ArchetypeLookAssociation.query.filter_by(
                archetype_id=archetype.id, category="MORNING"
            ).count()
            evening_count = ArchetypeLookAssociation.query.filter_by(
                archetype_id=archetype.id, category="EVENING"
            ).count()
            special_count = ArchetypeLookAssociation.query.filter_by(
                archetype_id=archetype.id, category="SPECIAL_OCCASION"
            ).count()
            
            print(f"\n{archetype.name}:")
            print(f"  - MORNING: {morning_count} looks")
            print(f"  - EVENING: {evening_count} looks")
            print(f"  - SPECIAL_OCCASION: {special_count} looks")
            print(f"  - Total: {morning_count + evening_count + special_count} looks")
        
        print("\n✅ All looks have been assigned to all archetypes!")

if __name__ == "__main__":
    assign_all_looks_to_all_archetypes()

