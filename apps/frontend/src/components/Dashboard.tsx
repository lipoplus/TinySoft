import React, { useEffect, useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { memos } from '../api/memos'
import { VoiceRecorder } from './VoiceRecorder'
import { ResumeEditor } from './ResumeEditor'
import type { MemoDetailResponse } from '../api/memos'

interface UploadingMemo {
  name: string
  progress: number
}

export const Dashboard: React.FC = () => {
  const [memoList, setMemoList] = useState<MemoDetailResponse[]>([])
  const [selectedMemo, setSelectedMemo] = useState<MemoDetailResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadingMemo, setUploadingMemo] = useState<UploadingMemo | null>(null)
  const [isDownloading, setIsDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { logout, email } = useAuth()
  const navigate = useNavigate()

  const fetchMemos = useCallback(async () => {
    try {
      setIsLoading(true)
      const data = await memos.listMemos()
      setMemoList(data)
      if (data.length > 0) {
        setSelectedMemo(data[0])
      }
    } catch (err) {
      setError('Failed to load memos')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchMemos()
  }, [fetchMemos])

  const handleRecordingComplete = async (blob: Blob, filename: string) => {
    try {
      setIsUploading(true)
      setUploadingMemo({ name: filename, progress: 0 })

      const file = new File([blob], filename, { type: blob.type })
      const response = await memos.uploadMemo(file)
      setUploadingMemo(null)

      const newMemo: MemoDetailResponse = {
        id: response.id,
        file_name: response.file_name,
        status: response.status,
        created_at: response.created_at,
        transcription: null,
        resume: null,
      }

      setMemoList((prev) => [newMemo, ...prev])
      setSelectedMemo(newMemo)
      setError(null)

      setTimeout(() => fetchMemos(), 2000)
    } catch (err) {
      setError('Failed to upload memo')
      console.error(err)
      setUploadingMemo(null)
    } finally {
      setIsUploading(false)
    }
  }

  const handleDownloadResume = async () => {
    if (!selectedMemo) return

    try {
      setIsDownloading(true)
      const blob = await memos.downloadResume(selectedMemo.id)

      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `resume-${selectedMemo.id}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('Failed to download resume')
      console.error(err)
    } finally {
      setIsDownloading(false)
    }
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Voice Resume</h1>
          <div className="flex items-center gap-6">
            <span className="text-gray-700">{email}</span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <div className="text-sm font-medium text-red-800">{error}</div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-4">Record New Memo</h2>
              <VoiceRecorder
                onRecordingComplete={handleRecordingComplete}
                disabled={isUploading}
              />
              {uploadingMemo && (
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-800">Uploading: {uploadingMemo.name}</p>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${uploadingMemo.progress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            {selectedMemo && (
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-4">Resume</h2>
                <ResumeEditor
                  initialText={selectedMemo.resume?.resume_text || ''}
                  onSave={() => {}}
                  onDownload={handleDownloadResume}
                  isDownloading={isDownloading}
                />
              </div>
            )}
          </div>

          <div className="lg:col-span-1">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Your Memos</h2>
            {isLoading ? (
              <div className="text-center py-8">
                <p className="text-gray-600">Loading memos...</p>
              </div>
            ) : (
              <div className="space-y-2">
                {memoList.length === 0 ? (
                  <p className="text-gray-600 text-center py-8">No memos yet</p>
                ) : (
                  memoList.map((memo) => (
                    <button
                      key={memo.id}
                      onClick={() => setSelectedMemo(memo)}
                      className={`w-full text-left p-3 rounded-lg border-2 transition-colors ${
                        selectedMemo?.id === memo.id
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 bg-white hover:border-purple-300'
                      }`}
                    >
                      <p className="font-medium text-gray-900 truncate">{memo.file_name}</p>
                      <p className="text-sm text-gray-600">
                        {new Date(memo.created_at).toLocaleDateString()}
                      </p>
                      <div className="mt-2 flex gap-2">
                        {memo.transcription && (
                          <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            Transcribed
                          </span>
                        )}
                        {memo.resume && (
                          <span className="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                            Resume
                          </span>
                        )}
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
