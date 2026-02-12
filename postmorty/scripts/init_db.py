from ..core import database
import os

def init_db():
    # SQL files are now in a subfolder
    sql_dir = os.path.join(os.path.dirname(__file__), "sql")
    
    scripts = ["init_db.sql", "init_ohlcv_daily.sql", "init_valuations.sql"]
    
    conn = None
    try:
        conn = database.get_connection()
        cur = conn.cursor()
        
        for script in scripts:
            sql_path = os.path.join(sql_dir, script)
            print(f"Executing {script}...")
            if os.path.exists(sql_path):
                with open(sql_path, "r") as f:
                    sql = f.read()
                cur.execute(sql)
                print(f"{script} executed successfully!")
            else:
                print(f"Warning: {sql_path} not found.")
        
        conn.commit()
        print("Schema initialization complete!")
        cur.close()
    except Exception as e:
        print(f"Error initializing schema: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
