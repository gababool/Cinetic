from sqlalchemy import func
from app import db

class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    username = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    ml = db.Column(db.Boolean, default=False, nullable=False) # ML user, not real one
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ratings = db.relationship("Rating", back_populates="user", cascade="all, delete-orphan")