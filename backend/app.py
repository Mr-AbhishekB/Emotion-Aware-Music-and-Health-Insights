from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
from lyricsgenius import Genius
import requests
from dotenv import load_dotenv
import re
from transformers import pipeline
import tf_keras as keras
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

genius = Genius("qVNhO3eE4ze3oeAuJTSS3DY3mJaDviSMo8JYA9NfJQIDnx8bGQ4gnUd9cnC-IBKJ")
# Initialize the database
db = SQLAlchemy(app)

load_dotenv()

# Initialize Spotify client
sp_oauth = SpotifyOAuth(
    client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
    client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.environ.get("NEXT_PUBLIC_SPOTIFY_REDIRECT_URI"),
    scope="user-library-read user-read-currently-playing",
    # cache_path=".spotipyoauthcache"
)

# Load trained model & label encoder
# model = load_model("rmodel.pkl")
# label_classes = np.load("label_classes.npy", allow_pickle=True)
sentiment_analyzer = pipeline("text-classification",
                          model="j-hartmann/emotion-english-distilroberta-base",
                          truncation=True,
                          max_length=512)
# Initialize VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username, password=password).first()
    if user:
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"message": "Username already exists"}), 400
    
    try:
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Signup successful"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Database error"}), 500

@app.route('/get_current_track', methods=['GET'])
def get_current_track():
    token_info = sp_oauth.get_cached_token()
    # print(f"Token Info: {token_info}")  # Debugging Output

    if token_info:
        if 'refresh_token' in token_info:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            # print(f"Refreshed Token Info: {token_info}")  # Debugging Output

        access_token = token_info['access_token']
        sp = spotipy.Spotify(auth=access_token)
        current_track = sp.current_user_playing_track()
        print(f"Current Track Data: {current_track}")  # Debugging Output

        if not current_track or not current_track.get('item'):
            return jsonify({"message": "No song is currently playing"}), 200

        track = current_track['item']
        artist = track['artists'][0]['name']
        song_name = track['name']

        # Fetch lyrics
        song = genius.search_song(song_name, artist)
        if song:
            lyrics = song.lyrics
            current_track['lyrics'] = lyrics

        print(current_track.get('lyrics'))
        # print(f"Final Response Data: {current_track}")  # Debugging Output

        return jsonify(current_track), 200
    else:
        print("Failed to authenticate with Spotify.")  # Debugging Output
        return jsonify({"message": "Failed to authenticate with Spotify"}), 401
def clean_lyrics(raw_lyrics):
    if not raw_lyrics:
        return ""
    
    # Remove first 206 characters
    text = raw_lyrics[206:]
    
    # Remove contributor information at the beginning
    text = re.sub(r'^\d+\s+Contributors.*?Lyrics', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove everything up to and including "Read More" (song description/background info)
    text = re.sub(r'^.*?Read More\s*', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove production credits in square brackets
    text = re.sub(r'\[Produced by[^\]]*\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[Video by[^\]]*\]', '', text, flags=re.IGNORECASE)
    
    # Remove section labels but keep the content
    text = re.sub(r'\[(Chorus|Verse \d+|Bridge|Pre-Chorus|Post-Chorus|Outro|Intro|Hook)\]', '', text, flags=re.IGNORECASE)
    
    # Remove any remaining square bracket content (other metadata)
    text = re.sub(r'\[[^\]]*\]', '', text)
    
    # Remove translation language mentions
    text = re.sub(r'(Türkçe|Ελληνικά|Français|Deutsch|Español|Italiano|Português)', '', text, flags=re.IGNORECASE)
    
    # Remove multiple consecutive newlines and replace with single newline
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # Remove leading/trailing whitespace and newlines
    text = text.strip()
    
    # Remove any remaining metadata patterns (URLs, special characters clusters)
    text = re.sub(r'https?://[^\s]+', '', text)
    text = re.sub(r'[^\w\s\n\'\.\,\!\?\-]', ' ', text)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s+', '\n', text)
    
    return text.strip()


@app.route('/predict_mood', methods=['POST'])
def predict_mood():
    data = request.json
    lyrics = data.get('lyrics')
    if not lyrics:
        return jsonify({"error": "No lyrics provided"}), 400

    cleaned_lyrics = clean_lyrics(lyrics)
    print(cleaned_lyrics)  # Debugging Output
    
    
    if not cleaned_lyrics:
        return jsonify({"error": "No valid lyrics found after cleaning"}), 400

   
    result = sentiment_analyzer(cleaned_lyrics)

    return jsonify({"predicted_mood": result}), 200

if __name__ == '__main__':
    app.run(debug=True)
