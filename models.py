from extensions import db, bcrypt
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from werkzeug.security import generate_password_hash, check_password_hash
import json
import uuid

# User Product Collection (many-to-many relationship)
class UserProduct(db.Model):
    __tablename__ = 'user_products'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)  # Optional notes like purchase date, shade, etc.
    expiration_date = db.Column(db.Date, nullable=True)
    last_used = db.Column(db.DateTime, nullable=True)
    usage_count = db.Column(db.Integer, default=0)
    purchase_date = db.Column(db.Date, nullable=True)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id'),)
    
    def to_dict(self):
        from datetime import date
        days_until_expiry = None
        is_expiring_soon = False
        is_expired = False
        
        if self.expiration_date:
            days_until_expiry = (self.expiration_date - date.today()).days
            is_expiring_soon = 0 <= days_until_expiry <= 30
            is_expired = days_until_expiry < 0
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'notes': self.notes,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'usage_count': self.usage_count or 0,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'days_until_expiry': days_until_expiry,
            'is_expiring_soon': is_expiring_soon,
            'is_expired': is_expired
        }

# Look History - Track user's tried looks and ratings
class LookHistory(db.Model):
    __tablename__ = 'look_history'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    look_id = db.Column(db.Integer, db.ForeignKey('looks.id'), nullable=False)
    tried_at = db.Column(db.DateTime, default=datetime.utcnow)
    rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    notes = db.Column(db.Text, nullable=True)  # User notes about the look
    difficulty_rating = db.Column(db.String(20), nullable=True)  # 'easy', 'medium', 'hard'
    time_taken = db.Column(db.Integer, nullable=True)  # Actual time taken in minutes
    completed_instructions = db.Column(JSON, nullable=True)  # Array of completed instruction indices [0, 1, 2, ...]
    
    __table_args__ = (db.UniqueConstraint('user_id', 'look_id'),)
    
    def to_dict(self):
        look = Look.query.get(self.look_id)
        return {
            'id': self.id,
            'user_id': self.user_id,
            'look_id': self.look_id,
            'look_name': look.name if look else None,
            'look_image': look.image_url if look else None,
            'tried_at': self.tried_at.isoformat() if self.tried_at else None,
            'rating': self.rating,
            'notes': self.notes,
            'difficulty_rating': self.difficulty_rating,
            'time_taken': self.time_taken,
            'completed_instructions': self.completed_instructions or []
        }

# User Model
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256))
    remember_token = db.Column(db.String(100), unique=True, nullable=True)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def generate_remember_token(self):
        self.remember_token = bcrypt.generate_password_hash(str(datetime.utcnow())).decode('utf-8')
        return self.remember_token

    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "id": self.id,
            "email": self.email,
        }

