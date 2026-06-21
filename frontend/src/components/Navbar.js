import { NavLink } from 'react-router-dom';
import './Navbar.css';

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">Suman Nandy</div>
      <ul className="navbar-links">
        <li><NavLink to="/" end>Home</NavLink></li>
        <li><NavLink to="/ai-features">AI Features</NavLink></li>
        <li><NavLink to="/chat">Chat Feature</NavLink></li>
        <li><NavLink to="/custom-test">Custom Test</NavLink></li>
        <li><NavLink to="/salesforce">Salesforce</NavLink></li>
      </ul>
    </nav>
  );
}

export default Navbar;
