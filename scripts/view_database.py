import sqlite3
import pandas as pd
from tabulate import tabulate
import os

def print_table_contents(db_path, output_file):
    conn = sqlite3.connect(db_path)
    
    # Get all table names
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    with open(output_file, 'w') as f:
        f.write("Database Preview Report\n")
        f.write("=====================\n\n")
        
        for table in tables:
            table_name = table[0]
            f.write(f"\nTable: {table_name}\n")
            f.write("=" * (len(table_name) + 7) + "\n")
            
            # Get table contents using pandas
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            
            # Convert to formatted table string
            table_str = tabulate(df, headers='keys', tablefmt='grid', showindex=False)
            f.write(table_str + "\n\n")
    
    conn.close()
    print(f"Database preview has been saved to {output_file}")

if __name__ == "__main__":
    db_path = "../instance/crow_counter.db"
    output_file = "../database_preview.txt"
    
    # Make sure paths are absolute
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(os.path.dirname(script_dir), "instance", "crow_counter.db")
    output_file = os.path.join(os.path.dirname(script_dir), "database_preview.txt")
    
    print_table_contents(db_path, output_file)