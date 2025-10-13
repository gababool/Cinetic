import pandas as pd
from pathlib import Path
from app import create_app, db
from app.models.users import User
from app.models.ratings import Rating
from app.models.movies import Movie


### Script to be run once on a databse empty of ratings and users to seed it for ML training ###


# Ensure the distinct userId sequence is exactly [1, 2, ..., N] in that order.
# This guarantees autoincrement IDs will align with CSV userId without explicit PK setting.
def sanity_check(df):
    uids = df["userId"].dropna().astype(int).unique()
    n = len(uids)
    expected = list(range(1, n + 1))
    if list(uids) != expected:
        last_uid = int(df["userId"].iloc[-1])
        raise ValueError(
            f"Sanity check failed: unique userId sequence != 1..N in order. "
            f"N={n}, last CSV userId={last_uid}. "
            f"First few found: {list(uids[:10])} ; expected start: {expected[:10]}"
        )


def import_ml_ratings():
    app = create_app()
    with app.app_context():

        ROOT = Path(__file__).resolve().parents[3]
        csv_path = ROOT / "data/ml-latest-small/ratings_cleaned.csv"

        df = pd.read_csv(
            csv_path,
            dtype={"userId":"int32","rating":"UInt8","imdbId":"string","tmdbId":"Int32"},
            parse_dates=["date_rated"],
        )

        # Sanity check to ensure autoincrement alignment is safe
        sanity_check(df)

        unique_ml_users = df['userId'].unique() # Get unique users

        # Add ML users
        for uid in unique_ml_users:
            user = User(ml=True)
            db.session.add(user) 
            print(f"Successfully added user: {uid}")
        db.session.commit()

        # Loop through all rows and add rating to database
        for row in df.itertuples(index=False):
            movie = Movie.query.filter_by(imdb_id=row.imdbId).first()
            if not movie:
                continue
            tmdbId = None if pd.isna(row.tmdbId) else int(row.tmdbId)
            rating = Rating(
                user_id = int(row.userId),
                imdb_id = row.imdbId,
                tmdb_id = tmdbId,
                rating = row.rating,
                date_rated = row.date_rated.date()
            )
            db.session.add(rating) 
            print(f"Successfully added rating for : {rating.imdb_id}")
        db.session.commit()


def main():
    import_ml_ratings()

if __name__ == "__main__":
    main()


