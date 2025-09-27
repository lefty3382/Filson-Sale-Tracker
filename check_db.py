import sqlite3

conn = sqlite3.connect('sale_tracker.db')
cursor = conn.cursor()

# Check tables
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", tables)

# If items table exists, check count
if tables:
    for table in tables:
        table_name = table[0]
        count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"{table_name}: {count} records")
        
        # Show first 3 records if any exist
        if count > 0:
            records = cursor.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
            for record in records:
                print(f"  {record}")

conn.close()