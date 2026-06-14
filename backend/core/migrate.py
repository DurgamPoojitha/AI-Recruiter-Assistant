import sqlite3
import os

db_path = "data/recruiter.db"
if not os.path.exists(db_path):
    print("DB not found, skipping migration.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS organizations (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
        
        # Insert a default org if none exists
        cursor.execute("SELECT count(*) FROM organizations")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO organizations (name) VALUES ('Default Org')")
            
        default_org_id = 1
        
        try:
            cursor.execute("ALTER TABLE recruiters ADD COLUMN org_id INTEGER REFERENCES organizations(id)")
            cursor.execute(f"UPDATE recruiters SET org_id = {default_org_id}")
        except sqlite3.OperationalError:
            pass # Column exists
            
        try:
            cursor.execute("ALTER TABLE jobs ADD COLUMN org_id INTEGER REFERENCES organizations(id)")
            cursor.execute(f"UPDATE jobs SET org_id = {default_org_id}")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE candidates ADD COLUMN org_id INTEGER REFERENCES organizations(id)")
            cursor.execute(f"UPDATE candidates SET org_id = {default_org_id}")
        except sqlite3.OperationalError:
            pass

        conn.commit()
        print("Migration complete.")
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN risk_level TEXT DEFAULT 'Low'")
        cursor.execute("ALTER TABLE candidates ADD COLUMN risk_factors TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
