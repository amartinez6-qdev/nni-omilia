import { useRef, useState } from 'react'
import './App.css'

type Result = {
  transcript: string
  interpretation: string
  valid_greek_phone: boolean
}

type ViewState = 'idle' | 'recording' | 'processing' | 'result' | 'error'

const API_URL = '/api/interpret'

function getSupportedMimeType(): string | undefined {
  const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4']
  return candidates.find((type) => MediaRecorder.isTypeSupported(type))
}

function App() {
  const [viewState, setViewState] = useState<ViewState>('idle')
  const [result, setResult] = useState<Result | null>(null)
  const [error, setError] = useState<string | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const stopStream = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
  }

  const submitRecording = async (blob: Blob) => {
    if (blob.size === 0) {
      setViewState('error')
      setError('The recording was empty. Please try again.')
      return
    }

    setViewState('processing')
    const formData = new FormData()
    formData.append('audio', blob, 'recording.webm')

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        body: formData,
      })
      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail ?? 'The audio could not be processed.')
      }

      setResult(payload as Result)
      setViewState('result')
    } catch (requestError) {
      setViewState('error')
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'The audio could not be processed.',
      )
    }
  }

  const startRecording = async () => {
    setError(null)
    setResult(null)

    if (!navigator.mediaDevices?.getUserMedia || !('MediaRecorder' in window)) {
      setViewState('error')
      setError('This browser does not support microphone recording.')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = getSupportedMimeType()
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream)

      chunksRef.current = []
      streamRef.current = stream
      recorderRef.current = recorder
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data)
      }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || 'audio/webm',
        })
        recorderRef.current = null
        stopStream()
        void submitRecording(blob)
      }
      recorder.onerror = () => {
        recorderRef.current = null
        stopStream()
        setViewState('error')
        setError('Recording failed. Please try again.')
      }
      recorder.start()
      setViewState('recording')
    } catch {
      stopStream()
      setViewState('error')
      setError('Microphone permission was denied or unavailable.')
    }
  }

  const stopRecording = () => {
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop()
  }

  const handleRecordButton = () => {
    if (viewState === 'recording') stopRecording()
    else if (viewState === 'idle' || viewState === 'result' || viewState === 'error') {
      void startRecording()
    }
  }

  const isBusy = viewState === 'processing'
  const buttonLabel = viewState === 'recording' ? 'Stop recording' : 'Start recording'

  return (
    <main className="app-shell">
      <section className="card" aria-live="polite">
        <p className="eyebrow">Natural Number Interpretation</p>
        <h1>Speak a phone number</h1>
        <p className="intro">
          Record a number in English or Spanish and receive the most direct interpretation.
        </p>

        <button
          className={`record-button ${viewState === 'recording' ? 'recording' : ''}`}
          type="button"
          onClick={handleRecordButton}
          disabled={isBusy}
        >
          <span className="record-dot" aria-hidden="true" />
          {isBusy ? 'Processing...' : buttonLabel}
        </button>

        {viewState === 'recording' && (
          <p className="status recording-status">Listening. Press the button to stop.</p>
        )}
        {isBusy && <p className="status">Transcribing audio...</p>}

        {error && (
          <div className="message error-message" role="alert">
            {error}
          </div>
        )}

        {result && viewState === 'result' && (
          <div className="result-panel">
            <div className="result-row">
              <span className="result-label">Transcript</span>
              <p>{result.transcript}</p>
            </div>
            <div className="result-row">
              <span className="result-label">Interpretation</span>
              <p className="number-result">{result.interpretation}</p>
            </div>
            <div className="validity-row">
              <span>Greek phone number</span>
              <strong className={result.valid_greek_phone ? 'valid' : 'invalid'}>
                {result.valid_greek_phone ? 'VALID' : 'INVALID'}
              </strong>
            </div>
          </div>
        )}

        <p className="hint">The recording is processed locally by the application backend.</p>
      </section>
    </main>
  )
}

export default App
