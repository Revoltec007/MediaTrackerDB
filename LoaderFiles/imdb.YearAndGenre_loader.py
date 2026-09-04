import pandas as pd
import pyodbc
import numpy as np

''' =====================================================================
        1. DATABASE CONNECTION SETUP
        Here we enter the local MS SQL server data.
    ===================================================================== '''
server = 'YOUR_SERVER_NAME' 
database = 'YOUR_DATABASE_NAME'

conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

''' =====================================================================
        2. READ TSV FILE AND CLEAN DATA
        Load the IMDb dataset. Since it's a TSV, we use sep='\t'.
        We only load the 4 columns needed for our dimension table.
    ===================================================================== '''
file_path = r'D:\1_MSSQL_Databases\imdb-export-user\title.basics.tsv'

# Read specific columns from the TSV file
columns_to_use = ['tconst', 'startYear', 'endYear', 'genres']
df = pd.read_csv(file_path, sep='\t', usecols=columns_to_use)

# IMDb uses '\N' to represent null values. Replace them with standard NaN.
df = df.replace(r'\\N', np.nan, regex=True)

# Drop rows where StartYear or Genres are missing, as the SQL table requires them (NOT NULL).
df = df.dropna(subset=['startYear', 'genres'])

# Convert NaN to Python None for correct SQL NULL insertion.
df = df.replace({np.nan: None})

''' =============================================================================
        3. LOAD DATA INTO SQL SERVER
        Connect to the database, truncate the old data, and insert the new rows.
    ============================================================================= '''
try:
    # Open connection
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.fast_executemany = True
    
    # Clear the table before loading new data (Full Load)
    cursor.execute("TRUNCATE TABLE imdb.YearAndGenre")
    
    # Prepare the INSERT INTO query
    insert_query = """
    INSERT INTO imdb.YearAndGenre (
        [Const], [StartYear], [EndYear], [Genres]
    ) VALUES (?, ?, ?, ?)
    """
    
    # Convert the DataFrame to a list of lists and then load it
    data_to_insert = df.values.tolist()
    total_rows = len(data_to_insert)
    
    chunk_size = 100000
    
    print(f"Loading starts... ALL together {total_rows} row is waiting for loading.")
    
    # Chunking) cycle
    for i in range(0, total_rows, chunk_size):
        chunk = data_to_insert[i : i + chunk_size]
        cursor.executemany(insert_query, chunk)
        
        # Print progress
        current_loaded = min(i + chunk_size, total_rows)
        print(f" -> Loaded: {current_loaded} / {total_rows} row")
      
    # Commit the transaction
    conn.commit()
    print("Success: IMDb dimension data has been loaded into MediaTrackerDB!")

except Exception as e:
    # Print error and rollback in case of failure
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