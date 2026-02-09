"""
Seed data script for NARS Persona application
Populates the database with archetypes, looks, and products
"""

from app import app, db
from models import Archetype, Look, Product, ArchetypeLookAssociation, LookProductAssociation
import json

# Define archetypes based on the 5-bit binary personality system
ARCHETYPES = [
    {
        "name": "The Minimalist",
        "description": "You appreciate simplicity and clean lines. Your beauty routine is efficient yet effective, focusing on quality over quantity. You prefer natural, subtle looks that enhance your features without overwhelming them.",
        "binary_representation": "00000"
    },
    {
        "name": "The Bold Innovator",
        "description": "You're not afraid to stand out and express yourself through makeup. You love experimenting with colors, textures, and trends. Your confidence shines through your adventurous beauty choices.",
        "binary_representation": "11111"
    },
    {
        "name": "The Classic Elegance",
        "description": "You embody timeless sophistication. Your makeup style is polished and refined, favoring traditional techniques that never go out of style. You appreciate quality and craftsmanship.",
        "binary_representation": "01010"
    },
    {
        "name": "The Creative Artist",
        "description": "Makeup is your canvas. You view beauty as an art form and love to create unique, expressive looks. You're drawn to creative techniques and aren't afraid to break the rules.",
        "binary_representation": "10101"
    },
    {
        "name": "The Natural Glow",
        "description": "You believe in enhancing your natural beauty. Your approach is fresh, dewy, and effortless. You prefer lightweight products that let your skin breathe while giving you a healthy, radiant look.",
        "binary_representation": "00011"
    },
    {
        "name": "The Glamorous",
        "description": "You love drama and luxury. Your makeup is statement-making with bold lips, defined eyes, and flawless skin. You're not afraid to shine and be the center of attention.",
        "binary_representation": "11100"
    },
    {
        "name": "The Versatile Chameleon",
        "description": "You adapt your look to any occasion. You're comfortable with both minimal and bold styles, switching effortlessly between different aesthetics based on your mood and setting.",
        "binary_representation": "01100"
    },
    {
        "name": "The Edgy Rebel",
        "description": "You challenge beauty norms with unconventional choices. Dark, moody, and dramatic looks appeal to you. You use makeup to express your unique personality and aren't bound by traditional rules.",
        "binary_representation": "10010"
    }
]

