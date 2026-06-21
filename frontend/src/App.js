import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import AIFeatures from './pages/AIFeatures';
import Chat from './pages/Chat';
import CustomTest from './pages/CustomTest';
import Salesforce from './pages/Salesforce';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/ai-features" element={<AIFeatures />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/custom-test" element={<CustomTest />} />
          <Route path="/salesforce" element={<Salesforce />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
