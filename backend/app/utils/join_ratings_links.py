import pandas as pd

ratings_path = "../../../data/ml-latest-small/ratings.csv"
links_path   = "../../../data/ml-latest-small/links.csv"
output_path  = "../../../data/ml-latest-small/ratings_cleaned.csv"

links = pd.read_csv(links_path, dtype={"imdbId": str})
ratings = pd.read_csv(ratings_path)

# Double the rating score to fit 1-10 scale used my Cinetic / IMDb / TMDb
ratings["rating"] = (ratings["rating"] * 2).astype(pd.Int64Dtype())

links["tmdbId"] = links["tmdbId"].astype(pd.Int64Dtype()) # To make sure tmdbIds are integers

# Prefix 'tt' to imdbId
links["imdbId"] = "tt" + links["imdbId"]

# Merge
merged = pd.merge(ratings, links, on="movieId", how="inner")

# Convert timestamp to date
merged["date_rated"] = pd.to_datetime(merged["timestamp"], unit="s").dt.date

# Drop movieId and timestamp
merged = merged.drop(columns=["movieId", "timestamp"])

# Save output
merged.to_csv(output_path, index=False)
print(f"Merged file saved as {output_path}")
