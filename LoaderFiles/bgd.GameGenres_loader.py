import csv
import pyodbc

''' =====================================================================
        1. DATABASE CONNECTION SETUP
        Using the secure ODBC Driver 18 settings.
    ===================================================================== '''
server = 'DESKTOP-PSQN9E7' # YOUR_SERVER_NAME
database = 'MediaTrackerDB'

conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;'

''' =====================================================================
        2. FILE PATH & BATCH CONFIGURATION
        Update the file_path to match your local folder.
    ===================================================================== '''
file_path = 'D:/8b_MediaTrackerDB/game_genres_2026-09-28.csv'
batch_size = 50000

''' =====================================================================
        3. READ CSV AND LOAD DATA INTO SQL SERVER IN BATCHES
        Processing more than 500k rows in chunks to optimize memory and speed.
    ===================================================================== '''
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Enable fast bulk insert mode
    cursor.fast_executemany = True 
    
    # Clear the table before loading fresh data
    cursor.execute("TRUNCATE TABLE bgd.GameGenres")
    
    insert_query = """
    INSERT INTO bgd.GameGenres (
        [GameID], [GameName], [GenreID], [GenreName]
    ) VALUES (?, ?, ?, ?)
    """
    
    records_to_insert = []
    total_inserted = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        # Skip the header row (game_id, game_name, genre_id, genre_name)
        header = next(reader)
        
        for row in reader:
            game_id = int(row[0])
            game_name = row[1]
            
            # Handle empty values for nullable GenreID and GenreName columns
            genre_id = int(float(row[2])) if row[2] != '' else None
            genre_name = row[3] if row[3] != '' else None
            
            records_to_insert.append((game_id, game_name, genre_id, genre_name))
            
            # Execute insert when batch size is reached
            if len(records_to_insert) >= batch_size:
                cursor.executemany(insert_query, records_to_insert)
                conn.commit()
                total_inserted += len(records_to_insert)
                print(f"Progress: {total_inserted} rows inserted...")
                records_to_insert.clear()

        # Insert any remaining rows from the final batch
        if records_to_insert:
            cursor.executemany(insert_query, records_to_insert)
            conn.commit()
            total_inserted += len(records_to_insert)

    print(f"Success: All {total_inserted} rows have been loaded into bgd.GameGenres!")

except Exception as e:
    print("An error occurred during data load:")
    print(e)
    if 'conn' in locals():
        conn.rollback()

finally:
    ''' =====================================================================
            4. CLOSE CONNECTION
        ===================================================================== '''
    if 'conn' in locals():
        cursor.close()
        conn.close()