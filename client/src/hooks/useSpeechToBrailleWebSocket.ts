import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Message types from the server
 */
export type ServerMessageType =
  | 'ready'
  | 'config_updated'
  | 'recording_started'
  | 'recording_stopped'
  | 'speech_started'
  | 'speech_ended'
  | 'vad_status'
  | 'status'
  | 'processing'
  | 'result'
  | 'error';

export interface RecordingStartedMessage {
  type: 'recording_started';
  message?: string;
}

export interface RecordingStoppedMessage {
  type: 'recording_stopped';
  message?: string;
}

/**
 * Server message structures
 */
export interface ReadyMessage {
  type: 'ready';
  message: string;
  model: string;
}

export interface ConfigUpdatedMessage {
  type: 'config_updated';
  config: {
    language?: string;
    task?: string;
    braille_table?: string;
  };
}

export interface SpeechStartedMessage {
  type: 'speech_started';
  message: string;
}

export interface SpeechEndedMessage {
  type: 'speech_ended';
  message: string;
}

export interface VADStatusMessage {
  type: 'vad_status';
  enabled: boolean;
  is_speech_active: boolean;
  probability: number;
}

export interface SpeechEndedMessageVAD {
  type: 'speech_ended';
  duration: number;
}

export interface StatusMessage {
  type: 'status';
  recording: boolean;
  buffer_size: number;
  duration_seconds: number;
}

export interface ProcessingMessage {
  type: 'processing';
  message: string;
}

export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
  probability: number;
}

export interface SegmentTimestamp {
  id: number;
  start: number;
  end: number;
  text: string;
  words?: WordTimestamp[];
  avg_logprob: number;
  no_speech_prob: number;
}

export interface ResultMessage {
  type: 'result';
  transcribed_text: string;
  braille: string;
  language?: string;
  table_used: string;
  audio_duration?: number;
  segments?: SegmentTimestamp[];
  success: boolean;
}

export interface ErrorMessage {
  type: 'error';
  message: string;
  success?: boolean;
}

export type ServerMessage =
  | ReadyMessage
  | ConfigUpdatedMessage
  | RecordingStartedMessage
  | RecordingStoppedMessage
  | SpeechStartedMessage
  | SpeechEndedMessage
  | VADStatusMessage
  | StatusMessage
  | ProcessingMessage
  | ResultMessage
  | ErrorMessage;

/**
 * WebSocket connection status
 */
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'ready' | 'error';

/**
 * Configuration for the WebSocket connection
 */
export interface WebSocketConfig {
  braille_table?: string;
  language?: string;
  task?: string;
}

/**
 * Hook return type
 */
export interface UseSpeechToBrailleWebSocketReturn {
  // Connection state
  connectionStatus: ConnectionStatus;
  isReady: boolean;
  error: string | null;

  // Recording state
  isRecording: boolean;
  isSpeaking: boolean;
  isProcessing: boolean;

  // Results
  result: ResultMessage | null;
  accumulatedResults: ResultMessage[];
  statusInfo: StatusMessage | null;

  // Actions
  connect: () => void;
  disconnect: () => void;
  startRecording: () => void;
  stopRecording: () => void;
  sendAudioChunk: (audioData: Float32Array) => void;
  updateConfig: (config: WebSocketConfig) => void;
}

/**
 * Custom hook for WebSocket-based speech-to-braille translation
 *
 * Features:
 * - Automatic reconnection
 * - Audio chunk streaming
 * - Voice activity detection feedback
 * - Real-time transcription and braille translation
 *
 * @param url WebSocket URL (default: ws://127.0.0.1:8000/ws/speech-to-braille)
 * @param autoConnect Whether to connect automatically on mount (default: true)
 */
