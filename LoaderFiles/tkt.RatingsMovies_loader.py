import json
import pyodbc

''' =====================================================================
        1. DATABASE CONNECTION SETUP
    ===================================================================== '''
server = 'YOUR_SERVER_NAME'
database = 'MediaTrackerDB'

conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;'

''' =====================================================================
        2. READ AND PARSE JSON FILE
    ===================================================================== '''
file_path = 'D:/1_MSSQL_Databases/Interesting/ratings-movies.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

''' =====================================================================
        3. DATA TRANSFORMATION & FLATTENING
        Expanding nested JSON and formatting the date.
    ===================================================================== '''
records_to_insert = []

for item in data:
    # Truncating the date to the first 10 characters (YYYY-MM-DD)
    rated_at = item.get('rated_at', '')[:10] if item.get('rated_at') else None
    rating = item.get('rating')
    
    # Since this is the ratings-movies file, the MediaTypeID is fixed at 0 (Movie).
    media_type_id = 0
    
    movie = item.get('movie', {})
    ids = movie.get('ids', {})
    
    trakt_id = ids.get('trakt')
    title = movie.get('title')
    release_year = movie.get('year')
    
    imdb_id = ids.get('imdb')
    tmdb_id = int(ids.get('tmdb')) if ids.get('tmdb') is not None else None
    
    # The tuple follows the column order of the SQL table exactly.
    records_to_insert.append((
        trakt_id, rated_at, rating, media_type_id,
        title, release_year, imdb_id, tmdb_id
    ))

''' =====================================================================
        4. LOAD DATA INTO SQL SERVER
    ===================================================================== '''
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    cursor.fast_executemany = True 
    
    # Clearing the table before loading new, updated data
    cursor.execute("TRUNCATE TABLE tkt.RatingsMovies")
    
    insert_query = """
    INSERT INTO tkt.RatingsMovies (
        [TraktID], [RatedAt], [Rating], [MediaTypeID], 
        [Title], [ReleaseYear], [ImdbID], [TmdbID]
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    cursor.executemany(insert_query, records_to_insert)
    conn.commit()
    print(f"Success: {len(records_to_insert)} rows have been loaded into tkt.RatingsMovies!")

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