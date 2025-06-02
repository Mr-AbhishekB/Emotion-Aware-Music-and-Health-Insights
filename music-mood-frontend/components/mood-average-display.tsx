import React, { useState } from 'react';

const MoodAverageDisplay = ({ userId = 1 }) => {
  const [moodData, setMoodData] = useState<MoodData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchMoodAverage = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:5000/get_mood_average/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch mood data');
      }

      const data = await response.json();
      setMoodData(data);
    } catch (err:any) {
      setError(err.message);
      console.error('Error fetching mood average:', err);
    } finally {
      setLoading(false);
    }
  };

interface MoodData {
    mood_interpretation: string;
    average_mood: number;
    total_predictions: number;
    username: string;
    mood_numbers: number[];
}

interface MoodAverageDisplayProps {
    userId?: number;
}

const getMoodColor = (interpretation: string): string => {
    const colors: { [key: string]: string } = {
        'Very Positive': 'text-green-600 bg-green-50 border-green-200',
        'Positive': 'text-green-500 bg-green-40 border-green-100',
        'Slightly Positive': 'text-blue-500 bg-blue-50 border-blue-200',
        'Neutral': 'text-gray-600 bg-gray-50 border-gray-200',
        'Slightly Negative': 'text-orange-500 bg-orange-50 border-orange-200',
        'Negative': 'text-red-500 bg-red-50 border-red-200',
        'Very Negative': 'text-red-600 bg-red-100 border-red-300'
    };
    return colors[interpretation] || 'text-gray-600 bg-gray-50 border-gray-200';
};

interface MoodEmojiMap {
    [key: string]: string;
}

const getMoodEmoji = (interpretation: string): string => {
    const emojis: MoodEmojiMap = {
        'Very Positive': '😄',
        'Positive': '😊',
        'Slightly Positive': '🙂',
        'Neutral': '😐',
        'Slightly Negative': '😕',
        'Negative': '😞',
        'Very Negative': '😢'
    };
    return emojis[interpretation] || '😐';
};

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">
        Mood Analytics
      </h2>
      
      <button
        onClick={fetchMoodAverage}
        disabled={loading}
        className={`w-full py-3 px-4 rounded-lg font-semibold text-white transition-all duration-200 ${
          loading
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800 shadow-md hover:shadow-lg'
        }`}
      >
        {loading ? (
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
            Calculating...
          </div>
        ) : (
          'Get My Overall Mood'
        )}
      </button>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600 text-sm font-medium">Error: {error}</p>
        </div>
      )}

      {moodData && (
        <div className="mt-6 space-y-4">
          {/* Main Mood Display */}
          <div className={`p-4 rounded-lg border-2 ${getMoodColor(moodData.mood_interpretation)}`}>
            <div className="text-center">
              <div className="text-4xl mb-2">
                {getMoodEmoji(moodData.mood_interpretation)}
              </div>
              <h3 className="text-xl font-bold mb-1">
                {moodData.mood_interpretation}
              </h3>
              <p className="text-lg font-semibold">
                Average Score: {moodData.average_mood}/10
              </p>
            </div>
          </div>

          {/* Detailed Stats */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-700 mb-2">Statistics</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Total Predictions:</span>
                <span className="font-semibold ml-1">{moodData.total_predictions}</span>
              </div>
              <div>
                <span className="text-gray-600">User:</span>
                <span className="font-semibold ml-1">{moodData.username}</span>
              </div>
            </div>
          </div>

          {/* Mood History Preview */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-700 mb-2">Recent Mood Scores</h4>
            <div className="flex flex-wrap gap-2">
              {moodData.mood_numbers.slice(-10).map((mood, index) => (
                <span
                  key={index}
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    mood >= 7
                      ? 'bg-green-100 text-green-700'
                      : mood >= 5
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-red-100 text-red-700'
                  }`}
                >
                  {mood}
                </span>
              ))}
              {moodData.mood_numbers.length > 10 && (
                <span className="px-2 py-1 rounded text-xs text-gray-500 bg-gray-200">
                  +{moodData.mood_numbers.length - 10} more
                </span>
              )}
            </div>
          </div>

          {/* Motivational Message */}
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-700">
              {moodData.average_mood >= 7
                ? "Keep up the positive vibes! 🌟"
                : moodData.average_mood >= 5
                ? "You're doing great! Stay balanced ⚖️"
                : "Remember, every day is a new chance to feel better 💪"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MoodAverageDisplay;