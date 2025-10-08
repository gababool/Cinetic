import os
import time
from dotenv import load_dotenv
import requests
from app import create_app, db
from app.models.movies import Movie, Genre, Director, Actor

load_dotenv()

TMDB_TOKEN = os.getenv("TMDB_TOKEN")
TMDB_DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"
TMDB_MOVIE_DETAILS_URL = "https://api.themoviedb.org/3/movie/{tmdb_id}"

REQUEST_SLEEP = 0.03
DETAIL_RETRIES = 3


HEADERS = {
    "Authorization": f"Bearer {TMDB_TOKEN}",
    "Accept": "application/json",
}

GENRES = {
    "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35, "Crime": 80,
    "Drama": 18, "Family": 10751, "Fantasy": 14, "History": 36, "Horror": 27,
    "Music": 10402, "Mystery": 9648, "Romance": 10749, "Science Fiction": 878,
    "Thriller": 53, "War": 10752, "Western": 37,
}

# Fetch movie list from TMDB
def fetch_movies(sort_by, genre_id=None, pages=25, min_votes=None):
    movies = []
    for page in range(1, pages + 1):
        params = {
            "sort_by": sort_by,
            "include_adult": "false",
            "include_video": "false",
            "with_release_type": "2|3",
            "page": page,
            "vote_average.gte": 6, 
            "with_runtime.gte": 60, 

        }
        if genre_id:
            params["with_genres"] = genre_id
        if min_votes:
            params["vote_count.gte"] = min_votes
        
        r = requests.get(TMDB_DISCOVER_URL, headers=HEADERS, params=params, timeout=20)
        if r.status_code != 200:
            print(f"Error fetching page {page}: {r.status_code}")
            break
        
        results = r.json().get("results", [])
        if not results:
            break
        
        movies.extend(results)
        time.sleep(REQUEST_SLEEP)
    
    return movies

# Fetch all movie data in a single API call using append_to_response 
# Returns: dict with movie details, credits, and external IDs
def fetch_movie_complete_data(tmdb_id):
    for attempt in range(DETAIL_RETRIES):
        try:
            params = {
                "append_to_response": "credits,external_ids"
            }
            r = requests.get(
                TMDB_MOVIE_DETAILS_URL.format(tmdb_id=tmdb_id),
                headers=HEADERS,
                params=params,
                timeout=10
            )
            if r.status_code == 200:
                return r.json()
            time.sleep(REQUEST_SLEEP * (attempt + 1))
        except Exception as e:
            print(f"Error fetching data for tmdb_id {tmdb_id}: {e}")
            time.sleep(REQUEST_SLEEP * (attempt + 1))
    return None

# Get existing director or create new one
def get_or_create_director(tmdb_person_id, name):
    with db.session.no_autoflush:
        director = Director.query.filter_by(tmdb_person_id=tmdb_person_id).first()
    if not director:
        director = Director(tmdb_person_id=tmdb_person_id, name=name)
        db.session.add(director)
    return director

# Get existing actor or create new one
def get_or_create_actor(tmdb_person_id, name):
    with db.session.no_autoflush:
        actor = Actor.query.filter_by(tmdb_person_id=tmdb_person_id).first()
    if not actor:
        actor = Actor(tmdb_person_id=tmdb_person_id, name=name)
        db.session.add(actor)
    return actor

