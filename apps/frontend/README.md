# Voice Resume Frontend

A React 19 + Vite + Tailwind CSS frontend for the Voice Resume application. Provides signup/login, voice memo recording, transcription viewing, and resume editing.

## Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool and dev server
- **Tailwind CSS v4** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Axios** - HTTP client for API communication

## Features

### Authentication
- Signup with email/password
- Login functionality
- Session persistence via localStorage
- Protected routes

### Voice Recording
- Record audio directly from browser microphone
- Real-time duration display
- Automatic file naming with timestamps
- Audio upload to backend

### Resume Management
- View generated resume from voice transcription
- Edit resume text
- Download resume as PDF
- View transcription status and history
- Memo list sidebar with filtering

## Development

```bash
# Install dependencies
npm install

# Start dev server (runs on http://localhost:5173)
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

## Environment

Create `.env.local` (or use the provided `.env.example`):

```env
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── api/              # API client and service functions
│   ├── client.ts     # Axios instance with auth interceptors
│   ├── auth.ts       # Authentication endpoints
│   └── memos.ts      # Voice memo and resume endpoints
├── components/       # React components
│   ├── Login.tsx
│   ├── Signup.tsx
│   ├── Dashboard.tsx # Main app interface
│   ├── VoiceRecorder.tsx
│   ├── ResumeEditor.tsx
│   └── ProtectedRoute.tsx
├── context/          # React context for state management
│   ├── auth.ts       # Auth context definition
│   └── AuthContextProvider.tsx
├── hooks/            # Custom React hooks
│   └── useAuth.ts    # Auth hook
└── App.tsx           # Main app with routing
```

## API Integration

The frontend communicates with the FastAPI backend at the configured `VITE_API_URL`. Key endpoints:

- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /memos/upload` - Upload voice memo
- `GET /memos` - List user's memos
- `GET /memos/{id}` - Get memo details with transcription/resume
- `GET /memos/{id}/resume/download` - Download resume PDF

## Notes

- Audio is recorded in WebM format using the Web Audio API
- Session tokens are stored in localStorage
- All API requests include the session token in the Authorization header
- The app redirects unauthenticated users to `/login`
- Responsive design works on desktop, tablet, and mobile
