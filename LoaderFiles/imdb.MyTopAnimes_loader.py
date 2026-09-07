import pandas as pd
import pyodbc
import numpy as np
import io

''' =====================================================================
        1. DATABASE CONNECTION SETUP
        Set your local MS SQL Server details here.
    ===================================================================== '''
server = 'YOUR_SERVER_NAME'
database = 'MediaTrackerDB'

conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

''' =====================================================================
        2. READ AND CLEAN CSV FILE
        Fixed encoding to 'latin1' to avoid UnicodeDecodeError with special chars.
    ==================================================================== '''
file_path = r'D:\1_MSSQL_Databases\my_top_animes.csv' 

with open(file_path, 'r', encoding='latin1') as f:
    lines = f.readlines()

cleaned_lines = [lines[0]]
for line in lines[1:]:
    line = line.strip()
    # Remove outer quotes and unescape inner quotes if the row is wrapped
    if line.startswith('"') and line.endswith('"'):
        line = line[1:-1].replace('""', '"')
    cleaned_lines.append(line + '\n')

df = pd.read_csv(io.StringIO("".join(cleaned_lines)))

''' =====================================================================
        3. DATA TRANSFORMATION & MAPPING
        Map IMDb CSV column names to our exact SQL Server schema names.
    ===================================================================== '''
column_mapping = {
    'Original Title': 'OriginalTitle',
    'Title Type': 'TitleType',
    'IMDb Rating': 'IMDBRating',
    'Runtime (mins)': 'RuntimeMins',
    'Num Votes': 'NumVotes',
    'Release Date': 'ReleaseDate',
    'Your Rating': 'YourRating',
    'Date Rated': 'DateRated'
}
df = df.rename(columns=column_mapping)

# Format all potential date columns (replace '.' with '-')
date_columns = ['Created', 'Modified', 'ReleaseDate', 'DateRated']
for col in date_columns:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace('.', '-', regex=False)
        # Convert "nan" or "None" strings back to actual NaN
        df[col] = df[col].replace(['nan', 'None', ''], np.nan)

# Replace NaN values with Python None for correct SQL NULL insertion
df = df.replace({np.nan: None})

# Reorder the DataFrame columns to match the target SQL table schema exactly
columns_to_insert = [
    'Const', 'Position', 'Created', 'Modified', 'Description', 
    'Title', 'OriginalTitle', 'URL', 'TitleType', 'IMDBRating', 
    'RuntimeMins', 'Year', 'Genres', 'NumVotes', 'ReleaseDate', 
    'Directors', 'YourRating', 'DateRated'
]
df = df[columns_to_insert]

''' =====================================================================
        4. LOAD DATA INTO SQL SERVER
        Connect, truncate old data, and bulk insert.
    ===================================================================== '''
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Enable fast bulk insert
    cursor.fast_executemany = True 
    
    # Clear the table before loading new data
    cursor.execute("TRUNCATE TABLE imdb.MyTopAnimes")
    
    # Prepare the INSERT query with 18 parameters
    insert_query = """
    INSERT INTO imdb.MyTopAnimes (
        [Const], [Position], [Created], [Modified], [Description], 
        [Title], [OriginalTitle], [URL], [TitleType], [IMDBRating], 
        [RuntimeMins], [Year], [Genres], [NumVotes], [ReleaseDate], 
        [Directors], [YourRating], [DateRated]
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # Convert DataFrame to a list of lists and insert
    data_to_insert = df.values.tolist()
    cursor.executemany(insert_query, data_to_insert)
    
    conn.commit()
    print(f"Success: {len(df)} rows have been loaded into imdb.MyTopAnimes!")

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