# Define looks with detailed instructions
LOOKS = [
    {
        "name": "Natural Everyday Glow",
        "makeup_category": "face,lips",
        "author": "NARS Beauty Team",
        "artist_instruction": "Focus on creating a healthy, radiant complexion that looks like you, only better. Use light, buildable coverage and cream products for a dewy finish.",
        "artist_instruction_title": "Pro Tip: Layer for Luminosity",
        "instructions": [
            {"step": 1, "title": "Prep & Prime", "description": "Start with a hydrating primer to create a smooth, glowing base."},
            {"step": 2, "title": "Light Coverage", "description": "Apply tinted moisturizer or light foundation with fingers for a natural finish."},
            {"step": 3, "title": "Conceal Strategically", "description": "Use concealer only where needed - under eyes and on any blemishes."},
            {"step": 4, "title": "Add Warmth", "description": "Apply cream blush to the apples of cheeks and blend upward."},
            {"step": 5, "title": "Highlight", "description": "Dab liquid highlighter on high points of face for a natural glow."},
            {"step": 6, "title": "Finish Lips", "description": "Complete with a tinted lip balm or nude lipstick."}
        ],
        "tags": "natural,everyday,minimal,beginner-friendly",
        "image_url": "https://images.pexels.com/photos/3373714/pexels-photo-3373714.jpeg,https://images.pexels.com/photos/3373718/pexels-photo-3373718.jpeg",
        "expertise_required": "beginner",
        "application_time": 10
    },
    {
        "name": "Bold Red Lip",
        "makeup_category": "lips",
        "author": "François Nars, Founder & Creative Director",
        "artist_instruction": "The key to a perfect red lip is precision and confidence. Choose a red that complements your skin tone and keep the rest of your makeup minimal to let the lips be the star.",
        "artist_instruction_title": "Master the Classic Red",
        "instructions": [
            {"step": 1, "title": "Prep Lips", "description": "Exfoliate and moisturize lips for a smooth canvas."},
            {"step": 2, "title": "Line Precisely", "description": "Use a red lip liner to define your lip shape and prevent feathering."},
            {"step": 3, "title": "Fill In", "description": "Fill lips with liner to create a base for longer wear."},
            {"step": 4, "title": "Apply Lipstick", "description": "Use a lip brush for precise application of red lipstick."},
            {"step": 5, "title": "Blot & Layer", "description": "Blot with tissue and apply a second layer for intensity."},
            {"step": 6, "title": "Clean Edges", "description": "Use concealer on a small brush to clean and perfect the edges."}
        ],
        "tags": "classic,bold,evening,special-occasion",
        "image_url": "https://images.pexels.com/photos/3373723/pexels-photo-3373723.jpeg,https://images.pexels.com/photos/3373730/pexels-photo-3373730.jpeg",
        "expertise_required": "intermediate",
        "application_time": 15
    },
    {
        "name": "Smokey Eye",
        "makeup_category": "eyes",
        "author": "NARS Pro Team",
        "artist_instruction": "Build intensity gradually with the smokey eye. Start light and add depth slowly. The key is blending - take your time to create that signature soft, smudged effect.",
        "artist_instruction_title": "Creating the Perfect Smoke",
        "instructions": [
            {"step": 1, "title": "Prime Eyelids", "description": "Apply eye primer to ensure long-lasting, crease-free color."},
            {"step": 2, "title": "Base Shade", "description": "Apply a medium neutral shade across the entire lid."},
            {"step": 3, "title": "Define Crease", "description": "Use a darker shade in the crease and blend thoroughly."},
            {"step": 4, "title": "Add Depth", "description": "Apply darkest shade to outer V and lower lash line."},
            {"step": 5, "title": "Smoke It Out", "description": "Blend edges softly for that signature smokey effect."},
            {"step": 6, "title": "Highlight", "description": "Add shimmer to inner corner and brow bone."},
            {"step": 7, "title": "Line & Lash", "description": "Apply eyeliner and mascara to complete the look."}
        ],
        "tags": "dramatic,evening,eyes,advanced",
        "image_url": "https://images.pexels.com/photos/3373736/pexels-photo-3373736.jpeg,https://images.pexels.com/photos/3065209/pexels-photo-3065209.jpeg",
        "expertise_required": "advanced",
        "application_time": 25
    },
    {
        "name": "Fresh Dewy Skin",
        "makeup_category": "face",
        "author": "NARS Beauty Team",
        "artist_instruction": "Create luminous, glass-like skin by focusing on hydration and strategic highlighting. Less is more - let your skin shine through.",
        "artist_instruction_title": "Achieving the Dewy Glow",
        "instructions": [
            {"step": 1, "title": "Hydrate", "description": "Apply hydrating serum and moisturizer, let absorb fully."},
            {"step": 2, "title": "Luminous Base", "description": "Mix liquid highlighter with your foundation for an all-over glow."},
            {"step": 3, "title": "Sheer Coverage", "description": "Apply thinly with damp sponge for natural finish."},
            {"step": 4, "title": "Cream Products", "description": "Use cream blush and highlighter for seamless blending."},
            {"step": 5, "title": "Strategic Highlight", "description": "Apply liquid highlighter to high points: cheekbones, bridge of nose, cupid's bow."},
            {"step": 6, "title": "Set Strategically", "description": "Only set T-zone lightly, leave cheeks dewy."}
        ],
        "tags": "natural,glowing,fresh,daytime",
        "image_url": "https://images.pexels.com/photos/3373745/pexels-photo-3373745.jpeg,https://images.pexels.com/photos/3373752/pexels-photo-3373752.jpeg",
        "expertise_required": "beginner",
        "application_time": 15
    },
    {
        "name": "Defined Brows & Lashes",
        "makeup_category": "eyes",
        "author": "NARS Beauty Team",
        "artist_instruction": "Well-groomed brows and defined lashes frame the face beautifully. This look is perfect for days when you want polish without much color.",
        "artist_instruction_title": "Frame Your Features",
        "instructions": [
            {"step": 1, "title": "Brush Brows", "description": "Brush brows upward to see natural shape."},
            {"step": 2, "title": "Fill Sparse Areas", "description": "Use brow pencil with light, hair-like strokes."},
            {"step": 3, "title": "Set Brows", "description": "Apply clear or tinted brow gel."},
            {"step": 4, "title": "Curl Lashes", "description": "Use eyelash curler for 10 seconds."},
            {"step": 5, "title": "Apply Mascara", "description": "Wiggle wand at roots, then sweep through to tips."},
            {"step": 6, "title": "Second Coat", "description": "Apply second coat to outer lashes for added drama."}
        ],
        "tags": "minimal,everyday,eyes,quick",
        "image_url": "https://images.pexels.com/photos/3065280/pexels-photo-3065280.jpeg,https://images.pexels.com/photos/3065281/pexels-photo-3065281.jpeg",
        "expertise_required": "beginner",
        "application_time": 10
    },
    {
        "name": "Bronzed Goddess",
        "makeup_category": "face",
        "author": "NARS Pro Team",
        "artist_instruction": "Create a sun-kissed, sculpted look with strategic bronzer placement. The goal is to look like you've been kissed by the sun, not baked by it.",
        "artist_instruction_title": "Sculpt & Warm",
        "instructions": [
            {"step": 1, "title": "Even Canvas", "description": "Apply foundation or tinted moisturizer."},
            {"step": 2, "title": "Contour", "description": "Apply bronzer to hollows of cheeks, temples, and jawline."},
            {"step": 3, "title": "Add Warmth", "description": "Sweep bronzer across forehead, nose, and chin where sun naturally hits."},
            {"step": 4, "title": "Blend", "description": "Blend thoroughly for a seamless, natural finish."},
            {"step": 5, "title": "Warm Cheeks", "description": "Add peachy-bronze blush to apples of cheeks."},
            {"step": 6, "title": "Highlight", "description": "Add golden highlighter to high points for extra dimension."}
        ],
        "tags": "bronze,sculpted,warm,summer",
        "image_url": "https://images.pexels.com/photos/3065287/pexels-photo-3065287.jpeg,https://images.pexels.com/photos/3065307/pexels-photo-3065307.jpeg",
        "expertise_required": "intermediate",
        "application_time": 20
    },
    {
        "name": "Colorful Eye Statement",
        "makeup_category": "eyes",
        "author": "NARS Creative Team",
        "artist_instruction": "Don't be afraid of color! Start with one bold shade and build from there. Keep the rest of your makeup simple to let the eyes pop.",
        "artist_instruction_title": "Playing with Color",
        "instructions": [
            {"step": 1, "title": "Prime", "description": "Use eye primer for vibrant, long-lasting color."},
            {"step": 2, "title": "Base", "description": "Apply white or light base to make colors pop."},
            {"step": 3, "title": "Main Color", "description": "Pack your chosen bold color on the lid."},
            {"step": 4, "title": "Blend Edges", "description": "Use a transition shade to soften edges."},
            {"step": 5, "title": "Lower Lash", "description": "Bring color to lower lash line for cohesion."},
            {"step": 6, "title": "Define", "description": "Add black liner and mascara to intensify the look."}
        ],
        "tags": "colorful,bold,creative,statement",
        "image_url": "https://images.pexels.com/photos/3065313/pexels-photo-3065313.jpeg,https://images.pexels.com/photos/3065323/pexels-photo-3065323.jpeg",
        "expertise_required": "intermediate",
        "application_time": 20
    },
    {
        "name": "Soft Romantic",
        "makeup_category": "face,eyes,lips",
        "author": "NARS Beauty Team",
        "artist_instruction": "Create a soft, romantic look with rosy tones and gentle definition. This is perfect for daytime events and creates a youthful, fresh appearance.",
        "artist_instruction_title": "Romantic Softness",
        "instructions": [
            {"step": 1, "title": "Luminous Base", "description": "Apply light foundation with radiant finish."},
            {"step": 2, "title": "Soft Pink Cheeks", "description": "Apply pink cream blush to apples of cheeks."},
            {"step": 3, "title": "Neutral Eyes", "description": "Use soft pink and taupe shades on lids."},
            {"step": 4, "title": "Define Gently", "description": "Apply brown liner softly on upper lash line."},
            {"step": 5, "title": "Flutter Lashes", "description": "Apply mascara focusing on length not volume."},
            {"step": 6, "title": "Pink Lips", "description": "Finish with soft pink or nude-pink lipstick."}
        ],
        "tags": "romantic,soft,pink,daytime,special-occasion",
        "image_url": "https://images.pexels.com/photos/3065327/pexels-photo-3065327.jpeg,https://images.pexels.com/photos/3373762/pexels-photo-3373762.jpeg",
        "expertise_required": "beginner",
        "application_time": 15
    }
]

