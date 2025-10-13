from sqlalchemy import func
from app import db

class Rating(db.Model):
    __tablename__ = "ratings"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    imdb_id = db.Column(db.String(255), db.ForeignKey('movies.imdb_id'), nullable=False)
    tmdb_id= db.Column(db.Integer, nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    date_rated = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = db.relationship("User", back_populates="ratings")
    movie = db.relationship("Movie", back_populates="ratings", foreign_keys=[imdb_id])
