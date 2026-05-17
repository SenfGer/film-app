import streamlit as st
import requests
import random

# --- HIER DEINE SCHLÜSSEL EINTRAGEN ---
TMDB_API_KEY = "b2ab8673d812267dfbced837fe6811f9"
JSONBIN_BIN_ID = "6a098848c0954111d836f3ca"
JSONBIN_API_KEY = "$2a$10$L8rsFKwP2zPMnaYLuK2m7e10y8aOK4STql6Ml9oUFfscLKdLh.giK"

# Genre-Dictionary (TMDB IDs)
GENRES = {
    "Egal / Alles": "", "Action": "28", "Abenteuer": "12", "Animation": "16",
    "Komödie": "35", "Krimi": "80", "Dokumentation": "99", "Drama": "18",
    "Familie": "10751", "Fantasy": "14", "Horror": "27", "Mystery": "9648", 
    "Romantik": "10749", "Science Fiction": "878", "Thriller": "53"
}

# --- NEU: Online Blacklist abrufen ---
def load_blacklist():
    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
    headers = {'X-Master-Key': JSONBIN_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('record', [])
    except Exception as e:
        st.error("Fehler beim Laden der Blacklist.")
    return []

# --- NEU: Online Blacklist aktualisieren ---
def add_to_blacklist(movie_id):
    blacklist = load_blacklist()
    if str(movie_id) not in blacklist:
        blacklist.append(str(movie_id))
        url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
        headers = {
            'Content-Type': 'application/json',
            'X-Master-Key': JSONBIN_API_KEY
        }
        requests.put(url, json=blacklist, headers=headers)

def fetch_movies(genre_id, min_rating, min_year):
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "de-DE",
        "with_watch_providers": "9", 
        "with_watch_monetization_types": "flatrate",
        "watch_region": "DE",
        "vote_average.gte": min_rating,
        "primary_release_date.gte": f"{min_year}-01-01",
        "vote_count.gte": 50,
    }
    if genre_id:
        params["with_genres"] = genre_id
        
    response = requests.get(url, params=params)
    if response.status_code != 200:
        st.error("Verbindungsfehler zu TMDB!")
        return []
    return response.json().get("results", [])

# --- BENUTZEROBERFLÄCHE ---
st.set_page_config(page_title="Zufallsfilm", page_icon="🍿")

st.title("🎬 Filmabend: Timm & Dani")
st.write("Der automatische Zufallsgenerator, damit der *Humor Fuchs* und du nicht mehr ewig suchen müsst!")
st.divider()

col_settings, col_result = st.columns([1, 2])

with col_settings:
    st.subheader("Eure Filter")
    selected_genre_name = st.selectbox("Kategorie:", list(GENRES.keys()))
    selected_genre_id = GENRES[selected_genre_name]
    
    min_rating = st.slider("Mindestbewertung (1-10):", min_value=1.0, max_value=9.0, value=6.0, step=0.5)
    min_year = st.number_input("Erscheinungsjahr ab:", min_value=1950, max_value=2026, value=2010, step=1)
    
    search_button = st.button("🎲 Zufallsfilm finden", use_container_width=True)

with col_result:
    if search_button:
        with st.spinner('Suche im Prime-Katalog...'):
            movies = fetch_movies(selected_genre_id, min_rating, min_year)
            blacklist = load_blacklist()
            
            available_movies = [m for m in movies if str(m['id']) not in blacklist]
            
            if not available_movies:
                st.warning("Keine Filme gefunden. Versucht mal, die Filter etwas lockerer einzustellen!")
            else:
                st.session_state['current_movie'] = random.choice(available_movies)

    if 'current_movie' in st.session_state:
        movie = st.session_state['current_movie']
        
        st.subheader(movie.get('title', 'Unbekannter Titel'))
        
        if movie.get('poster_path'):
            poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
            st.image(poster_url, width=250)
            
        st.write(f"**Bewertung:** ⭐ {movie.get('vote_average', '-')}/10")
        st.write(f"**Erscheinungsdatum:** {movie.get('release_date', '-')}")
        st.write(f"**Beschreibung:** {movie.get('overview', 'Keine Beschreibung verfügbar.')}")
        
        if st.button("🚫 Diesen Film für immer ausschließen"):
            with st.spinner('Speichere in der Cloud-Blacklist...'):
                add_to_blacklist(movie['id'])
            st.success("Erledigt! Der Film steht auf der Blacklist.")
            del st.session_state['current_movie']
            st.rerun()