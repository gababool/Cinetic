from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Print for debugging (remove later)
    print("Using database URL:", app.config["SQLALCHEMY_DATABASE_URI"])

    db.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    # Import models
    from .models import movies, users, ratings

    return app
