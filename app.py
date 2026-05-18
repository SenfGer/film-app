import streamlit as st
import requests
import random
import urllib.parse

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
def fetch_movies(genre_ids, min_rating, min_year, max_year, exclude_genre_ids=""):
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "de-DE",
        "with_watch_providers": "9", 
        "with_watch_monetization_types": "flatrate",
        "watch_region": "DE",
        "vote_average.gte": min_rating,
        "primary_release_date.gte": f"{min_year}-01-01",
        "primary_release_date.lte": f"{max_year}-12-31",
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

def fetch_catalog_movies(genre_ids, min_year, max_year, exclude_genre_ids=""):
    url = "https://api.themoviedb.org/3/discover/movie"
    movies = []
    for page in range(1, 3):
        params = {
            "api_key": TMDB_API_KEY,
            "language": "de-DE",
            "with_watch_providers": "9", 
            "with_watch_monetization_types": "flatrate",
            "watch_region": "DE",
            "sort_by": "vote_average.desc", 
            "primary_release_date.gte": f"{min_year}-01-01", 
            "primary_release_date.lte": f"{max_year}-12-31", 
            "page": page,
            "vote_count.gte": 150 
        }
        if genre_ids:
            params["with_genres"] = genre_ids
        if exclude_genre_ids:
            params["without_genres"] = exclude_genre_ids
            
        response = requests.get(url, params=params)
        if response.status_code == 200:
            movies.extend(response.json().get("results", []))
    return movies

def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY, "language": "de-DE"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def search_and_check_prime(query):
    search_url = "https://api.themoviedb.org/3/search/movie"
    params_search = {"api_key": TMDB_API_KEY, "language": "de-DE", "query": query}
    response = requests.get(search_url, params=params_search)
    
    if response.status_code != 200:
        return None, False
        
    results = response.json().get("results", [])
    if not results:
        return None, False
        
    best_match = results[0]
    movie_id = best_match['id']
    
    prov_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers"
    prov_response = requests.get(prov_url, params={"api_key": TMDB_API_KEY})
    
    on_prime = False
    if prov_response.status_code == 200:
        providers_data = prov_response.json().get("results", {})
        de_providers = providers_data.get("DE", {})
        flatrate = de_providers.get("flatrate", [])
        on_prime = any(str(p['provider_id']) in ["9", "119"] for p in flatrate)
        
    return best_match, on_prime

def get_prime_link(title):
    encoded_title = urllib.parse.quote_plus(title)
    return f"https://www.amazon.de/s?k={encoded_title}&i=instant-video"

# --- BENUTZEROBERFLÄCHE ---
st.set_page_config(page_title="Zufallsfilm", page_icon="🍿")

st.title("🎬 Filmabend: Timm & Dani")
st.write("Für mein Bebi <3") 
st.divider()

tab_search, tab_direct, tab_catalog, tab_blacklist = st.tabs(["🎲 Zufallsfilm", "🔍 Direktsuche", "📚 Katalog", "🚫 Blacklist"])

# --- TAB 1: FILMAUSWAHL ---
with tab_search:
    col_settings, col_result = st.columns([1, 2])

    with col_settings:
        st.subheader("Eure Filter")
        
        selected_genre_names = []
        with st.expander("✅ Gesuchte Kategorie(n) wählen"):
            for genre in [g for g in GENRES.keys() if g != "Egal / Alles"]:
                if st.checkbox(genre, key=f"include_{genre}"):
                    selected_genre_names.append(genre)
        
        if selected_genre_names:
            st.caption(f"📌 **Gesucht:** {', '.join(selected_genre_names)}")
        else:
            st.caption("📌 **Gesucht:** Egal / Alles")
            
        selected_genre_ids = ",".join([GENRES[name] for name in selected_genre_names])
        
        st.write("") 
        
        exclude_genre_names = []
        with st.expander("❌ Diese Kategorien ausschließen"):
            for genre in [g for g in GENRES.keys() if g != "Egal / Alles"]:
                if st.checkbox(genre, key=f"exclude_{genre}"):
                    exclude_genre_names.append(genre)
                    
        if exclude_genre_names:
            st.caption(f"🚫 **Ausgeschlossen:** {', '.join(exclude_genre_names)}")
        else:
            st.caption("🚫 **Ausgeschlossen:** Nichts")
            
        exclude_genre_ids = "|".join([GENRES[name] for name in exclude_genre_names])
        
        st.divider()
        
        min_rating = st.slider("Mindestbewertung (1-10):", min_value=1.0, max_value=9.0, value=6.0, step=0.5)
        year_range = st.slider("Erscheinungsjahr:", min_value=1950, max_value=2026, value=(2010, 2026), step=1)
        min_year = year_range[0]
        max_year = year_range[1]
        
        st.divider()
        search_button = st.button("🎲 Zufallsfilm finden", use_container_width=True)

    with col_result:
        if search_button:
            with st.spinner('Suche im Prime-Katalog...'):
                movies = fetch_movies(selected_genre_ids, min_rating, min_year, max_year, exclude_genre_ids)
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
            
            prime_link = get_prime_link(movie.get('title', ''))
            st.markdown(f"### [▶️ In der Amazon-App öffnen]({prime_link})")
            
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

