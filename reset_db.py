#!/usr/bin/env python
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Import your app and db from wherever they are defined
sys.path.append("/app")
from app import app, db

def reset_database():
    with app.app_context():
        # Connect to the database
        conn = db.engine.connect()
        
        try:
            # Disable foreign key checks temporarily
            conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
            
            # Drop all tables
            print("Dropping all tables...")
            db.drop_all()
            
            # Re-enable foreign key checks
            conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))
            
            # Create all tables from scratch
            print("Creating all tables...")
            db.create_all()
            
            print("Database reset complete!")
            
        except Exception as e:
            print(f"Error resetting database: {e}")
            sys.exit(1)
        finally:
            conn.close()

if __name__ == "__main__":
    reset_database()
