"""
Script to assign new products to looks
"""
from app import app, db
from models import Product, Look, LookProductAssociation

def show_products_and_looks():
    """Display all products and looks for reference"""
    with app.app_context():
        products = Product.query.order_by(Product.id).all()
        looks = Look.query.order_by(Look.id).all()
        
        print("\n=== ALL PRODUCTS ===")
        for p in products:
            print(f"ID: {p.id:2d} | {p.name:50s} | Category: {p.category}")
        
        print("\n=== ALL LOOKS ===")
        for look in looks:
            # Get current products for this look
            associations = LookProductAssociation.query.filter_by(look_id=look.id).all()
            product_ids = [a.product_id for a in associations]
            products_in_look = Product.query.filter(Product.id.in_(product_ids)).all() if product_ids else []
            
            print(f"\nID: {look.id} | {look.name}")
            print(f"  Current products ({len(products_in_look)}):")
            for prod in products_in_look:
                print(f"    - [{prod.id}] {prod.name}")

def assign_products_to_look(look_id, product_ids):
    """
    Assign products to a specific look
    
    Args:
        look_id: ID of the look
        product_ids: List of product IDs to assign
    """
    with app.app_context():
        look = Look.query.get(look_id)
        if not look:
            print(f"❌ Look with ID {look_id} not found")
            return
        
        added_count = 0
        skipped_count = 0
        
        for product_id in product_ids:
            product = Product.query.get(product_id)
            if not product:
                print(f"  ⚠️  Product ID {product_id} not found, skipping")
                skipped_count += 1
                continue
            
            # Check if association already exists
            existing = LookProductAssociation.query.filter_by(
                look_id=look_id, 
                product_id=product_id
            ).first()
            
            if existing:
                print(f"  ⚠️  {product.name} already linked to {look.name}, skipping")
                skipped_count += 1
                continue
            
            # Create new association
            association = LookProductAssociation(
                look_id=look_id,
                product_id=product_id
            )
            db.session.add(association)
            added_count += 1
            print(f"  ✓ Added: {product.name}")
        
        db.session.commit()
        print(f"\n✅ Complete! Added {added_count} products to '{look.name}', skipped {skipped_count}")

def assign_products_batch():
    """
    Batch assign products to looks based on categories
    
    Example mappings - customize these based on your needs!
    """
    
    # Define which products go with which looks
    # Format: look_id: [list of product_ids]
    
    assignments = {
        # Natural Everyday Glow (Look ID: 1)
        1: [13, 14, 21, 23],  # Light Reflecting Foundation, Concealer, Bronzer, Powder
        
        # Bold Red Lip (Look ID: 2)
        2: [13, 14, 19, 21],  # Foundation, Concealer, Velvet Lip Pencil, Powder
        
        # Smokey Eye (Look ID: 3)
        3: [13, 14, 16, 18, 21],  # Foundation, Concealer, Mascara, Eyeliner, Powder
        
        # Fresh Dewy Skin (Look ID: 4)
        4: [13, 14, 15, 24],  # Foundation, Concealer, Blush, Highlighting Powder
        
        # Defined Brows & Lashes (Look ID: 5)
        5: [13, 14, 16, 23],  # Foundation, Concealer, Mascara, Brow Perfector
        
        # Bronzed Goddess (Look ID: 6)
        6: [13, 14, 15, 21, 24],  # Foundation, Concealer, Blush, Bronzer, Highlighting
        
        # Colorful Eye Statement (Look ID: 7)
        7: [13, 14, 16, 17, 22],  # Foundation, Concealer, Mascara, Eyeshadow, Palette
        
        # Soft Romantic (Look ID: 8)
        8: [13, 14, 15, 20, 24],  # Foundation, Concealer, Blush, Powermatte Lip, Highlighting
    }
    
    print("\n🔄 Starting batch product assignment...\n")
    
    for look_id, product_ids in assignments.items():
        assign_products_to_look(look_id, product_ids)
        print()

if __name__ == "__main__":
    import sys
    
    print("=" * 70)
    print("NARS Product-Look Assignment Tool")
    print("=" * 70)
    
    # Show current state
    show_products_and_looks()
    
    print("\n" + "=" * 70)
    print("ASSIGNMENT OPTIONS:")
    print("=" * 70)
    print("\nThe script above has example assignments in assign_products_batch()")
    print("Edit the 'assignments' dictionary to customize which products go with which looks")
    print("\nProduct IDs 13-32 are your NEW products")
    print("Product IDs 1-12 are the OLD products")
    print("\nTo run the batch assignment, uncomment the line below:")
    print("\n# assign_products_batch()")
    print("\n" + "=" * 70)
    
    # Uncomment the line below to run batch assignment
    # assign_products_batch()
    
    # Or assign individual products to a look:
    # assign_products_to_look(look_id=1, product_ids=[13, 14, 15])

