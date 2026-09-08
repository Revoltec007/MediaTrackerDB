import json
import pyodbc

''' =====================================================================
        1. DATABASE CONNECTION SETUP
    ===================================================================== '''
server = 'YOUR_SERVER_NAME'
database = 'MediaTrackerDB'

conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

''' =====================================================================
        2. READ AND PARSE JSON FILE
    ==================================================================== '''
file_path = r'D:\watched-movies-1.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

''' =====================================================================
        3. DATA TRANSFORMATION & FLATTENING
    ===================================================================== '''
records_to_insert = []
user_id = 11122233 # Constant UserID for your profile

for item in data:
    # Extract the nested movie object and its ids
    movie = item.get('movie', {})
    ids = movie.get('ids', {})
    
    # Flatten the necessary fields
    trakt_id = ids.get('trakt')
    
    # Slicing [:10] converts '2026-08-16T20:44:01.000Z' to '2026-08-16'
    last_updated_at = item.get('last_updated_at', '')[:10] if item.get('last_updated_at') else None
    last_watched_at = item.get('last_watched_at', '')[:10] if item.get('last_watched_at') else None
    
    imdb_id = ids.get('imdb')
    tmdb_id = int(ids.get('tmdb')) if ids.get('tmdb') is not None else None
    
    release_year = movie.get('year')
    title = movie.get('title')
    plays = item.get('plays')
    
    # Append as a tuple matching the SQL schema order perfectly
    records_to_insert.append((
        trakt_id, last_updated_at, last_watched_at, user_id,
        imdb_id, tmdb_id, release_year, title, plays
    ))

''' =====================================================================
        4. LOAD DATA INTO SQL SERVER (APPEND ONLY)
    ===================================================================== '''
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Enable fast bulk insert
    cursor.fast_executemany = True 
    
    # Note: TRUNCATE TABLE statement is intentionally omitted here to allow appending multiple JSON export files sequentially.
    
    # Prepare the INSERT query
    insert_query = """
    INSERT INTO tkt.WatchedMovies (
        [TraktID], [LastUdatedAt], [LastWatchedAt], [UserID], 
        [ImdbID], [TmdbID], [ReleaseYear], [Title], [Plays]
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # Execute bulk insert
    cursor.executemany(insert_query, records_to_insert)
    
    conn.commit()
    print(f"Success: {len(records_to_insert)} rows have been appended to tkt.WatchedMovies!")

except Exception as e:
    print("An error occurred during data load:")
    print(e)
    if 'conn' in locals():
        conn.rollback()

finally:
    ''' =====================================================================
            5. CLOSE CONNECTION
        ===================================================================== '''
    if 'conn' in locals():
        cursor.close()
        conn.close()