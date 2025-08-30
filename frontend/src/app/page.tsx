import { FiMessageSquare, FiClock, FiSettings, FiSend} from "react-icons/fi";
export default function Home() {
  return (
    <div className="main-sidebar">
      <aside className="sidebar">
      <h2 className="side-text">Naija Constitution Ai</h2>
      <div className="sidebar-links">
        <a href="#" className="sidebar-link"><FiMessageSquare size={18} />New Chat</a>
        <a href="#" className="sidebar-link"><FiClock size={18} />History</a>
        <a href="#" className="sidebar-link"><FiSettings size={18} />Settings</a>
        </div>
      </aside>
    <main className="main">
      <div className="center-content">
        <div className="chat-logo"></div>
        <h1 className="greeting">Hello there,<br />How can I assist you today?</h1>
      </div>
      <div className="search-container relative w-full max-w-md">
          <input type="text" placeholder="Ask me anything..." className="search-input w-full pr-10 pl-3 py-2 border rounded-lg" />
          <FiSend size={20} className="send-icon"/>
        </div>
    </main>
    </div>
  );
}