# --- TAB 2: DIREKTSUCHE ---
with tab_direct:
    st.subheader("🔍 Läuft der Film auf Prime?")
    search_query = st.text_input("Filmtitel eingeben:")
    
    if st.button("Film prüfen"):
        if search_query:
            with st.spinner("Prüfe Lizenzen..."):
                found_movie, on_prime = search_and_check_prime(search_query)
                
                if found_movie:
                    col_img, col_info = st.columns([1, 2])
                    with col_img:
                        if found_movie.get('poster_path'):
                            st.image(f"https://image.tmdb.org/t/p/w500{found_movie['poster_path']}", width=200)
                    with col_info:
                        st.subheader(found_movie.get('title', 'Unbekannter Titel'))
                        if on_prime:
                            st.success("✅ Juhu! Dieser Film ist aktuell im Prime-Abo enthalten!")
                        else:
                            st.error("❌ Leider aktuell NICHT kostenlos im Prime-Abo verfügbar.")
                        
                        prime_link = get_prime_link(found_movie.get('title', ''))
                        st.markdown(f"**[▶️ In der Amazon-App öffnen / Kaufoption prüfen]({prime_link})**")
                            
                        st.write(f"**Erscheinungsdatum:** {found_movie.get('release_date', '-')[:4]}")
                        st.write(f"**Beschreibung:** {found_movie.get('overview', 'Keine Beschreibung verfügbar.')}")
                else:
                    st.warning("Wir konnten leider keinen Film mit diesem Namen finden. Tippfehler?")
        else:
            st.info("Bitte tippe zuerst einen Filmnamen ein.")

# --- TAB 3: KATALOG ---
with tab_catalog:
    st.subheader("📚 Der Prime-Katalog")
    st.write("Stöbert durch die Top 40 der am besten bewerteten Prime-Filme eurer Auswahl.") 
    
    # NEU: Mehrfachauswahl für Gesuchte Kategorien im Katalog (wie auf Tab 1)
    catalog_genre_names = []
    with st.expander("✅ Gesuchte Kategorie(n) wählen"):
        for genre in [g for g in GENRES.keys() if g != "Egal / Alles"]:
            if st.checkbox(genre, key=f"cat_include_{genre}"):
                catalog_genre_names.append(genre)
                
    if catalog_genre_names:
        st.caption(f"📌 **Gesucht:** {', '.join(catalog_genre_names)}")
    else:
        st.caption("📌 **Gesucht:** Egal / Alles")
        
    catalog_genre_ids = ",".join([GENRES[name] for name in catalog_genre_names])
    
    st.write("")
    
    exclude_genre_names_cat = []
    with st.expander("❌ Diese Kategorien im Katalog ausschließen"):
        for genre in [g for g in GENRES.keys() if g != "Egal / Alles"]:
            if st.checkbox(genre, key=f"cat_exclude_{genre}"):
                exclude_genre_names_cat.append(genre)
                
    if exclude_genre_names_cat:
        st.caption(f"🚫 **Ausgeschlossen:** {', '.join(exclude_genre_names_cat)}")
    else:
        st.caption("🚫 **Ausgeschlossen:** Nichts")
        
    exclude_genre_ids_cat = "|".join([GENRES[name] for name in exclude_genre_names_cat])
    
    st.write("")
    
    catalog_year_range = st.slider("Filme ab welchem Jahr?", min_value=1950, max_value=2026, value=(2010, 2026), step=1, key="cat_year_slider")
    cat_min_year = catalog_year_range[0]
    cat_max_year = catalog_year_range[1]
    
    # ANGEPASST: Button-Text allgemeiner gehalten und neue Variable übergeben
    if st.button("Bestbewertete Filme laden", use_container_width=True):
        with st.spinner("Lade die Blockbuster..."):
            cat_movies = fetch_catalog_movies(catalog_genre_ids, cat_min_year, cat_max_year, exclude_genre_ids_cat)
            
            if cat_movies:
                cols = st.columns(4)
                for idx, cm in enumerate(cat_movies):
                    with cols[idx % 4]:
                        if cm.get('poster_path'):
                            st.image(f"https://image.tmdb.org/t/p/w300{cm['poster_path']}", use_container_width=True)
                        st.write(f"**{cm.get('title')}**")
                        
                        prime_link = get_prime_link(cm.get('title', ''))
                        st.markdown(f"**[▶️ In der Amazon-App öffnen]({prime_link})**")
                        
                        st.caption(f"⭐ {cm.get('vote_average', '-')}/10 | Jahr: {cm.get('release_date', '-')[:4]}")
                        st.divider() 
            else:
                st.warning("Keine Filme in diesem Zeitraum gefunden.")

# --- TAB 4: BLACKLIST VERWALTUNG ---
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
