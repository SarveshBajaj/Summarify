import sqlite3
import os
from loguru import logger

# Path to the database file
DB_PATH = os.path.join("data", "summarify.db")

def migrate_database():
    """Migrate the database to add new columns for model support"""
    try:
        # Check if database file exists
        if not os.path.exists(DB_PATH):
            logger.error(f"Database file not found at {DB_PATH}")
            return False
        
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if model_type column exists
        cursor.execute("PRAGMA table_info(queries)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add model_type column if it doesn't exist
        if "model_type" not in columns:
            logger.info("Adding model_type column to queries table")
            cursor.execute("ALTER TABLE queries ADD COLUMN model_type TEXT DEFAULT 'huggingface'")
        
        # Add model_name column if it doesn't exist
        if "model_name" not in columns:
            logger.info("Adding model_name column to queries table")
            cursor.execute("ALTER TABLE queries ADD COLUMN model_name TEXT")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info("Database migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error migrating database: {str(e)}")
        return False

if __name__ == "__main__":
    # Configure logging
    logger.add("logs/migration.log", rotation="1 MB", level="INFO")
    
    # Run migration
    success = migrate_database()
    
    if success:
        print("Database migration completed successfully")
    else:
        print("Database migration failed. Check logs for details.")
