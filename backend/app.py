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

app = Flask(__name__)

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

genius = Genius("qVNhO3eE4ze3oeAuJTSS3DY3mJaDviSMo8JYA9NfJQIDnx8bGQ4gnUd9cnC-IBKJ")
# Initialize the database
db = SQLAlchemy(app)

# Initialize Spotify client
sp_oauth = SpotifyOAuth(client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
                        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
                        redirect_uri=os.environ.get("NEXT_PUBLIC_SPOTIFY_REDIRECT_URI"),
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
    token_info = sp_oauth.get_cached_token()
    print(f"Token Info: {token_info}")  # Debugging Output

    if token_info:
        if 'refresh_token' in token_info:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            print(f"Refreshed Token Info: {token_info}")  # Debugging Output

        access_token = token_info['access_token']
        sp = spotipy.Spotify(auth=access_token)
        current_track = sp.current_user_playing_track()
        print(f"Current Track Data: {current_track}")  # Debugging Output

        if current_track and current_track.get('item'):
            track = current_track['item']
            track_id = track['id']
            artist = track['artists'][0]['name']
            song_name = track['name']

            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            audio_features_url = f"https://api.spotify.com/v1/audio-features/{track_id}"
            audio_response = requests.get(audio_features_url, headers=headers)

            if audio_response.status_code == 200:
                audio_features = audio_response.json()
                current_track['audio_features'] = {
                    "tempo": audio_features.get('tempo'),
                    "danceability": audio_features.get('danceability'),
                    "energy": audio_features.get('energy'),
                    "valence": audio_features.get('valence')
                }
            else:
                print(f"Failed to retrieve audio features: {audio_response.status_code}")

            # Fetch lyrics
            song = genius.search_song(song_name, artist)
            if song:
                lyrics = song.lyrics
                current_track['lyrics'] = lyrics

            print(f"Final Response Data: {current_track}")  # Debugging Output

        return jsonify(current_track), 200
    else:
        print("Failed to authenticate with Spotify.")  # Debugging Output
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
