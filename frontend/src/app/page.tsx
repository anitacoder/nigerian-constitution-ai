"use client";
import { useState } from "react";
import { FiMessageSquare, FiClock, FiSettings, FiSend } from "react-icons/fi";

type ChatMessage = {
  role: "user" | "bot";
  text: string;
};

export default function Home() {
  const [message, setMessage] = useState<string>("");
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const sendMessage = async (customMessage?: string) => {
    const msgToSend = customMessage ?? message;
    if (!msgToSend.trim()) return;

    setChat((prev) => [...prev, { role: "user", text: msgToSend }]);
    setMessage("")
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/ask_question", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: msgToSend }),
      });

      if (!res.ok) throw new Error("Failed to get response");

      const data: { results: string } = await res.json();

      setChat((prev) => [...prev, { role: "bot", text: data.results }]);
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error ? err.message : "An unknown error occurred";
      setChat((prev) => [...prev, { role: "bot", text: "Error: " + errorMsg }]);
    } finally {
      setLoading(false);
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    setMessage("");
    sendMessage(question);
  }

  return (
    <div className="main-sidebar">
      <main className="main flex flex-col">
        {chat.length === 0 ? (
          <div className="center-content">
            <div className="chat-logo"></div>
            <h1 className="greeting">
              Hello there,
              <br />
              How can I assist you today?
            </h1>
            <div className="suggested-questions">
          <button className="question-box">
            What is the 1999 Nigerian Constitution?
          </button>
          <button className="question-box" onClick={() => handleSuggestedQuestion("What are the fundamental human rights?")}>
          What is the 1999 Nigerian Constitution?
          </button>
          <button className="question-box" onClick={() => handleSuggestedQuestion("Explain separation of powers in Nigeria")}>
            Explain separation of powers in Nigeria
          </button>
          <button className="question-box" onClick={() => handleSuggestedQuestion("How is the president elected?")}>
            How is the president elected?
          </button>
        </div>
          </div>
        ) : (
        <div className="chat-container">
          {chat.map((msg, idx) => (
            <div key={idx} className={`chat-message ${msg.role === "user" ? "user-message" : "bot-message"}`}>
              {msg.text}
            </div>
          ))}

          {loading && <div className="typing-indicator">Typing...</div>}
    </div>

        )}

        <div className="search-container">
          <input type="text" placeholder="Ask me anything..."className="search-input w-full pr-10 pl-3 py-2 border rounded-lg"value={message} onChange={(e) => setMessage(e.target.value)} onKeyDown={handleKeyDown}/>
          <FiSend size={20} className="send-icon" onClick={() => sendMessage()} />
        </div>
      </main>
    </div>
  );
}
