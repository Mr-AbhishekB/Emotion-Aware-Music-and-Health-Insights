"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Music, Brain, LogOut, RefreshCw, Loader2 } from "lucide-react"
import CurrentTrack from "@/components/current-track"
import MoodAnalysis from "@/components/mood-analysis"

interface User {
  username: string
}

interface DashboardProps {
  user: User
  onLogout: () => void
}

interface SpotifyTrack {
  item?: {
    name: string
    artists: Array<{ name: string }>
    album: {
      name: string
      images: Array<{ url: string }>
    }
    external_urls: {
      spotify: string
    }
  }
  lyrics?: string
  is_playing?: boolean
}

interface MoodPrediction {
  predicted_mood: Array<{
    label: string
    score: number
  }>
}

export default function Dashboard({ user, onLogout }: DashboardProps) {
  const [currentTrack, setCurrentTrack] = useState<SpotifyTrack | null>(null)
  const [moodPrediction, setMoodPrediction] = useState<MoodPrediction | null>(null)
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState("")

  const fetchCurrentTrack = async () => {
    setLoading(true)
    setError("")

    try {
      const response = await fetch("http://localhost:5000/get_current_track")

      if (response.ok) {
        const data = await response.json()
        setCurrentTrack(data)

        // Auto-analyze mood if lyrics are available
        if (data.lyrics) {
          await analyzeMood(data.lyrics)
        }
      } else {
        const errorData = await response.json()
        setError(errorData.message || "Failed to fetch current track")
      }
    } catch (err) {
      setError("Network error. Please check if the backend is running.")
    } finally {
      setLoading(false)
    }
  }

  const analyzeMood = async (lyrics: string) => {
    setAnalyzing(true)
    setError("")

    try {
      const response = await fetch("http://localhost:5000/predict_mood", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ lyrics }),
      })

      if (response.ok) {
        const data = await response.json()
        setMoodPrediction(data)
      } else {
        const errorData = await response.json()
        setError(errorData.error || "Failed to analyze mood")
      }
    } catch (err) {
      setError("Failed to analyze mood")
    } finally {
      setAnalyzing(false)
    }
  }

  // Auto-fetch current track when component mounts
  useEffect(() => {
    fetchCurrentTrack()
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center">
            <div className="flex items-center mr-4">
              <Music className="h-8 w-8 text-purple-600 mr-2" />
              <Brain className="h-8 w-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">MoodTunes Dashboard</h1>
              <p className="text-gray-600">Welcome back, {user.username}!</p>
            </div>
          </div>
          <Button variant="outline" onClick={onLogout}>
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </Button>
        </div>

        {/* Main Content */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Current Track Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Music className="mr-2 h-5 w-5" />
                Current Track
              </CardTitle>
              <CardDescription>Your currently playing Spotify track</CardDescription>
            </CardHeader>
            <CardContent>
              {!currentTrack ? (
                <div className="text-center py-8">
                  <Music className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">
                    {loading ? "Loading your current track..." : "No track currently playing"}
                  </p>
                  <Button onClick={fetchCurrentTrack} disabled={loading}>
                    {loading ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="mr-2 h-4 w-4" />
                    )}
                    {loading ? "Loading..." : "Refresh Track"}
                  </Button>
                  <div className="text-sm text-gray-500 mt-4">
                    <p>Make sure you're playing a song on Spotify!</p>
                  </div>
                </div>
              ) : (
                <CurrentTrack track={currentTrack} onRefresh={fetchCurrentTrack} loading={loading} />
              )}
            </CardContent>
          </Card>

          {/* Mood Analysis Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Brain className="mr-2 h-5 w-5" />
                Mood Analysis
              </CardTitle>
              <CardDescription>AI-powered emotion detection from lyrics</CardDescription>
            </CardHeader>
            <CardContent>
              <MoodAnalysis
                prediction={moodPrediction}
                analyzing={analyzing}
                hasLyrics={!!currentTrack?.lyrics}
                onAnalyze={() => currentTrack?.lyrics && analyzeMood(currentTrack.lyrics)}
              />
            </CardContent>
          </Card>
        </div>

        {/* Error Display */}
        {error && (
          <Alert className="mt-6 border-red-200 bg-red-50">
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        )}

        {/* Instructions */}
        <Card className="mt-6">
          <CardContent className="pt-6">
            <div className="text-center text-sm text-gray-600">
              <p><strong>How to use:</strong></p>
              <p>1. Play a song on your Spotify app (phone/desktop)</p>
              <p>2. Click "Refresh Track" to get your currently playing song</p>
              <p>3. The app will automatically analyze the mood of the lyrics</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}