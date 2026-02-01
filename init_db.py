from app import create_app
from models import db
import os

def init_database():
    app = create_app('production')
    
    with app.app_context():
        print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        try:
            # Drop all tables first
            db.drop_all()
            print("Dropped all existing tables")
            
            # Create all tables
            db.create_all()
            print("Database tables created successfully!")
            
            # Check created tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables in database: {tables}")
            
            return True
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
            return False

if __name__ == "__main__":
    init_database() 