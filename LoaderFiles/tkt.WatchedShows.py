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
    ===================================================================== '''
file_path = r'D:\1_MSSQL_Databases\watched-shows.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

''' =====================================================================
        3. DATA TRANSFORMATION & FLATTENING
        Extract nested fields and convert date strings to standard DATE format.
    ===================================================================== '''
records_to_insert = []
user_id = 11122233          # Constant UserID for your profile

for item in data:
    # Extract the nested show object and ids
    show = item.get('show', {})
    ids = show.get('ids', {})
    
    # Flatten the necessary fields
    trakt_id = ids.get('trakt')
    
    # Slicing [:10] converts '2026-07-27T19:51:00.000Z' to '2026-07-27'
    last_updated_at = item.get('last_updated_at', '')[:10] if item.get('last_updated_at') else None
    last_watched_at = item.get('last_watched_at', '')[:10] if item.get('last_watched_at') else None
    
    imdb_id = ids.get('imdb')
    tmdb_id = int(ids.get('tmdb')) if ids.get('tmdb') is not None else None
    
    release_year = show.get('year')
    title = show.get('title')
    aired_episodes = show.get('aired_episodes')
    
    # Append as a tuple matching the SQL schema order
    records_to_insert.append((
        trakt_id, last_updated_at, last_watched_at, user_id,
        imdb_id, tmdb_id, release_year, title, aired_episodes
    ))

''' =====================================================================
        4. LOAD DATA INTO SQL SERVER
    ===================================================================== '''
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    cursor.fast_executemany = True 
    
    # Clear the table before loading new data
    cursor.execute("TRUNCATE TABLE tkt.WatchedShows")
    
    # Prepare the INSERT query
    insert_query = """
    INSERT INTO tkt.WatchedShows (
        [TraktID], [LastUpdatedAt], [LastWatchedAt], [UserID], 
        [ImdbID], [TmdbID], [ReleaseYear], [Title], [AiredEpisodes]
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # Execute bulk insert
    cursor.executemany(insert_query, records_to_insert)
    
    conn.commit()
    print(f"Success: {len(records_to_insert)} rows have been loaded into tkt.WatchedShows!")

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