# Process a single movie: fetch complete data and upsert to database
def process_movie(basic_info, genre_obj=None):
    tmdb_id = basic_info["id"]
    
    # Check if movie already exists by tmdb_id
    movie = Movie.query.filter_by(tmdb_id=tmdb_id).first()
    if movie:
        print(f"Movie {movie.title} already exists, skipping...")
        # Add genre association if provided
        if genre_obj and genre_obj not in movie.genres:
            movie.genres.append(genre_obj)
        return movie
    
    # Fetch all data in single call
    data = fetch_movie_complete_data(tmdb_id)
    if not data:
        print(f"Could not fetch data for tmdb_id {tmdb_id}, skipping...")
        return None
    
    # Extract IMDb ID from external_ids
    external_ids = data.get("external_ids", {})
    imdb_id = external_ids.get("imdb_id")
    
    if not imdb_id:
        print(f"No IMDb ID for {data.get('title', 'Unknown')} (tmdb: {tmdb_id}), skipping...")
        return None
    
    # Create movie object
    movie = Movie(
        imdb_id=imdb_id,
        tmdb_id=tmdb_id,
        original_title=data.get("original_title" or data.get("title")),
        title=data.get("title"),
        overview=data.get("overview"),
        release_date=data.get("release_date"),
        popularity=data.get("popularity"),
        vote_average=data.get("vote_average"),
        vote_count=data.get("vote_count"),
        original_language=data.get("original_language"),
        runtime=data.get("runtime"),
        poster_path=data.get("poster_path"),
        backdrop_path=data.get("backdrop_path"),
    )

    # Add movie to session
    db.session.add(movie)
    
    # Add genre
    if genre_obj:
        movie.genres.append(genre_obj)
    
    # Process credits (to retrieve actors/directors)
    credits = data.get("credits", {})
    
    # Process directors
    crew = credits.get("crew", [])
    directors = [person for person in crew if person.get("job") == "Director"]
    
    for director_info in directors:
        director = get_or_create_director(
            tmdb_person_id=director_info["id"],
            name=director_info["name"]
        )
        if director not in movie.directors:
            movie.directors.append(director)
    
    # Process top 6 actors
    cast = credits.get("cast", [])
    top_actors = cast[:6]
    
    for actor_info in top_actors:
        actor = get_or_create_actor(
            tmdb_person_id=actor_info["id"],
            name=actor_info["name"]
        )
        if actor not in movie.actors:
            movie.actors.append(actor)
    
    print(f"Added movie: {movie.title} ({imdb_id})")
    return movie


def main():
    app = create_app()
    with app.app_context():
        # Ensure all genres exist
        print("Setting up genres...")
        for name, gid in GENRES.items():
            genre = Genre.query.filter_by(tmdb_id=gid).first()
            if not genre:
                genre = Genre(tmdb_id=gid, name=name)
                db.session.add(genre)
        db.session.commit()
        print("Genres ready!")
        
        # Fetch top-rated movies per genre
        print("\nFetching top-rated movies by genre...")
        for name, gid in GENRES.items():
            print(f"\nProcessing genre: {name}")
            genre = Genre.query.filter_by(tmdb_id=gid).first()
            
            top_movies = fetch_movies(
                "vote_average.desc",
                genre_id=gid,
                pages=50,
                min_votes=500
            )
            
            print(f"Found {len(top_movies)} top-rated {name} movies")
            
            for i, movie_data in enumerate(top_movies, 1):
                print(f"  Processing {i}/{len(top_movies)}...", end="\r")
                process_movie(movie_data, genre_obj=genre)
                
                # Commit every 10 movies to avoid losing progress
                if i % 10 == 0:
                    db.session.commit()
            
            db.session.commit()
            print(f"Completed {name} genre!")
        
        # Fetch overall popular movies
        print("\n\nFetching popular movies...")
        popular_movies = fetch_movies("popularity.desc", pages=25, min_votes=500)
        print(f"Found {len(popular_movies)} popular movies")
        
        for i, movie_data in enumerate(popular_movies, 1):
            print(f"  Processing {i}/{len(popular_movies)}...", end="\r")
            process_movie(movie_data)
            
            if i % 10 == 0:
                db.session.commit()
        
        db.session.commit()
        print("\n\nFinished seeding database!")
        
        # Print results 
        total_movies = Movie.query.count()
        total_directors = Director.query.count()
        total_actors = Actor.query.count()
        print(f"\nSummary:")
        print(f"  Total movies: {total_movies}")
        print(f"  Total directors: {total_directors}")
        print(f"  Total actors: {total_actors}")


if __name__ == "__main__":
    main()