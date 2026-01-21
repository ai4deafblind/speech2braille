import React, { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { useQuery } from '@tanstack/react-query'
import { listTablesApiTablesGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import type { BrailleTable } from '@/lib/client'
import { Mic, MicOff, Loader2, Vibrate, Wifi, WifiOff, AlertCircle, Globe, Clock } from 'lucide-react'
import { useSpeechToBrailleWebSocket } from '@/hooks/useSpeechToBrailleWebSocket'

type StatusType = 'idle' | 'listening' | 'processing' | 'success' | 'error'

// Language options for faster-whisper
const LANGUAGES = [
  { code: null, name: 'Auto-detect' },
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'it', name: 'Italian' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'nl', name: 'Dutch' },
  { code: 'pl', name: 'Polish' },
  { code: 'ru', name: 'Russian' },
  { code: 'ja', name: 'Japanese' },
  { code: 'zh', name: 'Chinese' },
  { code: 'ar', name: 'Arabic' },
  { code: 'hi', name: 'Hindi' },
  { code: 'ko', name: 'Korean' },
  { code: 'id', name: 'Indonesian' },
]

// Haptic feedback patterns based on SPEC.md Social Haptics design
const HapticPatterns = {
  listening: [100],
  processing: [50, 100, 150, 100, 50],
  success: [200, 100, 150],
  error: [150, 50, 100, 50, 50],
  heartbeat: [300],
  speechStart: [80, 40, 80],
} as const

const triggerHaptic = (pattern: readonly number[]) => {
  if ('vibrate' in navigator) {
    navigator.vibrate(pattern)
  }
}

export function SpeechToBraille() {
  // Load saved preferences
  const [selectedTable, setSelectedTable] = useState(() => {
    return localStorage.getItem('speech2braille_table') || 'en-ueb-g2.ctb'
  })
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(() => {
    const saved = localStorage.getItem('speech2braille_language')
    return saved === 'null' ? null : saved
  })
  const [hapticsEnabled, setHapticsEnabled] = useState(() => {
    const saved = localStorage.getItem('speech2braille_haptics')
    return saved !== null ? saved === 'true' : true
  })

  const mediaStreamRef = useRef<MediaStream | null>(null)
  const heartbeatIntervalRef = useRef<number | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // WebSocket connection
  const {
    connectionStatus,
    isReady,
    error: wsError,
    isRecording: wsIsRecording,
    isSpeaking,
    isProcessing,
    result,
    accumulatedResults,
    statusInfo,
    connect,
    disconnect,
    startRecording: wsStartRecording,
    stopRecording: wsStopRecording,
    sendAudioChunk,
    updateConfig,
  } = useSpeechToBrailleWebSocket()

  // Fetch available braille tables
  const { data: tables = [] } = useQuery(listTablesApiTablesGetOptions())

  // Persist preferences
  useEffect(() => {
    localStorage.setItem('speech2braille_table', selectedTable)
  }, [selectedTable])

  useEffect(() => {
    localStorage.setItem('speech2braille_language', selectedLanguage === null ? 'null' : selectedLanguage)
  }, [selectedLanguage])

  useEffect(() => {
    localStorage.setItem('speech2braille_haptics', String(hapticsEnabled))
  }, [hapticsEnabled])

  // Update WebSocket config
  useEffect(() => {
    if (isReady) {
      updateConfig({
        braille_table: selectedTable,
        language: selectedLanguage,
        task: 'transcribe',
      })
    }
  }, [selectedTable, selectedLanguage, isReady, updateConfig])

  // Determine status
  const status: StatusType = wsError
    ? 'error'
    : isProcessing
    ? 'processing'
    : result
    ? 'success'
    : wsIsRecording
    ? 'listening'
    : 'idle'

  // Haptic feedback
  useEffect(() => {
    if (!hapticsEnabled) return
    switch (status) {
      case 'listening':
        triggerHaptic(HapticPatterns.listening)
        break
      case 'processing':
        triggerHaptic(HapticPatterns.processing)
        break
      case 'success':
        triggerHaptic(HapticPatterns.success)
        break
      case 'error':
        triggerHaptic(HapticPatterns.error)
        break
    }
  }, [status, hapticsEnabled])

  useEffect(() => {
    if (hapticsEnabled && isSpeaking) {
      triggerHaptic(HapticPatterns.speechStart)
    }
  }, [isSpeaking, hapticsEnabled])

  // Heartbeat
  useEffect(() => {
    if (hapticsEnabled && status === 'idle' && isReady) {
      heartbeatIntervalRef.current = window.setInterval(() => {
        triggerHaptic(HapticPatterns.heartbeat)
      }, 5000)
    }
    return () => {
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current)
      }
    }
  }, [status, hapticsEnabled, isReady])

  // Audio visualization
  const drawWaveform = () => {
    if (!analyserRef.current || !canvasRef.current) return

    const analyser = analyserRef.current
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const bufferLength = analyser.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)
    analyser.getByteTimeDomainData(dataArray)

    ctx.fillStyle = 'rgb(243, 244, 246)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    ctx.lineWidth = 2
    ctx.strokeStyle = isSpeaking ? 'rgb(34, 197, 94)' : 'rgb(59, 130, 246)'
    ctx.beginPath()

    const sliceWidth = (canvas.width * 1.0) / bufferLength
    let x = 0

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0
      const y = (v * canvas.height) / 2

      if (i === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }

      x += sliceWidth
    }

    ctx.lineTo(canvas.width, canvas.height / 2)
    ctx.stroke()

    if (wsIsRecording) {
      animationFrameRef.current = requestAnimationFrame(drawWaveform)
    }
  }

  // Start recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })
      mediaStreamRef.current = stream

      const audioContext = new AudioContext({ sampleRate: 16000 })
      audioContextRef.current = audioContext

      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 2048
      analyserRef.current = analyser

      const processor = audioContext.createScriptProcessor(4096, 1, 1)

      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0)
        sendAudioChunk(new Float32Array(inputData))
      }

      source.connect(analyser)
      source.connect(processor)
      processor.connect(audioContext.destination)

      wsStartRecording()
      drawWaveform()
    } catch (error) {
      console.error('Error accessing microphone:', error)
    }
  }

  // Stop recording
  const stopRecording = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      mediaStreamRef.current = null
    }

    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    wsStopRecording()
  }

  // Group tables by language
  const groupedTables = (tables || []).reduce(
    (acc: Record<string, BrailleTable[]>, table: BrailleTable) => {
      const lang = table.language || 'unknown'
      if (!acc[lang]) acc[lang] = []
      acc[lang].push(table)
      return acc
    },
    {} as Record<string, BrailleTable[]>
  )

  // Get braille dot pattern from character
  const getBrailleDots = (char: string): number[] => {
    const codePoint = char.charCodeAt(0)
    if (codePoint < 0x2800 || codePoint > 0x28ff) return []

    const offset = codePoint - 0x2800
    const dots: number[] = []

    // Braille Unicode encoding uses bits 0-7 for dots 1-8
    if (offset & 0x01) dots.push(1)
    if (offset & 0x02) dots.push(2)
    if (offset & 0x04) dots.push(3)
    if (offset & 0x08) dots.push(4)
    if (offset & 0x10) dots.push(5)
    if (offset & 0x20) dots.push(6)
    if (offset & 0x40) dots.push(7)
    if (offset & 0x80) dots.push(8)

    return dots
  }

  // Render braille character component
  const BrailleChar = ({ char }: { char: string }) => {
    const activeDots = getBrailleDots(char)
    const isSpace = char === ' ' || char === '\u00A0'

    // Debug: log the character and its dots
    if (activeDots.length > 0) {
      console.log(`Char: "${char}" (U+${char.charCodeAt(0).toString(16).toUpperCase()}) -> Dots:`, activeDots)
    }

    if (isSpace) {
      return (
        <div className="inline-flex flex-col items-center gap-2 px-2">
          <div className="grid grid-cols-2 gap-x-2.5 gap-y-2">
            {[1, 2, 3].map((row) => (
              <React.Fragment key={row}>
                <div
                  className="w-3 h-3 rounded-full bg-slate-100 dark:bg-slate-800 opacity-20 border border-slate-300 dark:border-slate-600"
                  title={`Dot ${row} (space)`}
                />
                <div
                  className="w-3 h-3 rounded-full bg-slate-100 dark:bg-slate-800 opacity-20 border border-slate-300 dark:border-slate-600"
                  title={`Dot ${row + 3} (space)`}
                />
              </React.Fragment>
            ))}
          </div>
        </div>
      )
    }

    const isDotActive = (dotNumber: number) => activeDots.includes(dotNumber)

    return (
      <div className="inline-flex flex-col items-center gap-2 px-2">
        <div className="grid grid-cols-2 gap-x-2.5 gap-y-2">
          {/* Left column: dots 1, 2, 3 */}
          <div
            className={`w-3 h-3 rounded-full transition-all ${
              isDotActive(1)
                ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
                : 'bg-slate-200 dark:bg-slate-700 opacity-30'
            }`}
            title="Dot 1"
          />
          {/* Right column: dots 4, 5, 6 */}
          <div
            className={`w-3 h-3 rounded-full transition-all ${
              isDotActive(4)
                ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
                : 'bg-slate-200 dark:bg-slate-700 opacity-30'
            }`}
            title="Dot 4"
          />

          <div
            className={`w-3 h-3 rounded-full transition-all ${
              isDotActive(2)
                ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
                : 'bg-slate-200 dark:bg-slate-700 opacity-30'
            }`}
            title="Dot 2"
          />
          <div
            className={`w-3 h-3 rounded-full transition-all ${
              isDotActive(5)
                ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
                : 'bg-slate-200 dark:bg-slate-700 opacity-30'
            }`}
            title="Dot 5"
          />

          <div
            className={`w-3 h-3 rounded-full transition-all ${
              isDotActive(3)
                ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
                : 'bg-slate-200 dark:bg-slate-700 opacity-30'
            }`}
            title="Dot 3"
          />
          <div
            className={`w-3 h-3 rounded-full transition-all ${
              isDotActive(6)
                ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
                : 'bg-slate-200 dark:bg-slate-700 opacity-30'
            }`}
            title="Dot 6"
          />
        </div>
      </div>
    )
  }

  // Connection indicator
  const ConnectionIndicator = () => {
    const statusConfig = {
      disconnected: { icon: WifiOff, color: 'text-gray-400', text: 'Disconnected' },
      connecting: { icon: Loader2, color: 'text-yellow-500', text: 'Connecting...' },
      connected: { icon: Wifi, color: 'text-blue-500', text: 'Connected' },
      ready: { icon: Wifi, color: 'text-green-500', text: 'Ready' },
      error: { icon: AlertCircle, color: 'text-red-500', text: 'Error' },
    }

    const config = statusConfig[connectionStatus]
    const Icon = config.icon

    return (
      <div className="flex items-center gap-2">
        <Icon
          className={`h-4 w-4 ${config.color} ${connectionStatus === 'connecting' ? 'animate-spin' : ''}`}
        />
        <span className="text-sm font-medium">{config.text}</span>
      </div>
    )
  }

  // Status indicator
  const StatusIndicator = () => {
    const statusConfig = {
      idle: { color: 'bg-gray-400', text: 'Ready to record', pulse: false },
      listening: {
        color: isSpeaking ? 'bg-green-500' : 'bg-red-500',
        text: isSpeaking ? 'Speaking...' : 'Listening...',
        pulse: true,
      },
      processing: { color: 'bg-yellow-500', text: 'Processing...', pulse: true },
      success: { color: 'bg-green-500', text: 'Complete', pulse: false },
      error: { color: 'bg-red-600', text: 'Error', pulse: false },
    }

    const config = statusConfig[status]

    return (
      <div className="flex items-center gap-2 mb-4">
        <div
          className={`w-3 h-3 rounded-full ${config.color} ${config.pulse ? 'animate-pulse' : ''}`}
        />
        <span className="text-sm font-medium">{config.text}</span>
        {statusInfo && (
          <span className="text-xs text-gray-500 ml-2">
            ({statusInfo.duration_seconds.toFixed(1)}s)
          </span>
        )}
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle>Speech-to-Braille Converter</CardTitle>
              <CardDescription>
                Real-time speech-to-braille translation with automatic voice detection
              </CardDescription>
            </div>
            <Button
              variant={hapticsEnabled ? 'default' : 'outline'}
              size="sm"
              onClick={() => setHapticsEnabled(!hapticsEnabled)}
              className="flex items-center gap-2"
            >
              <Vibrate className="h-4 w-4" />
              {hapticsEnabled ? 'Haptics On' : 'Haptics Off'}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Connection Status */}
          <div className="flex items-center justify-between">
            <ConnectionIndicator />
            {connectionStatus === 'disconnected' && (
              <Button size="sm" onClick={connect}>
                Connect
              </Button>
            )}
            {(connectionStatus === 'connected' || connectionStatus === 'ready') && (
              <Button size="sm" variant="outline" onClick={disconnect}>
                Disconnect
              </Button>
            )}
          </div>

          {/* Status */}
          <StatusIndicator />

          {/* Configuration */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="language" className="flex items-center gap-2">
                <Globe className="h-4 w-4" />
                Speech Language
              </Label>
              <Select
                value={selectedLanguage === null ? 'auto' : selectedLanguage}
                onValueChange={(val) => setSelectedLanguage(val === 'auto' ? null : val)}
                disabled={!isReady}
              >
                <SelectTrigger id="language">
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  {LANGUAGES.map((lang) => (
                    <SelectItem key={lang.code || 'auto'} value={lang.code || 'auto'}>
                      {lang.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="table">Braille Table</Label>
              <Select value={selectedTable} onValueChange={setSelectedTable} disabled={!isReady}>
                <SelectTrigger id="table">
                  <SelectValue placeholder="Select a braille table" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(groupedTables).map(([lang, langTables]) => (
                    <div key={lang}>
                      <div className="px-2 py-1.5 text-sm font-semibold text-gray-500">
                        {lang.toUpperCase()}
                      </div>
                      {(langTables as BrailleTable[]).map((table: BrailleTable) => (
                        <SelectItem key={table.filename} value={table.filename}>
                          {table.display_name}
                        </SelectItem>
                      ))}
                    </div>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Separator />

          {/* Audio Visualization */}
          {wsIsRecording && (
            <div className="space-y-2">
              <Label>Audio Input</Label>
              <canvas
                ref={canvasRef}
                width={800}
                height={100}
                className="w-full h-24 bg-gray-50 rounded-lg border"
              />
            </div>
          )}

          {/* Recording Controls */}
          <div className="flex flex-col items-center gap-4">
            <Button
              size="lg"
              variant={wsIsRecording ? 'destructive' : 'default'}
              onClick={wsIsRecording ? stopRecording : startRecording}
              disabled={!isReady || isProcessing}
              className="w-32 h-32 rounded-full"
            >
              {isProcessing ? (
                <Loader2 className="h-12 w-12 animate-spin" />
              ) : wsIsRecording ? (
                <MicOff className="h-12 w-12" />
              ) : (
                <Mic className="h-12 w-12" />
              )}
            </Button>
            <p className="text-sm text-gray-600 text-center max-w-md">
              {!isReady
                ? 'Connect to server to start'
                : wsIsRecording
                ? 'Speak naturally, pauses will be detected automatically'
                : 'Click to start recording'}
            </p>
          </div>

          {/* Real-time Results */}
          {accumulatedResults.length > 0 && (
            <>
              <Separator />
              <div className="space-y-4">
                {/* Latest Language Detection */}
                {accumulatedResults[accumulatedResults.length - 1]?.language && (
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="flex items-center gap-1">
                      <Globe className="h-3 w-3" />
                      Detected: {LANGUAGES.find(l => l.code === accumulatedResults[accumulatedResults.length - 1].language)?.name || accumulatedResults[accumulatedResults.length - 1].language}
                    </Badge>
                    <Badge variant="outline" className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {accumulatedResults.length} {accumulatedResults.length === 1 ? 'segment' : 'segments'}
                    </Badge>
                  </div>
                )}

                {/* Real-time Transcribed Text */}
                <div>
                  <h3 className="text-lg font-semibold mb-2">
                    Transcribed Text {wsIsRecording && <span className="text-sm text-gray-500">(Live)</span>}
                  </h3>
                  <div className="space-y-2">
                    {[...accumulatedResults].reverse().map((resultItem, resultIdx) => {
                      const originalIdx = accumulatedResults.length - 1 - resultIdx;
                      return (
                      <div key={originalIdx} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-blue-500">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline" className="text-xs">
                            Segment {originalIdx + 1}
                          </Badge>
                          {resultItem.audio_duration && (
                            <span className="text-xs text-gray-500">
                              {resultItem.audio_duration.toFixed(2)}s
                            </span>
                          )}
                        </div>
                        <p className="text-gray-800 dark:text-gray-200 font-medium mb-2">
                          {resultItem.transcribed_text}
                        </p>

                        {/* Braille output for this segment */}
                        <div className="mt-2 p-2 bg-white dark:bg-gray-900 rounded border space-y-2">
                          {/* Debug: Show raw braille unicode */}
                          <div className="text-xs text-gray-500 font-mono break-all">
                            Raw: {resultItem.braille || '(empty)'}
                          </div>

                          {resultItem.braille && resultItem.braille.length > 0 ? (
                            <div className="flex flex-wrap gap-x-3 gap-y-4 leading-loose">
                              {resultItem.braille.split('').slice(0, 50).map((char, charIdx) => (
                                <BrailleChar key={`${originalIdx}-${charIdx}`} char={char} />
                              ))}
                              {resultItem.braille.length > 50 && (
                                <span className="text-xs text-gray-400 self-center ml-2">
                                  +{resultItem.braille.length - 50} more
                                </span>
                              )}
                            </div>
                          ) : (
                            <p className="text-xs text-gray-400">No braille output</p>
                          )}
                        </div>

                        {/* Word-level timestamps if available */}
                        {resultItem.segments && resultItem.segments.length > 0 && (
                          <div className="mt-2 space-y-2">
                            {resultItem.segments.map((segment) => (
                              segment.words && segment.words.length > 0 && (
                                <div key={segment.id} className="flex flex-wrap gap-1">
                                  {segment.words.map((word, idx) => (
                                    <span
                                      key={idx}
                                      className="inline-flex items-center gap-1 px-2 py-1 bg-white dark:bg-gray-700 rounded text-xs"
                                      title={`${word.start.toFixed(2)}s - ${word.end.toFixed(2)}s`}
                                    >
                                      {word.word}
                                      <span className="text-xs text-gray-400">
                                        {(word.probability * 100).toFixed(0)}%
                                      </span>
                                    </span>
                                  ))}
                                </div>
                              )
                            ))}
                          </div>
                        )}
                      </div>
                    )})}
                  </div>
                </div>

                {/* Combined Braille Output */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="braille-output">Complete Braille Output</Label>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const combinedBraille = accumulatedResults.map(r => r.braille).join(' ')
                        navigator.clipboard.writeText(combinedBraille)
                      }}
                    >
                      Copy All Unicode
                    </Button>
                  </div>
                  <div
                    id="braille-output"
                    className="p-6 bg-white dark:bg-slate-950 border-2 border-slate-300 dark:border-slate-600 rounded-lg shadow-inner overflow-x-auto max-h-96 overflow-y-auto"
                  >
                    <div className="flex flex-wrap gap-x-3 gap-y-4 leading-loose">
                      {accumulatedResults.map((resultItem, idx) => (
                        <div key={idx} className="inline-flex flex-wrap gap-x-3 gap-y-4">
                          {resultItem.braille.split('').map((char, charIdx) => (
                            <BrailleChar key={`full-${idx}-${charIdx}`} char={char} />
                          ))}
                          {idx < accumulatedResults.length - 1 && (
                            <div className="w-8" key={`space-${idx}`} />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full" />
                      <span>Active dots shown in blue, inactive dots faded</span>
                    </div>
                    <span className="text-slate-400">Unicode Braille (U+2800–U+28FF)</span>
                  </div>
                </div>

                {/* Metadata */}
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="space-y-1">
                    <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">Table Used</p>
                    <p className="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                      {accumulatedResults[accumulatedResults.length - 1]?.table_used}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">Total Characters</p>
                    <p className="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                      {accumulatedResults.reduce((sum, r) => sum + r.braille.length, 0)}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">Total Segments</p>
                    <p className="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                      {accumulatedResults.length}
                    </p>
                  </div>
                </div>

                {/* Combined Original Text */}
                <div className="p-4 bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-blue-900 dark:text-blue-100">
                      Complete Transcription:
                    </p>
                    <p className="text-sm text-blue-800 dark:text-blue-200 font-mono break-words">
                      "{accumulatedResults.map(r => r.transcribed_text).join(' ')}"
                    </p>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Error Display */}
          {wsError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800">{wsError}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
