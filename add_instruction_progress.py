"""
Migration to add instruction progress tracking to look_history table
"""
from app import app, db
from flask import Flask

def add_instruction_progress_column():
    """Add completed_instructions JSON column to look_history table"""
    try:
        with app.app_context():
            # Use raw SQL to add the column
            sql = """
            ALTER TABLE look_history 
            ADD COLUMN completed_instructions JSON NULL COMMENT 'Array of completed instruction indices';
            """
            
            db.session.execute(db.text(sql))
            db.session.commit()
            print("✓ Added completed_instructions column to look_history table")
            print("\nMigration completed successfully!")
            
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()

if __name__ == "__main__":
    add_instruction_progress_column()

