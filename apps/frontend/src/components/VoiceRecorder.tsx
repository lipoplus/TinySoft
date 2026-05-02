import React, { useRef, useState } from 'react'

interface VoiceRecorderProps {
  onRecordingComplete: (blob: Blob, filename: string) => void
  disabled?: boolean
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onRecordingComplete, disabled }) => {
  const [isRecording, setIsRecording] = useState(false)
  const [duration, setDuration] = useState(0)
  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const audioChunks = useRef<Blob[]>([])
  const durationInterval = useRef<ReturnType<typeof setInterval> | null>(null)

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorder.current = new MediaRecorder(stream)
      audioChunks.current = []

      mediaRecorder.current.ondataavailable = (event) => {
        audioChunks.current.push(event.data)
      }

      mediaRecorder.current.onstop = () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' })
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
        onRecordingComplete(audioBlob, `memo-${timestamp}.webm`)

        stream.getTracks().forEach((track) => track.stop())
      }

      mediaRecorder.current.start()
      setIsRecording(true)
      setDuration(0)

      durationInterval.current = setInterval(() => {
        setDuration((prev) => prev + 1)
      }, 1000)
    } catch (error) {
      console.error('Error accessing microphone:', error)
      alert('Error accessing microphone. Please check permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop()
      setIsRecording(false)

      if (durationInterval.current) {
        clearInterval(durationInterval.current)
      }
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg border-2 border-purple-200">
      <div className="mb-4">
        <p className="text-lg font-semibold text-gray-900 text-center">
          {isRecording ? 'Recording...' : 'Ready to record'}
        </p>
        {isRecording && (
          <p className="text-3xl font-mono font-bold text-purple-600 text-center mt-2">
            {formatDuration(duration)}
          </p>
        )}
      </div>

      <div className="flex gap-4">
        {!isRecording ? (
          <button
            onClick={startRecording}
            disabled={disabled}
            className="flex items-center gap-2 px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            <span className="text-xl">🎤</span>
            Start Recording
          </button>
        ) : (
          <>
            <button
              onClick={stopRecording}
              className="flex items-center gap-2 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              <span className="text-xl">⏹️</span>
              Stop Recording
            </button>
            <div className="flex items-center gap-2 px-4 py-3 bg-white rounded-lg border border-gray-300">
              <span className="inline-block w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
              <span className="text-sm text-gray-600">Recording</span>
            </div>
          </>
        )}
      </div>

      <p className="text-sm text-gray-600 mt-4 text-center">
        Speak clearly into your microphone to create your voice resume.
      </p>
    </div>
  )
}
