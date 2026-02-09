#!/usr/bin/env python3
"""
Update existing products with new images from PRODUCTS_DATA.md
"""
from app import app, db
from models import Product

def update_products_with_new_images():
    """Update existing products with new images and names"""
    try:
        with app.app_context():
            # Mapping of old product IDs to new data
            updates = {
                13: {
                    'name': 'Sheer Glow Foundation',
                    'image_url': 'https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/0607845060499.webp',
                    'product_url': 'https://www.narscosmetics.com/USA/sheer-glow-foundation/999NACSGLWF01.html'
                },
                14: {
                    'name': 'Mini Radiant Creamy Concealer',
                    'image_url': 'https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw64f68406/hi-res/0607845019787.jpg',
                    'product_url': 'https://www.narscosmetics.com/USA/mini-radiant-creamy-concealer/999NAC0000103.html'
                },
                15: {
                    'name': 'Powder Blush',
                    'image_url': 'https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/LRFPowder_3.webp',
                    'product_url': 'https://www.narscosmetics.com/USA/powder-blush/999NAC0000192.html?dwvar_999NAC0000192_color=4251173412&cgid=just-arrived'
                },
                16: {
                    'name': 'Climax Mascara',
                    'image_url': 'https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/0607845060499.webp',
                    'product_url': 'https://www.narscosmetics.com/USA/climax-mascara/0607845060499.html'
                },
                17: {
                    'name': 'Explicit Lipstick',
                    'image_url': 'https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw308e6ac4/2025/July/ExplicitLipstick/Soldier/NARS_FA25_BeautyInBloom_PDPCrop_Soldier_Swatch_ExplicitLipstick_LoveGame_GLBL.jpg',
                    'product_url': 'https://www.narscosmetics.com/USA/explicit-lipstick/999NAC0000268.html?dwvar_999NAC0000268_color=4251146218&cgid=just-arrived'
                },
                18: {
                    'name': 'Powermatte Lipstick',
                    'image_url': 'https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw4ce7ac65/2023/October/PowermatteLipstick/0194251139920_PMLS_StartMeUp_1.jpg?sw=856&sh=750&sm=fit',
                    'product_url': 'https://www.narscosmetics.com/USA/powermatte-lipstick/999NAC0000147.html?dwvar_999NAC0000147_color=4251139920&cgid=best-sellers'
                },
                20: {
                    'name': 'Light Reflecting™ Prismatic Powder - Pressed',
                    'image_url': 'https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dwc938185b/2025/July/LRFPowder/LRFPowder_3.jpg',
                    'product_url': 'https://www.narscosmetics.com/USA/light-reflecting%E2%84%A2-prismatic-powder---pressed/999NAC0000257.html?dwvar_999NAC0000257_color=4251156675&cgid=just-arrived'
                },
                21: {
                    'name': 'Laguna Bronzing Powder',
                    'image_url': 'https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw299f43fd/2023/March/Makeup/LagunaBronzer/Swatches/999NAC0000155_BronzingPowder_Laguna02_1.jpg',
                    'product_url': 'https://www.narscosmetics.com/USA/laguna-bronzing-powder/999NAC0000155.html?dwvar_999NAC0000155_color=4251136721&cgid=best-sellers'
                },
                24: {
                    'name': 'Light Reflecting™ Setting Powder - Pressed',
                    'image_url': 'https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/NARS_SP26_IncrementalBundle_PDPCrop_Soldier_withCRTN_MiniMultipleSet_OrgasmCrave_DolceVita_GLBL_2000x2000.webp',
                    'product_url': 'https://www.narscosmetics.com/USA/light-reflecting-pressed-setting-powder/999NAC0000099.html?dwvar_999NAC0000099_color=4251165912&cgid=just-arrived'
                },
                25: {
                    'name': 'Afterglow Lip Balm',
                    'image_url': 'https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dwd4db353f/2025/December/AfterglowLipBalm/Default/NARS_SP26_AfterglowLipBalm_PDPCrop_Soldier_Swatch_Orgasm_Sephora_US_2000x2000.jpg',
                    'product_url': 'https://www.narscosmetics.com/USA/afterglow-lip-balm/999NAC0000283.html?dwvar_999NAC0000283_color=4251154732&cgid=makeup'
                },
                26: {
                    'name': 'Light Reflecting™ Luminizing Powder',
                    'image_url': 'https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/NARS_SU25_LightReflectingLuminizingPowder_PDPCrop_Soldier_Eros_GLBL_2000x2000.jpg',
                    'product_url': 'https://www.narscosmetics.com/USA/light-reflecting%E2%84%A2-luminizing-powder/999NAC0000263.html'
                }
            }
            
            print("\n=== Updating Products ===\n")
            updated_count = 0
            
            for product_id, data in updates.items():
                product = Product.query.get(product_id)
                if product:
                    product.name = data['name']
                    product.image_url = data['image_url']
                    product.product_url = data['product_url']
                    updated_count += 1
                    print(f"✓ Updated ID {product_id}: {data['name']}")
            
            db.session.commit()
            
            print(f"\n✅ Successfully updated {updated_count} products")
            
            # Verify
            print("\n=== Verification ===\n")
            for product_id in list(updates.keys())[:5]:
                product = Product.query.get(product_id)
                if product:
                    print(f"{product.name}")
                    print(f"  Image: {product.image_url[:60]}...")
                    print(f"  URL: {product.product_url[:60]}...")
                    print()
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()

if __name__ == "__main__":
    update_products_with_new_images()

