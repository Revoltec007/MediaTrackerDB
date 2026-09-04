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
        IMDb exports often wrap entire data rows in double quotes. 
        We need to read the raw text and clean it before passing it to pandas.
    ===================================================================== '''
file_path = r'D:\1_MSSQL_Databases\favorite_composers.csv'

# Open and clean the file line by line
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

cleaned_lines = [lines[0]] # Keep the header row as is
for line in lines[1:]:
    line = line.strip()
    # Remove outer quotes and unescape inner quotes if the row is wrapped
    if line.startswith('"') and line.endswith('"'):
        line = line[1:-1].replace('""', '"')
    cleaned_lines.append(line + '\n')

# Load the cleaned string data into a pandas DataFrame
df = pd.read_csv(io.StringIO("".join(cleaned_lines)))

''' =====================================================================
        3. DATA TRANSFORMATION
        Format dates, handle NULLs, and add missing required columns.
    ===================================================================== '''

# Format the 'Birth Date' to YYYY-MM-DD so SQL Server recognizes it as DATE
if 'Birth Date' in df.columns:
    df['Birth Date'] = df['Birth Date'].str.replace('.', '-', regex=False)

# Replace NaN values with Python None for correct SQL NULL insertion
df = df.replace({np.nan: None})

# Add the UserID column with your personal ID
df['UserID'] = 99011122

# Reorder the DataFrame columns to match the target SQL table schema exactly
columns_to_insert = [
    'Const', 'Position', 'Created', 'Modified', 
    'Description', 'Name', 'Known For', 'Birth Date', 'UserID'
]
df = df[columns_to_insert]

''' =====================================================================
        4. LOAD DATA INTO SQL SERVER
        Connect to the database, truncate old data, and insert the new rows.
    ===================================================================== '''
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Clear the table before loading new data (Full Load)
    cursor.execute("TRUNCATE TABLE imdb.FavoriteComposers")
    
    # Prepare the INSERT INTO query
    insert_query = """
    INSERT INTO imdb.FavoriteComposers (
        [Const], [Position], [Created], [Modified], 
        [Description], [Name], [KnownFor], [BirthDate], [UserID]
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # Convert DataFrame to a list of lists and insert
    data_to_insert = df.values.tolist()
    cursor.executemany(insert_query, data_to_insert)
    
    conn.commit()
    print(f"Success: {len(df)} rows have been loaded into imdb.FavoriteComposers!")

except Exception as e:
    # Print error and rollback in case of failure
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