# Sample products
PRODUCTS = [
    {"name": "NARS Natural Radiant Longwear Foundation", "image_url": "https://www.narscosmetics.com/dw/image/v2/AAQP_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw5c5f5a5e/hi-res/0607845024095.jpg"},
    {"name": "NARS Radiant Creamy Concealer", "image_url": "https://www.narscosmetics.com/dw/image/v2/AAQP_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw4b5d4f5e/hi-res/0607845024101.jpg"},
    {"name": "NARS Light Reflecting Setting Powder", "image_url": "https://www.narscosmetics.com/dw/image/v2/AAQP_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw7c8d9e0f/hi-res/0607845094104.jpg"},
    {"name": "NARS Blush in Orgasm", "image_url": "https://www.narscosmetics.com/dw/image/v2/AAQP_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw9d0e1f2g/hi-res/0607845011101.jpg"},
    {"name": "NARS Laguna Bronzing Powder", "image_url": "https://www.narscosmetics.com/dw/image/v2/AAQP_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw1e2f3g4h/hi-res/0607845011118.jpg"},
    {"name": "NARS Velvet Matte Lipstick - Dragon Girl", "image_url": "https://www.narscosmetics.com/dw/image/v2/AAQP_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw5h6i7j8k/hi-res/0607845011125.jpg"},
    {"name": "NARS Powermatte Lip Pigment", "image_url": "https://www.narscosmetics.com/dw/image/v2/AAQP_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw9k0l1m2n/hi-res/0607845011132.jpg"},
    {"name": "NARS Larger Than Life Eyeliner", "image_url": "https://www.narscosmetics.com/dw/image/v2/AAQP_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw3n4o5p6q/hi-res/0607845011149.jpg"},
    {"name": "NARS Climax Mascara", "image_url": "https://www.narscosmetics.com/dw/image/v2/AAQP_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw7q8r9s0t/hi-res/0607845011156.jpg"},
    {"name": "NARS Eyeshadow Palette", "image_url": "https://www.narscosmetics.com/dw/image/v2/AAQP_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw1t2u3v4w/hi-res/0607845011163.jpg"},
    {"name": "NARS Brow Perfector", "image_url": "https://www.narscosmetics.com/dw/image/v2/AAQP_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw5w6x7y8z/hi-res/0607845011170.jpg"},
    {"name": "NARS Light Reflecting Highlighter", "image_url": "https://www.narscosmetics.com/dw/image/v2/AAQP_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw9z0a1b2c/hi-res/0607845011187.jpg"}
]

