"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Music, Brain, Heart, Loader2 } from "lucide-react"
import Dashboard from "@/components/dashboard"

interface User {
  username: string
  user_id?: string // ✅ Added to hold user_id from backend
}

interface AuthResponse {
  message: string
  user_id?: string // ✅ Added to extract user_id from response
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  useEffect(() => {
    // Check if user is already logged in
    const savedUser = localStorage.getItem("user")
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    }
  }, [])

  const handleAuth = async (endpoint: string, username: string, password: string) => {
    setLoading(true)
    setError("")
    setSuccess("")

    try {
      const response = await fetch(`http://localhost:5000/${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      })

      const data: AuthResponse = await response.json()

      if (response.ok) {
        if (endpoint === "login") {
          // ✅ Store user_id from backend response
          const userData = { username, user_id: data.user_id }
          setUser(userData)
          localStorage.setItem("user", JSON.stringify(userData))
          setSuccess("Login successful!")
        } else {
          setSuccess("Signup successful! Please login.")
        }
      } else {
        setError(data.message || "Authentication failed")
      }
    } catch (err) {
      setError("Network error. Please check if the backend is running.")
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
        const userStr = localStorage.getItem("user")
        const userId = userStr ? JSON.parse(userStr).user_id : undefined
    setUser(null)
    const res = await fetch(`http://localhost:5000/logout`, {
      method: "DELETE",
        headers: {
    "Content-Type": "application/json",
  },
      body: JSON.stringify({ user_id: userId }),
    })
    localStorage.removeItem("user")
    setSuccess("Logged out successfully")
  }

  if (user) {
    return <Dashboard user={user} onLogout={handleLogout} />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Music className="h-12 w-12 text-purple-600 mr-2" />
            <Brain className="h-12 w-12 text-blue-600 mr-2" />
            <Heart className="h-12 w-12 text-pink-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">MoodTunes</h1>
          <p className="text-gray-600">Discover the emotion in your music</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Welcome to MoodTunes</CardTitle>
            <CardDescription>Sign in to analyze the mood of your currently playing Spotify tracks</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login">Login</TabsTrigger>
                <TabsTrigger value="signup">Sign Up</TabsTrigger>
              </TabsList>

              <TabsContent value="login">
                <AuthForm type="login" onSubmit={handleAuth} loading={loading} />
              </TabsContent>

              <TabsContent value="signup">
                <AuthForm type="signup" onSubmit={handleAuth} loading={loading} />
              </TabsContent>
            </Tabs>

            {error && (
              <Alert className="mt-4 border-red-200 bg-red-50">
                <AlertDescription className="text-red-800">{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="mt-4 border-green-200 bg-green-50">
                <AlertDescription className="text-green-800">{success}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

interface AuthFormProps {
  type: "login" | "signup"
  onSubmit: (endpoint: string, username: string, password: string) => void
  loading: boolean
}

function AuthForm({ type, onSubmit, loading }: AuthFormProps) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(type, username, password)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="username">Username</Label>
        <Input
          id="username"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          disabled={loading}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={loading}
        />
      </div>

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            {type === "login" ? "Signing In..." : "Creating Account..."}
          </>
        ) : type === "login" ? (
          "Sign In"
        ) : (
          "Create Account"
        )}
      </Button>
    </form>
  )
}
