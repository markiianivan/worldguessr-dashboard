import pyarrow as pa
pa.set_memory_pool(pa.system_memory_pool())

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import requests
import time
import re
from datetime import datetime
from zoneinfo import ZoneInfo
import reverse_geocoder as rg
import plotly.express as px
import plotly.graph_objects as go

# Set page config
st.set_page_config(
    page_title="WorldGuessr Head-to-Head Dashboard",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom color mapping for consistency
COLORS = {
    'markiianivan': '#FF8C00', # Dark Orange
    'troutfly': '#1E90FF',      # Dodger Blue
    'draw': '#9CA3AF'          # Gray
}

# Geocoding Mappings
CONTINENT_MAP = {
    # Europe
    'DE': 'Europe', 'ES': 'Europe', 'FR': 'Europe', 'GB': 'Europe', 'RO': 'Europe',
    'SE': 'Europe', 'NO': 'Europe', 'PL': 'Europe', 'UA': 'Europe', 'HU': 'Europe',
    'IT': 'Europe', 'PT': 'Europe', 'CZ': 'Europe', 'CH': 'Europe', 'LT': 'Europe',
    'RS': 'Europe', 'BG': 'Europe', 'EE': 'Europe', 'BE': 'Europe', 'IE': 'Europe',
    'DK': 'Europe', 'SI': 'Europe', 'FI': 'Europe', 'HR': 'Europe', 'GR': 'Europe',
    'SK': 'Europe', 'AT': 'Europe', 'IS': 'Europe', 'LV': 'Europe', 'FO': 'Europe',
    'NL': 'Europe', 'AL': 'Europe', 'BA': 'Europe', 'LU': 'Europe', 'LI': 'Europe',
    'ME': 'Europe', 'MK': 'Europe', 'GL': 'Europe',
    # North America
    'US': 'North America', 'CA': 'North America', 'MX': 'North America',
    'PA': 'North America', 'DO': 'North America', 'GT': 'North America',
    'CR': 'North America', 'BZ': 'North America',
    # South America
    'BR': 'South America', 'AR': 'South America', 'PE': 'South America',
    'CO': 'South America', 'CL': 'South America', 'UY': 'South America',
    'BO': 'South America', 'EC': 'South America', 'PY': 'South America',
    # Asia
    'ID': 'Asia', 'PH': 'Asia', 'TR': 'Asia', 'JP': 'Asia', 'TH': 'Asia',
    'IN': 'Asia', 'VN': 'Asia', 'MY': 'Asia', 'KH': 'Asia', 'TW': 'Asia',
    'KR': 'Asia', 'BD': 'Asia', 'LK': 'Asia', 'OM': 'Asia', 'JO': 'Asia',
    'MN': 'Asia', 'QA': 'Asia', 'IL': 'Asia', 'PS': 'Asia', 'AE': 'Asia',
    'KZ': 'Asia', 'KG': 'Asia', 'BT': 'Asia', 'SG': 'Asia',
    # Africa
    'ZA': 'Africa', 'KE': 'Africa', 'NG': 'Africa', 'GH': 'Africa', 'SN': 'Africa',
    'BW': 'Africa', 'TN': 'Africa', 'NA': 'Africa', 'RW': 'Africa', 'UG': 'Africa',
    'LS': 'Africa',
    # Oceania
    'AU': 'Oceania', 'NZ': 'Oceania'
}

ISO2_TO_ISO3 = {
    'US': 'USA', 'AU': 'AUS', 'BR': 'BRA', 'MX': 'MEX', 'CA': 'CAN', 'ID': 'IDN', 'RU': 'RUS',
    'DE': 'DEU', 'PH': 'PHL', 'AR': 'ARG', 'ES': 'ESP', 'FR': 'FRA', 'TR': 'TUR', 'GB': 'GBR',
    'PE': 'PER', 'CO': 'COL', 'JP': 'JPN', 'TH': 'THA', 'RO': 'ROU', 'SE': 'SWE', 'NO': 'NOR',
    'PL': 'POL', 'CL': 'CHL', 'UA': 'UKR', 'HU': 'HUN', 'NZ': 'NZL', 'IT': 'ITA', 'ZA': 'ZAF',
    'IN': 'IND', 'KE': 'KEN', 'VN': 'VNM', 'PT': 'PRT', 'MY': 'MYS', 'KH': 'KHM', 'CZ': 'CZE',
    'NG': 'NGA', 'UY': 'URY', 'GH': 'GHA', 'TW': 'TWN', 'KR': 'KOR', 'CH': 'CHE', 'BD': 'BGD',
    'LK': 'LKA', 'PA': 'PAN', 'LT': 'LTU', 'BO': 'BOL', 'RS': 'SRB', 'BG': 'BGR', 'EE': 'EST',
    'EC': 'ECU', 'BE': 'BEL', 'IE': 'IRL', 'DK': 'DNK', 'SI': 'SVN', 'OM': 'OMN', 'JO': 'JOR',
    'FI': 'FIN', 'HR': 'HRV', 'GR': 'GRC', 'MN': 'MNG', 'SK': 'SVK', 'AT': 'AUT', 'QA': 'QAT',
    'IL': 'ISR', 'BW': 'BWA', 'IS': 'ISL', 'PS': 'PSE', 'TN': 'TUN', 'NA': 'NAM', 'AE': 'ARE',
    'DO': 'DOM', 'GT': 'GTM', 'CR': 'CRI', 'KZ': 'KAZ', 'LV': 'LVA', 'FO': 'FRO', 'GL': 'GRL',
    'NL': 'NLD', 'AL': 'ALB', 'RW': 'RWA', 'UG': 'UGA', 'BA': 'BIH', 'LS': 'LSO', 'LU': 'LUX',
    'KG': 'KGZ', 'LI': 'LIE', 'ME': 'MNE', 'BT': 'BTN', 'SG': 'SGP', 'MK': 'MKD', 'PY': 'PRY',
    'BZ': 'BLZ'
}

COUNTRY_NAME_MAP = {
    'US': 'United States', 'AU': 'Australia', 'BR': 'Brazil', 'MX': 'Mexico', 'CA': 'Canada',
    'ID': 'Indonesia', 'RU': 'Russia', 'DE': 'Germany', 'PH': 'Philippines', 'AR': 'Argentina',
    'ES': 'Spain', 'FR': 'France', 'TR': 'Turkey', 'GB': 'United Kingdom', 'PE': 'Peru',
    'CO': 'Colombia', 'JP': 'Japan', 'TH': 'Thailand', 'RO': 'Romania', 'SE': 'Sweden',
    'NO': 'Norway', 'PL': 'Poland', 'CL': 'Chile', 'UA': 'Ukraine', 'HU': 'Hungary',
    'NZ': 'New Zealand', 'IT': 'Italy', 'ZA': 'South Africa', 'IN': 'India', 'KE': 'Kenya',
    'VN': 'Vietnam', 'PT': 'Portugal', 'MY': 'Malaysia', 'KH': 'Cambodia', 'CZ': 'Czechia',
    'NG': 'Nigeria', 'UY': 'Uruguay', 'GH': 'Ghana', 'TW': 'Taiwan', 'KR': 'South Korea',
    'CH': 'Switzerland', 'BD': 'Bangladesh', 'LK': 'Sri Lanka', 'PA': 'Panama', 'LT': 'Lithuania',
    'BO': 'Bolivia', 'RS': 'Serbia', 'BG': 'Bulgaria', 'EE': 'Estonia', 'EC': 'Ecuador',
    'BE': 'Belgium', 'IE': 'Ireland', 'DK': 'Denmark', 'SI': 'Slovenia', 'OM': 'Oman',
    'SN': 'Senegal', 'JO': 'Jordan', 'FI': 'Finland', 'HR': 'Croatia', 'GR': 'Greece',
    'MN': 'Mongolia', 'SK': 'Slovakia', 'AT': 'Austria', 'QA': 'Qatar', 'IL': 'Israel',
    'BW': 'Botswana', 'IS': 'Iceland', 'PS': 'Palestine', 'TN': 'Tunisia', 'NA': 'Namibia',
    'AE': 'United Arab Emirates', 'DO': 'Dominican Republic', 'GT': 'Guatemala', 'CR': 'Costa Rica',
    'KZ': 'Kazakhstan', 'LV': 'Latvia', 'FO': 'Faroe Islands', 'GL': 'Greenland', 'NL': 'Netherlands',
    'AL': 'Albania', 'RW': 'Rwanda', 'UG': 'Uganda', 'BA': 'Bosnia and Herzegovina', 'LS': 'Lesotho',
    'LU': 'Luxembourg', 'KG': 'Kyrgyzstan', 'LI': 'Liechtenstein', 'ME': 'Montenegro', 'BT': 'Bhutan',
    'SG': 'Singapore', 'MK': 'North Macedonia', 'PY': 'Paraguay', 'BZ': 'Belize'
}

UKRAINE_OBLAST_MAP = {
    'Kiev': 'Kyiv Oblast',
    'Kyiv City': 'Kyiv Oblast',
    'Dnipropetrovsk': 'Dnipropetrovsk Oblast',
    'Chernihiv': 'Chernihiv Oblast',
    "Vinnyts'ka": 'Vinnytsia Oblast',
    'Lviv': 'Lviv Oblast',
    'Sumy': 'Sumy Oblast',
    'Poltava': 'Poltava Oblast',
    'Khmelnytskyi': 'Khmelnytskyi Oblast',
    'Cherkasy': 'Cherkasy Oblast',
    'Kirovohrad': 'Kirovohrad Oblast',
    'Zhytomyr': 'Zhytomyr Oblast',
    'Mykolaiv': 'Mykolaiv Oblast',
    'Odessa': 'Odessa Oblast',
    'Kharkiv': 'Kharkiv Oblast',
    'Ivano-Frankivsk': 'Ivano-Frankivsk Oblast',
    'Rivne': 'Rivne Oblast',
    'Zakarpattia': 'Zakarpattia Oblast',
    'Ternopil': 'Ternopil Oblast',
    'Volyn': 'Volyn Oblast',
    'Chernivtsi': 'Chernivtsi Oblast',
    'Zaporizhia': 'Zaporizhia Oblast',
    'Donetsk': 'Donetsk Oblast',
    'Kherson': 'Kherson Oblast',
    'Luhansk': 'Luhansk Oblast',
    # Border Areas
    'Lublin Voivodeship': 'Border (Poland)',
    'Kursk': 'Border (Russia)',
    'Botosani': 'Border (Romania)',
    'Satu Mare': 'Border (Romania)',
    'Maramures': 'Border (Romania)'
}

# --- 1. Token Safety & Ingestion ---
def get_default_token():
    # Try loading from local .token file first
    token_file = os.path.join(os.path.dirname(__file__), ".token")
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            pass
            
    # Fallback: Extract from export_history.py in the downloads directory
    try:
        history_script = "/Users/markiian-ivan/Downloads/WorldGuessr Analysis/export_history.py"
        if os.path.exists(history_script):
            with open(history_script, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.search(r'SECRET_TOKEN\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
    except Exception:
        pass
    return ""

def save_token_locally(token):
    token_file = os.path.join(os.path.dirname(__file__), ".token")
    try:
        with open(token_file, 'w', encoding='utf-8') as f:
            f.write(token.strip())
    except Exception:
        pass

def get_default_github_settings():
    repo = "markiianivan/worldguessr-dashboard"
    token = ""
    try:
        if "GITHUB_REPO" in st.secrets:
            repo = st.secrets["GITHUB_REPO"]
        if "GITHUB_TOKEN" in st.secrets:
            token = st.secrets["GITHUB_TOKEN"]
    except Exception:
        pass
    github_file = os.path.join(os.path.dirname(__file__), ".github_settings")
    if os.path.exists(github_file):
        try:
            with open(github_file, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
                if len(lines) >= 1 and lines[0].strip():
                    repo = lines[0].strip()
                if len(lines) >= 2 and lines[1].strip():
                    token = lines[1].strip()
        except Exception:
            pass
    return repo, token

def save_github_settings_locally(repo, token):
    github_file = os.path.join(os.path.dirname(__file__), ".github_settings")
    try:
        with open(github_file, 'w', encoding='utf-8') as f:
            f.write(f"{repo.strip()}\n{token.strip()}\n")
    except Exception:
        pass

def load_from_github(repo, filename, token=None):
    raw_url = f"https://raw.githubusercontent.com/{repo}/main/{filename}"
    try:
        res = requests.get(raw_url, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    if token:
        url = f"https://api.github.com/repos/{repo}/contents/{filename}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3.raw"
        }
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
    return None

def save_to_github(repo, token, filename, updated_data):
    url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    sha = None
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            sha = res.json().get("sha")
    except Exception:
        pass
    import base64
    content_str = json.dumps(updated_data, indent=4, ensure_ascii=False)
    content_base64 = base64.b64encode(content_str.encode('utf-8')).decode('utf-8')
    payload = {
        "message": "Sync game history via WorldGuessr Dashboard",
        "content": content_base64
    }
    if sha:
        payload["sha"] = sha
    try:
        res = requests.put(url, headers=headers, json=payload, timeout=20)
        if res.status_code in [200, 201]:
            return True
    except Exception:
        pass
    return False

# --- 2. Incremental Syncing Logic ---
def sync_worldguessr_data(secret_token, filepath, github_repo=None, github_token=None):
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": "https://www.worldguessr.com",
        "Referer": "https://www.worldguessr.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }
    
    history_url = "https://api.worldguessr.com/api/gameHistory"
    details_url = "https://api.worldguessr.com/api/gameDetails"
    
    # Load existing file (try GitHub first, fallback to local)
    local_data = []
    existing_ids = set()
    loaded_from_github = False
    
    if github_repo:
        try:
            github_data = load_from_github(github_repo, "worldguessr_full_history.json", github_token)
            if github_data is not None:
                local_data = github_data
                loaded_from_github = True
        except Exception as e:
            st.warning(f"Failed to load existing history from GitHub: {e}")
            
    if not loaded_from_github and os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                local_data = json.load(f)
        except Exception as e:
            st.error(f"Error loading existing local history: {e}")
            local_data = []
            
    existing_ids = {g.get('game', {}).get('gameId') for g in local_data if g.get('game', {}).get('gameId')}
    st.info(f"Sync starting. Currently have {len(local_data)} games in database.")
    
    current_page = 1
    total_pages = 1
    new_games = []
    stop_sync = False
    
    progress_bar = st.progress(0)
    status_box = st.empty()
    
    while current_page <= total_pages:
        status_box.text(f"Fetching history page {current_page}...")
        payload = {
            "secret": secret_token,
            "page": current_page,
            "limit": 10
        }
        
        try:
            res = requests.post(history_url, headers=headers, json=payload, timeout=10)
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            st.error(f"Failed to fetch history page {current_page}: {e}")
            break
            
        total_pages = data.get("pagination", {}).get("totalPages", 1)
        games = data.get("games", [])
        
        if not games:
            break
            
        for idx, game in enumerate(games):
            game_id = game.get("gameId")
            if not game_id:
                continue
                
            if game_id in existing_ids:
                status_box.text("Found first duplicate game. Incremental sync complete!")
                stop_sync = True
                break
                
            status_box.text(f"Fetching details for new game: {game_id}...")
            details_payload = {
                "secret": secret_token,
                "gameId": game_id
            }
            
            try:
                detail_res = requests.post(details_url, headers=headers, json=details_payload, timeout=10)
                detail_res.raise_for_status()
                new_games.append(detail_res.json())
            except Exception as e:
                st.warning(f"Failed to fetch details for {game_id}: {e}")
                
            time.sleep(1.5) # Polite delay
            
        # Update progress bar
        progress_val = min(1.0, current_page / max(1, total_pages))
        progress_bar.progress(progress_val)
        
        if stop_sync:
            break
            
        current_page += 1
        
    progress_bar.progress(1.0)
    status_box.empty()
    
    if new_games:
        # Prepend new games to keep newest-first order
        updated_data = new_games + local_data
        
        # Save to GitHub if repo and token are provided
        if github_repo and github_token:
            status_box.text("Uploading updated database to GitHub...")
            try:
                success = save_to_github(github_repo, github_token, "worldguessr_full_history.json", updated_data)
                if success:
                    st.success("Successfully uploaded synced data to GitHub!")
                else:
                    st.error("Failed to upload synced data to GitHub.")
            except Exception as e:
                st.error(f"Failed to upload to GitHub: {e}")
                
        # Save to file atomically to prevent file watcher race condition crashes
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        try:
            temp_filepath = filepath + ".tmp"
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, indent=4, ensure_ascii=False)
            os.replace(temp_filepath, filepath)
            st.success(f"Successfully added {len(new_games)} new matches! Total matches now: {len(updated_data)}")
            # Clear caches to force reload
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Failed to write updated data to file: {e}")
    else:
        st.success("No new matches found. Dashboard is up to date!")
        
    return False

# --- 3. Data Loading & Preprocessing ---
@st.cache_data(hash_funcs={float: lambda x: x})
def load_and_process_data(filepath, mtime, github_repo=None, github_token=None):
    raw_data = []
    loaded_from_github = False
    
    if github_repo:
        try:
            github_data = load_from_github(github_repo, "worldguessr_full_history.json", github_token)
            if github_data is not None:
                raw_data = github_data
                loaded_from_github = True
        except Exception as e:
            st.error(f"Failed to load from GitHub: {e}. Falling back to local file.")
            
    if not loaded_from_github:
        if not os.path.exists(filepath):
            return pd.DataFrame(), pd.DataFrame()
        with open(filepath, 'r') as f:
            raw_data = json.load(f)
        
    kyiv_tz = ZoneInfo("Europe/Kyiv")
    games_list = []
    rounds_list = []
    
    for item in raw_data:
        game = item.get('game', {})
        players = game.get('players', [])
        
        # Keep only games where both markiianivan and troutfly participated
        player_names = {p.get('username') for p in players if p.get('username')}
        if not ('markiianivan' in player_names and 'troutfly' in player_names):
            continue
            
        game_id = game.get('gameId')
        started_at_str = game.get('startedAt')
        if not started_at_str:
            continue
            
        # Parse UTC time and convert to Kyiv EEST/EET
        try:
            started_at_utc = datetime.fromisoformat(started_at_str.replace("Z", "+00:00"))
            started_at_kyiv = started_at_utc.astimezone(kyiv_tz)
        except Exception:
            continue
            
        # Classify Map location
        loc = game.get('settings', {}).get('location', 'unknown')
        if loc == 'all':
            map_type = 'World'
        elif 'ukraine' in loc.lower() or loc in ['umpacock-zov-ukraine', 'cities-of-ukraine']:
            map_type = 'Ukraine'
        elif loc == 'europe':
            map_type = 'Europe'
        else:
            map_type = 'Other'
            
        markiian_player = next((p for p in players if p.get('username') == 'markiianivan'), None)
        troutfly_player = next((p for p in players if p.get('username') == 'troutfly'), None)
        
        if not markiian_player or not troutfly_player:
            continue
            
        m_pts = markiian_player.get('totalPoints', 0)
        t_pts = troutfly_player.get('totalPoints', 0)
        
        # Winner resolution
        winner = None
        result = game.get('result', {})
        winner_id = result.get('winner')
        
        if winner_id == markiian_player.get('playerId'):
            winner = 'markiianivan'
        elif winner_id == troutfly_player.get('playerId'):
            winner = 'troutfly'
        else:
            # Fallback to total points comparison
            if m_pts > t_pts:
                winner = 'markiianivan'
            elif t_pts > m_pts:
                winner = 'troutfly'
            else:
                winner = 'draw'
                
        games_list.append({
            'game_id': game_id,
            'started_at': started_at_kyiv,
            'map_type': map_type,
            'location_id': loc,
            'total_rounds': game.get('settings', {}).get('rounds', 10),
            'm_points': m_pts,
            't_points': t_pts,
            'winner': winner
        })
        
        # Parse rounds
        for r in game.get('rounds', []):
            round_num = r.get('roundNumber')
            r_loc = r.get('location')
            if not r_loc or r_loc.get('lat') is None or r_loc.get('long') is None:
                continue
                
            lat, lon = r_loc['lat'], r_loc['long']
            all_guesses = r.get('allGuesses', [])
            m_guess = next((g for g in all_guesses if g.get('username') == 'markiianivan'), None)
            t_guess = next((g for g in all_guesses if g.get('username') == 'troutfly'), None)
            
            rounds_list.append({
                'game_id': game_id,
                'map_type': map_type,
                'round_number': round_num,
                'lat': lat,
                'lon': lon,
                'm_score': m_guess.get('points', 0) if m_guess else 0,
                't_score': t_guess.get('points', 0) if t_guess else 0,
                'm_time': m_guess.get('timeTaken', 0) if m_guess else 0,
                't_time': t_guess.get('timeTaken', 0) if t_guess else 0
            })
            
    df_games = pd.DataFrame(games_list)
    df_rounds = pd.DataFrame(rounds_list)
    
    # Reverse geocode round coordinates in batch (running single-threaded mode=1 for Streamlit safety)
    if not df_rounds.empty:
        coords = list(zip(df_rounds['lat'], df_rounds['lon']))
        geocoded = rg.search(coords, mode=1, verbose=False)
        
        df_rounds['country_code'] = [res.get('cc') for res in geocoded]
        df_rounds['admin1'] = [res.get('admin1') for res in geocoded]
        
        df_rounds['continent'] = df_rounds['country_code'].map(CONTINENT_MAP).fillna('Other')
        df_rounds['uk_oblast'] = df_rounds['admin1'].map(UKRAINE_OBLAST_MAP).fillna(df_rounds['admin1'] + ' Oblast')
        df_rounds['country_name'] = df_rounds['country_code'].map(COUNTRY_NAME_MAP).fillna(df_rounds['country_code'])
        df_rounds['iso3'] = df_rounds['country_code'].map(ISO2_TO_ISO3).fillna('UNK')
        
    return df_games, df_rounds

# --- 4. Sidebar Controls & Filtering ---
st.sidebar.markdown("<h1 style='color: #FF8C00; text-align: center; margin-bottom: 0px;'>🗺️ WORLDGUESSR</h1>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; margin-top: 0px; font-size: 0.9em; opacity: 0.8;'>H2H Match Analytics</p>", unsafe_allow_html=True)
st.sidebar.divider()

# Setup Config Variables
default_dir = "/Users/markiian-ivan/Downloads/WorldGuessr Analysis"
dir_path = st.sidebar.text_input("Raw Data Directory:", value=default_dir)

# Check for GitHub settings from secrets or local config first
default_github_repo, default_github_token = get_default_github_settings()

# Find JSON files in dir_path
json_files = []
if os.path.exists(dir_path) and os.path.isdir(dir_path):
    json_files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
    json_files.sort(key=lambda x: os.path.getmtime(os.path.join(dir_path, x)), reverse=True)

json_path = None
mtime = 0.0

if json_files:
    file_name = st.sidebar.selectbox("Select History File:", json_files)
    json_path = os.path.join(dir_path, file_name)
    mtime = os.path.getmtime(json_path)
elif default_github_repo:
    # If running in cloud and GitHub Repo is configured, bypass directory check
    json_path = os.path.join(os.path.dirname(__file__), "worldguessr_full_history.json")
    if os.path.exists(json_path):
        mtime = os.path.getmtime(json_path)
else:
    st.sidebar.error("No JSON files found in directory!")
    st.stop()

# Auto File Watcher running in a Streamlit fragment (checks for file changes every 3s)
@st.fragment(run_every=3)
def file_watcher_fragment(filepath, current_mtime):
    if filepath and os.path.exists(filepath):
        new_mtime = os.path.getmtime(filepath)
        if new_mtime != current_mtime:
            st.session_state.last_mtime = new_mtime
            st.rerun()

if json_path:
    file_watcher_fragment(json_path, mtime)

# Sync parameters
st.sidebar.divider()
st.sidebar.subheader("🔄 Sync Settings")

# Extract and mask default token
default_token = get_default_token()
token_input = st.sidebar.text_input(
    "API Secret Token:", 
    value=default_token,
    type="password",
    help="Your secret API token is masked. Clear it or enter a new one to update."
)

st.sidebar.markdown("---")
st.sidebar.subheader("🐙 GitHub Storage Settings")
github_repo_input = st.sidebar.text_input(
    "GitHub Repo:",
    value=default_github_repo,
    help="Format: username/repo"
)
github_token_input = st.sidebar.text_input(
    "GitHub Personal Access Token:",
    value=default_github_token,
    type="password",
    help="Your GitHub classic token to read and write database changes."
)

col_sync1, col_sync2 = st.sidebar.columns(2)
with col_sync1:
    if st.button("Sync History", use_container_width=True):
        if token_input:
            save_token_locally(token_input)
            if github_repo_input:
                save_github_settings_locally(github_repo_input, github_token_input)
            with st.spinner("Syncing latest games..."):
                did_update = sync_worldguessr_data(token_input, json_path, github_repo_input, github_token_input)
                if did_update:
                    st.rerun()
        else:
            st.error("Enter a token first!")
with col_sync2:
    if st.button("Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Load all data for bounds calculation before building filter widgets
df_games, df_rounds = load_and_process_data(json_path, mtime, github_repo_input, github_token_input)

if df_games.empty:
    st.warning("No valid games found with both players!")
    st.stop()

# --- Sidebar Match Filters ---
st.sidebar.divider()
st.sidebar.subheader("📅 Interactive Filters")

# Map Type Toggle
map_filter = st.sidebar.radio("Map Type Context:", ["All Maps", "World", "Ukraine"])

# Date range slider
min_date = df_games['started_at'].min().date()
max_date = df_games['started_at'].max().date()
date_range = st.sidebar.date_input(
    "Date Range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# Hour range slider
hour_range = st.sidebar.slider(
    "Hour of Day (Kyiv Time):",
    min_value=0, max_value=23,
    value=(0, 23),
    format="%02d:00"
)

# Time of Day Slots Multiselect
def get_time_of_day(hr):
    if 6 <= hr < 12: return 'Morning'
    elif 12 <= hr < 18: return 'Afternoon'
    elif 18 <= hr < 24: return 'Evening'
    else: return 'Night'

time_slots = st.sidebar.multiselect(
    "Time Slots:",
    options=['Morning', 'Afternoon', 'Evening', 'Night'],
    default=['Morning', 'Afternoon', 'Evening', 'Night']
)

# Apply filters to dataframes
df_games_filtered = df_games.copy()
df_games_filtered['date'] = df_games_filtered['started_at'].dt.date
df_games_filtered['hour'] = df_games_filtered['started_at'].dt.hour
df_games_filtered['time_of_day'] = df_games_filtered['hour'].apply(get_time_of_day)

df_games_filtered = df_games_filtered[
    (df_games_filtered['date'] >= start_date) & 
    (df_games_filtered['date'] <= end_date) & 
    (df_games_filtered['hour'] >= hour_range[0]) & 
    (df_games_filtered['hour'] <= hour_range[1]) & 
    (df_games_filtered['time_of_day'].isin(time_slots))
]

if map_filter == "World":
    df_games_filtered = df_games_filtered[df_games_filtered['map_type'] == 'World']
elif map_filter == "Ukraine":
    df_games_filtered = df_games_filtered[df_games_filtered['map_type'] == 'Ukraine']

# Sync rounds to filtered games
df_rounds_filtered = df_rounds[df_rounds['game_id'].isin(df_games_filtered['game_id'])]

# Active dataset info
st.sidebar.divider()
st.sidebar.markdown(
    f"""
    <div style='background-color: #1F2937; padding: 10px; border-radius: 8px; border: 1px solid #FF8C00; font-size: 0.85em;'>
        <b>Matches loaded:</b> <code style='color: #FF8C00;'>{len(df_games_filtered)}</code><br/>
        <b>Rounds loaded:</b> <code style='color: #FF8C00;'>{len(df_rounds_filtered)}</code><br/>
        <b>Timezone:</b> Europe/Kyiv (EEST)
    </div>
    """,
    unsafe_allow_html=True
)

# --- 5. Main UI Header ---
st.markdown("<h1 style='margin-bottom: 0px;'>⚔️ WorldGuessr Head-to-Head Analytics</h1>", unsafe_allow_html=True)
st.markdown(
    f"<p style='font-size: 1.1em; opacity: 0.8;'>H2H Match history analysis of "
    f"<span style='color: #FF8C00; font-weight: bold;'>markiianivan</span> vs "
    f"<span style='color: #1E90FF; font-weight: bold;'>troutfly</span> — filtering on <b>{map_filter}</b></p>",
    unsafe_allow_html=True
)

# Create layout tabs (adding a dedicated Interactive Round Map page)
tab_overview, tab_momentum, tab_heatmap, tab_fatigue, tab_geography, tab_round_map = st.tabs([
    "📊 Overview", 
    "📈 Momentum Tracker", 
    "🔥 Time/Day Heatmap", 
    "📉 Fatigue Curves", 
    "🌍 Geospatial Insights",
    "📍 Interactive Round Map"
])

# --- Tab 1: Overview & KPI Cards ---
with tab_overview:
    # Calculations for stats
    tot_matches = len(df_games_filtered)
    
    m_wins = sum(df_games_filtered['winner'] == 'markiianivan')
    t_wins = sum(df_games_filtered['winner'] == 'troutfly')
    draws = sum(df_games_filtered['winner'] == 'draw')
    
    m_win_pct = (m_wins / tot_matches * 100) if tot_matches > 0 else 0
    t_win_pct = (t_wins / tot_matches * 100) if tot_matches > 0 else 0
    
    m_avg_pts = df_games_filtered['m_points'].mean() if tot_matches > 0 else 0
    t_avg_pts = df_games_filtered['t_points'].mean() if tot_matches > 0 else 0
    
    m_max_pts = df_games_filtered['m_points'].max() if tot_matches > 0 else 0
    t_max_pts = df_games_filtered['t_points'].max() if tot_matches > 0 else 0
    
    # Grid of Metric Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(
            f"""
            <div style='background-color: #1F2937; padding: 15px; border-radius: 8px; border-left: 5px solid #9CA3AF;'>
                <p style='font-size: 0.85em; margin-bottom: 5px; opacity: 0.7;'>TOTAL MATCHES</p/>
                <h2 style='margin: 0px;'>{tot_matches}</h2>
            </div>
            """, unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div style='background-color: #1F2937; padding: 15px; border-radius: 8px; border-left: 5px solid #FF8C00;'>
                <p style='font-size: 0.85em; margin-bottom: 5px; opacity: 0.7;'>MY H2H WINS (WIN RATE)</p/>
                <h2 style='margin: 0px; color: #FF8C00;'>{m_wins} <span style='font-size: 0.6em; font-weight: normal;'>({m_win_pct:.1f}%)</span></h2>
            </div>
            """, unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
            <div style='background-color: #1F2937; padding: 15px; border-radius: 8px; border-left: 5px solid #1E90FF;'>
                <p style='font-size: 0.85em; margin-bottom: 5px; opacity: 0.7;'>TROUTFLY WINS (WIN RATE)</p/>
                <h2 style='margin: 0px; color: #1E90FF;'>{t_wins} <span style='font-size: 0.6em; font-weight: normal;'>({t_win_pct:.1f}%)</span></h2>
            </div>
            """, unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            f"""
            <div style='background-color: #1F2937; padding: 15px; border-radius: 8px; border-left: 5px solid #9CA3AF;'>
                <p style='font-size: 0.85em; margin-bottom: 5px; opacity: 0.7;'>AVERAGE GAME SCORE</p/>
                <h3 style='margin: 0px;'>
                    <span style='color: #FF8C00;'>{m_avg_pts:.0f}</span> vs 
                    <span style='color: #1E90FF;'>{t_avg_pts:.0f}</span>
                </h3>
            </div>
            """, unsafe_allow_html=True
        )
    with col5:
        st.markdown(
            f"""
            <div style='background-color: #1F2937; padding: 15px; border-radius: 8px; border-left: 5px solid #9CA3AF;'>
                <p style='font-size: 0.85em; margin-bottom: 5px; opacity: 0.7;'>RECORD GAME SCORE</p/>
                <h3 style='margin: 0px;'>
                    <span style='color: #FF8C00;'>{m_max_pts}</span> vs 
                    <span style='color: #1E90FF;'>{t_max_pts}</span>
                </h3>
            </div>
            """, unsafe_allow_html=True
        )
        
    st.markdown("<br/>", unsafe_allow_html=True)
    st.subheader("📋 Match Breakdown History")
    
    # Detail DataFrame
    df_games_table = df_games_filtered.sort_values('started_at', ascending=False).copy()
    df_games_table['started_at'] = df_games_table['started_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    df_games_table.rename(columns={
        'started_at': 'Timestamp (Kyiv)',
        'map_type': 'Map Type',
        'location_id': 'Map Location ID',
        'total_rounds': 'Rounds',
        'm_points': 'My Score',
        't_points': 'Troutfly Score',
        'winner': 'Winner'
    }, inplace=True)
    
    # Styled display table
    st.dataframe(
        df_games_table[['Timestamp (Kyiv)', 'Map Type', 'Map Location ID', 'Rounds', 'My Score', 'Troutfly Score', 'Winner']],
        use_container_width=True,
        hide_index=True
    )

# --- Tab 2: Momentum Tracker (Rolling Averages) ---
with tab_momentum:
    st.subheader("📈 Rolling Moving Averages (5-Game & 10-Game)")
    st.markdown("Track shifts in performance levels over time. Calculations are performed chronologically.")
    
    # Momentum charts need a chronological index
    df_momentum = df_games_filtered.sort_values('started_at').reset_index(drop=True).copy()
    
    if len(df_momentum) < 1:
        st.warning("Insufficient matches in the filtered view to calculate rolling averages.")
    else:
        # Calculate rolling metrics
        df_momentum['m_win'] = (df_momentum['winner'] == 'markiianivan').astype(float)
        df_momentum['t_win'] = (df_momentum['winner'] == 'troutfly').astype(float)
        
        # rolling win rate
        df_momentum['m_win_rate_5'] = df_momentum['m_win'].rolling(window=5, min_periods=1).mean() * 100
        df_momentum['t_win_rate_5'] = df_momentum['t_win'].rolling(window=5, min_periods=1).mean() * 100
        df_momentum['m_win_rate_10'] = df_momentum['m_win'].rolling(window=10, min_periods=1).mean() * 100
        df_momentum['t_win_rate_10'] = df_momentum['t_win'].rolling(window=10, min_periods=1).mean() * 100
        
        # rolling accuracy
        df_momentum['m_accuracy'] = (df_momentum['m_points'] / (df_momentum['total_rounds'] * 5000)) * 100
        df_momentum['t_accuracy'] = (df_momentum['t_points'] / (df_momentum['total_rounds'] * 5000)) * 100
        
        df_momentum['m_acc_5'] = df_momentum['m_accuracy'].rolling(window=5, min_periods=1).mean()
        df_momentum['t_acc_5'] = df_momentum['t_accuracy'].rolling(window=5, min_periods=1).mean()
        df_momentum['m_acc_10'] = df_momentum['m_accuracy'].rolling(window=10, min_periods=1).mean()
        df_momentum['t_acc_10'] = df_momentum['t_accuracy'].rolling(window=10, min_periods=1).mean()
        
        df_momentum['Game Index'] = df_momentum.index + 1
        
        # User toggles
        window_select = st.radio("Choose Rolling Window Size:", ["5-Game Rolling Window", "10-Game Rolling Window"], horizontal=True)
        
        # Build layout cols for Win Rate and Accuracy charts
        chart_col1, chart_col2 = st.columns(2)
        
        # Select target columns based on window selection
        win_m_col = 'm_win_rate_5' if "5-Game" in window_select else 'm_win_rate_10'
        win_t_col = 't_win_rate_5' if "5-Game" in window_select else 't_win_rate_10'
        acc_m_col = 'm_acc_5' if "5-Game" in window_select else 'm_acc_10'
        acc_t_col = 't_acc_5' if "5-Game" in window_select else 't_acc_10'
        
        with chart_col1:
            fig_win = go.Figure()
            fig_win.add_trace(go.Scatter(
                x=df_momentum['Game Index'], y=df_momentum[win_m_col],
                mode='lines+markers', name='markiianivan',
                line=dict(color=COLORS['markiianivan'], width=3),
                marker=dict(size=6)
            ))
            fig_win.add_trace(go.Scatter(
                x=df_momentum['Game Index'], y=df_momentum[win_t_col],
                mode='lines+markers', name='troutfly',
                line=dict(color=COLORS['troutfly'], width=3),
                marker=dict(size=6)
            ))
            fig_win.update_layout(
                title=f"H2H Rolling Win Rate ({window_select})",
                xaxis_title="Chronological Game Number",
                yaxis_title="Win Rate (%)",
                yaxis_range=[-5, 105],
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_win, use_container_width=True)
            
        with chart_col2:
            fig_acc = go.Figure()
            fig_acc.add_trace(go.Scatter(
                x=df_momentum['Game Index'], y=df_momentum[acc_m_col],
                mode='lines+markers', name='markiianivan',
                line=dict(color=COLORS['markiianivan'], width=3),
                marker=dict(size=6)
            ))
            fig_acc.add_trace(go.Scatter(
                x=df_momentum['Game Index'], y=df_momentum[acc_t_col],
                mode='lines+markers', name='troutfly',
                line=dict(color=COLORS['troutfly'], width=3),
                marker=dict(size=6)
            ))
            fig_acc.update_layout(
                title=f"H2H Rolling Point Accuracy ({window_select})",
                xaxis_title="Chronological Game Number",
                yaxis_title="Point Accuracy (%)",
                yaxis_range=[-5, 105],
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_acc, use_container_width=True)

# --- Tab 3: Time/Day Heatmap ---
with tab_heatmap:
    st.subheader("🔥 Time & Day Point Differential Heatmap")
    st.markdown(
        "Point Differential values correspond to: **My Score minus Troutfly's Score**.<br/>"
        "🟢 **Orange cells** represent games won by markiianivan, 🔵 **Blue cells** show matches won by troutfly. "
        "Cell intensity corresponds to the margin size.", 
        unsafe_allow_html=True
    )
    
    # Calculate Day of Week & Hour Category on local Kyiv Time
    df_heatmap = df_games_filtered.copy()
    df_heatmap['day_of_week'] = df_heatmap['started_at'].dt.day_name()
    df_heatmap['diff'] = df_heatmap['m_points'] - df_heatmap['t_points']
    
    if df_heatmap.empty:
        st.warning("No matches match the active filters to render the heatmap.")
    else:
        # Group and pivot
        df_heat_grouped = df_heatmap.groupby(['day_of_week', 'time_of_day'])['diff'].mean().reset_index()
        
        # Define axes orders
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        times_order = ['Morning', 'Afternoon', 'Evening', 'Night']
        
        # Reindex pivot to prevent missing items
        pivot_df = df_heat_grouped.pivot(index='day_of_week', columns='time_of_day', values='diff')
        pivot_df = pivot_df.reindex(index=days_order, columns=times_order)
        
        # Compute totals for annotations
        games_count_pivot = df_heatmap.groupby(['day_of_week', 'time_of_day'])['diff'].count().reset_index().pivot(
            index='day_of_week', columns='time_of_day', values='diff'
        ).reindex(index=days_order, columns=times_order).fillna(0).astype(int)
        
        # Custom custom scale: diverging blue to grey to orange
        custom_colorscale = [
            [0.0, '#1E90FF'],  # Blue (opponent lead)
            [0.5, '#1F2937'],  # Dark Grey (equal/draw)
            [1.0, '#FF8C00']   # Orange (my lead)
        ]
        
        # Format annotations text (value & game count)
        z_values = pivot_df.values
        z_text = []
        for r in range(len(days_order)):
            row_text = []
            for c in range(len(times_order)):
                val = z_values[r][c]
                count = games_count_pivot.values[r][c]
                if np.isnan(val):
                    row_text.append("")
                else:
                    row_text.append(f"{val:+.0f}<br><span style='font-size:0.8em;opacity:0.7;'>({count} g)</span>")
            z_text.append(row_text)
            
        # Max absolute differential for symmetric bounds
        max_val = np.nanmax(np.abs(z_values)) if not np.isnan(z_values).all() else 5000
        if max_val == 0:
            max_val = 5000
            
        fig_heat = go.Figure(data=go.Heatmap(
            z=z_values,
            x=times_order,
            y=days_order,
            text=z_text,
            texttemplate="%{text}",
            colorscale=custom_colorscale,
            zmin=-max_val,
            zmax=max_val,
            colorbar=dict(title="Point Differential"),
            hovertemplate="Day: %{y}<br>Time: %{x}<br>Avg Diff: %{z:+.0f} pts<extra></extra>"
        ))
        
        fig_heat.update_layout(
            title="Kyiv Local Time Day & Hour Point Differential Matrix",
            xaxis_title="Time of Day (Kyiv)",
            yaxis_title="Day of the Week",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        st.plotly_chart(fig_heat, use_container_width=True)

# --- Tab 4: Fatigue Curves ---
with tab_fatigue:
    st.subheader("📉 The 'Fatigue' Stamina Curve")
    st.markdown("Average scores strictly by Round Number (Rounds 1 through 10) to compare warm-up capabilities and late-game fatigue.")
    
    # Group rounds
    if df_rounds_filtered.empty:
        st.warning("No round-level data found in the filtered view.")
    else:
        df_fatigue = df_rounds_filtered.groupby('round_number')[['m_score', 't_score', 'm_time', 't_time']].mean().reset_index()
        
        col_fat1, col_fat2 = st.columns(2)
        
        with col_fat1:
            fig_fat_score = go.Figure()
            fig_fat_score.add_trace(go.Scatter(
                x=df_fatigue['round_number'], y=df_fatigue['m_score'],
                mode='lines+markers', name='markiianivan',
                line=dict(color=COLORS['markiianivan'], width=3),
                marker=dict(size=8)
            ))
            fig_fat_score.add_trace(go.Scatter(
                x=df_fatigue['round_number'], y=df_fatigue['t_score'],
                mode='lines+markers', name='troutfly',
                line=dict(color=COLORS['troutfly'], width=3),
                marker=dict(size=8)
            ))
            fig_fat_score.update_layout(
                title="Average Points Scored by Round Number",
                xaxis=dict(title="Round Number", tickmode='linear', tick0=1, dtick=1),
                yaxis=dict(title="Average Score (0-5,000)"),
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_fat_score, use_container_width=True)
            
        with col_fat2:
            fig_fat_time = go.Figure()
            fig_fat_time.add_trace(go.Scatter(
                x=df_fatigue['round_number'], y=df_fatigue['m_time'],
                mode='lines+markers', name='markiianivan',
                line=dict(color=COLORS['markiianivan'], width=3),
                marker=dict(size=8)
            ))
            fig_fat_time.add_trace(go.Scatter(
                x=df_fatigue['round_number'], y=df_fatigue['t_time'],
                mode='lines+markers', name='troutfly',
                line=dict(color=COLORS['troutfly'], width=3),
                marker=dict(size=8)
            ))
            fig_fat_time.update_layout(
                title="Average Time Taken by Round Number",
                xaxis=dict(title="Round Number", tickmode='linear', tick0=1, dtick=1),
                yaxis=dict(title="Average Time Taken (seconds)"),
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_fat_time, use_container_width=True)

# --- Tab 5: Geospatial Insights (Vector Shape Maps) ---
with tab_geography:
    st.subheader("🌍 Geospatial Boundary Shape Maps")
    st.markdown(
        "Interactive **Vector Choropleth Shape Maps**. Regions are filled with colors indicating the H2H average point differential "
        "(🟢 **Orange** highlights where you lead, 🔵 **Blue** shows where troutfly leads, and ⚪ **Grey** represents equal/unplayed regions). "
        "These maps render natively offline and do not rely on Mapbox tile servers.",
        unsafe_allow_html=True
    )
    
    geo_map_type = st.radio("Select Shape Map Context:", ["World Map", "Ukraine Map"], key="geo_tab_toggle", horizontal=True)
    
    if df_rounds_filtered.empty:
        st.warning("No round data available to render the shape map under the active filters.")
    else:
        # Custom diverging colorscale matching the theme
        custom_scale = [
            [0.0, '#1E90FF'],  # Blue (troutfly lead)
            [0.5, '#1F2937'],  # Dark Grey (neutral)
            [1.0, '#FF8C00']   # Orange (markiianivan lead)
        ]
        
        if geo_map_type == "Ukraine Map":
            df_uk_rounds = df_rounds_filtered[df_rounds_filtered['map_type'] == 'Ukraine'].copy()
            
            if df_uk_rounds.empty:
                st.warning("No rounds played on Ukraine maps found matching active filters.")
            else:
                # Group by Oblast to compute average points
                df_oblast = df_uk_rounds.groupby('uk_oblast').agg(
                    m_score_mean=('m_score', 'mean'),
                    t_score_mean=('t_score', 'mean'),
                    rounds_count=('m_score', 'count')
                ).reset_index()
                df_oblast['diff'] = df_oblast['m_score_mean'] - df_oblast['t_score_mean']
                
                # Try loading the local GeoJSON boundaries file
                geojson_path = os.path.join(os.path.dirname(__file__), "ukraine_oblasts.geojson")
                if os.path.exists(geojson_path):
                    try:
                        with open(geojson_path, 'r', encoding='utf-8') as f:
                            ukraine_geojson = json.load(f)
                            
                        # Filter out unmatched borders so they don't break fitbounds or map styling
                        geojson_names = {feat['properties'].get('shapeName') for feat in ukraine_geojson['features']}
                        df_oblast_filtered = df_oblast[df_oblast['uk_oblast'].isin(geojson_names)].copy()
                        
                        max_diff = max(df_oblast_filtered['diff'].abs().max() if not df_oblast_filtered.empty else 1.0, 1.0)
                        
                        fig_uk_choropleth = px.choropleth(
                            df_oblast_filtered,
                            geojson=ukraine_geojson,
                            locations="uk_oblast",
                            featureidkey="properties.shapeName",
                            color="diff",
                            color_continuous_scale=custom_scale,
                            range_color=[-max_diff, max_diff],
                            hover_name="uk_oblast",
                            hover_data={
                                "uk_oblast": False,
                                "m_score_mean": ":.0f",
                                "t_score_mean": ":.0f",
                                "rounds_count": True,
                                "diff": ":.0f"
                            },
                            labels={'diff': 'Avg Point Diff'}
                        )
                        
                        fig_uk_choropleth.update_geos(
                            projection_type="mercator",
                            center=dict(lat=48.3794, lon=31.1656),
                            projection_scale=6,
                            visible=False
                        )
                        
                        fig_uk_choropleth.update_layout(
                            title="Ukraine Shape Map: Average Round Point Differential by Oblast",
                            coloraxis_colorbar=dict(title="Point Diff"),
                            margin=dict(l=0, r=0, t=40, b=0),
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)"
                        )
                        
                        st.plotly_chart(fig_uk_choropleth, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"Error loading Ukraine GeoJSON boundary file: {e}")
                else:
                    st.error("Ukraine GeoJSON file (ukraine_oblasts.geojson) was not found. Please click 'Sync' to download it or drop it in the folder.")
                    
        else: # World Map Shape Map
            df_world_rounds = df_rounds_filtered[df_rounds_filtered['map_type'] == 'World'].copy()
            
            if df_world_rounds.empty:
                st.warning("No rounds played on World maps found matching active filters.")
            else:
                # Group by Country
                df_country = df_world_rounds.groupby(['country_name', 'continent', 'iso3']).agg(
                    m_score_mean=('m_score', 'mean'),
                    t_score_mean=('t_score', 'mean'),
                    rounds_count=('m_score', 'count')
                ).reset_index()
                df_country['diff'] = df_country['m_score_mean'] - df_country['t_score_mean']
                
                # Continent scope drill-down
                continents = ["All Continents", "Europe", "North America", "South America", "Asia", "Africa", "Oceania"]
                selected_continent = st.selectbox("Select Map Region:", continents, key="shape_continent")
                
                # Plotly built-in scopes: "world", "usa", "europe", "asia", "africa", "north america", "south america"
                plotly_scope = "world"
                zoom_center = None
                
                if selected_continent == "Europe":
                    plotly_scope = "europe"
                elif selected_continent == "North America":
                    plotly_scope = "north america"
                elif selected_continent == "South America":
                    plotly_scope = "south america"
                elif selected_continent == "Asia":
                    plotly_scope = "asia"
                elif selected_continent == "Africa":
                    plotly_scope = "africa"
                elif selected_continent == "Oceania":
                    plotly_scope = "world"
                    zoom_center = dict(center=dict(lat=-25.0, lon=135.0), projection_scale=3)
                
                # Filter dataset
                if selected_continent != "All Continents":
                    df_country_filtered = df_country[df_country['continent'] == selected_continent]
                else:
                    df_country_filtered = df_country.copy()
                    
                if df_country_filtered.empty:
                    st.warning(f"No rounds played in {selected_continent} found matching active filters.")
                else:
                    max_diff = max(df_country_filtered['diff'].abs().max(), 1.0)
                    
                    fig_world_choropleth = px.choropleth(
                        df_country_filtered,
                        locations="iso3",
                        color="diff",
                        color_continuous_scale=custom_scale,
                        range_color=[-max_diff, max_diff],
                        hover_name="country_name",
                        hover_data={
                            "iso3": False,
                            "m_score_mean": ":.0f",
                            "t_score_mean": ":.0f",
                            "rounds_count": True,
                            "diff": ":.0f"
                        },
                        scope=plotly_scope,
                        labels={'diff': 'Avg Point Diff'}
                    )
                    
                    # Apply premium dark vector aesthetics
                    geos_settings = dict(
                        showframe=False,
                        showcoastlines=True,
                        coastlinecolor="#4B5563",
                        showland=True,
                        landcolor="#1F2937",
                        showocean=True,
                        oceancolor="#0E1117",
                        showlakes=True,
                        lakecolor="#0E1117",
                        showcountries=True,
                        countrycolor="#4B5563"
                    )
                    if zoom_center:
                        geos_settings.update(zoom_center)
                        
                    fig_world_choropleth.update_geos(**geos_settings)
                    
                    fig_world_choropleth.update_layout(
                        title=f"World Shape Map: Average H2H Point Differential ({selected_continent})",
                        coloraxis_colorbar=dict(title="Point Diff"),
                        margin=dict(l=0, r=0, t=40, b=0),
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_world_choropleth, use_container_width=True)

# --- Tab 6: Interactive Round Map (Shows All Individual Rounds - Vector ScatterGeo) ---
with tab_round_map:
    st.subheader("📍 Offline-Optimized Vector Round Map")
    st.markdown(
        "This map plots **every target round coordinate** on a native vector map (no external tiles loaded). "
        "🔴 **Orange circles** represent rounds where you outscored troutfly. "
        "🔵 **Blue circles** show rounds where troutfly outscored you. "
        "⚪ **White/Grey circles** represent rounds with equal points.",
        unsafe_allow_html=True
    )
    
    if df_rounds_filtered.empty:
        st.warning("No rounds available under active filters to plot.")
    else:
        df_all_rounds = df_rounds_filtered.copy()
        df_all_rounds['diff'] = df_all_rounds['m_score'] - df_all_rounds['t_score']
        
        # Label round winner for color mapping
        def get_round_winner(diff):
            if diff > 0: return 'markiianivan'
            elif diff < 0: return 'troutfly'
            else: return 'draw'
            
        df_all_rounds['Round Winner'] = df_all_rounds['diff'].apply(get_round_winner)
        
        # Select coordinate filters
        col_map_opt1, col_map_opt2 = st.columns(2)
        with col_map_opt1:
            score_filter_slider = st.slider(
                "Filter rounds where My Score is at least:",
                min_value=0, max_value=5000, value=0, step=100, key="score_slider_geo"
            )
        with col_map_opt2:
            time_filter_slider = st.slider(
                "Filter rounds where My Guess Time was under (seconds):",
                min_value=0, max_value=60, value=60, step=5, key="time_slider_geo"
            )
            
        # Apply local map filters
        df_all_rounds_filtered = df_all_rounds[
            (df_all_rounds['m_score'] >= score_filter_slider) &
            (df_all_rounds['m_time'] <= time_filter_slider)
        ]
        
        if df_all_rounds_filtered.empty:
            st.warning("No individual rounds match the map filters.")
        else:
            # Color map definitions
            color_discrete_map = {
                'markiianivan': COLORS['markiianivan'],
                'troutfly': COLORS['troutfly'],
                'draw': COLORS['draw']
            }
            
            # Use natural earth/mercator vector projection
            fig_indiv_map = px.scatter_geo(
                df_all_rounds_filtered,
                lat='lat',
                lon='lon',
                color='Round Winner',
                color_discrete_map=color_discrete_map,
                category_orders={'Round Winner': ['markiianivan', 'troutfly', 'draw']},
                hover_name='uk_oblast',
                hover_data={
                    'lat': False, 'lon': False,
                    'map_type': True,
                    'round_number': True,
                    'm_score': True,
                    't_score': True,
                    'm_time': True,
                    't_time': True
                },
                projection="natural earth" if map_filter != "Ukraine" else "mercator"
            )
            
            # Apply dark mode vector styling
            geos_settings = dict(
                showframe=False,
                showcoastlines=True,
                coastlinecolor="#4B5563",
                showland=True,
                landcolor="#1F2937",
                showocean=True,
                oceancolor="#0E1117",
                showlakes=True,
                lakecolor="#0E1117",
                showcountries=True,
                countrycolor="#4B5563"
            )
            
            # Center on Ukraine if using Ukraine map
            if map_filter == "Ukraine":
                geos_settings.update(dict(
                    center=dict(lat=48.3794, lon=31.1656),
                    projection_scale=6,
                    visible=False
                ))
            elif map_filter == "World" and not df_all_rounds_filtered.empty:
                # Dynamically center on mean coordinates
                geos_settings.update(dict(
                    center=dict(
                        lat=float(df_all_rounds_filtered['lat'].mean()),
                        lon=float(df_all_rounds_filtered['lon'].mean())
                    ),
                    projection_scale=1.5
                ))
                
            fig_indiv_map.update_geos(**geos_settings)
            
            fig_indiv_map.update_layout(
                title=f"All Individual Target Coordinates Mapped ({len(df_all_rounds_filtered)} rounds shown)",
                margin=dict(l=0, r=0, t=40, b=0),
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
            )
            
            # Make markers clearly visible
            fig_indiv_map.update_traces(marker=dict(size=8, opacity=0.75))
            st.plotly_chart(fig_indiv_map, use_container_width=True)
