from flask import Flask, request, jsonify, current_app
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from datetime import timedelta, datetime
import os
from dotenv import load_dotenv
from flask_migrate import Migrate
import bcrypt
import json
from sqlalchemy.dialects.postgresql import JSON
import uuid
import secrets
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy import text
import time
import traceback
from functools import wraps

# Import local modules
from models import db, User, Consultation, Feedback, Archetype, Look, ArchetypeLookAssociation, Product
from config import config
from algorithm import calculate_consultation_result
from product_scraper import extract_product_info

# Load environment variables
load_dotenv()

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # CORS Configuration
    if os.getenv('CORS_ENABLED', 'true').lower() == 'true':
        allowed_origins = os.getenv('ALLOWED_ORIGINS', '').split(',')
        CORS(app, 
             resources={r"/*": {
                 "origins": allowed_origins,
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization"]
             }},
             supports_credentials=True
        )
    else:
        # CORS disabled
        CORS(app, resources={r"/*": {"origins": []}})
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)

    # Configure logging
    if not app.debug:
        file_handler = RotatingFileHandler('nars.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('NARS backend startup')

    # Check database connection within app context
    with app.app_context():
        try:
            # Use text() to properly format the SQL query
            db.session.execute(text('SELECT 1'))
            app.logger.info("Database connection successful")
        except Exception as e:
            app.logger.warning(f"Database connection failed: {str(e)}")

    # Add a custom JWT verification function for admin access
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        # Allow normal token verification to proceed
        return False

    # Add a custom identity handler for admin routes
    @jwt.user_identity_loader
    def user_identity_lookup(identity):
        return identity

    # Add a custom claims loader for admin token
    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        # You can add role information here if needed
        return {}

    # Create an admin_required decorator for admin routes
    def admin_required():
        def wrapper(fn):
            @wraps(fn)
            @jwt_required()
            def decorator(*args, **kwargs):
                # Get the current user identity
                current_user_id = get_jwt_identity()
                
                # Check if the user exists in the database
                user = User.query.get(current_user_id)
                
                # List of allowed admin emails
                admin_emails = ['admin@narspersona.com']
                
                # If user exists and is in the admin list, proceed
                if user and user.email in admin_emails:
                    return fn(*args, **kwargs)
                else:
                    return jsonify({"error": "Admin access required"}), 403
            return decorator
        return wrapper

    def get_user_by_email(email):
        return User.query.filter_by(email=email).first()

    def verify_password(db_session, email, password):
        user = get_user_by_email(email)
        if user:
            return bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8'))
        return False

    def create_user(email, password):
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        
        if not data:
            return jsonify({"msg": "Missing JSON in request"}), 400
            
        email = data.get('email')
        password = data.get('password')
        remember_me = data.get('remember_me', False)
        
        if not email or not password:
            return jsonify({"msg": "Missing email or password"}), 400
        
        try:
            user = get_user_by_email(email)
            
            if not user:
                user = create_user(email, password)
            elif not verify_password(db.session, email, password):
                return jsonify({"msg": "Invalid credentials"}), 401
            
            # Set token expiration based on remember_me flag
            expires_delta = timedelta(days=30) if remember_me else timedelta(hours=1)
            access_token = create_access_token(
                identity=str(user.id),
                expires_delta=expires_delta
            )
            
            # Update last login time
            user.last_login = datetime.utcnow()
            
            response_data = {
                "user": {"id": user.id, "email": user.email},
                "access_token": access_token
            }
            
            # Generate and store remember token if remember_me is True
            if remember_me:
                # Generate a secure token
                remember_token = secrets.token_hex(32)
                user.remember_token = remember_token
                response_data["remember_token"] = remember_token
            
            db.session.commit()
            return jsonify(response_data), 200
                
        except Exception as e:
            db.session.rollback()
            print(f"Login error: {str(e)}")
            return jsonify({"msg": "An error occurred"}), 500

    @app.route('/login/token', methods=['POST'])
    def login_with_token():
        data = request.get_json()
        
        if not data:
            return jsonify({"msg": "Missing JSON in request"}), 400
        
        email = data.get('email')
        remember_token = data.get('remember_token')
        
        if not email or not remember_token:
            return jsonify({"msg": "Missing email or token"}), 400
        
        try:
            # Find user by email and token
            user = User.query.filter_by(
                email=email, 
                remember_token=remember_token
            ).first()
            
            if not user:
                return jsonify({"msg": "Invalid token"}), 401
            
            # Check if token is not too old (optional, for added security)
            token_max_age = timedelta(days=30)
            if user.last_login and datetime.utcnow() - user.last_login > token_max_age:
                # Token is too old, invalidate it
                user.remember_token = None
                db.session.commit()
                return jsonify({"msg": "Token expired"}), 401
            
            # Update last login time
            user.last_login = datetime.utcnow()
            
            # Create a new access token
            access_token = create_access_token(
                identity=str(user.id),
                expires_delta=timedelta(days=30)  # Long-lived token for remembered users
            )
            
            # Generate a new remember token for security
            new_remember_token = secrets.token_hex(32)
            user.remember_token = new_remember_token
            
            db.session.commit()
            
            return jsonify({
                "user": {"id": user.id, "email": user.email},
                "access_token": access_token,
                "remember_token": new_remember_token
            }), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Token login error: {str(e)}")
            return jsonify({"msg": "An error occurred"}), 500

    @app.route('/consultations', methods=['POST'])
    @jwt_required()
    def create_consultation():
        try:
            current_user_id = int(get_jwt_identity())
            print(f"User ID from token: {current_user_id}")
            
            data = request.get_json()
            if not data or not isinstance(data, dict):
                return jsonify({
                    "error": "Bad Request",
                    "message": "Invalid JSON format"
                }), 400
            
            if 'answers' not in data:
                return jsonify({
                    "error": "Bad Request",
                    "message": "Missing 'answers' field in request"
                }), 400
            
            answers = data['answers']
            
            required_questions = {f"q{i}" for i in range(1, 11)}
            missing_questions = required_questions - set(answers.keys())
            if missing_questions:
                return jsonify({
                    "error": "Unprocessable Entity",
                    "message": "Missing required questions",
                    "details": list(missing_questions)
                }), 422
            
            valid_answers = {'strongly_agree', 'agree', 'neutral', 'disagree', 'strongly_disagree'}
            for q_num, answer in answers.items():
                if not isinstance(answer, str) or answer.lower() not in valid_answers:
                    return jsonify({
                        "error": "Unprocessable Entity",
                        "message": f"Invalid answer for {q_num}",
                        "valid_options": list(valid_answers)
                    }), 422
            
            result = calculate_consultation_result(answers)
            
            consultation = Consultation(
                user_id=current_user_id,
                answers=answers,
                result=result,
                status='completed'
            )
            
            db.session.add(consultation)
            db.session.commit()
            
            return jsonify({
                "message": "Consultation created successfully",
                "result": result,
                "consultation_id": consultation.id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e)
            }), 500

    @app.route('/consultations', methods=['GET'])
    @jwt_required()
    def get_consultations():
        try:
            current_user_id = int(get_jwt_identity())
            
            # Query consultations for the current user
            consultations = Consultation.query.filter_by(user_id=current_user_id).order_by(Consultation.created_at.desc()).all()
            
            # Format the response
            consultations_list = [{
                'id': consultation.id,
                'status': consultation.status,
                'timestamp': consultation.created_at.isoformat(),
                'result': json.loads(consultation.result_json) if consultation.result_json else None,
                'answers': json.loads(consultation.answers_json) if consultation.answers_json else None
            } for consultation in consultations]
            
            return jsonify(consultations_list), 200
            
        except Exception as e:
            print(f"Error fetching consultations: {str(e)}")
            return jsonify({
                "error": "Internal Server Error",
                "message": "Error fetching consultations"
            }), 500

    @app.route('/consultations/<int:consultation_id>', methods=['GET'])
    @jwt_required()
    def get_consultation(consultation_id):
        try:
            current_user_id = int(get_jwt_identity())
            
            # Query the specific consultation
            consultation = Consultation.query.filter_by(
                id=consultation_id, 
                user_id=current_user_id
            ).first()
            
            if not consultation:
                return jsonify({
                    "error": "Not Found",
                    "message": "Consultation not found"
                }), 404
            
            # Format the response
            consultation_data = {
                'id': consultation.id,
                'status': consultation.status,
                'timestamp': consultation.created_at.isoformat(),
                'result': json.loads(consultation.result_json) if consultation.result_json else None,
                'answers': json.loads(consultation.answers_json) if consultation.answers_json else None
            }
            
            return jsonify(consultation_data), 200
            
        except Exception as e:
            print(f"Error fetching consultation: {str(e)}")
            return jsonify({
                "error": "Internal Server Error",
                "message": "Error fetching consultation"
            }), 500

    @app.route('/consultations/<int:consultation_id>/feedback', methods=['POST'])
    @jwt_required()
    def create_or_update_feedback(consultation_id):
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not all(key in data for key in ['is_satisfied', 'has_purchased']):
            return jsonify({'error': 'Missing required fields'}), 400

        try:
            # Check for existing feedback
            feedback = Feedback.query.filter_by(consultation_id=consultation_id).first()
            
            if feedback:
                # Update existing feedback
                feedback.is_satisfied = data['is_satisfied']
                feedback.has_purchased = data['has_purchased']
                feedback.notes = data.get('notes', '')
            else:
                # Create new feedback with user_id
                feedback = Feedback(
                    consultation_id=consultation_id,
                    user_id=current_user_id,
                    is_satisfied=data['is_satisfied'],
                    has_purchased=data['has_purchased'],
                    notes=data.get('notes', '')
                )
                db.session.add(feedback)

            db.session.commit()
            return jsonify(feedback.to_dict()), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/consultations/<int:consultation_id>/feedback', methods=['GET'])
    @jwt_required()
    def get_consultation_feedback(consultation_id):
        feedback = Feedback.query.filter_by(consultation_id=consultation_id).first()
        if not feedback:
            return jsonify({'message': 'No feedback found'}), 404

        return jsonify(feedback.to_dict()), 200

    @app.route('/archetypes', methods=['GET'])
    @jwt_required()
    def get_archetypes():
        try:
            archetypes = Archetype.query.all()
            return jsonify([archetype.to_dict() for archetype in archetypes]), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/archetypes/<int:archetype_id>', methods=['GET'])
    @jwt_required()
    def get_archetype(archetype_id):
        try:
            # Get archetype by ID
            archetype = Archetype.query.get(archetype_id)
            
            if not archetype:
                return jsonify({"error": "Archetype not found"}), 404
            
            # Return the archetype data
            return jsonify(archetype.to_dict()), 200
        except Exception as e:
            print(f"Error getting archetype: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500

    @app.route('/archetypes/<int:archetype_id>/looks', methods=['GET'])
    @jwt_required()
    def get_archetype_looks(archetype_id):
        try:
            # Get archetype by ID
            archetype = Archetype.query.get(archetype_id)
            
            if not archetype:
                return jsonify({"error": "Archetype not found"}), 404
            
            # Get looks for this archetype
            associations = ArchetypeLookAssociation.query.filter_by(archetype_id=archetype_id).all()
            
            # Group looks by category
            looks_by_category = {}
            for assoc in associations:
                look = Look.query.get(assoc.look_id)
                category = assoc.category
                if category not in looks_by_category:
                    looks_by_category[category] = []
                
                # Add look to its category
                look_data = look.to_dict()
                look_data["tags"] = look.tags.split(",") if look.tags else []
                looks_by_category[category].append(look_data)
            
            # Format the response
            result = []
            for cat, category_looks in looks_by_category.items():
                result.append({
                    "category": cat,
                    "looks": category_looks
                })
            
            return jsonify(result), 200
        except Exception as e:
            print(f"Error getting archetype looks: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500

    @app.route('/admin/archetypes', methods=['POST'])
    @admin_required()
    def create_archetype():
        try:
            data = request.get_json()
            archetype = Archetype(
                name=data['name'],
                description=data['description'],
                binary_representation=data['binary_representation']
            )
            db.session.add(archetype)
            db.session.commit()
            return jsonify(archetype.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/admin/archetypes/bulk', methods=['POST'])
    @admin_required()
    def create_archetypes_bulk():
        try:
            # Get current user
            current_user_id = get_jwt_identity()
            print(f"User ID attempting bulk archetype upload: {current_user_id}")
            
            # Find user by ID
            user = User.query.get(current_user_id)
            
            if not user:
                print(f"No user found with ID: {current_user_id}")
                return jsonify({"error": "User not found"}), 404
            
            print(f"User found: {user.email}")
            
            # Get JSON data from request
            data = request.get_json()
            
            if not data or not isinstance(data, list):
                return jsonify({"error": "Invalid data format. Expected a list of archetypes"}), 400
            
            created_archetypes = []
            
            # Begin a transaction
            db.session.begin_nested()
            
            for archetype_data in data:
                # Validate required fields
                required_fields = ['name', 'binary_representation', 'description']
                for field in required_fields:
                    if field not in archetype_data:
                        db.session.rollback()
                        return jsonify({"error": f"Missing required field: {field}"}), 400
                
                # Check if archetype with this binary code already exists
                existing = Archetype.query.filter_by(binary_representation=archetype_data['binary_representation']).first()
                if existing:
                    print(f"Archetype with binary code {archetype_data['binary_representation']} already exists as '{existing.name}'")
                    continue
                
                # Create new archetype
                new_archetype = Archetype(
                    name=archetype_data['name'],
                    binary_representation=archetype_data['binary_representation'],
                    description=archetype_data['description']
                )
                
                db.session.add(new_archetype)
                created_archetypes.append({
                    'id': new_archetype.id,
                    'name': new_archetype.name,
                    'binary_representation': new_archetype.binary_representation
                })
            
            # Commit the transaction
            db.session.commit()
            
            return jsonify({
                "message": f"Successfully created {len(created_archetypes)} archetypes",
                "archetypes": created_archetypes
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Error in bulk archetype upload: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": "Failed to create archetypes in bulk",
                "message": str(e)
            }), 500

    @app.route('/admin/archetypes/bulk-associate-looks', methods=['POST'])
    @admin_required()
    def bulk_associate_archetypes_looks():
        try:
            data = request.get_json()
            
            if not data or not isinstance(data, list):
                return jsonify({
                    "error": "Bad Request",
                    "message": "Expected a list of archetype-look associations"
                }), 400
            
            results = {
                'successful': [],
                'failed': []
            }
            
            for association in data:
                try:
                    if 'archetype_id' not in association or 'look_ids' not in association:
                        results['failed'].append({
                            'association': association,
                            'error': "Missing archetype_id or look_ids"
                        })
                        continue
                    
                    archetype_id = association['archetype_id']
                    look_ids = association['look_ids']
                    clear_existing = association.get('clear_existing', False)
                    
                    archetype = Archetype.query.get(archetype_id)
                    if not archetype:
                        results['failed'].append({
                            'association': association,
                            'error': f"Archetype with ID {archetype_id} not found"
                        })
                        continue
                    
                    # Get current look associations
                    current_looks = list(archetype.looks)
                    
                    # Clear existing associations if specified
                    if clear_existing:
                        print(f"Clearing existing looks for archetype {archetype.name}")
                        archetype.looks = []
                        db.session.flush()  # Flush changes to DB without committing
                    
                    # Add new associations
                    added_looks = []
                    for look_id in look_ids:
                        look = Look.query.get(look_id)
                        if not look:
                            print(f"Look with ID {look_id} not found")
                            continue
                            
                        # Check if look is already associated
                        if not clear_existing and look in archetype.looks:
                            print(f"Look {look.name} already associated with archetype {archetype.name}")
                            continue
                        
                        print(f"Adding look {look.name} to archetype {archetype.name}")
                        archetype.looks.append(look)
                        added_looks.append({
                            'id': look.id,
                            'name': look.name
                        })
                    
                    # Commit changes for this archetype
                    db.session.commit()
                    
                    results['successful'].append({
                        'archetype_id': archetype_id,
                        'archetype_name': archetype.name,
                        'added_looks': added_looks,
                        'cleared_existing': clear_existing,
                        'total_looks': len(archetype.looks)
                    })
                    
                except Exception as e:
                    db.session.rollback()
                    print(f"Error processing association: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    results['failed'].append({
                        'association': association,
                        'error': str(e)
                    })
            
            return jsonify({
                'message': f"Processed {len(data)} associations",
                'results': results
            }), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Error in bulk association: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': "Failed to process bulk associations",
                'message': str(e)
            }), 500

    @app.route('/looks', methods=['GET'])
    @jwt_required()
    def get_looks():
        try:
            category = request.args.get('category')
            makeup_category = request.args.get('makeup_category')
            
            query = Look.query
            
            if category:
                query = query.filter_by(category=category.upper())
            
            # Filter by makeup_category if provided
            if makeup_category:
                # Use LIKE to match makeup_category within comma-separated values
                query = query.filter(Look.makeup_category.like(f'%{makeup_category}%'))
            
            looks = query.all()
            return jsonify([look.to_dict() for look in looks]), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/looks/<int:look_id>', methods=['GET'])
    @jwt_required()
    def get_look(look_id):
        look = Look.query.get(look_id)
        if not look:
            return jsonify({"error": "Look not found"}), 404
        
        return jsonify(look.to_dict()), 200

    @app.route('/looks', methods=['POST'])
    @jwt_required()
    def create_look():
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'category', 'image_url']  # Removed author
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Validate that artist_instruction_title can't exist without artist_instruction
        artist_instruction_title = data.get('artist_instruction_title')
        artist_instruction = data.get('artist_instruction')
        if artist_instruction_title and not artist_instruction:
            return jsonify({"error": "artist_instruction_title cannot exist without artist_instruction"}), 400
        
        # Handle image_url as a list or a single string
        image_url = data['image_url']
        if isinstance(image_url, list):
            # Convert list to comma-separated string
            image_url = ','.join(image_url)
        
        # Handle makeup_category as a list or a single string
        makeup_category = data.get('makeup_category')
        if isinstance(makeup_category, list):
            # Convert list to comma-separated string
            makeup_category = ','.join(makeup_category)
        
        # Create new look
        new_look = Look(
            name=data['name'],
            category=data['category'],
            makeup_category=makeup_category,
            author=data.get('author'),
            artist_instruction=artist_instruction,
            artist_instruction_title=artist_instruction_title,
            instructions=data.get('instructions'),
            tags=','.join(data['tags']) if 'tags' in data and data['tags'] else None,
            image_url=image_url,
            expertise_required=data.get('expertise_required'),
            application_time=data.get('application_time')
        )
        
        # Add associated products if provided
        if 'product_ids' in data and data['product_ids']:
            for product_id in data['product_ids']:
                product = Product.query.get(product_id)
                if product:
                    new_look.products.append(product)
        
        # Add associated archetypes if provided
        if 'archetype_ids' in data and data['archetype_ids']:
            for archetype_id in data['archetype_ids']:
                archetype = Archetype.query.get(archetype_id)
                if archetype:
                    new_look.archetypes.append(archetype)
        
        db.session.add(new_look)
        db.session.commit()
        
        return jsonify(new_look.to_dict()), 201

    @app.route('/looks/<int:look_id>', methods=['PUT'])
    @jwt_required()
    def update_look(look_id):
        look = Look.query.get(look_id)
        if not look:
            return jsonify({"error": "Look not found"}), 404
        
        data = request.json
        
        # Validate that artist_instruction_title can't exist without artist_instruction
        if 'artist_instruction_title' in data and data['artist_instruction_title']:
            artist_instruction = data.get('artist_instruction', look.artist_instruction)
            if not artist_instruction:
                return jsonify({"error": "artist_instruction_title cannot exist without artist_instruction"}), 400
        
        # Update fields
        if 'name' in data:
            look.name = data['name']
        if 'makeup_category' in data:
            # Handle makeup_category as a list or a single string
            makeup_category = data['makeup_category']
            if isinstance(makeup_category, list):
                # Convert list to comma-separated string
                makeup_category = ','.join(makeup_category)
            look.makeup_category = makeup_category
        if 'author' in data:
            look.author = data['author']
        if 'artist_instruction' in data:
            look.artist_instruction = data['artist_instruction']
        if 'artist_instruction_title' in data:
            look.artist_instruction_title = data['artist_instruction_title']
        if 'instructions' in data:
            look.instructions = data['instructions']
        if 'tags' in data:
            look.tags = ','.join(data['tags']) if data['tags'] else None
        if 'image_url' in data:
            # Handle image_url as a list or a single string
            image_url = data['image_url']
            if isinstance(image_url, list):
                # Convert list to comma-separated string
                image_url = ','.join(image_url)
            look.image_url = image_url
        if 'expertise_required' in data:
            look.expertise_required = data['expertise_required']
        if 'application_time' in data:
            look.application_time = data['application_time']
        
        # Update products if provided
        if 'product_ids' in data:
            # Clear existing products
            look.products = []
            # Add new products
            for product_id in data['product_ids']:
                product = Product.query.get(product_id)
                if product:
                    look.products.append(product)
        
        # Update archetypes if provided
        if 'archetype_ids' in data:
            # Clear existing archetypes
            look.archetypes = []
            # Add new archetypes
            for archetype_id in data['archetype_ids']:
                archetype = Archetype.query.get(archetype_id)
                if archetype:
                    look.archetypes.append(archetype)
        
        db.session.commit()
        
        return jsonify(look.to_dict()), 200

    @app.route('/admin/looks/bulk', methods=['POST'])
    @admin_required()
    def create_looks_bulk():
        try:
            # Get current user
            current_user_id = get_jwt_identity()
            print(f"User ID attempting bulk upload: {current_user_id}")
            
            # Find user by ID (not email)
            user = User.query.get(current_user_id)
            
            if not user:
                print(f"No user found with ID: {current_user_id}")
                return jsonify({"error": "User not found"}), 404
            
            print(f"User found: {user.email}, Admin status: {getattr(user, 'is_admin', False)}")
            
            # Get JSON data from request
            data = request.get_json()
            
            if not data or not isinstance(data, list):
                return jsonify({"error": "Invalid data format. Expected a list of looks"}), 400
            
            created_looks = []
            
            # Begin a transaction
            db.session.begin_nested()
            
            for look_data in data:
                # Validate required fields
                required_fields = ['name', 'category']  # Removed author
                for field in required_fields:
                    if field not in look_data:
                        db.session.rollback()
                        return jsonify({"error": f"Missing required field: {field}"}), 400
                
                # Validate that artist_instruction_title can't exist without artist_instruction
                artist_instruction_title = look_data.get('artist_instruction_title')
                artist_instruction = look_data.get('artist_instruction')
                if artist_instruction_title and not artist_instruction:
                    db.session.rollback()
                    return jsonify({"error": f"artist_instruction_title cannot exist without artist_instruction for look '{look_data['name']}'"}), 400
                
                # Handle image_url as a list or a single string
                image_url = look_data.get('image_url')
                if isinstance(image_url, list):
                    # Convert list to comma-separated string
                    image_url = ','.join(image_url)
                
                # Handle makeup_category as a list or a single string
                makeup_category = look_data.get('makeup_category')
                if isinstance(makeup_category, list):
                    # Convert list to comma-separated string
                    makeup_category = ','.join(makeup_category)
                
                # Create new look
                new_look = Look(
                    name=look_data['name'],
                    category=look_data['category'],
                    expertise_required=look_data.get('expertise_required'),
                    application_time=look_data.get('application_time'),
                    image_url=image_url,
                    author=look_data.get('author'),
                    artist_instruction=artist_instruction,
                    artist_instruction_title=artist_instruction_title,
                    instructions=look_data.get('instructions'),
                    makeup_category=makeup_category
                )
                
                db.session.add(new_look)
                created_looks.append({
                    'id': new_look.id,
                    'name': new_look.name
                })
            
            # Commit the transaction
            db.session.commit()
            
            return jsonify({
                "message": f"Successfully created {len(created_looks)} looks",
                "looks": created_looks
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Error in bulk upload: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": "Failed to create looks in bulk",
                "message": str(e)
            }), 500

    @app.route('/products/<int:product_id>/looks', methods=['GET'])
    @jwt_required()
    def get_product_looks(product_id):
        try:
            product = Product.query.get_or_404(product_id)
            
            # Get the looks associated with this product
            looks = [{
                'id': look.id,
                'name': look.name,
                'image_url': look.image_url,
                'expertise_required': look.expertise_required,
                'application_time': look.application_time
            } for look in product.looks]
            
            return jsonify({
                'product_id': product.id,
                'product_name': product.name,
                'look_count': len(looks),
                'looks': looks
            }), 200
            
        except Exception as e:
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e)
            }), 500

    @app.route('/admin/products/bulk', methods=['POST'])
    @admin_required()
    def create_products_bulk():
        try:
            # Get current user
            current_user_id = get_jwt_identity()
            print(f"User ID attempting bulk product upload: {current_user_id}")
            
            # Find user by ID
            user = User.query.get(current_user_id)
            
            if not user:
                print(f"No user found with ID: {current_user_id}")
                return jsonify({"error": "User not found"}), 404
            
            print(f"User found: {user.email}")
            
            # Get JSON data from request
            data = request.get_json()
            
            if not data or not isinstance(data, list):
                return jsonify({"error": "Invalid data format. Expected a list of products"}), 400
            
            created_products = []
            skipped_products = []
            
            # Begin a transaction
            db.session.begin_nested()
            
            for product_data in data:
                # Validate required fields
                if 'name' not in product_data or 'image_url' not in product_data:
                    db.session.rollback()
                    return jsonify({"error": "Missing required fields: name and image_url"}), 400
                
                # Check if product with this name already exists
                existing_product = Product.query.filter_by(name=product_data['name']).first()
                if existing_product:
                    print(f"Product with name {product_data['name']} already exists")
                    skipped_products.append({
                        'id': existing_product.id,
                        'name': existing_product.name,
                        'image_url': existing_product.image_url
                    })
                    continue
                
                # Create new product
                new_product = Product(
                    name=product_data['name'],
                    image_url=product_data['image_url']
                )
                
                db.session.add(new_product)
                created_products.append({
                    'id': new_product.id,
                    'name': new_product.name,
                    'image_url': new_product.image_url
                })
            
            # Commit the transaction
            db.session.commit()
            
            return jsonify({
                "message": f"Successfully created {len(created_products)} products, skipped {len(skipped_products)} existing products",
                "created": created_products,
                "skipped": skipped_products
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Error in bulk product upload: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": "Failed to create products in bulk",
                "message": str(e)
            }), 500

    @app.route('/health', methods=['GET'])
    def health_check():
        db_status = "unknown"
        try:
            # Use text() here too
            db.session.execute(text('SELECT 1'))
            db_status = "healthy"
            app.logger.info("Health check: Database connection successful")
        except Exception as e:
            db_status = "unhealthy"
            app.logger.error(f"Health check: Database connection failed: {str(e)}")
        
        response = {
            "status": "success",
            "message": "NARS backend deployed successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "environment": current_app.config.get('ENV', 'production')
        }
        
        return jsonify(response), 200

    @app.before_request
    def log_request_info():
        # Store the start time for request duration calculation
        request.start_time = time.time()
        app.logger.info(f"Request started: {request.method} {request.path}")

    @app.after_request
    def log_response_info(response):
        # Calculate request duration
        duration = time.time() - request.start_time
        app.logger.info(f"Request completed: {request.method} {request.path} - Status: {response.status_code} - Duration: {duration:.4f}s")
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        # Get the full traceback
        tb = traceback.format_exc()
        app.logger.error(f"Unhandled exception: {str(e)}\n{tb}")
        
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "details": str(e)
        }), 500

    @app.route('/', methods=['GET'])
    def root():
        app.logger.info("Root endpoint called")
        return jsonify({
            "status": "success",
            "message": "NARS API is running",
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    @app.route('/debug/db', methods=['GET'])
    def db_status():
        try:
            # Simple query to check database
            result = db.session.execute(text('SELECT 1')).scalar()
            
            return jsonify({
                "status": "connected",
                "result": result
            }), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    @app.route('/admin/check', methods=['GET'])
    @admin_required()
    def admin_check():
        """Simple endpoint to verify admin access"""
        return jsonify({"status": "success", "message": "Admin access confirmed"}), 200

    @app.route('/admin/archetypes/<int:archetype_id>', methods=['DELETE'])
    @admin_required()
    def delete_archetype(archetype_id):
        try:
            archetype = Archetype.query.get_or_404(archetype_id)
            db.session.delete(archetype)
            db.session.commit()
            return jsonify({
                "message": f"Archetype {archetype_id} deleted successfully"
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "error": "Failed to delete archetype",
                "message": str(e)
            }), 500

    @app.route('/admin/looks/<int:look_id>', methods=['DELETE'])
    @admin_required()
    def delete_look(look_id):
        try:
            look = Look.query.get_or_404(look_id)
            db.session.delete(look)
            db.session.commit()
            return jsonify({
                "message": f"Look {look_id} deleted successfully"
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "error": "Failed to delete look",
                "message": str(e)
            }), 500

    @app.route('/admin/products/<int:product_id>', methods=['DELETE'])
    @admin_required()
    def delete_product(product_id):
        try:
            product = Product.query.get_or_404(product_id)
            db.session.delete(product)
            db.session.commit()
            return jsonify({
                "message": f"Product {product_id} deleted successfully"
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "error": "Failed to delete product",
                "message": str(e)
            }), 500

    @app.route('/admin/archetypes/<int:archetype_id>/associations', methods=['GET'])
    @admin_required()
    def get_archetype_associations(archetype_id):
        try:
            archetype = Archetype.query.get_or_404(archetype_id)
            associations = []
            for look in archetype.looks:
                assoc = ArchetypeLookAssociation.query.get(look_id=look.id, archetype_id=archetype.id).first()
                associations.append({
                    'look_id': look.id,
                    'look_name': look.name,
                    'look_category': assoc.category,
                    'look_image_url': look.image_url
                })
            
            return jsonify({
                'archetype_id': archetype_id,
                'archetype_name': archetype.name,
                'associations_count': len(associations),
                'associations': associations
            }), 200
        except Exception as e:
            return jsonify({
                'error': 'Failed to fetch associations',
                'message': str(e)
            }), 500

    @app.route('/admin/archetypes/<int:archetype_id>/looks/<int:look_id>', methods=['DELETE'])
    @admin_required()
    def delete_archetype_look_association(archetype_id, look_id):
        try:
            archetype = Archetype.query.get_or_404(archetype_id)
            look = Look.query.get_or_404(look_id)
            
            if look not in archetype.looks:
                return jsonify({
                    'error': 'Association not found',
                    'message': f'Look {look_id} is not associated with Archetype {archetype_id}'
                }), 404
            
            archetype.looks.remove(look)
            db.session.commit()
            
            return jsonify({
                'message': f'Successfully removed association between Archetype {archetype_id} and Look {look_id}'
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Failed to delete association',
                'message': str(e)
            }), 500

    @app.route('/admin/looks/<int:look_id>/associations', methods=['GET'])
    @admin_required()
    def get_look_associations(look_id):
        try:
            look = Look.query.get_or_404(look_id)
            
            archetype_associations = [{
                'archetype_id': archetype.id,
                'archetype_name': archetype.name,
                'binary_representation': archetype.binary_representation
            } for archetype in look.archetypes]
            
            product_associations = [{
                'product_id': product.id,
                'product_name': product.name,
                'image_url': product.image_url
            } for product in look.products]
            
            return jsonify({
                'look_id': look_id,
                'look_name': look.name,
                'archetype_associations': {
                    'count': len(archetype_associations),
                    'items': archetype_associations
                },
                'product_associations': {
                    'count': len(product_associations),
                    'items': product_associations
                }
            }), 200
        except Exception as e:
            return jsonify({
                'error': 'Failed to fetch associations',
                'message': str(e)
            }), 500

    @app.route('/admin/looks/<int:look_id>/products/<int:product_id>', methods=['DELETE'])
    @admin_required()
    def delete_look_product_association(look_id, product_id):
        try:
            look = Look.query.get_or_404(look_id)
            product = Product.query.get_or_404(product_id)
            
            if product not in look.products:
                return jsonify({
                    'error': 'Association not found',
                    'message': f'Product {product_id} is not associated with Look {look_id}'
                }), 404
            
            look.products.remove(product)
            db.session.commit()
            
            return jsonify({
                'message': f'Successfully removed association between Look {look_id} and Product {product_id}'
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Failed to delete association',
                'message': str(e)
            }), 500

    @app.route('/admin/associations', methods=['GET'])
    @admin_required()
    def get_all_associations():
        try:
            # Get all archetypes with their looks
            archetypes = Archetype.query.all()
            archetype_associations = []
            for archetype in archetypes:
                looks = []
                for look in archetype.looks:
                    assoc = ArchetypeLookAssociation.query.get(archetype_id=archetype.id, look_id=look.id).first()
                    look.appen({
                        'look_id': look.id,
                        'look_name': look.name,
                        'category': assoc.category
                    })
                
                archetype_associations.append({
                    'archetype_id': archetype.id,
                    'archetype_name': archetype.name,
                    'looks': looks
                })

            # Get all looks with their products
            looks = Look.query.all()
            look_product_associations = [{
                'look_id': look.id,
                'look_name': look.name,
                'products': [{
                    'product_id': product.id,
                    'product_name': product.name,
                    'image_url': product.image_url
                } for product in look.products]
            } for look in looks]

            return jsonify({
                'archetype_look_associations': {
                    'count': sum(len(a['looks']) for a in archetype_associations),
                    'items': archetype_associations
                },
                'look_product_associations': {
                    'count': sum(len(l['products']) for l in look_product_associations),
                    'items': look_product_associations
                }
            }), 200
        except Exception as e:
            return jsonify({
                'error': 'Failed to fetch associations',
                'message': str(e)
            }), 500

    @app.route('/admin/looks/bulk-associate-products', methods=['POST'])
    @admin_required()
    def bulk_associate_looks_products():
        try:
            data = request.get_json()
            
            if not data or not isinstance(data, list):
                return jsonify({
                    "error": "Bad Request",
                    "message": "Expected a list of look-product associations"
                }), 400
            
            results = {
                'successful': [],
                'failed': []
            }
            
            for association in data:
                try:
                    if 'look_id' not in association or 'product_ids' not in association:
                        results['failed'].append({
                            'association': association,
                            'error': "Missing look_id or product_ids"
                        })
                        continue
                    
                    look_id = association['look_id']
                    product_ids = association['product_ids']
                    clear_existing = association.get('clear_existing', False)
                    
                    look = Look.query.get(look_id)
                    if not look:
                        results['failed'].append({
                            'association': association,
                            'error': f"Look with ID {look_id} not found"
                        })
                        continue
                    
                    # Get current product associations
                    current_products = list(look.products)
                    
                    # Clear existing associations if specified
                    if clear_existing:
                        print(f"Clearing existing products for look {look.name}")
                        look.products = []
                        db.session.flush()  # Flush changes to DB without committing
                    
                    # Add new associations
                    added_products = []
                    for product_id in product_ids:
                        product = Product.query.get(product_id)
                        if not product:
                            print(f"Product with ID {product_id} not found")
                            continue
                            
                        # Check if product is already associated
                        if not clear_existing and product in look.products:
                            print(f"Product {product.name} already associated with look {look.name}")
                            continue
                        
                        print(f"Adding product {product.name} to look {look.name}")
                        look.products.append(product)
                        added_products.append({
                            'id': product.id,
                            'name': product.name
                        })
                    
                    # Commit changes for this look
                    db.session.commit()
                    
                    results['successful'].append({
                        'look_id': look_id,
                        'look_name': look.name,
                        'added_products': added_products,
                        'cleared_existing': clear_existing,
                        'total_products': len(look.products)
                    })
                    
                except Exception as e:
                    db.session.rollback()
                    print(f"Error processing association: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    results['failed'].append({
                        'association': association,
                        'error': str(e)
                    })
            
            return jsonify({
                'message': f"Processed {len(data)} associations",
                'results': results
            }), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Error in bulk association: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': "Failed to process bulk associations",
                'message': str(e)
            }), 500

    return app

# Create the app instance
app = create_app('production')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)