''' =====================================================================
    Use this file to fill up the dimension tables in the MediaTrackerDB database 
    if you already uploaded the game_infos csv into the database.
    ===================================================================== '''


USE MediaTrackerDB;
GO

-- 1. Dim_Genres
TRUNCATE TABLE bgd.Dim_Genres;
GO
INSERT INTO bgd.Dim_Genres (GenreID, GenreName)
SELECT 
    GenreID, 
    MAX(GenreName) AS GenreName
FROM bgd.GameGenres
WHERE GenreID IS NOT NULL
GROUP BY GenreID;
GO

-- 2. Dim_Themes
TRUNCATE TABLE bgd.Dim_Themes;
GO
INSERT INTO bgd.Dim_Themes (ThemeID, ThemeName)
SELECT 
    ThemeID, 
    MAX(ThemeName) AS ThemeName
FROM bgd.GameThemes
WHERE ThemeID IS NOT NULL
GROUP BY ThemeID;
GO

-- 3. Dim_Series
TRUNCATE TABLE bgd.Dim_Series;
GO
INSERT INTO bgd.Dim_Series (SeriesID, SeriesName)
SELECT 
    SeriesID, 
    MAX(SeriesName) AS SeriesName
FROM bgd.GameSeries
WHERE SeriesID IS NOT NULL
GROUP BY SeriesID;
GO

-- 4. Dim_Franchises
TRUNCATE TABLE bgd.Dim_Franchises;
GO
INSERT INTO bgd.Dim_Franchises (FranchiseID, FranchiseName)
SELECT 
    FranchiseID, 
    MAX(FranchiseName) AS FranchiseName
FROM bgd.GameFranchises
WHERE FranchiseID IS NOT NULL
GROUP BY FranchiseID;
GO