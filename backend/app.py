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
import json


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
    


# New Model to store mood prediction arrays
class MoodPrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mood_numbers = db.Column(db.Text, nullable=False)  # Store array as JSON string
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def get_mood_numbers(self):
        """Convert JSON string back to list"""
        return json.loads(self.mood_numbers)
    
    def set_mood_numbers(self, numbers_list):
        """Convert list to JSON string for storage"""
        self.mood_numbers = json.dumps(numbers_list)
        
# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username, password=password).first()
    print("User data: ", user.id)
    if user:
        return jsonify({"message": "Login successful" , "user_id": user.id}), 200
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







def calculate_mood_number(label, score):
    """
    Calculate mood number (1-10) based on label and score
    """
    # Define mood mappings - positive emotions get higher base values
    mood_mappings = {
        'joy': 8,
        'happiness': 8,
        'love': 8,
        'excitement': 7,
        'surprise': 6,
        'neutral': 5,
        'fear': 4,
        'anger': 3,
        'disgust': 3,
        'sadness': 2,
        'sad': 2
    }
    
    # Get base score for the emotion (default to 5 for unknown emotions)
    base_score = mood_mappings.get(label.lower(), 5)
    
    # Adjust based on confidence score
    # Score ranges from 0 to 1, we'll use it to fine-tune the base score
    if score >= 0.8:  # High confidence
        adjustment = 1
    elif score >= 0.6:  # Medium confidence
        adjustment = 0
    else:  # Low confidence
        adjustment = -1
    
    # Calculate final mood number
    mood_number = base_score + adjustment
    
    # Ensure it's within 1-10 range
    mood_number = max(1, min(10, mood_number))
    
    return mood_number



# @app.route('/predict_mood', methods=['POST'])
# def predict_mood():
#     data = request.json
#     lyrics = data.get('lyrics')
#     if not lyrics:
#         return jsonify({"error": "No lyrics provided"}), 400

#     cleaned_lyrics = clean_lyrics(lyrics)
#     print(cleaned_lyrics)  # Debugging Output
    
    
#     if not cleaned_lyrics:
#         return jsonify({"error": "No valid lyrics found after cleaning"}), 400

   
#     result = sentiment_analyzer(cleaned_lyrics)

#     return jsonify({"predicted_mood": result}), 200


@app.route('/predict_mood', methods=['POST'])
def predict_mood():
    data = request.json
    lyrics = data.get('lyrics')
    user_id = data.get('user_id')  # Add user_id to the request
    user_id = int(user_id)
    print(user_id)  # Debugging Output
    
    if not lyrics:
        return jsonify({"error": "No lyrics provided"}), 400
    
    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400
    
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    print(user)
    if not user:
        return jsonify({"error": "User not found"}), 404

    cleaned_lyrics = clean_lyrics(lyrics)
    print(cleaned_lyrics)  # Debugging Output
    
    if not cleaned_lyrics:
        return jsonify({"error": "No valid lyrics found after cleaning"}), 400

    result = sentiment_analyzer(cleaned_lyrics)
    
    # Extract label and score from the result
    predicted_mood = result[0]  # Assuming result is a list with one prediction
    label = predicted_mood['label']
    score = predicted_mood['score']
    
    # Calculate mood number
    mood_number = calculate_mood_number(label, score)
    
    # Get or create mood prediction record for the user
    mood_prediction = MoodPrediction.query.filter_by(user_id=user_id).first()
    
    if mood_prediction:
        # User already has a mood prediction record, add to existing array
        current_numbers = mood_prediction.get_mood_numbers()
        current_numbers.append(mood_number)
        mood_prediction.set_mood_numbers(current_numbers)
    else:
        # Create new mood prediction record
        mood_prediction = MoodPrediction(user_id=user_id)
        mood_prediction.set_mood_numbers([mood_number])
    
    # Save to database
    try:
        if not MoodPrediction.query.filter_by(user_id=user_id).first():
            db.session.add(mood_prediction)
        db.session.commit()
        
        return jsonify({
            "predicted_mood": result,
            "mood_number": mood_number,
            "total_predictions": len(mood_prediction.get_mood_numbers())
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    

# Route to clear mood history for a user
@app.route('/clear_mood_history/<int:user_id>', methods=['DELETE'])
def clear_mood_history(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    mood_prediction = MoodPrediction.query.filter_by(user_id=user_id).first()
    if mood_prediction:
        db.session.delete(mood_prediction)
        db.session.commit()
    
    return jsonify({"message": "Mood history cleared successfully"}), 200



@app.route('/get_mood_average/<int:user_id>', methods=['GET'])
def get_mood_average(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    mood_prediction = MoodPrediction.query.filter_by(user_id=user_id).first()
    if not mood_prediction:
        return jsonify({"error": "No mood data found for this user"}), 404
    
    mood_numbers = mood_prediction.get_mood_numbers()
    
    if not mood_numbers:
        return jsonify({"error": "No mood predictions available"}), 404
    
    # Calculate average
    average_mood = sum(mood_numbers) / len(mood_numbers)
    
    # Round to 2 decimal places for better readability
    average_mood = round(average_mood, 2)
    
    return jsonify({
        "user_id": user_id,
        "username": user.username,
        "mood_numbers": mood_numbers,
        "total_predictions": len(mood_numbers),
        "average_mood": average_mood,
        "mood_interpretation": interpret_mood_average(average_mood)
    }), 200

def interpret_mood_average(average):
    """
    Provide interpretation of the average mood score
    """
    if average >= 8.0:
        return "Very Positive"
    elif average >= 6.5:
        return "Positive"
    elif average >= 5.5:
        return "Slightly Positive"
    elif average >= 4.5:
        return "Neutral"
    elif average >= 3.0:
        return "Slightly Negative"
    elif average >= 1.5:
        return "Negative"
    else:
        return "Very Negative"


if __name__ == '__main__':
    app.run(debug=True)