export function useSpeechToBrailleWebSocket(
  url: string = 'ws://127.0.0.1:8000/ws/speech-to-braille',
  autoConnect: boolean = true
): UseSpeechToBrailleWebSocketReturn {
  // WebSocket reference
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);

  // Connection state
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [error, setError] = useState<string | null>(null);

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Results
  const [result, setResult] = useState<ResultMessage | null>(null);
  const [accumulatedResults, setAccumulatedResults] = useState<ResultMessage[]>([]);
  const [statusInfo, setStatusInfo] = useState<StatusMessage | null>(null);

  const isReady = connectionStatus === 'ready';

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: ServerMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'ready':
          setConnectionStatus('ready');
          setError(null);
          reconnectAttemptsRef.current = 0;
          console.log('WebSocket ready:', message.message);
          break;

        case 'config_updated':
          console.log('Config updated:', message.config);
          break;

        case 'recording_started':
          setIsRecording(true);
          setError(null);
          // Clear accumulated results when starting new recording
          setAccumulatedResults([]);
          setResult(null);
          break;

        case 'recording_stopped':
          setIsRecording(false);
          setIsSpeaking(false);
          break;

        case 'speech_started':
          setIsSpeaking(true);
          break;

        case 'speech_ended':
          setIsSpeaking(false);
          break;

        case 'status':
          setStatusInfo(message);
          break;

        case 'processing':
          setIsProcessing(true);
          break;

        case 'result':
          setResult(message);
          // Accumulate results for real-time display
          setAccumulatedResults((prev) => [...prev, message]);
          setIsProcessing(false);
          break;

        case 'error':
          setError(message.message);
          setIsProcessing(false);
          console.error('WebSocket error:', message.message);
          break;
      }
    } catch (err) {
      console.error('Failed to parse WebSocket message:', err);
    }
  }, []);

  /**
   * Handle WebSocket errors
   */
  const handleError = useCallback((event: Event) => {
    console.error('WebSocket error:', event);
    setError('Connection error occurred');
    setConnectionStatus('error');
  }, []);

  /**
   * Handle WebSocket close
   */
  const handleClose = useCallback(() => {
    console.log('WebSocket closed');
    setConnectionStatus('disconnected');
    setIsRecording(false);
    setIsSpeaking(false);
    setIsProcessing(false);

    // Attempt to reconnect with exponential backoff
    if (reconnectAttemptsRef.current < 5) {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
      console.log(`Reconnecting in ${delay}ms...`);

      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttemptsRef.current += 1;
        connect();
      }, delay);
    } else {
      setError('Failed to reconnect after multiple attempts');
    }
  }, []);

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      setConnectionStatus('connecting');
      setError(null);

      const ws = new WebSocket(url);
      ws.binaryType = 'arraybuffer';

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
      };

      ws.onmessage = handleMessage;
      ws.onerror = handleError;
      ws.onclose = handleClose;

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to connect:', err);
      setError('Failed to establish connection');
      setConnectionStatus('error');
    }
  }, [url, handleMessage, handleError, handleClose]);

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnectionStatus('disconnected');
    setIsRecording(false);
    setIsSpeaking(false);
    setIsProcessing(false);
  }, []);

  /**
   * Start recording session
   */
  const startRecording = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Not connected to server');
      return;
    }

    setResult(null);
    setStatusInfo(null);

    wsRef.current.send(
      JSON.stringify({
        type: 'start_recording',
      })
    );
  }, []);

  /**
   * Stop recording session
   */
  const stopRecording = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    wsRef.current.send(
      JSON.stringify({
        type: 'stop_recording',
      })
    );
  }, []);

  /**
   * Send audio chunk to server
   */
  const sendAudioChunk = useCallback((audioData: Float32Array) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    // Send as binary data
    wsRef.current.send(audioData.buffer);
  }, []);

  /**
   * Update configuration
   */
  const updateConfig = useCallback((config: WebSocketConfig) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Not connected to server');
      return;
    }

    wsRef.current.send(
      JSON.stringify({
        type: 'config',
        config,
      })
    );
  }, []);

  /**
   * Auto-connect on mount if enabled
   */
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect]); // Only run on mount/unmount

  return {
    // Connection state
    connectionStatus,
    isReady,
    error,

    // Recording state
    isRecording,
    isSpeaking,
    isProcessing,

    // Results
    result,
    accumulatedResults,
    statusInfo,

    // Actions
    connect,
    disconnect,
    startRecording,
    stopRecording,
    sendAudioChunk,
    updateConfig,
  };
}