class Consultation(db.Model):
    __tablename__ = 'consultations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    answers_json = db.Column(db.Text, nullable=False)  # Store answers as JSON string
    result_json = db.Column(db.Text, nullable=False)  # Store result as JSON string
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id, answers, result, status='completed'):
        self.user_id = user_id
        self.answers_json = json.dumps(answers)  # Convert dict to JSON string
        self.result_json = json.dumps(result)    # Convert dict to JSON string
        self.status = status
    
    @property
    def answers(self):
        return json.loads(self.answers_json)
    
    @property
    def result(self):
        return json.loads(self.result_json)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'answers': self.answers,
            'result': self.result,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_satisfied = db.Column(db.Boolean, nullable=False)
    has_purchased = db.Column(db.Boolean, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('feedbacks', lazy=True))
    consultation = db.relationship('Consultation', backref=db.backref('feedback', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'consultation_id': self.consultation_id,
            'user_id': self.user_id,
            'is_satisfied': self.is_satisfied,
            'has_purchased': self.has_purchased,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class Look(db.Model):
    __tablename__ = 'looks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    makeup_category = db.Column(db.String(100), nullable=True)  # Store multiple categories ('labbra,occhi,fondo') as comma-separated string
    author = db.Column(db.String(100), nullable=True)
    artist_instruction = db.Column(db.Text, nullable=True)  # Optional
    artist_instruction_title = db.Column(db.String(200), nullable=True)  # Optional, can't exist without artist_instruction
    instructions = db.Column(JSON, nullable=True)  # Store step-by-step instructions as JSON
    tags = db.Column(db.String(255), nullable=True)  # Comma-separated tags
    # Keep as string but make it longer to accommodate multiple URLs
    image_url = db.Column(db.String(2000), nullable=False)  # Store multiple URLs as comma-separated string
    expertise_required = db.Column(db.String(20), nullable=True)  # Optional
    application_time = db.Column(db.Integer, nullable=True)  # Optional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    archetypes = db.relationship('Archetype', secondary='archetype_look_association', back_populates='looks')
    products = db.relationship('Product', secondary='look_product_association', back_populates='looks')
    
    @property
    def product_count(self):
        """Return the number of products associated with this look"""
        return len(self.products)
    
    @property
    def image_urls(self):
        """Parse the comma-separated image_url string into a list"""
        if not self.image_url:
            return []
        return [url.strip() for url in self.image_url.split(',')]
    
    @property
    def cover_image(self):
        """Return the first image URL (cover image)"""
        urls = self.image_urls
        return urls[0] if urls else None
    
    @property
    def makeup_categories(self):
        """Parse the comma-separated makeup_category string into a list"""
        if not self.makeup_category:
            return []
        return [category.strip() for category in self.makeup_category.split(',')]
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'makeup_category': self.makeup_categories,  # Return as list
            'author': self.author,
            'artist_instruction': self.artist_instruction,
            'artist_instruction_title': self.artist_instruction_title,
            'instructions': self.instructions,
            'tags': self.tags.split(',') if self.tags else [],
            'image_url': self.image_urls,  # Return as list
            'cover_image': self.cover_image,
            'expertise_required': self.expertise_required,
            'application_time': self.application_time,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'products': [product.to_dict() for product in self.products],
            'product_count': self.product_count
        }

# Add the association table
class ArchetypeLookAssociation(db.Model):
    __tablename__ = 'archetype_look_association'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    archetype_id = db.Column(db.Integer, db.ForeignKey('archetypes.id'), nullable=False)
    look_id = db.Column(db.Integer, db.ForeignKey('looks.id'), nullable=False)
    category = db.Column(db.String(20), nullable=False)  # 'MORNING', 'EVENING', 'SPECIAL_OCCASION'
    
    __table_args__ = (db.UniqueConstraint('archetype_id', 'look_id'),)

# Update Archetype model to include the relationship
class Archetype(db.Model):
    __tablename__ = 'archetypes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    binary_representation = db.Column(db.String(5), nullable=False, unique=True)

    # Add this relationship
    looks = db.relationship('Look', secondary='archetype_look_association', back_populates='archetypes')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'binary_representation': self.binary_representation,
            'looks': [look.to_dict() for look in self.looks]
        }

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)  # 'foundation', 'blush', 'lipstick', etc.
    image_url = db.Column(db.String(500), nullable=False)
    product_url = db.Column(db.String(500), nullable=True)  # Link to NARS product page
    
    # Shade information stored as JSON
    # Format: {"shades": [{"name": "Deauville", "undertones": ["neutral", "cool"], "skin_tones": ["light", "fair"]}]}
    shades_json = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Many-to-many relationship with looks
    looks = db.relationship('Look', secondary='look_product_association', back_populates='products')
    
    @property
    def shades(self):
        """Parse shades from JSON"""
        if self.shades_json:
            return json.loads(self.shades_json)
        return None
    
    def get_recommended_shades(self, user_profile):
        """
        Get recommended shades based on user profile
        user_profile should have: skin_tone, undertone
        """
        if not self.shades or not user_profile:
            return []
        
        skin_tone = user_profile.get('skinTone', '').lower()
        undertone = user_profile.get('undertone', '').lower()
        
        recommended = []
        shades_list = self.shades.get('shades', [])
        
        for shade in shades_list:
            score = 0
            
            # Check undertone match
            if undertone and undertone in [u.lower() for u in shade.get('undertones', [])]:
                score += 2
            
            # Check skin tone match
            if skin_tone and skin_tone in [st.lower() for st in shade.get('skin_tones', [])]:
                score += 2
            
            if score > 0:
                recommended.append({
                    'name': shade.get('name'),
                    'match_score': score,
                    'reason': self._generate_reason(shade, undertone, skin_tone)
                })
        
        # Sort by match score
        recommended.sort(key=lambda x: x['match_score'], reverse=True)
        return recommended
    
    def _generate_reason(self, shade, undertone, skin_tone):
        """Generate a human-readable reason for the recommendation"""
        reasons = []
        
        if undertone and undertone in [u.lower() for u in shade.get('undertones', [])]:
            reasons.append(f"matches your {undertone} undertone")
        
        if skin_tone and skin_tone in [st.lower() for st in shade.get('skin_tones', [])]:
            reasons.append(f"perfect for {skin_tone} skin")
        
        return " and ".join(reasons) if reasons else "recommended for you"
    
    def to_dict(self, user_profile=None):
        base_dict = {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'image_url': self.image_url,
            'product_url': self.product_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'shades': self.shades
        }
        
        # Add personalized shade recommendations if user profile provided
        if user_profile:
            recommended = self.get_recommended_shades(user_profile)
            if recommended:
                base_dict['recommended_shades'] = recommended
                base_dict['has_match'] = True
            else:
                base_dict['has_match'] = False
        
        return base_dict

class LookProductAssociation(db.Model):
    __tablename__ = 'look_product_association'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    look_id = db.Column(db.Integer, db.ForeignKey('looks.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('look_id', 'product_id'),)


class UserWishlist(db.Model):
    __tablename__ = 'user_wishlist'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    occasion = db.Column(db.String(50), default='general')  # birthday, holiday, anniversary, general
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    priority = db.Column(db.Integer, default=0)  # for ordering
    
    # Relationships
    user = db.relationship('User', backref='wishlist_items')
    product = db.relationship('Product')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'product': self.product.to_dict() if self.product else None,
            'occasion': self.occasion,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'notes': self.notes,
            'priority': self.priority
        }


class SeasonalContent(db.Model):
    __tablename__ = 'seasonal_content'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content_type = db.Column(db.String(50), nullable=False)  # trend, holiday, look_of_week
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(500))
    related_look_ids = db.Column(db.Text)  # JSON string of look IDs
    related_product_ids = db.Column(db.Text)  # JSON string of product IDs
    extra_data = db.Column(db.Text)  # JSON for additional data (renamed from metadata)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'content_type': self.content_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'image_url': self.image_url,
            'related_look_ids': json.loads(self.related_look_ids) if self.related_look_ids else [],
            'related_product_ids': json.loads(self.related_product_ids) if self.related_product_ids else [],
            'metadata': json.loads(self.extra_data) if self.extra_data else {},  # Return as 'metadata' for API
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

