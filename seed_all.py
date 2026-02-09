"""
Comprehensive seed script for NARS Persona application
Populates database with archetypes, looks, and products from markdown files
Run this on Railway: railway run python seed_all.py
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

# Looks data from LOOKS_LIST_FOR_S3.md
LOOKS = [
    {
        "name": "Natural Everyday Glow",
        "makeup_category": "FACE,LIPS",
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
        "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/13914926a6a4d3356bba7d58a154e3c8.jpg,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/399ff3c93d8a992a847e436d3d0b27c0.jpg",
        "expertise_required": "beginner",
        "application_time": 10,
        "time_of_day": "MORNING"
    },
    {
        "name": "Bold Red Lip",
        "makeup_category": "LIPS",
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
        "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/65dde589543309e67267094f15a3dcdd.jpg,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/713fbe6ed995f9d882508ef6819aeb3b.jpg",
        "expertise_required": "intermediate",
        "application_time": 15,
        "time_of_day": "EVENING"
    },
    {
        "name": "Smokey Eye",
        "makeup_category": "EYES",
        "author": "NARS Pro Team",
        "artist_instruction": "Build intensity gradually with the smokey eye. Start light and add depth slowly. The key is blending - take your time to create that signature soft, smudged effect.",
        "artist_instruction_title": "Creating the Perfect Smoke",
        "instructions": [
            {"step": 1, "title": "Prime Lids", "description": "Apply eye primer to ensure longevity and prevent creasing."},
            {"step": 2, "title": "Base Shadow", "description": "Apply a neutral base shade all over the lid."},
            {"step": 3, "title": "Build Depth", "description": "Apply medium shade to the crease and outer corner."},
            {"step": 4, "title": "Deepen", "description": "Use darkest shade on outer V and lower lash line."},
            {"step": 5, "title": "Blend Seamlessly", "description": "Blend all shades together with a clean fluffy brush."},
            {"step": 6, "title": "Line & Define", "description": "Line upper lash line with gel or pencil liner."},
            {"step": 7, "title": "Highlight", "description": "Add shimmer to inner corner and brow bone."},
            {"step": 8, "title": "Finish", "description": "Apply multiple coats of volumizing mascara."}
        ],
        "tags": "dramatic,evening,eyes,advanced",
        "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/15de99e030251fce5cf31224678fb758.jpg,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/384b97256684b660fca7f374e4a9b69e.jpg",
        "expertise_required": "advanced",
        "application_time": 25,
        "time_of_day": "EVENING"
    },
    {
        "name": "Fresh Dewy Skin",
        "makeup_category": "FACE",
        "author": "NARS Beauty Team",
        "artist_instruction": "The secret to dewy skin is strategic product placement and the right formulas. Focus on cream and liquid products that mimic skin's natural moisture.",
        "artist_instruction_title": "Achieve That Glow",
        "instructions": [
            {"step": 1, "title": "Hydrate", "description": "Start with a moisturizing serum or face oil."},
            {"step": 2, "title": "Luminous Base", "description": "Apply a dewy primer focusing on dry areas."},
            {"step": 3, "title": "Light Foundation", "description": "Use a luminous foundation with a damp sponge."},
            {"step": 4, "title": "Cream Blush", "description": "Apply cream blush to cheeks while foundation is still fresh."},
            {"step": 5, "title": "Strategic Highlight", "description": "Apply liquid highlighter to high points - cheekbones, nose, cupid's bow."},
            {"step": 6, "title": "Set Strategically", "description": "Only set T-zone with translucent powder if needed."}
        ],
        "tags": "natural,glowing,fresh,daytime",
        "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/83fc0432ef91b53cbe8b2ba534c36856.jpg,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/7fd4e5e76e6aa46f29254b31f50f7c02.jpg",
        "expertise_required": "beginner",
        "application_time": 15,
        "time_of_day": "MORNING"
    },
    {
        "name": "Defined Brows & Lashes",
        "makeup_category": "EYES",
        "author": "NARS Beauty Team",
        "artist_instruction": "Well-groomed brows and voluminous lashes can transform your entire face. Focus on enhancing your natural shape rather than completely redrawing.",
        "artist_instruction_title": "Frame Your Face",
        "instructions": [
            {"step": 1, "title": "Brush Brows", "description": "Brush brows upward and outward with a spoolie."},
            {"step": 2, "title": "Fill Sparse Areas", "description": "Use brow pencil to fill any gaps with hair-like strokes."},
            {"step": 3, "title": "Set Brows", "description": "Apply clear or tinted brow gel to hold shape."},
            {"step": 4, "title": "Curl Lashes", "description": "Use an eyelash curler at the base of lashes."},
            {"step": 5, "title": "Mascara", "description": "Apply mascara in zigzag motion from root to tip."},
            {"step": 6, "title": "Lower Lashes", "description": "Lightly coat lower lashes with mascara."}
        ],
        "tags": "minimal,everyday,eyes,quick",
        "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/9f23dab271821061f36024ea95350a6a.jpg,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/a41cce1a05ff37c7e93102dd9d9d7c5e.jpg",
        "expertise_required": "beginner",
        "application_time": 10,
        "time_of_day": "MORNING"
    },
    {
        "name": "Bronzed Goddess",
        "makeup_category": "FACE",
        "author": "NARS Pro Team",
        "artist_instruction": "Achieve that sun-kissed glow by strategically placing bronzer where the sun naturally hits your face. The key is to blend, blend, blend for a seamless finish.",
        "artist_instruction_title": "Sculpt with Warmth",
        "instructions": [
            {"step": 1, "title": "Prep Skin", "description": "Apply foundation and concealer as usual."},
            {"step": 2, "title": "Bronzer Placement", "description": "Apply bronzer to temples, cheekbones, and jawline in a '3' shape."},
            {"step": 3, "title": "Blend", "description": "Blend out any harsh lines with a fluffy brush."},
            {"step": 4, "title": "Add Warmth", "description": "Sweep bronzer across nose bridge and chin."},
            {"step": 5, "title": "Golden Glow", "description": "Apply golden highlighter to high points."},
            {"step": 6, "title": "Warm Lips", "description": "Finish with a nude or peachy lip color."}
        ],
        "tags": "bronze,sculpted,warm,summer",
        "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Light%20Smokey%20-%20occhi-sera.png,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Louminos%20Look%20-%20Labra-giorno.png",
        "expertise_required": "intermediate",
        "application_time": 20,
        "time_of_day": "SPECIAL_OCCASION"
    },
    {
        "name": "Colorful Eye Statement",
        "makeup_category": "EYES",
        "author": "NARS Creative Team",
        "artist_instruction": "Don't be afraid of color! The trick is to start with a good base and build intensity gradually. Choose colors that complement your eye color.",
        "artist_instruction_title": "Bold Color Application",
        "instructions": [
            {"step": 1, "title": "Prime", "description": "Use eye primer to make colors pop and last longer."},
            {"step": 2, "title": "Transition Shade", "description": "Apply a neutral transition shade in the crease."},
            {"step": 3, "title": "Main Color", "description": "Pack your chosen vibrant color onto the lid."},
            {"step": 4, "title": "Deepen Crease", "description": "Use a deeper version of your main color in the crease."},
            {"step": 5, "title": "Lower Lash Line", "description": "Apply color to lower lash line for cohesion."},
            {"step": 6, "title": "Inner Corner", "description": "Add shimmer or lighter shade to inner corner."},
            {"step": 7, "title": "Clean Up", "description": "Clean up any fallout with concealer."},
            {"step": 8, "title": "Mascara", "description": "Finish with black mascara to define lashes."}
        ],
        "tags": "colorful,bold,creative,statement",
        "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/c2be61f3d6bcd004979ea51b1f61a72c.jpg,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/f06e1c90ac8722892dd31c9ef126c3d9.jpg",
        "expertise_required": "intermediate",
        "application_time": 20,
        "time_of_day": "SPECIAL_OCCASION"
    },
    {
        "name": "Soft Romantic",
        "makeup_category": "FACE,EYES,LIPS",
        "author": "NARS Beauty Team",
        "artist_instruction": "Create a dreamy, romantic look with soft pinks and subtle shimmer. The goal is to look naturally flushed and radiant, like you're in love.",
        "artist_instruction_title": "Romantic Radiance",
        "instructions": [
            {"step": 1, "title": "Flawless Base", "description": "Apply light, dewy foundation for a fresh complexion."},
            {"step": 2, "title": "Rosy Cheeks", "description": "Apply pink cream blush to the apples of cheeks."},
            {"step": 3, "title": "Soft Eyes", "description": "Apply champagne or rose gold shimmer to lids."},
            {"step": 4, "title": "Define Softly", "description": "Use soft brown in the crease for gentle definition."},
            {"step": 5, "title": "Pink Lips", "description": "Apply a rosy pink lipstick or gloss."},
            {"step": 6, "title": "Glow", "description": "Add champagne highlighter to cheekbones and cupid's bow."}
        ],
        "tags": "romantic,soft,pink,daytime,special-occasion",
        "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/f3d0fbdbaa122760f04239395d37520f.jpg,https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/Looks/5509766f914628cc4ef465d45148aeb1.jpg",
        "expertise_required": "beginner",
        "application_time": 15,
        "time_of_day": "SPECIAL_OCCASION"
    }
]

# Products data from PRODUCTS_DATA.md
PRODUCTS = [
    {"name": "Mini Radiant Creamy Concealer", "category": "Face", "image_url": "https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw64f68406/hi-res/0607845019787.jpg", "product_url": "https://www.narscosmetics.com/USA/mini-radiant-creamy-concealer/999NAC0000103.html"},
    {"name": "The Multiple Mini Duo", "category": "Face", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/NARS_SP26_IncrementalBundle_PDPCrop_Soldier_withCRTN_MiniMultipleSet_OrgasmCrave_DolceVita_GLBL_2000x2000.webp", "product_url": "https://www.narscosmetics.com/USA/the-multiple-mini-duo/999NAC0000284.html"},
    {"name": "Lipstick", "category": "Cheeks", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/0607845029694.webp", "product_url": "https://www.narscosmetics.com/USA/original-lipstick/999NAC0000104.html"},
    {"name": "Sheer Glow Foundation", "category": "Face", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/0607845060499.webp", "product_url": "https://www.narscosmetics.com/USA/sheer-glow-foundation/999NACSGLWF01.html"},
    {"name": "Natural Radiant Longwear", "category": "Lips", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/0607845066279.webp", "product_url": "https://www.narscosmetics.com/USA/natural-radiant-longwear-foundation/999NAC0000065.html"},
    {"name": "Explicit Lipstick", "category": "Lips", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/0607845066279.webp", "product_url": "https://www.narscosmetics.com/USA/explicit-lipstick/999NAC0000221.html"},
    {"name": "Kaia x NARS Favorites Set", "category": "Eyes", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/999NAC0000221_Soldier_Open_Closed_Unrestrained.webp", "product_url": "https://www.narscosmetics.com/USA/kaia-x-nars-favorites-set/kaiaxnarsfavoritesset.html"},
    {"name": "Light Reflecting™ Prismatic Powder - Pressed", "category": "Eyes", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/kaiaxnarsfavoritesset_1.webp", "product_url": "https://www.narscosmetics.com/USA/light-reflecting%E2%84%A2-prismatic-powder---pressed/999NAC0000257.html"},
    {"name": "The Multiple", "category": "Face", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/LRFPowder_3.webp", "product_url": "https://www.narscosmetics.com/USA/the-multiple/999NAC0000269.html"},
    {"name": "Powder Blush", "category": "Face", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/LRFPowder_3.webp", "product_url": "https://www.narscosmetics.com/USA/powder-blush/999NAC0000192.html"},
    {"name": "Light Reflecting™ Luminizing Powder", "category": "Lips", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/NARS_SP26_DeeplyBloomingCollection_PDPCrop_Blush_SoldierSwatch_NeverEnough_GLBL.webp", "product_url": "https://www.narscosmetics.com/USA/light-reflecting%E2%84%A2-luminizing-powder/999NAC0000263.html"},
    {"name": "Powermatte Lipstick", "category": "Eyes", "image_url": "https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw4ce7ac65/2023/October/PowermatteLipstick/0194251139920_PMLS_StartMeUp_1.jpg", "product_url": "https://www.narscosmetics.com/USA/powermatte-lipstick/999NAC0000147.html"},
    {"name": "Light Reflecting™ Setting Powder - Pressed", "category": "Eyes", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/NARS_SP26_IncrementalBundle_PDPCrop_Soldier_withCRTN_MiniMultipleSet_OrgasmCrave_DolceVita_GLBL_2000x2000.webp", "product_url": "https://www.narscosmetics.com/USA/light-reflecting-pressed-setting-powder/999NAC0000099.html"},
    {"name": "Light Reflecting™ Prismatic Powder - Pressed", "category": "Face", "image_url": "https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dwc938185b/2025/July/LRFPowder/LRFPowder_3.jpg", "product_url": "https://www.narscosmetics.com/USA/light-reflecting%E2%84%A2-prismatic-powder---pressed/999NAC0000257.html"},
    {"name": "Explicit Lipstick", "category": "Lips", "image_url": "https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw308e6ac4/2025/July/ExplicitLipstick/Soldier/NARS_FA25_BeautyInBloom_PDPCrop_Soldier_Swatch_ExplicitLipstick_LoveGame_GLBL.jpg", "product_url": "https://www.narscosmetics.com/USA/explicit-lipstick/999NAC0000268.html"},
    {"name": "Laguna Bronzing Powder", "category": "Tools", "image_url": "https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw299f43fd/2023/March/Makeup/LagunaBronzer/Swatches/999NAC0000155_BronzingPowder_Laguna02_1.jpg", "product_url": "https://www.narscosmetics.com/USA/laguna-bronzing-powder/999NAC0000155.html"},
    {"name": "Light Reflecting™ Luminizing Powder", "category": "Face", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/NARS_SU25_LightReflectingLuminizingPowder_PDPCrop_Soldier_Eros_GLBL_2000x2000.jpg", "product_url": "https://www.narscosmetics.com/USA/light-reflecting%E2%84%A2-luminizing-powder/999NAC0000263.html"},
    {"name": "Total Seduction Eyeshadow Stick", "category": "Face", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/NARS_SU25_TheHotEscape_PDPCrop_TotalSeductionEyeshadowStick_SoldierSwatch_Orgasm_GLBL_2000x2000.webp", "product_url": "https://www.narscosmetics.eu/en/total-seduction-eyeshadow-stick/0194251147000.html"},
    {"name": "Afterglow Lip Balm", "category": "Tools", "image_url": "https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dwd4db353f/2025/December/AfterglowLipBalm/Default/NARS_SP26_AfterglowLipBalm_PDPCrop_Soldier_Swatch_Orgasm_Sephora_US_2000x2000.jpg", "product_url": "https://www.narscosmetics.com/USA/afterglow-lip-balm/999NAC0000283.html"},
    {"name": "Afterglow Sensual Shine Lipstick", "category": "Tools", "image_url": "https://sykoniyfqdaggmtcarkr.supabase.co/storage/v1/object/public/NARS/products/NARS_SP26_DeeplyBloomingCollection_PDPCrop_AfterglowSensualShineLipstick_SoldierSwatch_FIRSTMOVE_GLBL.webpNARS_SU25_TheLipEdit_PDPCrop_Soldier_Swatch_AfterglowLipShine_DolceVita_GLBL.webp", "product_url": "https://www.narscosmetics.com/USA/afterglow-sensual-shine-lipstick/999NAC0000154.html"}
]

# Product-Look associations (simplified - assign products to relevant looks)
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

def seed_all():
    """Main seeding function"""
    with app.app_context():
        print("=" * 60)
        print("Starting comprehensive database seeding...")
        print("=" * 60)
        
        try:
            # 1. Seed Archetypes
            print("\n[1/5] Seeding Archetypes...")
            archetype_map = {}
            for arch_data in ARCHETYPES:
                existing = Archetype.query.filter_by(name=arch_data['name']).first()
                if existing:
                    print(f"  ✓ Archetype '{arch_data['name']}' already exists")
                    archetype_map[arch_data['name']] = existing
                else:
                    archetype = Archetype(
                        name=arch_data['name'],
                        description=arch_data['description'],
                        binary_representation=arch_data['binary_representation']
                    )
                    db.session.add(archetype)
                    archetype_map[arch_data['name']] = archetype
                    print(f"  + Created archetype: {arch_data['name']}")
            
            db.session.commit()
            print(f"✓ Archetypes seeded: {len(ARCHETYPES)} total")
            
            # 2. Seed Looks
            print("\n[2/5] Seeding Looks...")
            look_map = {}
            for look_data in LOOKS:
                existing = Look.query.filter_by(name=look_data['name']).first()
                if existing:
                    # Update existing look with new data
                    existing.makeup_category = look_data['makeup_category']
                    existing.image_url = look_data['image_url']
                    existing.time_of_day = look_data.get('time_of_day', 'MORNING')
                    existing.instructions = json.dumps(look_data['instructions'])
                    print(f"  ↻ Updated look: {look_data['name']}")
                    look_map[look_data['name']] = existing
                else:
                    look = Look(
                        name=look_data['name'],
                        makeup_category=look_data['makeup_category'],
                        author=look_data['author'],
                        artist_instruction=look_data['artist_instruction'],
                        artist_instruction_title=look_data['artist_instruction_title'],
                        instructions=json.dumps(look_data['instructions']),
                        tags=look_data['tags'],
                        image_url=look_data['image_url'],
                        expertise_required=look_data['expertise_required'],
                        application_time=look_data['application_time'],
                        time_of_day=look_data.get('time_of_day', 'MORNING')
                    )
                    db.session.add(look)
                    look_map[look_data['name']] = look
                    print(f"  + Created look: {look_data['name']}")
            
            db.session.commit()
            print(f"✓ Looks seeded: {len(LOOKS)} total")
            
            # 3. Seed Products
            print("\n[3/5] Seeding Products...")
            product_map = {}
            for prod_data in PRODUCTS:
                existing = Product.query.filter_by(name=prod_data['name'], category=prod_data['category']).first()
                if existing:
                    # Update existing product with new data
                    existing.image_url = prod_data['image_url']
                    existing.product_url = prod_data['product_url']
                    print(f"  ↻ Updated product: {prod_data['name']}")
                    product_map[prod_data['name']] = existing
                else:
                    product = Product(
                        name=prod_data['name'],
                        category=prod_data['category'],
                        image_url=prod_data['image_url'],
                        product_url=prod_data['product_url']
                    )
                    db.session.add(product)
                    product_map[prod_data['name']] = product
                    print(f"  + Created product: {prod_data['name']}")
            
            db.session.commit()
            print(f"✓ Products seeded: {len(PRODUCTS)} total")
            
            # 4. Associate ALL Looks with ALL Archetypes
            print("\n[4/5] Associating Looks with Archetypes (all-to-all)...")
            associations_created = 0
            for archetype_name, archetype in archetype_map.items():
                for look_name, look in look_map.items():
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
            
            db.session.commit()
            print(f"✓ Archetype-Look associations: {associations_created} created")
            
            # 5. Associate Products with Looks
            print("\n[5/5] Associating Products with Looks...")
            product_associations_created = 0
            for look_name, product_names in LOOK_PRODUCT_MAPPING.items():
                look = look_map.get(look_name)
                if not look:
                    print(f"  ! Warning: Look '{look_name}' not found")
                    continue
                
                for product_name in product_names:
                    product = product_map.get(product_name)
                    if not product:
                        print(f"  ! Warning: Product '{product_name}' not found")
                        continue
                    
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
            
            db.session.commit()
            print(f"✓ Look-Product associations: {product_associations_created} created")
            
            # Summary
            print("\n" + "=" * 60)
            print("DATABASE SEEDING COMPLETE!")
            print("=" * 60)
            print(f"✓ {len(ARCHETYPES)} Archetypes")
            print(f"✓ {len(LOOKS)} Looks")
            print(f"✓ {len(PRODUCTS)} Products")
            print(f"✓ {associations_created} Archetype-Look associations")
            print(f"✓ {product_associations_created} Look-Product associations")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error during seeding: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = seed_all()
    exit(0 if success else 1)

