import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listTablesApiTablesGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import type { BrailleTable } from '@/lib/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Loader2, Languages, Volume2 } from 'lucide-react'
import { BrailleToSpeechSettings } from './BrailleToSpeechSettings'
import { PresetSelector } from './PresetSelector'
import type { TTSSettings } from './BrailleToSpeechSettings'
import type { TTSPreset } from './PresetSelector'

interface VoiceInfo {
  voice_id: string
  language: string
  quality: string
}

export function BrailleToSpeech() {
  const [selectedTable, setSelectedTable] = useState<string>(() => {
    return localStorage.getItem('speech2braille_table') || 'en-ueb-g2.ctb'
  })
  const [selectedVoice, setSelectedVoice] = useState<string>('')
  const [brailleInput, setBrailleInput] = useState<string>('')
  const [backTranslatedText, setBackTranslatedText] = useState<string>('')
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [isSynthesizing, setIsSynthesizing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // TTS Settings state
  const [settings, setSettings] = useState<TTSSettings>(() => {
    const saved = localStorage.getItem('speech2braille_tts_settings')
    return saved ? JSON.parse(saved) : {
      length_scale: 1.0,
      volume: 1.0,
      noise_scale: 0.667,
      noise_w: 0.8,
      normalize_audio: true,
    }
  })
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [selectedPreset, setSelectedPreset] = useState<TTSPreset>('natural')

  // Persist selected table
  useEffect(() => {
    localStorage.setItem('speech2braille_table', selectedTable)
  }, [selectedTable])

  // Persist settings
  useEffect(() => {
    localStorage.setItem('speech2braille_tts_settings', JSON.stringify(settings))
  }, [settings])

  // Cleanup blob URL on unmount or re-synthesis
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
      }
    }
  }, [audioUrl])

  // Fetch available braille tables
  const { data: tables, isLoading: tablesLoading } = useQuery(listTablesApiTablesGetOptions())

  // Fetch available voices
  const { data: voices, isLoading: voicesLoading } = useQuery<VoiceInfo[]>({
    queryKey: ['voices'],
    queryFn: async () => {
      const res = await fetch('/api/voices')
      if (!res.ok) throw new Error('Failed to fetch voices')
      return res.json()
    },
  })

  // Set default voice when voices load
  useEffect(() => {
    if (voices && voices.length > 0 && !selectedVoice) {
      setSelectedVoice(voices[0].voice_id)
    }
  }, [voices, selectedVoice])

  const handleSynthesize = async () => {
    if (!brailleInput.trim()) return

    setIsSynthesizing(true)
    setError(null)
    setBackTranslatedText('')

    // Revoke previous blob URL
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
      setAudioUrl(null)
    }

    try {
      const res = await fetch('/api/braille-to-speech', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          braille: brailleInput,
          table: selectedTable,
          voice_id: selectedVoice || undefined,
          ...settings,
        }),
      })

      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(detail.detail || `Request failed: ${res.status}`)
      }

      // Read metadata from custom headers
      const translatedText = res.headers.get('X-Back-Translated-Text') || ''
      setBackTranslatedText(translatedText)

      // Create blob URL from WAV response
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      setAudioUrl(url)

      // Auto-play (silently catch browser policy blocks)
      setTimeout(() => {
        audioRef.current?.play().catch(() => {})
      }, 100)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setIsSynthesizing(false)
    }
  }

  // Group tables by language
  const groupedTables = tables?.reduce(
    (acc, table) => {
      const lang = table.language || 'other'
      if (!acc[lang]) {
        acc[lang] = []
      }
      acc[lang].push(table)
      return acc
    },
    {} as Record<string, BrailleTable[]>,
  )

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Configuration Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Languages className="w-5 h-5" />
            <CardTitle>Configuration</CardTitle>
          </div>
          <CardDescription>
            Select the braille table and voice for speech synthesis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Braille Table Selector */}
            <div className="space-y-2">
              <Label htmlFor="table-select">Braille Table</Label>
              {tablesLoading ? (
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading tables...
                </div>
              ) : (
                <Select value={selectedTable} onValueChange={setSelectedTable}>
                  <SelectTrigger id="table-select" className="w-full">
                    <SelectValue placeholder="Select a braille table" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(groupedTables || {})
                      .sort(([a], [b]) => a.localeCompare(b))
                      .map(([language, languageTables]) => (
                        <SelectGroup key={language}>
                          <SelectLabel className="capitalize">{language}</SelectLabel>
                          {languageTables.map((table) => (
                            <SelectItem key={table.filename} value={table.filename}>
                              {table.display_name}
                              {table.grade && ` (${table.grade.toUpperCase()})`}
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            {/* Voice Selector */}
            <div className="space-y-2">
              <Label htmlFor="voice-select">Voice</Label>
              {voicesLoading ? (
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading voices...
                </div>
              ) : voices && voices.length > 0 ? (
                <Select value={selectedVoice} onValueChange={setSelectedVoice}>
                  <SelectTrigger id="voice-select" className="w-full">
                    <SelectValue placeholder="Select a voice" />
                  </SelectTrigger>
                  <SelectContent>
                    {voices.map((voice) => (
                      <SelectItem key={voice.voice_id} value={voice.voice_id}>
                        {voice.voice_id} ({voice.language}, {voice.quality})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-sm text-slate-500">No voices available</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Braille Input Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Volume2 className="w-5 h-5" />
            <CardTitle>Braille to Speech</CardTitle>
          </div>
          <CardDescription>
            Enter braille text below to convert it to speech
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="braille-input">Braille Input</Label>
            <Textarea
              id="braille-input"
              placeholder="Enter braille text (Unicode braille characters)..."
              value={brailleInput}
              onChange={(e) => setBrailleInput(e.target.value)}
              rows={4}
              className="resize-none font-mono text-lg"
            />
          </div>

          <Button
            onClick={handleSynthesize}
            disabled={!brailleInput.trim() || isSynthesizing}
            className="w-full"
            size="lg"
          >
            {isSynthesizing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Synthesizing...
              </>
            ) : (
              'Convert to Speech'
            )}
          </Button>

          {/* Error Display */}
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">
                <strong>Error:</strong> {error}
              </p>
            </div>
          )}

          {/* Result */}
          {audioUrl && (
            <div className="space-y-4 pt-4 border-t">
              {/* Audio Player */}
              <div className="space-y-2">
                <Label>Audio Output</Label>
                <audio
                  ref={audioRef}
                  src={audioUrl}
                  controls
                  className="w-full"
                />
              </div>

              {/* Back-translated text */}
              {backTranslatedText && (
                <div className="p-4 bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-blue-900 dark:text-blue-100">
                      Back-Translated Text:
                    </p>
                    <p className="text-sm text-blue-800 dark:text-blue-200 font-mono break-words">
                      "{backTranslatedText}"
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Presets */}
      <PresetSelector
        selected={selectedPreset}
        onChange={(preset, newSettings) => {
          setSelectedPreset(preset)
          if (newSettings && Object.keys(newSettings).length > 0) {
            setSettings(newSettings)
          }
        }}
      />

      {/* Speech Settings */}
      <BrailleToSpeechSettings
        settings={settings}
        onChange={(newSettings) => {
          setSettings(newSettings)
          setSelectedPreset(null) // Reset to Custom when manually changed
        }}
        showAdvanced={showAdvanced}
        onToggleAdvanced={() => setShowAdvanced(!showAdvanced)}
      />

      {/* Info Card */}
      <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <CardContent className="pt-6">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            <strong>Note:</strong> This system works completely offline using liblouis for braille
            back-translation and piper for neural text-to-speech synthesis. Enter Unicode braille
            characters from a braille keyboard or display to hear the spoken output.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
