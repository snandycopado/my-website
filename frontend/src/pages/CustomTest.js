import { useState, useEffect } from 'react';
import './CustomTest.css';

const API_URL = 'https://my-website-w7br.onrender.com';

function CustomTest() {
  const [stage, setStage] = useState('home');
  const [topics, setTopics] = useState([]);
  const [topicName, setTopicName] = useState('');
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [answerKey, setAnswerKey] = useState([]);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchTopics = async () => {
    try {
      const res = await fetch(`${API_URL}/api/topics`);
      const data = await res.json();
      setTopics(data.topics);
    } catch (err) {
      console.error('Failed to fetch topics');
    }
  };

  useEffect(() => { fetchTopics(); }, []);

  const handleUpload = async () => {
    if (!topicName.trim() || files.length === 0) {
      alert('Please enter a topic name and select at least one file.');
      return;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('topic_name', topicName.trim());
      for (const file of files) {
        formData.append('files', file);
      }
      const res = await fetch(`${API_URL}/api/upload-topic`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed');
      await fetchTopics();
      setTopicName('');
      setFiles([]);
      alert('Files uploaded successfully!');
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleStartTest = async (topic) => {
    setSelectedTopic(topic);
    setLoading(true);
    setAnswers({});
    setResults(null);
    try {
      const formData = new FormData();
      formData.append('topic_name', topic.id);
      const res = await fetch(`${API_URL}/api/generate-custom-questions`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Failed to generate questions');
      const data = await res.json();
      setQuestions(data.questions);
      setAnswerKey(data._answer_key);
      setStage('exam');
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (questionId, option) => {
    if (results) return;
    setAnswers(prev => ({ ...prev, [questionId]: option }));
  };

  const handleSubmit = async () => {
    if (Object.keys(answers).length < questions.length) {
      alert('Please answer all questions before submitting.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/submit-custom-answers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic_name: selectedTopic.name,
          questions: answerKey,
          answers,
        }),
      });
      if (!res.ok) throw new Error('Failed to submit answers');
      const data = await res.json();
      setResults(data);
      setStage('results');
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setStage('home');
    setQuestions([]);
    setAnswerKey([]);
    setAnswers({});
    setResults(null);
    setSelectedTopic(null);
  };

  const getOptionLetter = (index) => ['A', 'B', 'C', 'D'][index];

  return (
    <div className="custom-test">
      <h1 className="ct-title">Custom Online Test</h1>
      <p className="ct-subtitle">Upload study material and generate personalized tests</p>

      {stage === 'home' && (
        <>
          <div className="upload-section">
            <h2>Upload Study Material</h2>
            <div className="upload-form">
              <input
                type="text"
                placeholder="Enter topic name (e.g., English Chapter 3)"
                value={topicName}
                onChange={e => setTopicName(e.target.value)}
                className="ct-input"
              />
              <label className="file-upload-label">
                <span>{files.length > 0 ? `${files.length} file(s) selected` : 'Choose Files'}</span>
                <input
                  type="file"
                  multiple
                  accept=".txt,.pdf,.doc,.docx"
                  onChange={e => setFiles(Array.from(e.target.files))}
                  className="file-input"
                />
              </label>
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="btn-upload"
              >
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>

          <div className="topics-section">
            <h2>Your Topics</h2>
            {topics.length === 0 ? (
              <p className="no-topics">No topics uploaded yet. Upload study material above to get started.</p>
            ) : (
              <div className="topics-grid">
                {topics.map(topic => (
                  <div key={topic.id} className="topic-card">
                    <div className="topic-info">
                      <h3>{topic.name}</h3>
                      <p>{topic.file_count} file(s): {topic.files.join(', ')}</p>
                    </div>
                    <button
                      onClick={() => handleStartTest(topic)}
                      disabled={loading}
                      className="btn-start-test"
                    >
                      {loading && selectedTopic?.id === topic.id ? 'Generating...' : 'Start Test'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {loading && (
            <div className="loading-container">
              <div className="spinner"></div>
              <p>AI is generating questions from your material...</p>
            </div>
          )}
        </>
      )}

      {stage === 'exam' && (
        <div className="exam-container">
          <div className="exam-header">
            <h2>Test: {selectedTopic?.name}</h2>
            <p className="answer-count">
              Answered: {Object.keys(answers).length} / {questions.length}
            </p>
          </div>
          <div className="questions-list">
            {questions.map((q, idx) => (
              <div key={q.id} className={`question-card ${answers[q.id] ? 'answered' : ''}`}>
                <h3 className="question-number">Question {idx + 1}</h3>
                <p className="question-text">{q.question}</p>
                <div className="options-grid">
                  {q.options.map((opt, optIdx) => {
                    const letter = getOptionLetter(optIdx);
                    const isSelected = answers[q.id] === letter;
                    return (
                      <button
                        key={optIdx}
                        className={`option-btn ${isSelected ? 'selected' : ''}`}
                        onClick={() => handleSelect(q.id, letter)}
                      >
                        <span className="option-letter">{letter}</span>
                        {opt}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="btn-submit"
          >
            {submitting ? 'Submitting...' : 'Submit Test'}
          </button>
          {submitting && (
            <div className="loading-container">
              <div className="spinner"></div>
              <p>AI is grading your test...</p>
            </div>
          )}
        </div>
      )}

      {stage === 'results' && results && (
        <div className="results-container">
          <div className="score-card">
            <h2>Test Results — {selectedTopic?.name}</h2>
            <div className="score-circle">
              <span className="score-number">{results.score}</span>
              <span className="score-total">/ {results.total}</span>
            </div>
            <p className="score-percentage">{results.percentage}%</p>
            <p className="score-label">
              {results.percentage >= 80 ? 'Excellent!' :
               results.percentage >= 60 ? 'Good Job!' :
               results.percentage >= 40 ? 'Keep Practicing!' : 'Needs Improvement'}
            </p>
          </div>
          <div className="results-detail">
            {results.results.map((r, idx) => (
              <div key={r.id} className={`result-card ${r.is_correct ? 'correct' : 'incorrect'}`}>
                <div className="result-status">{r.is_correct ? '✓' : '✗'}</div>
                <div className="result-content">
                  <p className="result-question"><strong>Q{idx + 1}:</strong> {r.question}</p>
                  <p>Your answer: <strong>{r.student_answer}</strong></p>
                  {!r.is_correct && <p>Correct answer: <strong className="correct-text">{r.correct_answer}</strong></p>}
                </div>
              </div>
            ))}
          </div>
          <div className="result-actions">
            <button onClick={() => handleStartTest(selectedTopic)} className="btn-retry">Retake Test</button>
            <button onClick={handleReset} className="btn-back">Back to Topics</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default CustomTest;
