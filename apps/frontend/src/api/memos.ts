import client from './client'

export interface MemoUploadResponse {
  id: string
  file_name: string
  status: string
  created_at: string
}

export interface TranscriptionResponse {
  id: string
  memo_id: string
  text: string
  language: string | null
  created_at: string
}

export interface ResumeResponse {
  id: string
  memo_id: string
  resume_text: string
  created_at: string
}

export interface MemoDetailResponse {
  id: string
  file_name: string
  status: string
  created_at: string
  transcription: TranscriptionResponse | null
  resume: ResumeResponse | null
}

export const memos = {
  uploadMemo: async (file: File): Promise<MemoUploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await client.post('/memos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  getMemo: async (memoId: string): Promise<MemoDetailResponse> => {
    const response = await client.get(`/memos/${memoId}`)
    return response.data
  },

  listMemos: async (): Promise<MemoDetailResponse[]> => {
    const response = await client.get('/memos')
    return response.data
  },

  downloadResume: async (memoId: string): Promise<Blob> => {
    const response = await client.get(`/memos/${memoId}/resume/download`, {
      responseType: 'blob',
    })
    return response.data
  },
}
