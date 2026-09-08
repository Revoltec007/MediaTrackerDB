import json
import pyodbc
import os

''' =====================================================================
        1. DATABASE CONNECTION SETUP
    ===================================================================== '''
server = 'YOUR_SERVER_NAME'
database = 'MediaTrackerDB'

conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'


''' =====================================================================
        2. FILE LOOP CONFIGURATION
        Set the range of your history files here.
    ===================================================================== '''

start_file = 1
end_file = 26

user_id = 11122233

''' =====================================================================
        UPDATED MEDIA TYPE MAPPING
        0 = Movie, 1 = Show, 2 = Episode
    ===================================================================== '''
def get_media_type_id(media_type):
    if media_type == 'movie':
        return 0
    elif media_type == 'show':
        return 1
    elif media_type == 'episode':
        return 2
    else:
        return 99 # Fallback for any unknown types

# Connect to the database outside the loop
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.fast_executemany = True

    insert_query = """
    INSERT INTO tkt.WatchedHistory (
        [WatchedID], [WatchedAt], [UserID], [MediaTypeID], 
        [ImdbID], [TmdbID], [TraktID], [ReleaseYear], [MovieTitle], 
        [EpisodeTitle], [ShowTitle], [Number], [Season], [AiredEpisodes]
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    print(f"Starting batch load for watched-history files from {start_file} to {end_file}...\n")

    for i in range(start_file, end_file + 1):
        file_path = rf'D:\1_MSSQL_Databases\watched-history-{i}.json'
        
        if not os.path.exists(file_path):
            print(f"File {file_path} not found. Skipping...")
            continue
            
        print(f"Processing: {file_path}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        records_to_insert = []
        
        for item in data:
            watched_id = item.get('id')
            watched_at = item.get('watched_at', '')[:10] if item.get('watched_at') else None
            
            media_type = item.get('type')
            media_type_id = get_media_type_id(media_type)
            
            imdb_id, tmdb_id, trakt_id, release_year = None, None, None, None
            movie_title, episode_title, show_title = None, None, None
            number, season, aired_episodes = None, None, None

            # Handle MOVIE parsing
            if media_type == 'movie':
                movie = item.get('movie', {})
                ids = movie.get('ids', {})
                
                imdb_id = ids.get('imdb')
                tmdb_id = int(ids.get('tmdb')) if ids.get('tmdb') is not None else None
                trakt_id = ids.get('trakt')
                release_year = movie.get('year')
                movie_title = movie.get('title')

            # Handle EPISODE parsing
            elif media_type == 'episode':
                show = item.get('show', {})
                episode = item.get('episode', {})
                
                show_ids = show.get('ids', {})
                episode_ids = episode.get('ids', {})
                
                imdb_id = show_ids.get('imdb') or episode_ids.get('imdb')
                tmdb_id = int(show_ids.get('tmdb')) if show_ids.get('tmdb') is not None else None
                trakt_id = show_ids.get('trakt')
                
                release_year = show.get('year')
                show_title = show.get('title')
                aired_episodes = show.get('aired_episodes')
                
                episode_title = episode.get('title')
                number = episode.get('number')
                season = episode.get('season')
                
            # Handle SHOW parsing (if an entire show is logged as watched)
            elif media_type == 'show':
                show = item.get('show', {})
                ids = show.get('ids', {})
                
                imdb_id = ids.get('imdb')
                tmdb_id = int(ids.get('tmdb')) if ids.get('tmdb') is not None else None
                trakt_id = ids.get('trakt')
                
                release_year = show.get('year')
                show_title = show.get('title')
                aired_episodes = show.get('aired_episodes')

            records_to_insert.append((
                watched_id, watched_at, user_id, media_type_id,
                imdb_id, tmdb_id, trakt_id, release_year, movie_title,
                episode_title, show_title, number, season, aired_episodes
            ))

        # We execute and commit per file
        try:
            cursor.executemany(insert_query, records_to_insert)
            conn.commit()
            print(f" -> SUCCESS: {len(records_to_insert)} rows loaded from {file_path}.")
        except Exception as file_error:
            conn.rollback()
            print(f"\n[!] ERROR in {file_path}. Rolling back this file only.")
            print(f"Details: {file_error}")
            print(f"Fix the error, set start_file = {i} and run again.")
            break # Stop the loop so you can fix the issue

except Exception as e:
    print("A critical database connection error occurred:")
    print(e)

finally:
    if 'conn' in locals():
        cursor.close()
        conn.close()
        print("\nDatabase connection closed.")