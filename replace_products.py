"""
Script to replace old products with new products in all look associations
"""
from app import app, db
from models import Product, Look, LookProductAssociation

def replace_old_with_new_products():
    """
    Replace old products (IDs 1-12) with new products (IDs 13-32) 
    in all look associations
    """
    
    # Mapping of old product ID -> new product ID
    product_mapping = {
        1: 13,  # NARS Natural Radiant Longwear Foundation -> Light Reflecting Foundation
        2: 14,  # NARS Radiant Creamy Concealer -> Radiant Creamy Concealer
        3: 22,  # NARS Light Reflecting Setting Powder -> Setting Powder
        4: 15,  # NARS Blush in Orgasm -> Blush
        5: 21,  # NARS Laguna Bronzing Powder -> Bronzing Powder
        6: 17,  # NARS Velvet Matte Lipstick - Dragon Girl -> Velvet Matte Lip Pencil
        7: 18,  # NARS Powermatte Lip Pigment -> Powermatte Lip Pigment
        8: 20,  # NARS Larger Than Life Eyeliner -> High-Pigment Longwear Eyeliner
        9: 16,  # NARS Climax Mascara -> Climax Mascara
        10: 24, # NARS Eyeshadow Palette -> Eyeshadow Palette
        11: 25, # NARS Brow Perfector -> Brow Perfector
        12: 26, # NARS Light Reflecting Highlighter -> Highlighting Powder
    }
    
    with app.app_context():
        print("\n" + "="*70)
        print("REPLACING OLD PRODUCTS WITH NEW PRODUCTS")
        print("="*70 + "\n")
        
        # Get all current associations
        old_associations = LookProductAssociation.query.all()
        print(f"Found {len(old_associations)} existing associations\n")
        
        # Group associations by look
        look_product_map = {}
        for assoc in old_associations:
            if assoc.look_id not in look_product_map:
                look_product_map[assoc.look_id] = []
            look_product_map[assoc.look_id].append(assoc.product_id)
        
        # Delete all old associations
        print("🗑️  Deleting old associations...")
        LookProductAssociation.query.delete()
        db.session.commit()
        print("✓ Old associations deleted\n")
        
        # Create new associations with mapped products
        print("➕ Creating new associations with updated products...\n")
        
        total_added = 0
        for look_id, old_product_ids in look_product_map.items():
            look = Look.query.get(look_id)
            if not look:
                continue
            
            print(f"Look: {look.name}")
            
            for old_product_id in old_product_ids:
                # Map to new product
                new_product_id = product_mapping.get(old_product_id, old_product_id)
                
                old_product = Product.query.get(old_product_id)
                new_product = Product.query.get(new_product_id)
                
                if not new_product:
                    print(f"  ⚠️  New product ID {new_product_id} not found, skipping")
                    continue
                
                # Create new association
                new_association = LookProductAssociation(
                    look_id=look_id,
                    product_id=new_product_id
                )
                db.session.add(new_association)
                total_added += 1
                
                if old_product_id in product_mapping:
                    print(f"  ✓ Replaced: {old_product.name if old_product else 'Unknown'}")
                    print(f"         -> {new_product.name}")
                else:
                    print(f"  ✓ Kept: {new_product.name}")
            
            print()
        
        # Commit all new associations
        db.session.commit()
        
        print("="*70)
        print(f"✅ Complete! Created {total_added} new associations")
        print("="*70 + "\n")
        
        # Show summary
        print("SUMMARY BY LOOK:")
        print("-"*70)
        for look_id in sorted(look_product_map.keys()):
            look = Look.query.get(look_id)
            associations = LookProductAssociation.query.filter_by(look_id=look_id).all()
            products = [Product.query.get(a.product_id) for a in associations]
            
            print(f"\n{look.name} ({len(products)} products):")
            for p in products:
                if p:
                    print(f"  - {p.name}")

if __name__ == "__main__":
    replace_old_with_new_products()

