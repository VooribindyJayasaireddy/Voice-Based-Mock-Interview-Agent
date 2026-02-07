# Voice Mock Interview Agent

An AI-powered voice interview platform that conducts realistic mock interviews with real-time speech recognition, intelligent evaluation, and text-to-speech feedback.

## 🎯 Features

- **Voice-Based Interviews**: Conduct interviews using natural voice interaction
- **Real-Time Transcription**: Automatic speech-to-text conversion using OpenAI Whisper
- **AI-Powered Evaluation**: Get instant feedback on relevance, clarity, and correctness
- **Text-to-Speech**: Questions are read aloud using Microsoft Edge TTS or ElevenLabs
- **Role-Specific Questions**: Customize interviews for different job roles
- **Interview Summary**: Comprehensive feedback with strengths and improvement areas

## 🏗️ Architecture

```
Microsoft/
├── backend/          # FastAPI backend server
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── core/     # Core configuration
│   │   ├── models/   # Database models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   └── utils/    # Utility functions
│   └── audio/        # Generated audio files
└── frontend/         # React frontend application
    └── src/
        ├── components/
        └── App.tsx   # Main application
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** and **Yarn** (for frontend)
- **PostgreSQL** (for database)
- **FFmpeg** (for audio processing)
- **OpenAI API Key** (for LLM and Whisper)

### Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # macOS/Linux
   ```
66
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:

   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/interview_db
   OPENAI_API_KEY=your_openai_api_key_here
   TTS_PROVIDER=edge  # or 'elevenlabs'
   ```

5. Start the backend server:

   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   yarn install
   ```

3. Configure environment variables:

   ```bash
   # Create .env file
   echo REACT_APP_BACKEND_URL=http://localhost:8000 > .env
   ```

4. Start the development server:

   ```bash
   yarn start
   ```

   The application will open at `http://localhost:3000`

## 📖 Usage

1. **Start Interview**: Enter a job role (e.g., "Software Engineer") and click "Start Interview"
2. **Answer Questions**: Click "Answer" to start recording your response
3. **Get Feedback**: Receive instant evaluation with scores and detailed feedback
4. **Continue**: Click "Next Question" to proceed or "End Interview" for a summary
5. **Review Summary**: View overall performance, strengths, and areas for improvement

## 🛠️ Tech Stack

### Backend

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **OpenAI** - GPT for question generation and evaluation
- **Whisper** - Speech-to-text transcription
- **Edge TTS / ElevenLabs** - Text-to-speech synthesis
- **PostgreSQL** - Database

### Frontend

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Axios** - HTTP client
- **Radix UI** - Accessible component primitives
- **Tailwind CSS** - Styling
- **React Hook Form** - Form management

## 🔧 Configuration

### TTS Provider Options

The application supports two TTS providers:

- **Edge TTS** (Default): Free Microsoft Edge TTS, no API key required
- **ElevenLabs**: Premium quality, requires API key

To use ElevenLabs, update your `.env`:

```env
TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=your_api_key
ELEVENLABS_VOICE_ID=your_voice_id
```

## 📝 API Endpoints

- `POST /interview/start?role={role}` - Start a new interview
- `POST /interview/{id}/answer` - Submit audio answer
- `GET /interview/{id}/next` - Get next question
- `GET /interview/{id}/summary` - Get interview summary

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- OpenAI for GPT and Whisper models
- Microsoft for Edge TTS
- ElevenLabs for premium TTS option
