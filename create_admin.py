from app import create_app, db
from models import User
import bcrypt

def create_admin_user():
    app = create_app('production')
    with app.app_context():
        # Check if admin already exists
        admin_email = 'admin@narspersona.com'
        admin = User.query.filter_by(email=admin_email).first()
        
        if admin:
            print(f"Admin user {admin_email} already exists")
            return
        
        # Create admin user with a secure password
        admin_password = '@NarsP3rsona!2025#'  # Change this to a secure password
        
        # Create the user
        admin = User(email=admin_email)
        admin.password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Add and commit to database
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user {admin_email} created successfully")

if __name__ == '__main__':
    create_admin_user()