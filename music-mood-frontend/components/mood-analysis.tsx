"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Brain, Loader2 } from "lucide-react"

interface MoodPrediction {
  predicted_mood: Array<{
    label: string
    score: number
  }>
}

interface MoodAnalysisProps {
  prediction: MoodPrediction | null
  analyzing: boolean
  hasLyrics: boolean
  onAnalyze: () => void
}

const emotionColors: Record<string, string> = {
  joy: "bg-yellow-100 text-yellow-800 border-yellow-300",
  sadness: "bg-blue-100 text-blue-800 border-blue-300",
  anger: "bg-red-100 text-red-800 border-red-300",
  fear: "bg-purple-100 text-purple-800 border-purple-300",
  surprise: "bg-orange-100 text-orange-800 border-orange-300",
  disgust: "bg-green-100 text-green-800 border-green-300",
  neutral: "bg-gray-100 text-gray-800 border-gray-300",
}

const emotionEmojis: Record<string, string> = {
  joy: "😊",
  sadness: "😢",
  anger: "😠",
  fear: "😨",
  surprise: "😲",
  disgust: "🤢",
  neutral: "😐",
}

export default function MoodAnalysis({ prediction, analyzing, hasLyrics, onAnalyze }: MoodAnalysisProps) {
  if (!hasLyrics) {
    return (
      <div className="text-center py-8">
        <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600 mb-2">No lyrics available</p>
        <p className="text-sm text-gray-500">Play a track with available lyrics to analyze its mood</p>
      </div>
    )
  }

  if (!prediction && !analyzing) {
    return (
      <div className="text-center py-8">
        <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600 mb-4">Ready to analyze mood</p>
        <Button onClick={onAnalyze}>
          <Brain className="mr-2 h-4 w-4" />
          Analyze Mood
        </Button>
      </div>
    )
  }

  if (analyzing) {
    return (
      <div className="text-center py-8">
        <Loader2 className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-spin" />
        <p className="text-gray-600">Analyzing emotional content...</p>
        <p className="text-sm text-gray-500 mt-2">This may take a few moments</p>
      </div>
    )
  }

  if (!prediction?.predicted_mood) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">No mood prediction available</p>
        <Button variant="outline" onClick={onAnalyze} className="mt-4">
          Try Again
        </Button>
      </div>
    )
  }

  // Sort emotions by confidence score
  const sortedEmotions = [...prediction.predicted_mood].sort((a, b) => b.score - a.score)
  const primaryEmotion = sortedEmotions[0]

  return (
    <div className="space-y-6">
      {/* Primary Emotion */}
      <div className="text-center">
        <div className="text-4xl mb-2">{emotionEmojis[primaryEmotion.label.toLowerCase()] || "🎵"}</div>
        <h3 className="text-xl font-semibold capitalize mb-1">{primaryEmotion.label}</h3>
        <p className="text-sm text-gray-600">
          Primary emotion detected ({Math.round(primaryEmotion.score * 100)}% confidence)
        </p>
      </div>

      {/* All Emotions */}
      <div className="space-y-3">
        <h4 className="font-medium text-sm text-gray-700">Emotion Breakdown:</h4>
        {sortedEmotions.map((emotion, index) => {
          const percentage = Math.round(emotion.score * 100)
          const colorClass = emotionColors[emotion.label.toLowerCase()] || emotionColors.neutral

          return (
            <div key={emotion.label} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{emotionEmojis[emotion.label.toLowerCase()] || "🎵"}</span>
                  <span className="capitalize font-medium">{emotion.label}</span>
                </div>
                <Badge variant="outline" className={colorClass}>
                  {percentage}%
                </Badge>
              </div>
              <Progress value={percentage} className="h-2" />
            </div>
          )
        })}
      </div>

      {/* Re-analyze Button */}
      <Button variant="outline" onClick={onAnalyze} className="w-full" size="sm">
        <Brain className="mr-2 h-4 w-4" />
        Re-analyze
      </Button>
    </div>
  )
}
