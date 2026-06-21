import './Home.css';

function Home() {
  return (
    <div className="home">
      <section className="hero">
        <div className="hero-content">
          <p className="hero-greeting">Hello, I'm</p>
          <h1 className="hero-name">Suman Nandy</h1>
          <h2 className="hero-title">Salesforce AI Developer</h2>
          <p className="hero-tagline">16 Years of IT Experience | Building the Future with Salesforce & AI</p>
        </div>
      </section>

      <section className="about">
        <h2 className="section-title">About Me</h2>
        <div className="about-content">
          <div className="about-card">
            <div className="about-icon">👨‍💻</div>
            <h3>Who I Am</h3>
            <p>
              A passionate technologist with 16 years of IT experience, specializing in
              Salesforce development and Artificial Intelligence. I bridge the gap between
              enterprise CRM solutions and cutting-edge AI technology.
            </p>
          </div>
          <div className="about-card">
            <div className="about-icon">🚀</div>
            <h3>What I Do</h3>
            <p>
              I design and build intelligent Salesforce solutions powered by AI.
              From Einstein AI integrations to custom ML models, I help businesses
              unlock the full potential of their Salesforce ecosystem.
            </p>
          </div>
          <div className="about-card">
            <div className="about-icon">🎓</div>
            <h3>Training & Mentoring</h3>
            <p>
              Providing advanced Salesforce and AI training to professionals and teams.
              My courses cover Salesforce development, AI integration, prompt engineering,
              and building AI-powered enterprise applications.
            </p>
          </div>
        </div>
      </section>

      <section className="skills">
        <h2 className="section-title">Core Skills</h2>
        <div className="skills-grid">
          {[
            'Salesforce Development', 'Apex & LWC', 'Salesforce AI (Einstein)',
            'Python & FastAPI', 'React.js', 'Machine Learning',
            'Prompt Engineering', 'REST APIs', 'Cloud Deployment'
          ].map(skill => (
            <span key={skill} className="skill-tag">{skill}</span>
          ))}
        </div>
      </section>

      <section className="cta">
        <h2>Ready to Level Up?</h2>
        <p>Join my advanced Salesforce & AI training programs and stay ahead in the tech world.</p>
      </section>

      <footer className="footer">
        <p>&copy; 2026 Suman Nandy. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default Home;
