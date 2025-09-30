"use client";
import { useState } from "react";
import { FiMessageSquare,FiPlus,FiSend } from "react-icons/fi";
import { useRouter, useParams} from "next/navigation"; 

type ChatMessage = {
  role: "user" | "bot";
  text: string;
};

export default function NewChatPage() {
  const { id } = useParams();
  const [message, setMessage] = useState<string>("");
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const router = useRouter();

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

      const reader = res.body?.getReader();
      const decoder = new TextDecoder("utf-8");
      let reply = "";

      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;
        if (loading) setLoading(false)
        reply += decoder.decode(value, { stream: true });

        setChat((prev) => {
          const updated = [...prev];
          if (updated[updated.length - 1]?.role === "bot") {
            updated[updated.length - 1].text = reply;
          } else {
            updated.push({ role: "bot", text: reply });
          }
          return updated;
        });
      }
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
          <input type="text" placeholder="Ask me anything..." className="search-input" value={message} onChange={(e) => setMessage(e.target.value)} onKeyDown={handleKeyDown}/>
        <div className="search-actions">
        <button className="icon-btn new-chat-btn" onClick={() => router.push(`/chat/${Date.now()}`)} title="Start new chat">
          <FiPlus size={18} />
        </button>
          <button className="icon-btn send-btn" onClick={() => sendMessage()}>
            <FiSend size={18} />
          </button>
      </div>
    </div>

      </main>
    </div>
  );
}
