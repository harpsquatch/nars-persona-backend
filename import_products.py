"""
Script to import products from PRODUCTS_DATA.md into MySQL database
"""
from app import app, db
from models import Product
import json
import re

def parse_products_file(filepath):
    """Parse the PRODUCTS_DATA.md file and extract product information"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by --- separator
    product_blocks = content.split('---')
    products = []
    
    for block in product_blocks:
        if not block.strip() or 'PRODUCT:' not in block:
            continue
        
        # Extract product information
        product = {}
        
        # Get product name
        name_match = re.search(r'PRODUCT:\s*(.+)', block)
        if name_match:
            product['name'] = name_match.group(1).strip()
        
        # Get category
        category_match = re.search(r'CATEGORY:\s*(.+)', block)
        if category_match:
            product['category'] = category_match.group(1).strip()
        
        # Get image URL
        image_match = re.search(r'IMAGE:\s*(.+)', block)
        if image_match:
            image_url = image_match.group(1).strip()
            if image_url:  # Only add if URL is provided
                product['image_url'] = image_url
        
        # Get product URL (link to NARS website)
        link_match = re.search(r'LINK:\s*(.+)', block)
        if link_match:
            product_url = link_match.group(1).strip()
            if product_url:  # Only add if URL is provided
                product['product_url'] = product_url
        
        # Get description
        desc_match = re.search(r'DESCRIPTION:\s*(.+)', block)
        if desc_match:
            description = desc_match.group(1).strip()
            if description:
                product['description'] = description
        
        # Get shades
        shades_section = re.search(r'SHADES:(.*?)(?=\n\n|\Z)', block, re.DOTALL)
        if shades_section:
            shades_text = shades_section.group(1)
            shades = []
            
            # Parse each shade
            shade_blocks = re.findall(r'- name:\s*"([^"]+)"(.*?)(?=\n\s*-|\Z)', shades_text, re.DOTALL)
            for shade_name, shade_attrs in shade_blocks:
                shade = {'name': shade_name}
                
                # Extract undertone
                undertone_match = re.search(r'undertone:\s*"([^"]+)"', shade_attrs)
                if undertone_match:
                    shade['undertone'] = undertone_match.group(1)
                
                # Extract skin_tone_range
                skin_tone_match = re.search(r'skin_tone_range:\s*"([^"]+)"', shade_attrs)
                if skin_tone_match:
                    shade['skin_tone_range'] = skin_tone_match.group(1)
                
                # Extract description
                desc_match = re.search(r'description:\s*"([^"]+)"', shade_attrs)
                if desc_match:
                    shade['description'] = desc_match.group(1)
                
                shades.append(shade)
            
            if shades:
                product['shades_json'] = json.dumps(shades)
        
        # Only add product if it has required fields
        if 'name' in product and 'category' in product:
            products.append(product)
    
    return products

def import_products(filepath):
    """Import products from file into database"""
    try:
        with app.app_context():
            print(f"Parsing products from {filepath}...")
            products_data = parse_products_file(filepath)
            
            print(f"\nFound {len(products_data)} products")
            print("\nImporting products...")
            
            imported_count = 0
            skipped_count = 0
            updated_count = 0
            
            for product_data in products_data:
                try:
                    # Check if product already exists
                    existing_product = Product.query.filter_by(name=product_data['name']).first()
                    
                    if existing_product:
                        # Update existing product
                        if 'image_url' in product_data:
                            existing_product.image_url = product_data['image_url']
                        if 'product_url' in product_data:
                            existing_product.product_url = product_data['product_url']
                        if 'category' in product_data:
                            existing_product.category = product_data['category']
                        if 'shades_json' in product_data:
                            existing_product.shades_json = product_data['shades_json']
                        
                        updated_count += 1
                        print(f"  ✓ Updated: {product_data['name']}")
                    else:
                        # Create new product
                        new_product = Product(
                            name=product_data['name'],
                            category=product_data['category'],
                            image_url=product_data.get('image_url', ''),
                            product_url=product_data.get('product_url'),
                            shades_json=product_data.get('shades_json')
                        )
                        db.session.add(new_product)
                        imported_count += 1
                        print(f"  ✓ Added: {product_data['name']}")
                
                except Exception as e:
                    print(f"  ✗ Error with {product_data.get('name', 'Unknown')}: {str(e)}")
                    skipped_count += 1
            
            # Commit all changes
            db.session.commit()
            
            print(f"\n{'='*50}")
            print(f"Import completed!")
            print(f"  New products added: {imported_count}")
            print(f"  Products updated: {updated_count}")
            print(f"  Products skipped: {skipped_count}")
            print(f"{'='*50}")
            
    except Exception as e:
        print(f"Error importing products: {e}")
        db.session.rollback()

if __name__ == "__main__":
    import os
    # Get the path to PRODUCTS_DATA.md in the parent directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    products_file = os.path.join(os.path.dirname(script_dir), 'PRODUCTS_DATA.md')
    import_products(products_file)

