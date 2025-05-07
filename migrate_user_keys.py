import sqlite3
import os
from loguru import logger

# Path to the database file
DB_PATH = os.path.join("data", "summarify.db")

def migrate_database():
    """Migrate the database to add user API keys table"""
    try:
        # Check if database file exists
        if not os.path.exists(DB_PATH):
            logger.error(f"Database file not found at {DB_PATH}")
            return False
        
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create user_api_keys table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            api_key TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, provider)
        )
        ''')
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info("Database migration for user API keys completed successfully")
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
        print("Database migration for user API keys completed successfully")
    else:
        print("Database migration failed. Check logs for details.")
