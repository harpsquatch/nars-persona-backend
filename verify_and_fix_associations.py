"""
Verify and fix database associations
Run this to ensure all associations are created
"""

from app import app, db
from models import Archetype, Look, Product, ArchetypeLookAssociation, LookProductAssociation

def verify_and_fix():
    with app.app_context():
        print("=" * 60)
        print("VERIFYING AND FIXING ASSOCIATIONS")
        print("=" * 60)
        
        # Get all entities
        archetypes = Archetype.query.all()
        looks = Look.query.all()
        products = Product.query.all()
        
        print(f"\nFound in database:")
        print(f"  - {len(archetypes)} Archetypes")
        print(f"  - {len(looks)} Looks")
        print(f"  - {len(products)} Products")
        
        if len(archetypes) == 0:
            print("\n❌ No archetypes found! Run seed_all.py first")
            return False
        
        if len(looks) == 0:
            print("\n❌ No looks found! Run seed_all.py first")
            return False
        
        # Check existing associations
        existing_arch_look = ArchetypeLookAssociation.query.count()
        existing_look_prod = LookProductAssociation.query.count()
        
        print(f"\nExisting associations:")
        print(f"  - {existing_arch_look} Archetype-Look associations")
        print(f"  - {existing_look_prod} Look-Product associations")
        
        # Create Archetype-Look associations (all-to-all)
        print("\n[1/2] Creating Archetype-Look associations...")
        associations_created = 0
        for archetype in archetypes:
            for look in looks:
                # Check if association exists
                existing = ArchetypeLookAssociation.query.filter_by(
                    archetype_id=archetype.id,
                    look_id=look.id
                ).first()
                
                if not existing:
                    association = ArchetypeLookAssociation(
                        archetype_id=archetype.id,
                        look_id=look.id
                    )
                    db.session.add(association)
                    associations_created += 1
                    print(f"  + Created: {archetype.name} <-> {look.name}")
        
        if associations_created > 0:
            db.session.commit()
            print(f"✓ Created {associations_created} new Archetype-Look associations")
        else:
            print(f"✓ All Archetype-Look associations already exist")
        
        # Product-Look associations mapping
        LOOK_PRODUCT_MAPPING = {
            "Natural Everyday Glow": ["Mini Radiant Creamy Concealer", "Sheer Glow Foundation", "The Multiple Mini Duo", "Powder Blush"],
            "Bold Red Lip": ["Explicit Lipstick", "Mini Radiant Creamy Concealer"],
            "Smokey Eye": ["Kaia x NARS Favorites Set", "Light Reflecting™ Prismatic Powder - Pressed", "Powermatte Lipstick"],
            "Fresh Dewy Skin": ["Sheer Glow Foundation", "The Multiple", "Light Reflecting™ Luminizing Powder"],
            "Defined Brows & Lashes": ["Light Reflecting™ Setting Powder - Pressed"],
            "Bronzed Goddess": ["Laguna Bronzing Powder", "The Multiple", "Powder Blush"],
            "Colorful Eye Statement": ["Kaia x NARS Favorites Set", "Total Seduction Eyeshadow Stick"],
            "Soft Romantic": ["Sheer Glow Foundation", "Powder Blush", "Afterglow Sensual Shine Lipstick", "Light Reflecting™ Luminizing Powder"]
        }
        
        # Create Look-Product associations
        print("\n[2/2] Creating Look-Product associations...")
        product_associations_created = 0
        
        for look_name, product_names in LOOK_PRODUCT_MAPPING.items():
            look = Look.query.filter_by(name=look_name).first()
            if not look:
                print(f"  ! Warning: Look '{look_name}' not found")
                continue
            
            for product_name in product_names:
                product = Product.query.filter_by(name=product_name).first()
                if not product:
                    print(f"  ! Warning: Product '{product_name}' not found")
                    continue
                
                # Check if association exists
                existing = LookProductAssociation.query.filter_by(
                    look_id=look.id,
                    product_id=product.id
                ).first()
                
                if not existing:
                    association = LookProductAssociation(
                        look_id=look.id,
                        product_id=product.id
                    )
                    db.session.add(association)
                    product_associations_created += 1
                    print(f"  + Created: {look_name} <-> {product_name}")
        
        if product_associations_created > 0:
            db.session.commit()
            print(f"✓ Created {product_associations_created} new Look-Product associations")
        else:
            print(f"✓ All Look-Product associations already exist")
        
        # Final count
        final_arch_look = ArchetypeLookAssociation.query.count()
        final_look_prod = LookProductAssociation.query.count()
        
        print("\n" + "=" * 60)
        print("FINAL RESULTS")
        print("=" * 60)
        print(f"✓ Total Archetype-Look associations: {final_arch_look}")
        print(f"✓ Total Look-Product associations: {final_look_prod}")
        print(f"✓ Expected Archetype-Look: {len(archetypes) * len(looks)}")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    success = verify_and_fix()
    exit(0 if success else 1)

