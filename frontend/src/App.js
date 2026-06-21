import { useState, useEffect } from 'react';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [message, setMessage] = useState('');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      fetch(`${API_URL}/`).then(res => res.json()),
      fetch(`${API_URL}/data`).then(res => res.json()),
    ])
      .then(([homeData, dataData]) => {
        setMessage(homeData.message);
        setItems(dataData.items);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="App"><p>Loading...</p></div>;
  if (error) return <div className="App"><p>Error: {error}</p></div>;

  return (
    <div className="App">
      <header className="App-header">
        <h1>{message}</h1>
        <h2>Items from API</h2>
        <ul>
          {items.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </header>
    </div>
  );
}

export default App;
