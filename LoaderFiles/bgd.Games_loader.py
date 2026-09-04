import pandas as pd
import pyodbc
import numpy as np

''' ==================================================================
        1. SETTING UP DATABASE CONNECTION
        Here we enter the local MS SQL server data.
    ================================================================== '''
server = 'YOUR_SERVER_NAME' 
database = 'YOUR_DATABASE_NAME'

# Using Windows Authentication (Trusted Connection)
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

''' ==================================================================
        2. CSV FILE LOADING AND DATA CLEANING
        We load the Backloggd data from the file.
    ================================================================== '''
file_path = r'D:\1_MSSQL_Databases\backloggd-user-2026-08-20.csv'
df = pd.read_csv(file_path)

# Pandas treats missing data (e.g., empty date or rating) as NaN.
# We need to convert these to Python None type, in accordance with SQL Server NULL values.
df = df.replace({np.nan: None})

''' ==================================================================
        3. LOADING DATA INTO SQL TABLE
        We connect to the database, truncate the existing data
        (Full Load), then insert the new data row by row.
    ================================================================== '''
try:
    # Open a connection
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Emptying the table first, before loading an updated CSV
    cursor.execute("TRUNCATE TABLE bgd.Games")
    
    # Preparing the INSERT INTO query with the 23 columns
    insert_query = """
    INSERT INTO bgd.Games (
        [ID], [GameName], [Played], [CurrentlyPlaying], [InBacklog], 
        [InWishlist], [Liked], [Rating], [Mastered], [StartDate], 
        [FinishDate], [TotalHours], [TotalMinutes], [PlaythroughHours], 
        [PlaythroughMinutes], [PlaythroughHourstoFinish], 
        [PlaythroughMinutestoFinish], [PlaythroughHourstoMaster], 
        [PlaythroughMinutestoMaster], [Replay], [Review], 
        [ReviewContainsSpoilers], [BackloggdURL]
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # We go through the rows of the DataFrame and insert them with parameters
    for index, row in df.iterrows():
        # Convert the elements of row to tuple for pyodbc
        cursor.execute(insert_query, tuple(row))
        
    # Commit transaction
    conn.commit()
    print("Successful operation: Backloggd data loaded into the MediaTrackerDB database!")

except Exception as e:
    # In case of an error, we print the error message and roll back the changes
    print("An error occurred while loading:")
    print(e)
    if 'conn' in locals():
        conn.rollback()

finally:
    ''' ==============================================================
        4. CLOSE CONNECTION
    ================================================================== '''
    if 'conn' in locals():
        cursor.close()
        conn.close()