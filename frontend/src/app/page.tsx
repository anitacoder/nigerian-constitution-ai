export default function Home() {
  return (
    <div className="main-sidebar">
      <aside className="sidebar">
        <h2 className="side-text">Naija Constitution Ai</h2>
        <a href="#">New Chat</a>
        <a href="#">History</a>
        <a href="#">Settings</a>
      </aside>
    <main className="main">
      <div className="center-content">
        <div className="chat-logo"></div>
        <h1 className="greeting">Hello there,<br />How can I assist you today?</h1>
      </div>
      <div className="search-container">
        <input type="text" placeholder="Ask me anything..." className="search-input"/>
      </div>
    </main>
    </div>
  );
}
