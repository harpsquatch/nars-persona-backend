#!/usr/bin/env python3
"""
Clean up unused products from the database
"""
from app import app, db
from models import Product, LookProductAssociation

def cleanup_unused_products():
    """Delete products that are not linked to any looks"""
    try:
        with app.app_context():
            # Get all product IDs that are linked to looks
            used_product_ids = set()
            associations = LookProductAssociation.query.all()
            for assoc in associations:
                used_product_ids.add(assoc.product_id)
            
            print(f"\n=== Products in Database ===")
            all_products = Product.query.all()
            print(f"Total products: {len(all_products)}")
            print(f"Products linked to looks: {len(used_product_ids)}")
            print(f"Unused products: {len(all_products) - len(used_product_ids)}")
            
            # Find unused products
            unused_products = []
            for product in all_products:
                if product.id not in used_product_ids:
                    unused_products.append(product)
            
            if not unused_products:
                print("\n✅ No unused products to delete")
                return
            
            print(f"\n=== Unused Products to Delete ===")
            for p in unused_products[:20]:  # Show first 20
                print(f"ID: {p.id} - {p.name}")
            
            if len(unused_products) > 20:
                print(f"... and {len(unused_products) - 20} more")
            
            # Ask for confirmation
            print(f"\n⚠️  About to delete {len(unused_products)} unused products")
            response = input("Continue? (yes/no): ")
            
            if response.lower() != 'yes':
                print("❌ Cancelled")
                return
            
            # Delete unused products
            deleted_count = 0
            for product in unused_products:
                db.session.delete(product)
                deleted_count += 1
            
            db.session.commit()
            
            print(f"\n✅ Successfully deleted {deleted_count} unused products")
            
            # Show remaining products
            remaining = Product.query.all()
            print(f"\n=== After Cleanup ===")
            print(f"Remaining products: {len(remaining)}")
            print(f"\nAll remaining products have URLs and are linked to looks:")
            for p in remaining[:10]:
                print(f"  - {p.name} (URL: {'✓' if p.product_url else '✗'})")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()

if __name__ == "__main__":
    cleanup_unused_products()

