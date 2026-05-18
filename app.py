import streamlit as st
import requests
import random

# --- HIER DEINE SCHLÜSSEL EINTRAGEN ---
TMDB_API_KEY = "b2ab8673d812267dfbced837fe6811f9"
JSONBIN_BIN_ID = "6a098848c0954111d836f3ca"
JSONBIN_API_KEY = "$2a$10$L8rsFKwP2zPMnaYLuK2m7e10y8aOK4STql6Ml9oUFfscLKdLh.giK"

GENRES = {
    "Egal / Alles": "", "Action": "28", "Abenteuer": "12", "Animation": "16",
    "Komödie": "35", "Krimi": "80", "Dokumentation": "99", "Drama": "18",
    "Familie": "10751", "Fantasy": "14", "Horror": "27", "Mystery": "9648", 
    "Romantik": "10749", "Science Fiction": "878", "Thriller": "53"
}

# --- DATENBANK FUNKTIONEN ---
def load_blacklist():
    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
    headers = {'X-Master-Key': JSONBIN_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('record', [])
    except Exception as e:
        pass
    return []

def update_blacklist_online(new_blacklist):
    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
    headers = {
        'Content-Type': 'application/json',
        'X-Master-Key': JSONBIN_API_KEY
    }
    requests.put(url, json=new_blacklist, headers=headers)

def add_to_blacklist(movie_id):
    blacklist = load_blacklist()
    if str(movie_id) not in blacklist:
        blacklist.append(str(movie_id))
        update_blacklist_online(blacklist)

def remove_from_blacklist(movie_id):
    blacklist = load_blacklist()
    if str(movie_id) in blacklist:
        blacklist.remove(str(movie_id))
        update_blacklist_online(blacklist)

# --- TMDB ABFRAGEN ---
def fetch_movies(genre_ids, min_rating, min_year, exclude_genre_ids=""):
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
    if genre_ids:
        params["with_genres"] = genre_ids
    
    if exclude_genre_ids:
        params["without_genres"] = exclude_genre_ids
        
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY, "language": "de-DE"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

# --- BENUTZEROBERFLÄCHE ---
st.set_page_config(page_title="Zufallsfilm", page_icon="🍿")

st.title("🎬 Filmabend: Timm & Dani")
st.write("Für mein Bebi <3") # <-- Text angepasst
st.divider()

tab_search, tab_blacklist = st.tabs(["🎲 Filmauswahl", "🚫 Blacklist verwalten"])

# --- TAB 1: FILMAUSWAHL ---
with tab_search:
    col_settings, col_result = st.columns([1, 2])

    with col_settings:
        st.subheader("Eure Filter")
        
        # Gesuchte Kategorien
        selected_genre_names = []
        with st.expander("✅ Gesuchte Kategorie(n) wählen"):
            for genre in [g for g in GENRES.keys() if g != "Egal / Alles"]:
                if st.checkbox(genre, key=f"include_{genre}"):
                    selected_genre_names.append(genre)
        
        # NEU: Anzeige der Auswahl unter dem Ausklapp-Menü
        if selected_genre_names:
            st.caption(f"📌 **Gesucht:** {', '.join(selected_genre_names)}")
        else:
            st.caption("📌 **Gesucht:** Egal / Alles")
            
        selected_genre_ids = ",".join([GENRES[name] for name in selected_genre_names])
        
        st.write("") # Kleiner Platzhalter
        
        # Ausgeschlossene Kategorien
        exclude_genre_names = []
        with st.expander("❌ Diese Kategorien ausschließen"):
            for genre in [g for g in GENRES.keys() if g != "Egal / Alles"]:
                if st.checkbox(genre, key=f"exclude_{genre}"):
                    exclude_genre_names.append(genre)
                    
        # NEU: Anzeige der Auswahl unter dem Ausklapp-Menü
        if exclude_genre_names:
            st.caption(f"🚫 **Ausgeschlossen:** {', '.join(exclude_genre_names)}")
        else:
            st.caption("🚫 **Ausgeschlossen:** Nichts")
            
        exclude_genre_ids = "|".join([GENRES[name] for name in exclude_genre_names])
        
        st.divider()
        
        min_rating = st.slider("Mindestbewertung (1-10):", min_value=1.0, max_value=9.0, value=6.0, step=0.5)
        min_year = st.slider("Erscheinungsjahr ab:", min_value=1950, max_value=2026, value=2010, step=1)
        
        st.divider()
        search_button = st.button("🎲 Zufallsfilm finden", use_container_width=True)

    with col_result:
        if search_button:
            with st.spinner('Suche im Prime-Katalog...'):
                movies = fetch_movies(selected_genre_ids, min_rating, min_year, exclude_genre_ids)
                blacklist = load_blacklist()
                
                available_movies = [m for m in movies if str(m['id']) not in blacklist]
                
                if not available_movies:
                    st.warning("Keine Filme gefunden. Versucht mal, die Filter etwas lockerer einzustellen!")
                else:
                    st.session_state['current_movie'] = random.choice(available_movies)

        if 'current_movie' in st.session_state:
            movie = st.session_state['current_movie']
            
            full_details = get_movie_details(movie['id'])
            genre_text = "Keine Angaben"
            if full_details and 'genres' in full_details:
                genre_text = ", ".join([g['name'] for g in full_details['genres']])
            
            st.subheader(movie.get('title', 'Unbekannter Titel'))
            
            if movie.get('poster_path'):
                poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
                st.image(poster_url, width=250)
                
            st.write(f"**Bewertung:** ⭐ {movie.get('vote_average', '-')}/10")
            st.write(f"**Erscheinungsdatum:** {movie.get('release_date', '-')}")
            st.write(f"**Genres:** {genre_text}")
            st.write(f"**Beschreibung:** {movie.get('overview', 'Keine Beschreibung verfügbar.')}")
            
            if st.button("🚫 Diesen Film für immer ausschließen"):
                with st.spinner('Speichere in der Cloud...'):
                    add_to_blacklist(movie['id'])
                st.success("Erledigt! Der Film steht auf der Blacklist.")
                del st.session_state['current_movie']
                st.rerun()

# --- TAB 2: BLACKLIST VERWALTUNG ---
with tab_blacklist:
    st.subheader("Ausgeschlossene Filme")
    st.write("Diese Filme werden euch bei der Zufallssuche nicht mehr vorgeschlagen.")
    
    current_blacklist = load_blacklist()
    
    if not current_blacklist:
        st.info("Eure Blacklist ist momentan leer.")
    else:
        if st.button("🔄 Liste neu laden"):
            st.rerun()
            
        st.divider()
        
        for movie_id in current_blacklist:
            details = get_movie_details(movie_id)
            if details:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{details.get('title')}** ({details.get('release_date', '')[:4]})")
                with col2:
                    if st.button("Freigeben", key=f"del_{movie_id}"):
                        remove_from_blacklist(movie_id)
                        st.success(f"'{details.get('title')}' wurde freigegeben!")
                        st.rerun()
