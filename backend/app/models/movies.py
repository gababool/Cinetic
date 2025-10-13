from app import db

movie_genres = db.Table(
    "movie_genres",
    db.Column("movie_id", db.String(16), db.ForeignKey("movies.imdb_id", ondelete="CASCADE"), primary_key=True),
    db.Column("genre_id", db.Integer, db.ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)

movie_directors = db.Table(
    "movie_directors",
    db.Column("movie_id", db.String(16), db.ForeignKey("movies.imdb_id", ondelete="CASCADE"), primary_key=True),
    db.Column("director_id", db.Integer, db.ForeignKey("directors.id", ondelete="CASCADE"), primary_key=True),
)

movie_actors = db.Table(
    "movie_actors",
    db.Column("movie_id", db.String(16), db.ForeignKey("movies.imdb_id", ondelete="CASCADE"), primary_key=True),
    db.Column("actor_id", db.Integer, db.ForeignKey("actors.id", ondelete="CASCADE"), primary_key=True),
)

class Movie(db.Model):
    __tablename__ = "movies"

    imdb_id = db.Column(db.String(16), primary_key=True, index=True)
    tmdb_id = db.Column(db.Integer, unique=True, nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    original_title = db.Column(db.String(255), nullable=False)
    overview = db.Column(db.Text)
    release_date = db.Column(db.String(20))
    popularity = db.Column(db.Float)
    vote_average = db.Column(db.Float)
    vote_count = db.Column(db.Integer)
    original_language = db.Column(db.String(10))
    runtime = db.Column(db.Integer)
    poster_path = db.Column(db.String(255))
    backdrop_path = db.Column(db.String(255))

    genres = db.relationship("Genre", secondary=movie_genres, back_populates="movies")
    directors = db.relationship("Director", secondary=movie_directors, back_populates="movies")
    actors = db.relationship("Actor", secondary=movie_actors, back_populates="movies")
    ratings = db.relationship( "Rating", back_populates="movie", foreign_keys="Rating.imdb_id", cascade="all, delete-orphan",)

class Genre(db.Model):
    __tablename__ = "genres"

    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)

    movies = db.relationship("Movie", secondary=movie_genres, back_populates="genres")

class Director(db.Model):
    __tablename__ = "directors"

    id = db.Column(db.Integer, primary_key=True)
    tmdb_person_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)

    movies = db.relationship("Movie", secondary=movie_directors, back_populates="directors")

class Actor(db.Model):
    __tablename__ = "actors"

    id = db.Column(db.Integer, primary_key=True)
    tmdb_person_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)

    movies = db.relationship("Movie", secondary=movie_actors, back_populates="actors")
