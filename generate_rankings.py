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
        
        if not member_data or not isinstance(member_data, list):
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
                
                # FIX: Robustly handle wins/losses data type
                player_wins_data = player_stats.get("wins")
                if isinstance(player_wins_data, dict):
                    wins_m00 = player_wins_data.get("m00", 0)
                else:
                    wins_m00 = 0 # Default to 0 if not a dict
                    print(f"    - Warning: 'wins' data for player {uid} is not a dict. Defaulting to 0 wins.")

                player_losses_data = player_stats.get("losses")
                if isinstance(player_losses_data, dict):
                    losses_m00 = player_losses_data.get("m00", 0)
                else:
                    losses_m00 = 0 # Default to 0 if not a dict
                    print(f"    - Warning: 'losses' data for player {uid} is not a dict. Defaulting to 0 losses.")

                total_wins += wins_m00
                total_losses += losses_m00
            except requests.exceptions.RequestException:
                print(f"    - Failed to fetch stats for player {uid}. Skipping.")
                continue

        if squad_levels: # Check if there's any valid player data to average
            squad_stats_all[squad_name] = {
                "level": sum(squad_levels) / len(squad_levels),
                "killsELO": sum(squad_kills_elo) / len(squad_kills_elo),
                "gamesELO": sum(squad_games_elo) / len(squad_games_elo),
                "wins": total_wins,
                "losses": total_losses
            }
        else: # If no valid member data for stats, set averages to 0
             squad_stats_all[squad_name] = {
                "level": 0,
                "killsELO": 0,
                "gamesELO": 0,
                "wins": 0,
                "losses": 0
            }
        
        total_processed_squads += 1
        print(f"  > Done processing {squad_name}. Total squads processed: {total_processed_squads}.")
        time.sleep(0.1) # Reduced delay to 0.1s; 1s might be too slow for 500+ squads

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