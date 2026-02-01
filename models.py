from extensions import db, bcrypt
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from werkzeug.security import generate_password_hash, check_password_hash
import json
import uuid

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
    image_url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Many-to-many relationship with looks
    looks = db.relationship('Look', secondary='look_product_association', back_populates='products')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class LookProductAssociation(db.Model):
    __tablename__ = 'look_product_association'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    look_id = db.Column(db.Integer, db.ForeignKey('looks.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('look_id', 'product_id'),)


