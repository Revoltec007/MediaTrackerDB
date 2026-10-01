from dotenv import load_dotenv
load_dotenv()
import os
import csv
import json
import time
from igdb.wrapper import IGDBWrapper

''' You will need a Twitch Developers Account with a registered application to get your Client ID and Access Token.
    
    Important:
    Rate Limit: The API allows only 4 requests per second

    Step 1: pip install igdb-api-v4

    Step 2: Get Your Twitch Credentials
    Go to the Twitch Developer Console and log in. https://dev.twitch.tv/console/apps
    Register a new application. Set the Client Type to Confidential and use localhost for the OAuth Redirect URL.
    Once created, you'll see your Client ID. Click "New Secret" to generate your Client Secret. Keep these safe; don't commit them to code.
    https://docs.romm.app/3.10.2/Getting-Started/Metadata-Providers/#igdb '''


# Store these in environment variables in your .env file for security.
CLIENT_ID = os.environ["TWITCH_CLIENT_ID"]
ACCESS_TOKEN = os.environ["TWITCH_APP_ACCESS_TOKEN"]

# Initialize the wrapper
wrapper = IGDBWrapper(CLIENT_ID, ACCESS_TOKEN)

PAGE_SIZE = 500  # IGDB max
OUTPUT_FILE = "game_infos.csv"

def fetch_page(offset):
    query = (
        f"fields name,genres.name,themes.name,franchises.name,series.name; "
        f"limit {PAGE_SIZE}; offset {offset};"
    )
    raw = wrapper.api_request("games", query)
    return json.loads(raw.decode("utf-8"))


def join_names(items):
    #Extracts the names from a list (e.g., genres, themes), separated by semicolons.
    if not items:
        return ""
    return "; ".join(item.get("name", "") for item in items if item.get("name"))

def main():
    offset = 0
    total_games = 0
    total_rows = 0

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Long format: one row = one game × one dimension relationship
        writer.writerow([
            "game_id", "game_name",
            "dim_type", "dim_id", "dim_name"
        ])

        while True:
            try:
                games = fetch_page(offset)
            except Exception as e:
                print(f"Request failed at offset {offset}: {e}")
                time.sleep(2)
                continue

            if not games:
                break

            for game in games:
                game_id = game.get("id")
                game_name = game.get("name", "")

                # The four dimension types we want to extract
                dimensions = [
                    ("genre",      game.get("genres", [])),
                    ("theme",      game.get("themes", [])),
                    ("franchise",  game.get("franchises", [])),
                    ("series", game.get("series", [])),
                ]

                wrote_any = False
                for dim_type, items in dimensions:
                    for item in items:
                        dim_id = item.get("id")
                        dim_name = item.get("name", "")
                        if dim_id is None:
                            continue
                        writer.writerow([game_id, game_name, dim_type, dim_id, dim_name])
                        total_rows += 1
                        wrote_any = True

                # If the game has no dimensions, let's still write a line, so that the game itself remains in the fact table.
                if not wrote_any:
                    writer.writerow([game_id, game_name, "", "", ""])
                    total_rows += 1

                total_games += 1

            print(f"Fetched offset {offset}, running total: {total_games} games, {total_rows} rows")

            if len(games) < PAGE_SIZE:
                break

            offset += PAGE_SIZE
            time.sleep(0.3)  #Stay under 4 req/second

    print(f"\nDone. {total_games} games -> {total_rows} rows in {OUTPUT_FILE}")


if __name__ == "__main__":
    main()