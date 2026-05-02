import React, { useState } from 'react'

interface ResumeEditorProps {
  initialText: string
  onSave: (text: string) => void
  onDownload: () => void
  isSaving?: boolean
  isDownloading?: boolean
}

export const ResumeEditor: React.FC<ResumeEditorProps> = ({
  initialText,
  onSave,
  onDownload,
  isSaving,
  isDownloading,
}) => {
  const [text, setText] = useState(initialText)
  const [isEditing, setIsEditing] = useState(false)

  const handleSave = () => {
    onSave(text)
    setIsEditing(false)
  }

  const handleDownload = () => {
    onDownload()
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-4">
          <h2 className="text-2xl font-bold text-white">Your Resume</h2>
        </div>

        <div className="p-6">
          {isEditing ? (
            <div className="space-y-4">
              <div>
                <label htmlFor="resume-text" className="block text-sm font-medium text-gray-700 mb-2">
                  Edit Resume
                </label>
                <textarea
                  id="resume-text"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  rows={16}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono text-sm"
                  placeholder="Edit your resume here..."
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  onClick={() => {
                    setText(initialText)
                    setIsEditing(false)
                  }}
                  className="px-6 py-2 bg-gray-300 text-gray-900 rounded-lg hover:bg-gray-400 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 min-h-[400px]">
                <div className="whitespace-pre-wrap font-mono text-sm text-gray-800">
                  {text || <span className="text-gray-400">No resume generated yet</span>}
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setIsEditing(true)}
                  disabled={!text}
                  className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  Edit Resume
                </button>
                <button
                  onClick={handleDownload}
                  disabled={!text || isDownloading}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {isDownloading ? 'Downloading...' : 'Download PDF'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
