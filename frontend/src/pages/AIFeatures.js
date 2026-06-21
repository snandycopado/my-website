import { useState } from 'react';
import './AIFeatures.css';

const API_URL = 'https://my-website-w7br.onrender.com';

function AIFeatures() {
  const [studentClass, setStudentClass] = useState('');
  const [questions, setQuestions] = useState([]);
  const [answerKey, setAnswerKey] = useState([]);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [stage, setStage] = useState('select');

  const handleGenerate = async () => {
    const cls = parseInt(studentClass);
    if (!cls || cls < 1 || cls > 12) return;
    setLoading(true);
    setResults(null);
    setAnswers({});
    try {
      const res = await fetch(`${API_URL}/api/generate-questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_class: cls }),
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
      const res = await fetch(`${API_URL}/api/submit-answers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_class: parseInt(studentClass),
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
    setStage('select');
    setQuestions([]);
    setAnswerKey([]);
    setAnswers({});
    setResults(null);
    setStudentClass('');
  };

  const getOptionLetter = (index) => ['A', 'B', 'C', 'D'][index];

  return (
    <div className="ai-features">
      <h1 className="ai-title">AI English Test</h1>
      <p className="ai-subtitle">AI-powered English assessment for students</p>

      {stage === 'select' && (
        <div className="class-selector">
          <h2>Select Your Class</h2>
          <div className="class-input-group">
            <select
              value={studentClass}
              onChange={e => setStudentClass(e.target.value)}
              className="class-select"
            >
              <option value="">-- Select Class --</option>
              {[...Array(12)].map((_, i) => (
                <option key={i + 1} value={i + 1}>Class {i + 1}</option>
              ))}
            </select>
            <button
              onClick={handleGenerate}
              disabled={!studentClass || loading}
              className="btn-generate"
            >
              {loading ? 'Generating...' : 'Start Test'}
            </button>
          </div>
          {loading && (
            <div className="loading-container">
              <div className="spinner"></div>
              <p>AI is generating your questions...</p>
            </div>
          )}
        </div>
      )}

      {stage === 'exam' && (
        <div className="exam-container">
          <div className="exam-header">
            <h2>English Test — Class {studentClass}</h2>
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
            <h2>Test Results</h2>
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
          <button onClick={handleReset} className="btn-generate">Take Another Test</button>
        </div>
      )}
    </div>
  );
}

export default AIFeatures;
