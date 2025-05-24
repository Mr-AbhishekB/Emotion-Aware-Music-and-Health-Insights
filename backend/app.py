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

app = Flask(__name__)

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Spotify API credentials
SPOTIFY_CLIENT_ID = "b053adbd0c014c598a0577db054379e5"
SPOTIFY_CLIENT_SECRET = "51c5f5ecd6364f9f972aa3e264fcff05"
NEXT_PUBLIC_SPOTIFY_REDIRECT_URI = "http://127.0.0.1:3000/api/auth/callback/spotify"

# Initialize Spotify client
sp_oauth = SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                         client_secret=SPOTIFY_CLIENT_SECRET,
                         redirect_uri=NEXT_PUBLIC_SPOTIFY_REDIRECT_URI,
                         scope="user-library-read user-read-currently-playing")

# Load trained model & label encoder
model = load_model("mood_prediction_lstm.h5")
label_classes = np.load("label_classes.npy", allow_pickle=True)

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

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Signup successful"}), 201

@app.route('/get_current_track', methods=['GET'])
def get_current_track():
    # Use get_cached_token instead of get_access_token
    token_info = sp_oauth.get_cached_token()
    print(token_info)
    if token_info:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        current_track = sp.current_user_playing_track()
        print(current_track)
        if current_track is None:
            return jsonify({"message": "No track currently playing"}), 200
        return jsonify(current_track), 200
    else:
        return jsonify({"message": "Failed to authenticate with Spotify"}), 401

@app.route('/predict_mood', methods=['POST'])
def predict_mood():
    data = request.json
    lyrics = data.get('lyrics')

    # Perform sentiment analysis on the lyrics
    sentiment_score = analyzer.polarity_scores(lyrics)["compound"]

    # Normalize the sentiment score
    scaler = MinMaxScaler()
    sentiment_score_normalized = scaler.fit_transform([[sentiment_score]])

    # Create sequences for LSTM input (example: using the last 10 sentiment scores)
    sequence_length = 10
    sentiment_sequence = get_recent_sentiment_scores(sequence_length)  # Implement this function to maintain a buffer of recent scores
    sentiment_sequence.append(sentiment_score_normalized[0][0])
    sentiment_sequence = sentiment_sequence[-sequence_length:]  # Keep only the last 10 scores

    # Reshape for LSTM input
    sentiment_sequence = np.array(sentiment_sequence).reshape(1, sequence_length, 1)

    # Predict mood
    prediction = model.predict(sentiment_sequence)
    predicted_mood = label_classes[np.argmax(prediction)]

    return jsonify({"predicted_mood": predicted_mood}), 200

def get_recent_sentiment_scores(sequence_length):
    # Implement this function to maintain a buffer of recent sentiment scores
    # For simplicity, we return a dummy list here
    return [0.5] * sequence_length

if __name__ == '__main__':
    app.run(debug=True)
