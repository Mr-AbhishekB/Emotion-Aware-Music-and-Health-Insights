"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { RefreshCw, ExternalLink, Loader2 } from "lucide-react"

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

interface CurrentTrackProps {
  track: SpotifyTrack
  onRefresh: () => void
  loading: boolean
}

export default function CurrentTrack({ track, onRefresh, loading }: CurrentTrackProps) {
  if (!track.item) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600 mb-4">No track currently playing</p>
        <Button variant="outline" onClick={onRefresh} disabled={loading}>
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
          Refresh
        </Button>
      </div>
    )
  }

  const { item } = track
  const albumImage = item.album.images[0]?.url

  return (
    <div className="space-y-4">
      <div className="flex items-start space-x-4">
        {albumImage && (
          <img
            src={albumImage || "/placeholder.svg"}
            alt={item.album.name}
            className="w-20 h-20 rounded-lg object-cover"
          />
        )}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-lg truncate">{item.name}</h3>
          <p className="text-gray-600 truncate">{item.artists[0]?.name}</p>
          <p className="text-sm text-gray-500 truncate">{item.album.name}</p>
          <div className="flex items-center mt-2 space-x-2">
            <Badge variant={track.is_playing ? "default" : "secondary"}>
              {track.is_playing ? "Playing" : "Paused"}
            </Badge>
            {track.lyrics && (
              <Badge variant="outline" className="text-green-600 border-green-600">
                Lyrics Available
              </Badge>
            )}
          </div>
        </div>
      </div>

      <div className="flex space-x-2">
        <Button variant="outline" onClick={onRefresh} disabled={loading} size="sm">
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
          Refresh
        </Button>
        <Button variant="outline" size="sm" asChild>
          <a href={item.external_urls.spotify} target="_blank" rel="noopener noreferrer">
            <ExternalLink className="mr-2 h-4 w-4" />
            Open in Spotify
          </a>
        </Button>
      </div>

      {!track.lyrics && (
        <div className="text-sm text-gray-500 bg-gray-50 p-3 rounded-lg">
          <p>No lyrics found for this track. Mood analysis requires lyrics to work.</p>
        </div>
      )}
    </div>
  )
}
