import requests
import json
import datetime
import time
import os

# --- Constants ---
# API Endpoints
SQUAD_LIST_URL = "https://wbapi.wbpjs.com/squad/getSquadList"
SQUAD_MEMBERS_URL = "https://wbapi.wbpjs.com/squad/getSquadMembers?squadName={}"
PLAYER_STATS_URL = "https://wbapi.wbpjs.com/players/getPlayer?uid={}"

# Output File
RANKING_DATA_FILE = 'squad_rankings.json'

# --- Main Data Collection Function ---
def generate_ranking_data():
    """Fetches data for all squads and generates a ranking JSON."""
    all_squads = []
    try:
        response = requests.get(SQUAD_LIST_URL)
        response.raise_for_status()
        all_squads = response.json()
        print(f"Fetched {len(all_squads)} squads.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching squad list: {e}")
        return

    squad_stats_all = {}
    total_processed_squads = 0

    for squad_name in all_squads:
        squad_name_clean = squad_name.replace(" ", "%20")
        
        print(f"  > Processing squad: {squad_name}")

        member_data = []
        try:
            response = requests.get(SQUAD_MEMBERS_URL.format(squad_name_clean))
            response.raise_for_status()
            member_data = response.json()
        except requests.exceptions.RequestException:
            print(f"    - Failed to fetch members for {squad_name}. Skipping.")
            continue
        
        if not member_data:
            print(f"    - No members found for {squad_name}. Skipping.")
            continue

        squad_levels = []
        squad_kills_elo = []
        squad_games_elo = []
        total_wins = 0
        total_losses = 0
        
        for member in member_data:
            uid = member.get("uid")
            if not uid:
                continue

            try:
                response = requests.get(PLAYER_STATS_URL.format(uid))
                response.raise_for_status()
                player_stats = response.json()
                
                squad_levels.append(player_stats.get("level", 0))
                squad_kills_elo.append(player_stats.get("killsELO", 0))
                squad_games_elo.append(player_stats.get("gamesELO", 0))
                
                wins_m00 = player_stats.get("wins", {}).get("m00", 0)
                losses_m00 = player_stats.get("losses", {}).get("m00", 0)
                total_wins += wins_m00
                total_losses += losses_m00
            except requests.exceptions.RequestException:
                print(f"    - Failed to fetch stats for player {uid}. Skipping.")
                continue

        if squad_levels:
            squad_stats_all[squad_name] = {
                "level": sum(squad_levels) / len(squad_levels),
                "killsELO": sum(squad_kills_elo) / len(squad_kills_elo),
                "gamesELO": sum(squad_games_elo) / len(squad_games_elo),
                "wins": total_wins,
                "losses": total_losses
            }
        
        total_processed_squads += 1
        print(f"  > Done processing {squad_name}. Total squads processed: {total_processed_squads}.")
        time.sleep(1) # Delay between squads to prevent API rate limiting

    # Final data structure for JSON
    final_data = {
        "last_updated": datetime.datetime.now(datetime.timezone.utc).timestamp(),
        "squad_stats": squad_stats_all
    }

    # Save the data
    with open(RANKING_DATA_FILE, 'w') as f:
        json.dump(final_data, f, indent=4)
    
    print(f"\nSuccessfully generated {RANKING_DATA_FILE} with data for {len(squad_stats_all)} squads.")

if __name__ == '__main__':
    generate_ranking_data()