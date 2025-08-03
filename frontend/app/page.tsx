'use client';
import { log } from "console";
import { useState, useRef, useEffect } from "react";

export default function Home() {
  const [question, setQuestion] = useState('');
  const [chat, setChat] = useState<{ role: 'user' | 'ai', content: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chat]);

  const handleSearch = async () => {
    if (!question.trim()) return;

    const currentQuestion = question;
    setQuestion('');
    setLoading(true);
    setChat((prev) => [ ...prev, { role: 'user', content: currentQuestion },{ role: 'ai', content: 'Generating......' },
    ]);
    try {
      const response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: currentQuestion }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");
      let aiAnswer = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value);
          const parts = text.split("\n\n").filter(Boolean);

          for (const part of parts) {
            if (!part.startsWith("data: ")) continue;
            const payload = JSON.parse(part.replace("data: ", ""));

            switch(payload.type) {
              case 'metadata':
                console.log("Metedata", payload);
                break;
              case 'chunk':
              aiAnswer += payload.content;
              setChat(prev => {
                const last = prev[prev.length - 1];
                if (last?.role === 'ai') {
                  return [...prev.slice(0, -1), { role: 'ai', content: aiAnswer }];
                } else {
                  return [...prev, { role: 'ai', content: aiAnswer }];
                }
              });
              break;
              case 'end':
                console.log("Streaming ended", payload);
                break;
              case 'error':
                setChat(prev => [...prev, { role: 'ai', content: `Error: ${payload.error}` }]);
                break;
            }
          }
        }
      }
    } catch (err) {
      setChat(prev => [...prev, { role: 'ai', content: 'An error occurred. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="main-container">
      <h1 className="first-heading">Hello, there!</h1>
      <h2 className="second-heading">What would you like to know about Nigeria?</h2>

      <div className="chat-board">
        {chat.map((msg, idx) => (
          <div
            key={idx}
            className={`chat-bubble ${msg.role === 'user' ? 'chat-user' : 'chat-ai'}`}
          >
            {msg.content}
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      <div className="search-bar-section">
        <div className="search-box-container">
          <input
            type="text"
            className="search-input"
            placeholder="Ask a question about the Nigerian Constitution..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
        </div>
        <button className="search-button" onClick={handleSearch}>Send</button>
      </div>
    

    </div>
  );
}