# Archetype to Look associations with categories
ARCHETYPE_LOOK_ASSOCIATIONS = [
    # The Minimalist (00000)
    {"archetype_binary": "00000", "look_name": "Natural Everyday Glow", "category": "MORNING"},
    {"archetype_binary": "00000", "look_name": "Fresh Dewy Skin", "category": "MORNING"},
    {"archetype_binary": "00000", "look_name": "Defined Brows & Lashes", "category": "EVENING"},
    
    # The Bold Innovator (11111)
    {"archetype_binary": "11111", "look_name": "Bold Red Lip", "category": "EVENING"},
    {"archetype_binary": "11111", "look_name": "Smokey Eye", "category": "EVENING"},
    {"archetype_binary": "11111", "look_name": "Colorful Eye Statement", "category": "SPECIAL_OCCASION"},
    
    # The Classic Elegance (01010)
    {"archetype_binary": "01010", "look_name": "Bold Red Lip", "category": "EVENING"},
    {"archetype_binary": "01010", "look_name": "Soft Romantic", "category": "MORNING"},
    {"archetype_binary": "01010", "look_name": "Defined Brows & Lashes", "category": "MORNING"},
    
    # The Creative Artist (10101)
    {"archetype_binary": "10101", "look_name": "Colorful Eye Statement", "category": "SPECIAL_OCCASION"},
    {"archetype_binary": "10101", "look_name": "Smokey Eye", "category": "EVENING"},
    {"archetype_binary": "10101", "look_name": "Bronzed Goddess", "category": "MORNING"},
    
    # The Natural Glow (00011)
    {"archetype_binary": "00011", "look_name": "Fresh Dewy Skin", "category": "MORNING"},
    {"archetype_binary": "00011", "look_name": "Natural Everyday Glow", "category": "MORNING"},
    {"archetype_binary": "00011", "look_name": "Soft Romantic", "category": "SPECIAL_OCCASION"},
    
    # The Glamorous (11100)
    {"archetype_binary": "11100", "look_name": "Smokey Eye", "category": "EVENING"},
    {"archetype_binary": "11100", "look_name": "Bold Red Lip", "category": "EVENING"},
    {"archetype_binary": "11100", "look_name": "Bronzed Goddess", "category": "SPECIAL_OCCASION"},
    
    # The Versatile Chameleon (01100)
    {"archetype_binary": "01100", "look_name": "Natural Everyday Glow", "category": "MORNING"},
    {"archetype_binary": "01100", "look_name": "Bronzed Goddess", "category": "EVENING"},
    {"archetype_binary": "01100", "look_name": "Soft Romantic", "category": "SPECIAL_OCCASION"},
    
    # The Edgy Rebel (10010)
    {"archetype_binary": "10010", "look_name": "Smokey Eye", "category": "EVENING"},
    {"archetype_binary": "10010", "look_name": "Bold Red Lip", "category": "EVENING"},
    {"archetype_binary": "10010", "look_name": "Colorful Eye Statement", "category": "SPECIAL_OCCASION"},
]

