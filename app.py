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
from models import db, User, Consultation, Feedback, Archetype, Look, ArchetypeLookAssociation, Product, UserProduct, LookHistory, UserWishlist, SeasonalContent
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
            
            # User must exist - no auto-creation
            if not user:
                return jsonify({"msg": "User not found. Please sign up first."}), 404
            
            # Verify password
            if not verify_password(db.session, email, password):
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

    @app.route('/signup', methods=['POST'])
    def signup():
        """
        Signup endpoint that creates a user and their first consultation from quiz answers
        """
        data = request.get_json()
        
        app.logger.info(f"Signup request received with data: {data}")
        
        if not data:
            return jsonify({"msg": "Missing JSON in request"}), 400
            
        email = data.get('email')
        password = data.get('password')
        answers = data.get('answers')
        remember_me = data.get('remember_me', False)
        
        app.logger.info(f"Email: {email}, Password: {'***' if password else None}, Answers: {answers}, Remember: {remember_me}")
        
        if not email or not password:
            return jsonify({"msg": "Missing email or password"}), 400
        
        if not answers or not isinstance(answers, dict):
            app.logger.error(f"Invalid answers: {answers}, Type: {type(answers)}")
            return jsonify({"msg": "Missing or invalid quiz answers", "received_type": str(type(answers))}), 400
        
        try:
            # Check if user already exists
            existing_user = get_user_by_email(email)
            if existing_user:
                return jsonify({"msg": "User already exists. Please log in."}), 409
            
            # Validate quiz answers
            required_questions = {f"q{i}" for i in range(1, 11)}
            missing_questions = required_questions - set(answers.keys())
            if missing_questions:
                app.logger.error(f"Missing questions: {missing_questions}")
                return jsonify({
                    "error": "Unprocessable Entity",
                    "message": "Missing required questions",
                    "details": list(missing_questions),
                    "received_keys": list(answers.keys())
                }), 422
            
            valid_answers = {'strongly_agree', 'agree', 'neutral', 'disagree', 'strongly_disagree'}
            for q_num, answer in answers.items():
                if not isinstance(answer, str) or answer.lower() not in valid_answers:
                    app.logger.error(f"Invalid answer for {q_num}: '{answer}' (type: {type(answer)})")
                    return jsonify({
                        "error": "Unprocessable Entity",
                        "message": f"Invalid answer for {q_num}",
                        "received_value": answer,
                        "valid_options": list(valid_answers)
                    }), 422
            
            # Create user
            user = create_user(email, password)
            
            # Calculate consultation result
            result = calculate_consultation_result(answers)
            
            # Create initial consultation
            consultation = Consultation(
                user_id=user.id,
                answers=answers,
                result=result,
                status='completed'
            )
            
            db.session.add(consultation)
            db.session.commit()
            
            # Set token expiration based on remember_me flag
            expires_delta = timedelta(days=30) if remember_me else timedelta(hours=1)
            access_token = create_access_token(
                identity=str(user.id),
                expires_delta=expires_delta
            )
            
            response_data = {
                "user": {"id": user.id, "email": user.email},
                "access_token": access_token,
                "consultation_id": consultation.id,
                "result": result
            }
            
            # Generate and store remember token if remember_me is True
            if remember_me:
                remember_token = secrets.token_hex(32)
                user.remember_token = remember_token
                db.session.commit()
                response_data["remember_token"] = remember_token
            
            return jsonify(response_data), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Signup error: {str(e)}")
            return jsonify({"msg": "An error occurred during signup"}), 500

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
    
    @app.route('/archetypes/by-binary/<string:binary>', methods=['GET'])
    @jwt_required()
    def get_archetype_by_binary(binary):
        """
        Get archetype by binary representation (e.g., '00000')
        """
        try:
            archetype = Archetype.query.filter_by(binary_representation=binary).first()
            
            if not archetype:
                return jsonify({'error': 'Archetype not found'}), 404
            
            return jsonify(archetype.to_dict()), 200
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
    
    @app.route('/archetypes/by-binary/<string:binary>/looks', methods=['GET'])
    @jwt_required()
    def get_archetype_looks_by_binary(binary):
        """
        Get looks for an archetype by binary representation (e.g., '00000')
        Includes personalized product shade recommendations and ownership status
        """
        try:
            # Get user profile for personalized recommendations
            user_id = get_jwt_identity()
            user_profile = None
            
            try:
                from models import Consultation
                consultation = Consultation.query.filter_by(user_id=user_id).order_by(Consultation.created_at.desc()).first()
                if consultation and consultation.result:
                    user_profile = consultation.result.get('profile', {})
            except Exception as e:
                print(f"Error fetching user profile: {str(e)}")
            
            # Get archetype by binary representation
            archetype = Archetype.query.filter_by(binary_representation=binary).first()
            
            if not archetype:
                return jsonify({"error": "Archetype not found"}), 404
            
            # Get looks for this archetype
            associations = ArchetypeLookAssociation.query.filter_by(archetype_id=archetype.id).all()
            
            # Get user's owned products
            user_products = UserProduct.query.filter_by(user_id=user_id).all()
            owned_product_ids = {up.product_id for up in user_products}
            
            # Group looks by category
            looks_by_category = {}
            for assoc in associations:
                look = Look.query.get(assoc.look_id)
                category = assoc.category
                if category not in looks_by_category:
                    looks_by_category[category] = []
                
                # Add look to its category with personalized products
                look_data = look.to_dict()
                look_data["tags"] = look.tags.split(",") if look.tags else []
                
                # Calculate look completion
                look_product_ids = [p['id'] for p in look_data.get('products', [])]
                owned_count = len([pid for pid in look_product_ids if pid in owned_product_ids])
                total_count = len(look_product_ids)
                
                look_data['completion'] = {
                    'owned_products': owned_count,
                    'total_products': total_count,
                    'percentage': round((owned_count / total_count * 100) if total_count > 0 else 0, 1),
                    'can_create': owned_count == total_count
                }
                
                # Add personalized shade recommendations and ownership to each product
                if user_profile and 'products' in look_data:
                    for product_data in look_data['products']:
                        product = Product.query.get(product_data['id'])
                        if product:
                            personalized = product.to_dict(user_profile=user_profile)
                            product_data.update(personalized)
                            product_data['owned'] = product.id in owned_product_ids
                
                looks_by_category[category].append(look_data)
            
            # Format response as list of category groups
            result = []
            for cat, category_looks in looks_by_category.items():
                result.append({
                    "category": cat,
                    "looks": category_looks
                })
            
            return jsonify(result), 200
        except Exception as e:
            print(f"Error getting archetype looks by binary: {str(e)}")
            import traceback
            traceback.print_exc()
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
        
        # Get user profile for personalized product recommendations
        user_id = get_jwt_identity()
        user_profile = None
        
        try:
            # Get user's latest consultation to extract profile
            from models import Consultation
            consultation = Consultation.query.filter_by(user_id=user_id).order_by(Consultation.created_at.desc()).first()
            if consultation and consultation.result:
                user_profile = consultation.result.get('profile', {})
        except Exception as e:
            print(f"Error fetching user profile: {str(e)}")
        
        # Convert look to dict with personalized product recommendations
        look_dict = look.to_dict()
        
        # Add personalized shade recommendations to each product
        if user_profile and 'products' in look_dict:
            for product_data in look_dict['products']:
                product = Product.query.get(product_data['id'])
                if product:
                    # Get personalized product dict
                    personalized = product.to_dict(user_profile=user_profile)
                    product_data.update(personalized)
        
        return jsonify(look_dict), 200

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

    # ============================================
    # USER PRODUCT COLLECTION ENDPOINTS
    # ============================================
    
    @app.route('/users/collection', methods=['GET'])
    @jwt_required()
    def get_user_collection():
        """Get all products in user's collection"""
        try:
            user_id = get_jwt_identity()
            
            user_products = UserProduct.query.filter_by(user_id=user_id).all()
            
            # Get full product details
            collection = []
            for up in user_products:
                product = Product.query.get(up.product_id)
                if product:
                    product_dict = product.to_dict()
                    product_dict['added_at'] = up.added_at.isoformat() if up.added_at else None
                    product_dict['notes'] = up.notes
                    collection.append(product_dict)
            
            return jsonify(collection), 200
        except Exception as e:
            print(f"Error getting user collection: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/users/collection/<int:product_id>', methods=['POST'])
    @jwt_required()
    def add_to_collection(product_id):
        """Add a product to user's collection with makeup bag details"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json() or {}
            
            # Check if product exists
            product = Product.query.get(product_id)
            if not product:
                return jsonify({"error": "Product not found"}), 404
            
            # Check if already in collection
            existing = UserProduct.query.filter_by(user_id=user_id, product_id=product_id).first()
            if existing:
                return jsonify({"message": "Product already in collection"}), 200
            
            # Parse dates if provided
            expiration_date = None
            purchase_date = None
            
            if data.get('expiration_date'):
                from datetime import datetime
                expiration_date = datetime.strptime(data['expiration_date'], '%Y-%m-%d').date()
            
            if data.get('purchase_date'):
                from datetime import datetime
                purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
            
            # Add to collection
            user_product = UserProduct(
                user_id=user_id,
                product_id=product_id,
                notes=data.get('notes', ''),
                expiration_date=expiration_date,
                purchase_date=purchase_date,
                usage_count=0
            )
            db.session.add(user_product)
            db.session.commit()
            
            return jsonify({
                "message": "Product added to collection",
                "product": product.to_dict()
            }), 201
        except Exception as e:
            db.session.rollback()
            print(f"Error adding to collection: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/users/collection/<int:product_id>', methods=['DELETE'])
    @jwt_required()
    def remove_from_collection(product_id):
        """Remove a product from user's collection"""
        try:
            user_id = get_jwt_identity()
            
            user_product = UserProduct.query.filter_by(user_id=user_id, product_id=product_id).first()
            if not user_product:
                return jsonify({"error": "Product not in collection"}), 404
            
            db.session.delete(user_product)
            db.session.commit()
            
            return jsonify({"message": "Product removed from collection"}), 200
        except Exception as e:
            db.session.rollback()
            print(f"Error removing from collection: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/users/collection/check', methods=['POST'])
    @jwt_required()
    def check_products_in_collection():
        """Check which products from a list are in user's collection"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            product_ids = data.get('product_ids', [])
            
            if not product_ids:
                return jsonify({"owned_product_ids": []}), 200
            
            user_products = UserProduct.query.filter(
                UserProduct.user_id == user_id,
                UserProduct.product_id.in_(product_ids)
            ).all()
            
            owned_ids = [up.product_id for up in user_products]
            
            return jsonify({"owned_product_ids": owned_ids}), 200
        except Exception as e:
            print(f"Error checking collection: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/looks/<int:look_id>/completion', methods=['GET'])
    @jwt_required()
    def get_look_completion(look_id):
        """Get completion status for a look (which products user owns)"""
        try:
            user_id = get_jwt_identity()
            
            look = Look.query.get(look_id)
            if not look:
                return jsonify({"error": "Look not found"}), 404
            
            # Get all products for this look
            look_product_ids = [p.id for p in look.products]
            
            # Get owned products
            user_products = UserProduct.query.filter(
                UserProduct.user_id == user_id,
                UserProduct.product_id.in_(look_product_ids)
            ).all()
            
            owned_ids = [up.product_id for up in user_products]
            
            # Calculate completion
            total_products = len(look_product_ids)
            owned_products = len(owned_ids)
            completion_percentage = (owned_products / total_products * 100) if total_products > 0 else 0
            
            # Get missing products
            missing_products = []
            for product in look.products:
                if product.id not in owned_ids:
                    missing_products.append(product.to_dict())
            
            return jsonify({
                "look_id": look_id,
                "look_name": look.name,
                "total_products": total_products,
                "owned_products": owned_products,
                "completion_percentage": round(completion_percentage, 1),
                "can_create": owned_products == total_products,
                "missing_products": missing_products,
                "owned_product_ids": owned_ids
            }), 200
        except Exception as e:
            print(f"Error getting look completion: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/users/shopping-list', methods=['GET'])
    @jwt_required()
    def get_shopping_list():
        """Generate shopping list of products user doesn't own from their looks"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            # Get user's latest consultation and archetype
            latest_consultation = Consultation.query.filter_by(user_id=user.id)\
                                                    .order_by(Consultation.created_at.desc())\
                                                    .first()
            
            if not latest_consultation or not latest_consultation.result.get('archetype_id'):
                return jsonify({"shopping_list": [], "message": "No archetype found"}), 200
            
            archetype_id = latest_consultation.result.get('archetype_id')
            
            # Get archetype and its looks
            archetype = Archetype.query.filter_by(binary_representation=archetype_id).first()
            if not archetype:
                return jsonify({"shopping_list": [], "message": "Archetype not found"}), 200
            
            # Get all looks for this archetype
            associations = ArchetypeLookAssociation.query.filter_by(archetype_id=archetype.id).all()
            look_ids = [assoc.look_id for assoc in associations]
            looks = Look.query.filter(Look.id.in_(look_ids)).all()
            
            # Get all products from these looks
            all_product_ids = set()
            product_look_map = {}  # Map product_id to list of looks
            
            for look in looks:
                for product in look.products:
                    all_product_ids.add(product.id)
                    if product.id not in product_look_map:
                        product_look_map[product.id] = []
                    product_look_map[product.id].append({
                        'look_id': look.id,
                        'look_name': look.name
                    })
            
            # Get owned products
            user_products = UserProduct.query.filter(
                UserProduct.user_id == user_id,
                UserProduct.product_id.in_(all_product_ids)
            ).all()
            
            owned_ids = {up.product_id for up in user_products}
            
            # Build shopping list (products not owned)
            shopping_list = []
            for product_id in all_product_ids:
                if product_id not in owned_ids:
                    product = Product.query.get(product_id)
                    if product:
                        product_dict = product.to_dict()
                        product_dict['used_in_looks'] = product_look_map.get(product_id, [])
                        product_dict['priority'] = len(product_look_map.get(product_id, []))  # Priority by number of looks
                        shopping_list.append(product_dict)
            
            # Sort by priority (most used products first)
            shopping_list.sort(key=lambda x: x['priority'], reverse=True)
            
            return jsonify({
                "shopping_list": shopping_list,
                "total_items": len(shopping_list),
                "total_owned": len(owned_ids),
                "total_products": len(all_product_ids)
            }), 200
        except Exception as e:
            print(f"Error generating shopping list: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Internal Server Error"}), 500

    # ============================================
    # LOOK HISTORY & PROGRESS ENDPOINTS
    # ============================================
    
    @app.route('/users/look-history', methods=['GET'])
    @jwt_required()
    def get_look_history():
        """Get user's look history with ratings"""
        try:
            user_id = get_jwt_identity()
            
            history = LookHistory.query.filter_by(user_id=user_id)\
                                      .order_by(LookHistory.tried_at.desc())\
                                      .all()
            
            return jsonify([h.to_dict() for h in history]), 200
        except Exception as e:
            print(f"Error getting look history: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/looks/<int:look_id>/mark-tried', methods=['POST'])
    @jwt_required()
    def mark_look_tried(look_id):
        """Mark a look as tried with optional rating and notes"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json() or {}
            
            # Check if look exists
            look = Look.query.get(look_id)
            if not look:
                return jsonify({"error": "Look not found"}), 404
            
            # Check if already tried
            existing = LookHistory.query.filter_by(user_id=user_id, look_id=look_id).first()
            
            if existing:
                # Update existing entry
                if 'rating' in data:
                    existing.rating = data['rating']
                if 'notes' in data:
                    existing.notes = data['notes']
                if 'difficulty_rating' in data:
                    existing.difficulty_rating = data['difficulty_rating']
                if 'time_taken' in data:
                    existing.time_taken = data['time_taken']
                existing.tried_at = datetime.utcnow()  # Update timestamp
            else:
                # Create new entry
                history_entry = LookHistory(
                    user_id=user_id,
                    look_id=look_id,
                    rating=data.get('rating'),
                    notes=data.get('notes'),
                    difficulty_rating=data.get('difficulty_rating'),
                    time_taken=data.get('time_taken')
                )
                db.session.add(history_entry)
            
            db.session.commit()
            
            return jsonify({
                "message": "Look marked as tried",
                "look_id": look_id
            }), 200
        except Exception as e:
            db.session.rollback()
            print(f"Error marking look as tried: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/looks/<int:look_id>/instructions/progress', methods=['PUT'])
    @jwt_required()
    def update_instruction_progress(look_id):
        """Update which instructions have been completed for a look"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            if 'completed_instructions' not in data:
                return jsonify({"error": "completed_instructions is required"}), 400
            
            completed_instructions = data['completed_instructions']
            if not isinstance(completed_instructions, list):
                return jsonify({"error": "completed_instructions must be an array"}), 400
            
            # Get or create look history entry
            history_entry = LookHistory.query.filter_by(user_id=user_id, look_id=look_id).first()
            
            if not history_entry:
                # Create new entry if it doesn't exist
                history_entry = LookHistory(
                    user_id=user_id,
                    look_id=look_id,
                    completed_instructions=completed_instructions
                )
                db.session.add(history_entry)
            else:
                # Update existing entry
                history_entry.completed_instructions = completed_instructions
            
            db.session.commit()
            
            # Calculate progress percentage
            look = Look.query.get(look_id)
            total_instructions = len(look.instructions) if look and look.instructions else 0
            completed_count = len(completed_instructions)
            progress_percentage = (completed_count / total_instructions * 100) if total_instructions > 0 else 0
            
            return jsonify({
                "message": "Instruction progress updated",
                "completed_instructions": completed_instructions,
                "progress_percentage": round(progress_percentage, 2),
                "completed_count": completed_count,
                "total_instructions": total_instructions
            }), 200
        except Exception as e:
            db.session.rollback()
            print(f"Error updating instruction progress: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/looks/<int:look_id>/rating', methods=['PUT'])
    @jwt_required()
    def update_look_rating(look_id):
        """Update rating for a tried look"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            if 'rating' not in data:
                return jsonify({"error": "Rating is required"}), 400
            
            rating = data['rating']
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                return jsonify({"error": "Rating must be between 1 and 5"}), 400
            
            history_entry = LookHistory.query.filter_by(user_id=user_id, look_id=look_id).first()
            
            if not history_entry:
                return jsonify({"error": "Look not tried yet"}), 404
            
            history_entry.rating = rating
            if 'notes' in data:
                history_entry.notes = data['notes']
            if 'difficulty_rating' in data:
                history_entry.difficulty_rating = data['difficulty_rating']
            
            db.session.commit()
            
            return jsonify({
                "message": "Rating updated",
                "rating": rating
            }), 200
        except Exception as e:
            db.session.rollback()
            print(f"Error updating rating: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/users/progress', methods=['GET'])
    @jwt_required()
    def get_user_progress():
        """Get user's skill progression and statistics"""
        try:
            user_id = get_jwt_identity()
            
            # Get all tried looks
            history = LookHistory.query.filter_by(user_id=user_id).all()
            
            if not history:
                return jsonify({
                    "total_looks_tried": 0,
                    "skill_level": "Beginner",
                    "skill_points": 0,
                    "next_level_points": 100,
                    "progress_percentage": 0,
                    "average_rating": 0,
                    "total_time_spent": 0,
                    "achievements": []
                }), 200
            
            # Calculate statistics
            total_looks_tried = len(history)
            total_time = sum([h.time_taken for h in history if h.time_taken]) or 0
            ratings = [h.rating for h in history if h.rating]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            # Calculate skill level based on looks tried and difficulty
            skill_points = 0
            
            for entry in history:
                # Base points for completing a look
                skill_points += 10
                
                # Bonus for rating
                if entry.rating:
                    skill_points += entry.rating
                
                # Bonus for difficulty
                look = Look.query.get(entry.look_id)
                if look:
                    if look.expertise_required == 'Beginner':
                        skill_points += 5
                    elif look.expertise_required == 'Intermediate':
                        skill_points += 15
                    elif look.expertise_required == 'Advanced':
                        skill_points += 30
            
            # Determine skill level
            if skill_points < 100:
                skill_level = "Beginner"
                next_level_points = 100
            elif skill_points < 300:
                skill_level = "Intermediate"
                next_level_points = 300
            elif skill_points < 600:
                skill_level = "Advanced"
                next_level_points = 600
            else:
                skill_level = "Expert"
                next_level_points = skill_points  # Already maxed
            
            progress_percentage = (skill_points / next_level_points * 100) if next_level_points > 0 else 100
            
            # Calculate achievements
            achievements = []
            if total_looks_tried >= 1:
                achievements.append({"name": "First Look", "icon": "🎨", "unlocked": True})
            if total_looks_tried >= 5:
                achievements.append({"name": "Makeup Explorer", "icon": "✨", "unlocked": True})
            if total_looks_tried >= 10:
                achievements.append({"name": "Beauty Enthusiast", "icon": "💄", "unlocked": True})
            if total_looks_tried >= 25:
                achievements.append({"name": "Makeup Master", "icon": "👑", "unlocked": True})
            if avg_rating >= 4.5:
                achievements.append({"name": "Perfectionist", "icon": "⭐", "unlocked": True})
            
            # Check for advanced looks
            advanced_looks = [h for h in history if Look.query.get(h.look_id) and Look.query.get(h.look_id).expertise_required == 'Advanced']
            if len(advanced_looks) >= 3:
                achievements.append({"name": "Advanced Artist", "icon": "🎭", "unlocked": True})
            
            return jsonify({
                "total_looks_tried": total_looks_tried,
                "skill_level": skill_level,
                "skill_points": skill_points,
                "next_level_points": next_level_points,
                "progress_percentage": round(progress_percentage, 1),
                "average_rating": round(avg_rating, 1),
                "total_time_spent": total_time,
                "achievements": achievements,
                "recent_looks": [h.to_dict() for h in history[:5]]  # Last 5 looks
            }), 200
        except Exception as e:
            print(f"Error getting user progress: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Internal Server Error"}), 500

    # ============================================
    # VIRTUAL MAKEUP BAG ENDPOINTS
    # ============================================
    
    @app.route('/users/makeup-bag', methods=['GET'])
    @jwt_required()
    def get_makeup_bag():
        """Get user's virtual makeup bag with usage insights"""
        try:
            user_id = get_jwt_identity()
            
            user_products = UserProduct.query.filter_by(user_id=user_id).all()
            
            # Get full product details with bag info
            bag_items = []
            for up in user_products:
                product = Product.query.get(up.product_id)
                if product:
                    product_dict = product.to_dict()
                    bag_info = up.to_dict()
                    product_dict.update(bag_info)
                    bag_items.append(product_dict)
            
            # Calculate insights
            total_products = len(bag_items)
            expiring_soon = len([item for item in bag_items if item.get('is_expiring_soon')])
            expired = len([item for item in bag_items if item.get('is_expired')])
            frequently_used = [item for item in bag_items if item.get('usage_count', 0) >= 5]
            rarely_used = [item for item in bag_items if item.get('usage_count', 0) < 2]
            
            return jsonify({
                "items": bag_items,
                "insights": {
                    "total_products": total_products,
                    "expiring_soon": expiring_soon,
                    "expired": expired,
                    "frequently_used": len(frequently_used),
                    "rarely_used": len(rarely_used)
                }
            }), 200
        except Exception as e:
            print(f"Error getting makeup bag: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/users/collection/<int:product_id>/update', methods=['PUT'])
    @jwt_required()
    def update_product_in_bag(product_id):
        """Update product details in makeup bag"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            user_product = UserProduct.query.filter_by(user_id=user_id, product_id=product_id).first()
            if not user_product:
                return jsonify({"error": "Product not in collection"}), 404
            
            # Update fields
            if 'notes' in data:
                user_product.notes = data['notes']
            
            if 'expiration_date' in data:
                if data['expiration_date']:
                    from datetime import datetime
                    user_product.expiration_date = datetime.strptime(data['expiration_date'], '%Y-%m-%d').date()
                else:
                    user_product.expiration_date = None
            
            if 'purchase_date' in data:
                if data['purchase_date']:
                    from datetime import datetime
                    user_product.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
                else:
                    user_product.purchase_date = None
            
            db.session.commit()
            
            return jsonify({
                "message": "Product updated",
                "product": user_product.to_dict()
            }), 200
        except Exception as e:
            db.session.rollback()
            print(f"Error updating product in bag: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/users/collection/<int:product_id>/use', methods=['POST'])
    @jwt_required()
    def log_product_use(product_id):
        """Log usage of a product"""
        try:
            user_id = get_jwt_identity()
            
            user_product = UserProduct.query.filter_by(user_id=user_id, product_id=product_id).first()
            if not user_product:
                return jsonify({"error": "Product not in collection"}), 404
            
            # Update usage
            user_product.usage_count = (user_product.usage_count or 0) + 1
            user_product.last_used = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                "message": "Usage logged",
                "usage_count": user_product.usage_count,
                "last_used": user_product.last_used.isoformat()
            }), 200
        except Exception as e:
            db.session.rollback()
            print(f"Error logging product use: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/users/makeup-bag/reminders', methods=['GET'])
    @jwt_required()
    def get_reminders():
        """Get replenishment reminders"""
        try:
            user_id = get_jwt_identity()
            from datetime import date, timedelta
            
            user_products = UserProduct.query.filter_by(user_id=user_id).all()
            
            reminders = []
            
            for up in user_products:
                product = Product.query.get(up.product_id)
                if not product:
                    continue
                
                reminder_type = None
                priority = 0
                message = ""
                
                # Check expiration
                if up.expiration_date:
                    days_until_expiry = (up.expiration_date - date.today()).days
                    if days_until_expiry < 0:
                        reminder_type = "expired"
                        priority = 3
                        message = f"{product.name} has expired"
                    elif days_until_expiry <= 7:
                        reminder_type = "expiring_urgent"
                        priority = 2
                        message = f"{product.name} expires in {days_until_expiry} days"
                    elif days_until_expiry <= 30:
                        reminder_type = "expiring_soon"
                        priority = 1
                        message = f"{product.name} expires in {days_until_expiry} days"
                
                # Check for rarely used products
                if up.usage_count == 0 and up.added_at:
                    days_since_added = (datetime.utcnow() - up.added_at).days
                    if days_since_added > 30:
                        if not reminder_type:  # Don't override expiration reminders
                            reminder_type = "unused"
                            priority = 0
                            message = f"{product.name} hasn't been used yet"
                
                # Check for frequently used (might need replenishment)
                if up.usage_count and up.usage_count >= 15:
                    if not reminder_type:  # Don't override other reminders
                        reminder_type = "replenish"
                        priority = 1
                        message = f"{product.name} is frequently used - consider replenishing"
                
                if reminder_type:
                    reminders.append({
                        "product_id": product.id,
                        "product_name": product.name,
                        "product_image": product.image_url,
                        "type": reminder_type,
                        "priority": priority,
                        "message": message,
                        "usage_count": up.usage_count or 0,
                        "days_until_expiry": (up.expiration_date - date.today()).days if up.expiration_date else None
                    })
            
            # Sort by priority (highest first)
            reminders.sort(key=lambda x: x['priority'], reverse=True)
            
            return jsonify({
                "reminders": reminders,
                "total_reminders": len(reminders)
            }), 200
        except Exception as e:
            print(f"Error getting reminders: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Internal Server Error"}), 500

    # ==================== WISHLIST ROUTES ====================
    
    @app.route('/users/wishlist', methods=['GET'])
    @jwt_required()
    def get_user_wishlist():
        """Get user's wishlist"""
        try:
            user_id = get_jwt_identity()
            
            wishlist_items = UserWishlist.query.filter_by(user_id=user_id).order_by(UserWishlist.added_at.desc()).all()
            
            items = []
            for item in wishlist_items:
                item_dict = item.to_dict()
                items.append(item_dict)
            
            # Calculate total value
            total_value = sum(item['product']['price'] if item['product'] and item['product'].get('price') else 0 for item in items)
            
            return jsonify({
                "items": items,
                "total_items": len(items),
                "total_value": total_value
            }), 200
        except Exception as e:
            print(f"Error getting wishlist: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/users/wishlist/<int:product_id>', methods=['POST'])
    @jwt_required()
    def add_to_wishlist(product_id):
        """Add product to wishlist"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json() or {}
            
            # Check if product exists
            product = Product.query.get(product_id)
            if not product:
                return jsonify({"error": "Product not found"}), 404
            
            # Check if already in wishlist
            existing = UserWishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
            if existing:
                return jsonify({"message": "Product already in wishlist", "item": existing.to_dict()}), 200
            
            # Add to wishlist
            wishlist_item = UserWishlist(
                user_id=user_id,
                product_id=product_id,
                occasion=data.get('occasion', 'general'),
                notes=data.get('notes'),
                priority=data.get('priority', 0)
            )
            db.session.add(wishlist_item)
            db.session.commit()
            
            return jsonify({
                "message": "Product added to wishlist",
                "item": wishlist_item.to_dict()
            }), 201
        except Exception as e:
            db.session.rollback()
            print(f"Error adding to wishlist: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/users/wishlist/<int:product_id>', methods=['DELETE'])
    @jwt_required()
    def remove_from_wishlist(product_id):
        """Remove product from wishlist"""
        try:
            user_id = get_jwt_identity()
            
            wishlist_item = UserWishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
            if not wishlist_item:
                return jsonify({"error": "Item not found in wishlist"}), 404
            
            db.session.delete(wishlist_item)
            db.session.commit()
            
            return jsonify({"message": "Product removed from wishlist"}), 200
        except Exception as e:
            db.session.rollback()
            print(f"Error removing from wishlist: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/users/wishlist/<int:product_id>/update', methods=['PUT'])
    @jwt_required()
    def update_wishlist_item(product_id):
        """Update wishlist item details"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            wishlist_item = UserWishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
            if not wishlist_item:
                return jsonify({"error": "Item not found in wishlist"}), 404
            
            # Update fields
            if 'occasion' in data:
                wishlist_item.occasion = data['occasion']
            if 'notes' in data:
                wishlist_item.notes = data['notes']
            if 'priority' in data:
                wishlist_item.priority = data['priority']
            
            db.session.commit()
            
            return jsonify({
                "message": "Wishlist item updated",
                "item": wishlist_item.to_dict()
            }), 200
        except Exception as e:
            db.session.rollback()
            print(f"Error updating wishlist item: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/users/wishlist/check', methods=['POST'])
    @jwt_required()
    def check_wishlist_status():
        """Check if products are in wishlist"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            product_ids = data.get('product_ids', [])
            
            wishlist_items = UserWishlist.query.filter(
                UserWishlist.user_id == user_id,
                UserWishlist.product_id.in_(product_ids)
            ).all()
            
            wishlisted_ids = [item.product_id for item in wishlist_items]
            
            return jsonify({
                "wishlisted_product_ids": wishlisted_ids
            }), 200
        except Exception as e:
            print(f"Error checking wishlist status: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/wishlist/share/<int:user_id>', methods=['GET'])
    def get_shared_wishlist(user_id):
        """Get shared wishlist (public route)"""
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            wishlist_items = UserWishlist.query.filter_by(user_id=user_id).order_by(UserWishlist.priority.desc(), UserWishlist.added_at.desc()).all()
            
            items = [item.to_dict() for item in wishlist_items]
            
            # Group by occasion
            grouped = {}
            for item in items:
                occasion = item['occasion'] or 'general'
                if occasion not in grouped:
                    grouped[occasion] = []
                grouped[occasion].append(item)
            
            return jsonify({
                "user_name": user.email.split('@')[0],  # Use email prefix as name
                "items": items,
                "grouped_by_occasion": grouped,
                "total_items": len(items)
            }), 200
        except Exception as e:
            print(f"Error getting shared wishlist: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500

    # ==================== SEASONAL CONTENT ROUTES ====================
    
    @app.route('/seasonal-content', methods=['GET'])
    def get_seasonal_content():
        """Get active seasonal content"""
        try:
            from datetime import date
            
            # Get content_type filter
            content_type = request.args.get('type')
            
            query = SeasonalContent.query.filter_by(is_active=True)
            
            # Filter by content type if provided
            if content_type:
                query = query.filter_by(content_type=content_type)
            
            # Filter by date range (current date should be within start_date and end_date)
            today = date.today()
            query = query.filter(
                db.or_(
                    SeasonalContent.start_date.is_(None),
                    SeasonalContent.start_date <= today
                )
            ).filter(
                db.or_(
                    SeasonalContent.end_date.is_(None),
                    SeasonalContent.end_date >= today
                )
            )
            
            content_items = query.order_by(SeasonalContent.created_at.desc()).all()
            
            # Group by content type
            grouped = {
                'trends': [],
                'holidays': [],
                'look_of_week': []
            }
            
            for item in content_items:
                item_dict = item.to_dict()
                
                # Fetch related looks if any
                if item.related_look_ids:
                    import json
                    look_ids = json.loads(item.related_look_ids)
                    looks = Look.query.filter(Look.id.in_(look_ids)).all()
                    item_dict['related_looks'] = [look.to_dict() for look in looks]
                
                # Fetch related products if any
                if item.related_product_ids:
                    import json
                    product_ids = json.loads(item.related_product_ids)
                    products = Product.query.filter(Product.id.in_(product_ids)).all()
                    item_dict['related_products'] = [product.to_dict() for product in products]
                
                if item.content_type in grouped:
                    grouped[item.content_type].append(item_dict)
            
            return jsonify({
                "content": [item.to_dict() for item in content_items],
                "grouped": grouped
            }), 200
        except Exception as e:
            print(f"Error getting seasonal content: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/seasonal-content', methods=['POST'])
    @jwt_required()
    @admin_required()
    def create_seasonal_content():
        """Create new seasonal content (admin only)"""
        try:
            data = request.get_json()
            from datetime import datetime
            import json
            
            content = SeasonalContent(
                title=data.get('title'),
                description=data.get('description'),
                content_type=data.get('content_type', 'trend'),
                start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
                end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
                is_active=data.get('is_active', True),
                image_url=data.get('image_url'),
                related_look_ids=json.dumps(data.get('related_look_ids', [])),
                related_product_ids=json.dumps(data.get('related_product_ids', [])),
                extra_data=json.dumps(data.get('metadata', {}))
            )
            
            db.session.add(content)
            db.session.commit()
            
            return jsonify({
                "message": "Seasonal content created",
                "content": content.to_dict()
            }), 201
        except Exception as e:
            db.session.rollback()
            print(f"Error creating seasonal content: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/seasonal-content/<int:content_id>', methods=['PUT'])
    @jwt_required()
    @admin_required()
    def update_seasonal_content(content_id):
        """Update seasonal content (admin only)"""
        try:
            content = SeasonalContent.query.get(content_id)
            if not content:
                return jsonify({"error": "Content not found"}), 404
            
            data = request.get_json()
            from datetime import datetime
            import json
            
            if 'title' in data:
                content.title = data['title']
            if 'description' in data:
                content.description = data['description']
            if 'content_type' in data:
                content.content_type = data['content_type']
            if 'start_date' in data:
                content.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            if 'end_date' in data:
                content.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            if 'is_active' in data:
                content.is_active = data['is_active']
            if 'image_url' in data:
                content.image_url = data['image_url']
            if 'related_look_ids' in data:
                content.related_look_ids = json.dumps(data['related_look_ids'])
            if 'related_product_ids' in data:
                content.related_product_ids = json.dumps(data['related_product_ids'])
            if 'metadata' in data:
                content.extra_data = json.dumps(data['metadata'])
            
            db.session.commit()
            
            return jsonify({
                "message": "Seasonal content updated",
                "content": content.to_dict()
            }), 200
        except Exception as e:
            db.session.rollback()
            print(f"Error updating seasonal content: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/seasonal-content/<int:content_id>', methods=['DELETE'])
    @jwt_required()
    @admin_required()
    def delete_seasonal_content(content_id):
        """Delete seasonal content (admin only)"""
        try:
            content = SeasonalContent.query.get(content_id)
            if not content:
                return jsonify({"error": "Content not found"}), 404
            
            db.session.delete(content)
            db.session.commit()
            
            return jsonify({"message": "Seasonal content deleted"}), 200
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting seasonal content: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500

    return app

# Create the app instance
app = create_app('production')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)