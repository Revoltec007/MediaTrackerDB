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
file_path = 'D:/Interesting/user-stats.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

''' =====================================================================
        # 3. DATA FLATTENING
        Flatten the nested JSON structure into a single tuple.
    ===================================================================== '''

user_id = 11112233

movies = data.get('movies', {})
shows = data.get('shows', {})
seasons = data.get('seasons', {})
episodes = data.get('episodes', {})
network = data.get('network', {})
ratings = data.get('ratings', {})
distribution = ratings.get('distribution', {})

# Create a single record mapping exactly to the 33 columns
record_to_insert = (
    user_id,
    movies.get('plays', 0), movies.get('watched', 0), movies.get('minutes', 0), 
    movies.get('collected', 0), movies.get('ratings', 0), movies.get('comments', 0),
    
    shows.get('watched', 0), shows.get('collected', 0), 
    shows.get('ratings', 0), shows.get('comments', 0),
    
    seasons.get('ratings', 0), seasons.get('comments', 0),
    
    episodes.get('plays', 0), episodes.get('watched', 0), episodes.get('minutes', 0), 
    episodes.get('collected', 0), episodes.get('ratings', 0), episodes.get('comments', 0),
    
    network.get('friends', 0), network.get('followers', 0), network.get('following', 0),
    
    ratings.get('total', 0),
    distribution.get('1', 0), distribution.get('2', 0), distribution.get('3', 0),
    distribution.get('4', 0), distribution.get('5', 0), distribution.get('6', 0),
    distribution.get('7', 0), distribution.get('8', 0), distribution.get('9', 0),
    distribution.get('10', 0)
)

''' =====================================================================
        4. LOAD DATA INTO SQL SERVER
    ===================================================================== '''
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Clear the table before loading the new stats (Full Load)
    cursor.execute("TRUNCATE TABLE tkt.UserStats")
    
    # Bracket notation is required due to dots in column names (e.g., [Movies.Plays])
    insert_query = """
    INSERT INTO tkt.UserStats (
        [UserStats.UserID], 
        [Movies.Plays], [Movies.Watched], [Movies.Minutes], [Movies.Collected], [Movies.Ratings], [Movies.Comments],
        [Shows.Watched], [Shows.Collected], [Shows.Ratings], [Shows.Comments],
        [Seasons.Ratings], [Seasons.Comments],
        [Episodes.Plays], [Episodes.Watched], [Episodes.Minutes], [Episodes.Collected], [Episodes.Ratings], [Episodes.Comments],
        [Network.Friends], [Network.Followers], [Network.Following],
        [Ratings.Total], 
        [Ratings.Rating_1], [Ratings.Rating_2], [Ratings.Rating_3], [Ratings.Rating_4], [Ratings.Rating_5], 
        [Ratings.Rating_6], [Ratings.Rating_7], [Ratings.Rating_8], [Ratings.Rating_9], [Ratings.Rating_10]
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
        ?, ?, ?
    )
    """
    
    cursor.execute(insert_query, record_to_insert)
    conn.commit()
    print("Success: User statistics have been loaded into tkt.UserStats!")

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