# Look to Product associations (which products are used in which looks)
LOOK_PRODUCT_ASSOCIATIONS = [
    # Natural Everyday Glow
    {"look_name": "Natural Everyday Glow", "product_names": ["NARS Natural Radiant Longwear Foundation", "NARS Radiant Creamy Concealer", "NARS Blush in Orgasm", "NARS Light Reflecting Highlighter"]},
    
    # Bold Red Lip
    {"look_name": "Bold Red Lip", "product_names": ["NARS Velvet Matte Lipstick - Dragon Girl", "NARS Radiant Creamy Concealer"]},
    
    # Smokey Eye
    {"look_name": "Smokey Eye", "product_names": ["NARS Eyeshadow Palette", "NARS Larger Than Life Eyeliner", "NARS Climax Mascara"]},
    
    # Fresh Dewy Skin
    {"look_name": "Fresh Dewy Skin", "product_names": ["NARS Natural Radiant Longwear Foundation", "NARS Light Reflecting Highlighter", "NARS Blush in Orgasm"]},
    
    # Defined Brows & Lashes
    {"look_name": "Defined Brows & Lashes", "product_names": ["NARS Brow Perfector", "NARS Climax Mascara"]},
    
    # Bronzed Goddess
    {"look_name": "Bronzed Goddess", "product_names": ["NARS Natural Radiant Longwear Foundation", "NARS Laguna Bronzing Powder", "NARS Light Reflecting Highlighter", "NARS Blush in Orgasm"]},
    
    # Colorful Eye Statement
    {"look_name": "Colorful Eye Statement", "product_names": ["NARS Eyeshadow Palette", "NARS Larger Than Life Eyeliner", "NARS Climax Mascara"]},
    
    # Soft Romantic
    {"look_name": "Soft Romantic", "product_names": ["NARS Natural Radiant Longwear Foundation", "NARS Blush in Orgasm", "NARS Eyeshadow Palette", "NARS Climax Mascara", "NARS Powermatte Lip Pigment"]},
]


