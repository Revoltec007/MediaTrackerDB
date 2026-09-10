import json
import pyodbc

''' =====================================================================
        1. DATABASE CONNECTION SETUP
        Using the secure ODBC Driver 18 settings.
    ===================================================================== '''
server = 'YOUR_SERVER_NAME' 
database = 'MediaTrackerDB'

conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;'

''' =====================================================================
        2. MEDIA TYPE MAPPING
        0 = Movie, 1 = Show, 2 = Episode, 3 = Season
    ===================================================================== '''
def get_media_type_id(media_type):
    if media_type == 'movie':
        return 0
    elif media_type == 'show':
        return 1
    elif media_type == 'episode':
        return 2
    elif media_type == 'season':
        return 3
    else:
        return 99 # Fallback for unknown types

''' =====================================================================
        3. READ AND PARSE JSON FILE
        Update the path to match your actual directory structure.
    ===================================================================== '''
file_path = 'D:/1_MSSQL_Databases/Interesting/lists-list-30642107-anime-watchlist.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

''' =====================================================================
        4. DATA TRANSFORMATION & FLATTENING
        Extracting the necessary nested fields.
    ===================================================================== '''
records_to_insert = []

for item in data:
    list_id = item.get('id')
    rank = item.get('rank')
    
    # Truncate listed_at to YYYY-MM-DD
    listed_at = item.get('listed_at', '')[:10] if item.get('listed_at') else None
    
    media_type = item.get('type')
    media_type_id = get_media_type_id(media_type)
    
    imdb_id, tmdb_id, trakt_id, release_year = None, None, None, None
    title, aired_episodes = None, None

    # Parse based on the media type to get the correct nested object
    if media_type == 'movie':
        media_obj = item.get('movie', {})
    elif media_type in ['show', 'season', 'episode']:
        # Trakt lists usually nest the main show details inside 'show' even if the list item type is 'season' or 'episode'
        media_obj = item.get('show', {})
    else:
        media_obj = {} # Fallback

    # Extract IDs and details
    if media_obj:
        ids = media_obj.get('ids', {})
        
        # Safeguard: The SQL schema sets ImdbID to NOT NULL. Replace None with 'N/A' if missing.
        imdb_id = ids.get('imdb')
        if imdb_id is None:
            imdb_id = 'N/A'
            
        tmdb_id = int(ids.get('tmdb')) if ids.get('tmdb') is not None else None
        trakt_id = ids.get('trakt')
        
        release_year = media_obj.get('year')
        title = media_obj.get('title')
        
        # Aired episodes only exist for shows/seasons
        aired_episodes = media_obj.get('aired_episodes')

    # Append tuple matching the SQL schema order
    records_to_insert.append((
        list_id, media_type_id, imdb_id, tmdb_id, trakt_id,
        release_year, title, aired_episodes, rank, listed_at
    ))

''' =====================================================================
        5. LOAD DATA INTO SQL SERVER
    ===================================================================== '''
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    cursor.fast_executemany = True 
    
    # Truncate the table for a fresh reload
    cursor.execute("TRUNCATE TABLE tkt.ListsAnimeWatchlist")
    
    insert_query = """
    INSERT INTO tkt.ListsAnimeWatchlist (
        [ID], [MediaTypeID], [ImdbID], [TmdbID], [TraktID], 
        [ReleaseYear], [Title], [AiredEpisodes], [Rank], [ListedAt]
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    cursor.executemany(insert_query, records_to_insert)
    conn.commit()
    print(f"Success: {len(records_to_insert)} rows have been loaded into tkt.ListsAnimeWatchlist!")

except Exception as e:
    print("An error occurred during data load:")
    print(e)
    if 'conn' in locals():
        conn.rollback()

finally:
    ''' =====================================================================
        6. CLOSE CONNECTION
        ===================================================================== '''
    if 'conn' in locals():
        cursor.close()
        conn.close()