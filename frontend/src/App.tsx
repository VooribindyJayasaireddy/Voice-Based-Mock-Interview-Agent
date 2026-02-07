import { useState, useRef, useEffect } from "react";
import "@/App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// State interface
interface EvaluationData {
  relevance: number;
  clarity: number;
  correctness: number;
  feedback: string;
}

interface InterviewState {
  interviewId: string;
  currentQuestion: string;
  transcript: string;
  evaluation: EvaluationData | null;
}

interface SummaryData {
  overall_feedback: string;
  strengths: string;
  improvements: string;
}

function App() {
  const [state, setState] = useState<InterviewState>({
    interviewId: "",
    currentQuestion: "",
    transcript: "",
    evaluation: null,
  });
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [currentAudio, setCurrentAudio] = useState("");
  const [role, setRole] = useState("Software Engineer");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Start interview
  const handleStartInterview = async () => {
    setIsLoading(true);
    setError("");
    setSummary(null);

    try {
      const response = await axios.post(
        `${BACKEND_URL}/interview/start?role=${encodeURIComponent(role)}`,
      );

      setState({
        interviewId: response.data.interview_id,
        currentQuestion: response.data.question,
        transcript: "",
        evaluation: null,
      });

      setCurrentAudio(response.data.audio_file);
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.response?.data?.msg ||
        err.message ||
        "Failed to start interview";
      setError(
        typeof errorMessage === "string"
          ? errorMessage
          : JSON.stringify(errorMessage),
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Play audio when currentAudio changes
  useEffect(() => {
    if (currentAudio && audioRef.current) {
      audioRef.current.src = `${BACKEND_URL}/audio/${currentAudio}`;
      audioRef.current
        .play()
        .catch((e) => console.error("Audio play error:", e));
    }
  }, [currentAudio]);

  // Start recording
  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Create MediaRecorder with WAV support fallback
      const options = { mimeType: "audio/webm" };
      const mediaRecorder = new MediaRecorder(stream, options);

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setError("");
    } catch (err: any) {
      setError("Microphone permission denied or not available");
    }
  };

  // Stop recording and submit
  const handleStopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/webm",
        });
        await submitAnswer(audioBlob);

        // Stop all tracks
        mediaRecorderRef.current?.stream
          .getTracks()
          .forEach((track) => track.stop());
      };

      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Submit answer
  const submitAnswer = async (audioBlob: Blob) => {
    setIsLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "answer.webm");

      const response = await axios.post(
        `${BACKEND_URL}/interview/${state.interviewId}/answer`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      );

      setState((prev) => ({
        ...prev,
        transcript: response.data.transcript,
        evaluation: response.data.evaluation,
      }));
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.response?.data?.msg ||
        err.message ||
        "Failed to submit answer";
      setError(
        typeof errorMessage === "string"
          ? errorMessage
          : JSON.stringify(errorMessage),
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Next question
  const handleNextQuestion = async () => {
    setIsLoading(true);
    setError("");

    try {
      const response = await axios.get(
        `${BACKEND_URL}/interview/${state.interviewId}/next`,
      );

      setState((prev) => ({
        ...prev,
        currentQuestion: response.data.question,
        transcript: "",
        evaluation: null,
      }));

      setCurrentAudio(response.data.audio_file);
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.response?.data?.msg ||
        err.message ||
        "Failed to get next question";
      setError(
        typeof errorMessage === "string"
          ? errorMessage
          : JSON.stringify(errorMessage),
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Get summary
  const handleGetSummary = async () => {
    setIsLoading(true);
    setError("");

    try {
      const response = await axios.get(
        `${BACKEND_URL}/interview/${state.interviewId}/summary`,
      );

      setSummary(response.data);
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.response?.data?.msg ||
        err.message ||
        "Failed to get summary";
      setError(
        typeof errorMessage === "string"
          ? errorMessage
          : JSON.stringify(errorMessage),
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="interview-card">
        <h1 className="title" data-testid="app-title">
          Voice Mock Interview
        </h1>

        {/* Error Display */}
        {error && (
          <div className="error-message" data-testid="error-message">
            {error}
          </div>
        )}

        {/* Summary View */}
        {summary ? (
          <div className="summary-section" data-testid="summary-section">
            <h2 className="section-title">Interview Summary</h2>
            <div className="summary-content">
              <div className="summary-item">
                <strong>Overall Feedback:</strong>
                <p>{summary.overall_feedback}</p>
              </div>
              <div className="summary-item">
                <strong>Strengths:</strong>
                <p>{summary.strengths}</p>
              </div>
              <div className="summary-item">
                <strong>Areas for Improvement:</strong>
                <p>{summary.improvements}</p>
              </div>
            </div>
            <button
              className="btn btn-primary"
              onClick={() => {
                setSummary(null);
                setState({
                  interviewId: "",
                  currentQuestion: "",
                  transcript: "",
                  evaluation: null,
                });
              }}
              data-testid="start-new-interview-btn"
            >
              Start New Interview
            </button>
          </div>
        ) : !state.interviewId ? (
          // Start Interview Section
          <div className="start-section" data-testid="start-section">
            <div className="input-group">
              <label htmlFor="role-input">Role:</label>
              <input
                id="role-input"
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="Enter job role"
                className="input-field"
                data-testid="role-input"
              />
            </div>
            <button
              className="btn btn-primary"
              onClick={handleStartInterview}
              disabled={isLoading || !role.trim()}
              data-testid="start-interview-btn"
            >
              {isLoading ? "Starting..." : "Start Interview"}
            </button>
          </div>
        ) : (
          // Interview In Progress
          <div className="interview-section" data-testid="interview-section">
            {/* Question Display */}
            <div className="question-section" data-testid="question-section">
              <h2 className="section-title">Current Question</h2>
              <p className="question-text" data-testid="question-text">
                {state.currentQuestion}
              </p>

              {/* Hidden audio element for playback */}
              <audio
                ref={audioRef}
                controls
                className="audio-player"
                data-testid="audio-player"
              />
            </div>

            {/* Recording Controls */}
            <div className="controls-section" data-testid="controls-section">
              {!isRecording ? (
                <button
                  className="btn btn-record"
                  onClick={handleStartRecording}
                  disabled={isLoading}
                  data-testid="start-recording-btn"
                >
                  Answer
                </button>
              ) : (
                <button
                  className="btn btn-stop"
                  onClick={handleStopRecording}
                  data-testid="stop-recording-btn"
                >
                  Stop
                </button>
              )}
              {isRecording && (
                <span
                  className="recording-indicator"
                  data-testid="recording-indicator"
                >
                  ● Recording...
                </span>
              )}
            </div>

            {/* Transcript and Evaluation */}
            {state.transcript && (
              <div className="result-section" data-testid="result-section">
                <div className="transcript-box" data-testid="transcript-box">
                  <h3 className="subsection-title">Your Answer</h3>
                  <p>{state.transcript}</p>
                </div>

                {state.evaluation && (
                  <div className="evaluation-box" data-testid="evaluation-box">
                    <h3 className="subsection-title">Evaluation</h3>
                    <div className="scores" data-testid="evaluation-scores">
                      <div className="score-item">
                        <span>Relevance:</span>
                        <span
                          className="score-value"
                          data-testid="score-relevance"
                        >
                          {state.evaluation.relevance}/10
                        </span>
                      </div>
                      <div className="score-item">
                        <span>Clarity:</span>
                        <span
                          className="score-value"
                          data-testid="score-clarity"
                        >
                          {state.evaluation.clarity}/10
                        </span>
                      </div>
                      <div className="score-item">
                        <span>Correctness:</span>
                        <span
                          className="score-value"
                          data-testid="score-correctness"
                        >
                          {state.evaluation.correctness}/10
                        </span>
                      </div>
                    </div>
                    <div className="feedback" data-testid="evaluation-feedback">
                      <strong>Feedback:</strong>
                      <p>{state.evaluation.feedback}</p>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="action-buttons" data-testid="action-buttons">
                  <button
                    className="btn btn-secondary"
                    onClick={handleNextQuestion}
                    disabled={isLoading}
                    data-testid="next-question-btn"
                  >
                    {isLoading ? "Loading..." : "Next Question"}
                  </button>
                  <button
                    className="btn btn-tertiary"
                    onClick={handleGetSummary}
                    disabled={isLoading}
                    data-testid="get-summary-btn"
                  >
                    {isLoading ? "Loading..." : "End Interview"}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