def seed_database():
    """Main function to seed the database"""
    with app.app_context():
        print("Starting database seeding...")
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("\nClearing existing data...")
        ArchetypeLookAssociation.query.delete()
        LookProductAssociation.query.delete()
        Look.query.delete()
        Archetype.query.delete()
        Product.query.delete()
        db.session.commit()
        print("Existing data cleared.")
        
        # Seed Archetypes
        print("\nSeeding archetypes...")
        archetype_map = {}
        for arch_data in ARCHETYPES:
            archetype = Archetype(
                name=arch_data["name"],
                description=arch_data["description"],
                binary_representation=arch_data["binary_representation"]
            )
            db.session.add(archetype)
            db.session.flush()  # Get the ID
            archetype_map[arch_data["binary_representation"]] = archetype
            print(f"  ✓ Created archetype: {archetype.name} ({archetype.binary_representation})")
        db.session.commit()
        
        # Seed Products
        print("\nSeeding products...")
        product_map = {}
        for prod_data in PRODUCTS:
            product = Product(
                name=prod_data["name"],
                image_url=prod_data["image_url"]
            )
            db.session.add(product)
            db.session.flush()
            product_map[prod_data["name"]] = product
            print(f"  ✓ Created product: {product.name}")
        db.session.commit()
        
        # Seed Looks
        print("\nSeeding looks...")
        look_map = {}
        for look_data in LOOKS:
            look = Look(
                name=look_data["name"],
                makeup_category=look_data["makeup_category"],
                author=look_data["author"],
                artist_instruction=look_data["artist_instruction"],
                artist_instruction_title=look_data["artist_instruction_title"],
                instructions=json.dumps(look_data["instructions"]),  # Store as JSON string
                tags=look_data["tags"],
                image_url=look_data["image_url"],
                expertise_required=look_data["expertise_required"],
                application_time=look_data["application_time"]
            )
            db.session.add(look)
            db.session.flush()
            look_map[look_data["name"]] = look
            print(f"  ✓ Created look: {look.name}")
        db.session.commit()
        
        # Seed Archetype-Look Associations
        print("\nCreating archetype-look associations...")
        for assoc in ARCHETYPE_LOOK_ASSOCIATIONS:
            archetype = archetype_map.get(assoc["archetype_binary"])
            look = look_map.get(assoc["look_name"])
            
            if archetype and look:
                association = ArchetypeLookAssociation(
                    archetype_id=archetype.id,
                    look_id=look.id,
                    category=assoc["category"]
                )
                db.session.add(association)
                print(f"  ✓ Associated {archetype.name} with {look.name} ({assoc['category']})")
        db.session.commit()
        
        # Seed Look-Product Associations
        print("\nCreating look-product associations...")
        for assoc in LOOK_PRODUCT_ASSOCIATIONS:
            look = look_map.get(assoc["look_name"])
            
            if look:
                for product_name in assoc["product_names"]:
                    product = product_map.get(product_name)
                    if product:
                        association = LookProductAssociation(
                            look_id=look.id,
                            product_id=product.id
                        )
                        db.session.add(association)
                print(f"  ✓ Associated {len(assoc['product_names'])} products with {look.name}")
        db.session.commit()
        
        print("\n✅ Database seeding completed successfully!")
        print(f"\nSummary:")
        print(f"  - {len(ARCHETYPES)} archetypes")
        print(f"  - {len(LOOKS)} looks")
        print(f"  - {len(PRODUCTS)} products")
        print(f"  - {len(ARCHETYPE_LOOK_ASSOCIATIONS)} archetype-look associations")
        print(f"  - {sum(len(a['product_names']) for a in LOOK_PRODUCT_ASSOCIATIONS)} look-product associations")


if __name__ == "__main__":
    seed_database()

