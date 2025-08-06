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
    total_api_calls_made = 0

    print("Starting detailed data collection for each squad...")

    for squad_name in all_squads:
        squad_name_clean = squad_name.replace(" ", "%20")
        
        print(f"  > Processing squad: {squad_name}")

        member_data = []
        try:
            response = requests.get(SQUAD_MEMBERS_URL.format(squad_name_clean))
            response.raise_for_status()
            member_data = response.json()
            total_api_calls_made += 1
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
        total_kills_per_vehicle = 0
        total_kills_per_weapon = 0
        total_deaths = 0
        total_coins = 0
        
        for member in member_data:
            uid = member.get("uid")
            if not uid:
                continue

            try:
                response = requests.get(PLAYER_STATS_URL.format(uid))
                response.raise_for_status()
                player_stats = response.json()
                total_api_calls_made += 1
                
                squad_levels.append(player_stats.get("level", 0))
                squad_kills_elo.append(player_stats.get("killsELO", 0))
                squad_games_elo.append(player_stats.get("gamesELO", 0))
                
                # FIX: Explicitly check if data is a dictionary before trying to sum it.
                player_wins_data = player_stats.get("wins")
                if isinstance(player_wins_data, dict):
                    total_wins += player_wins_data.get("m00", 0)

                player_losses_data = player_stats.get("losses")
                if isinstance(player_losses_data, dict):
                    total_losses += player_losses_data.get("m00", 0)
                
                kills_per_vehicle_data = player_stats.get("kills_per_vehicle")
                if isinstance(kills_per_vehicle_data, dict):
                    total_kills_per_vehicle += sum(kills_per_vehicle_data.values())
                
                kills_per_weapon_data = player_stats.get("kills_per_weapon")
                if isinstance(kills_per_weapon_data, dict):
                    total_kills_per_weapon += sum(kills_per_weapon_data.values())
                
                deaths_data = player_stats.get("deaths")
                if isinstance(deaths_data, dict):
                    total_deaths += sum(deaths_data.values())
                
                total_coins += player_stats.get("coins", 0)

            except requests.exceptions.RequestException:
                print(f"    - Failed to fetch stats for player {uid}. Skipping.")
                continue
            except (ValueError, TypeError) as e:
                print(f"    - Error parsing player stats for {uid}: {e}. Skipping.")
                continue

            time.sleep(0.05)

        if squad_levels:
            squad_stats_all[squad_name] = {
                "level": sum(squad_levels) / len(squad_levels),
                "killsELO": sum(squad_kills_elo) / len(squad_kills_elo),
                "gamesELO": sum(squad_games_elo) / len(squad_games_elo),
                "wins": total_wins,
                "losses": total_losses,
                "kills_per_vehicle": total_kills_per_vehicle,
                "kills_per_weapon": total_kills_per_weapon,
                "deaths": total_deaths,
                "coins": total_coins
            }
        else:
             squad_stats_all[squad_name] = {
                "level": 0, "killsELO": 0, "gamesELO": 0,
                "wins": 0, "losses": 0,
                "kills_per_vehicle": 0, "kills_per_weapon": 0, "deaths": 0, "coins": 0
            }
        
        print(f"  > Done processing {squad_name}. Total squads processed: {len(squad_stats_all)}.")
        time.sleep(0.5)

    final_data = {
        "last_updated": datetime.datetime.now(datetime.timezone.utc).timestamp(),
        "squad_stats": squad_stats_all
    }

    with open(RANKING_DATA_FILE, 'w') as f:
        json.dump(final_data, f, indent=4)
    
    print(f"\nSuccessfully generated {RANKING_DATA_FILE} with data for {len(squad_stats_all)} squads.")
    print(f"Total API calls made during this update: {total_api_calls_made}")

if __name__ == '__main__':
    generate_ranking_data()