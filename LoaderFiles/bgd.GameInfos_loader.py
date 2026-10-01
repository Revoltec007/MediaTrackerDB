import csv
import pyodbc

''' =====================================================================
    1. SETTING UP THE DATABASE CONNECTION
    ===================================================================== '''
server = 'YOUR_SERVER_NAME'
database = 'MediaTrackerDB'

conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;'

''' =====================================================================
    2. SETTING UP THE FILE PATH AND BATCH SIZE
    ===================================================================== '''
file_path = r'D:\8b_MediaTrackerDB\game_infos.csv' # Replace with the full path to your CSV file
batch_size = 50000

''' =====================================================================
    3. COMBINING CATEGORIES AND SQL QUERIES
    ===================================================================== '''
# We create separate lists (containers) for each dimension type.
data_batches = {
    'genre': [],
    'theme': [],
    'collection': [],
    'franchise': []
}

# We determine which category should be inserted into which table
insert_queries = {
    'genre': "INSERT INTO bgd.GameGenres ([GameID], [GameName], [GenreID], [GenreName]) VALUES (?, ?, ?, ?)",
    'theme': "INSERT INTO bgd.GameThemes ([GameID], [GameName], [ThemeID], [ThemeName]) VALUES (?, ?, ?, ?)",
    'collection': "INSERT INTO bgd.GameCollections ([GameID], [GameName], [CollectionID], [CollectionName]) VALUES (?, ?, ?, ?)",
    'franchise': "INSERT INTO bgd.GameFranchises ([GameID], [GameName], [FranchiseID], [FranchiseName]) VALUES (?, ?, ?, ?)"
}

''' =====================================================================
    4. CSV IMPORT AND DATA ROUTING
    ===================================================================== '''
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.fast_executemany = True 
    
    # Optional: Clearing the tables before the new full load
    cursor.execute("TRUNCATE TABLE bgd.GameGenres")
    cursor.execute("TRUNCATE TABLE bgd.GameThemes")
    cursor.execute("TRUNCATE TABLE bgd.GameCollections")
    cursor.execute("TRUNCATE TABLE bgd.GameFranchises")
    conn.commit()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        for row in reader:
            # Optional: Skipping empty or incomplete rows
            if not row or len(row) < 5:
                continue
                
            game_id = int(row[0]) if row[0] else None
            game_name = row[1].strip() if row[1] else None
            
            # We decide where the data should go based on the dim_type.
            dim_type = row[2].strip().lower() if row[2] else None
            
            # Cleaning: Trimming the superfluous ';;' from the end of the CSV.
            dim_id_str = row[3].strip()
            dim_name_str = row[4].replace(';;', '').strip()
            
            # Handling NULL values
            dim_id = int(float(dim_id_str)) if dim_id_str else None
            dim_name = dim_name_str if dim_name_str else None
            
            # If dim_type is included in our dictionary (genre, theme, collection, franchise)
            if dim_type in data_batches:
                
                # We don't store the `dim_type` column itself, only the 4 useful fields.
                data_batches[dim_type].append((game_id, game_name, dim_id, dim_name))
                
                ''' =====================================================================
                    5. LOADING DATA (IF THE BATCH IS FULL)
                    ===================================================================== '''
                if len(data_batches[dim_type]) >= batch_size:
                    cursor.executemany(insert_queries[dim_type], data_batches[dim_type])
                    conn.commit()
                    print(f"{batch_size} rows successfully loaded into: {dim_type}")
                    # Clear the list to allow the next batch to be processed
                    data_batches[dim_type].clear()
                    
        ''' =====================================================================
            6. REMAINING DATA LOADING AT THE END OF THE LOOP
            ===================================================================== '''
        for d_type, rows in data_batches.items():
            if rows:
                cursor.executemany(insert_queries[d_type], rows)
                conn.commit()
                print(f"Remaining {len(rows)} rows successfully loaded into: {d_type}")
                
    print("All data sorted and successfully loaded into the final tables!")

except Exception as e:
    print("An error occurred during loading:")
    print(e)
    if 'conn' in locals():
        conn.rollback()
        
finally:
    # Close connection
    if 'conn' in locals():
        cursor.close()
        conn.close()