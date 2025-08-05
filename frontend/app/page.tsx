'use client';
import { useState, useRef, useEffect } from 'react';

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
    setChat(prev => [
      ...prev,
      { role: 'user', content: currentQuestion },
      { role: 'ai', content: 'Generating......' },
    ]);

    try {
      const response = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: currentQuestion }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder('utf-8');
      let aiAnswer = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value);
          const parts = text.split('\n\n').filter(Boolean);

          for (const part of parts) {
            if (!part.startsWith('data: ')) continue;
            const payload = JSON.parse(part.replace('data: ', ''));

            switch (payload.type) {
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
                console.log('Streaming ended');
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

  const showInitialScreen = chat.length === 0;

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center py-8 relative">
      {showInitialScreen ? (
        <>
          <div className="text-center mb-10 mt-auto">
            <div className="mb-4">
              <div className="w-14 h-14 mx-auto flex items-center justify-center bg-gray-800 rounded-full">
                <svg viewBox="0 0 24 24" fill="white" className="w-8 h-8">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" />
                </svg>
              </div>
            </div>
            <h1 className="text-4xl font-medium italic">Hello dear!</h1>
            <h2 className="text-2xl mt-2 italic text-gray-300">Do you want to know more about the nigerian constitution ?</h2>
          </div>
          <div className="w-full max-w-2xl space-y-4 mb-auto">
            <div className="flex items-center justify-between text-sm text-gray-400">
              <span className="flex items-center gap-1">
              </span>
            </div>
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              {["What is the Constitution?", "Who makes the laws?", "What are my rights?"].map((text, i) => (
                <button key={i} onClick={() => { setQuestion(text); setTimeout(() => handleSearch(), 100); }}className="flex items-center gap-2 text-sm px-4 py-2 rounded-full bg-gray-800 hover:bg-gray-700">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2a10 10 0 100 20 10 10 0 000-20z" />
                  </svg>
                  {text}
                </button>
              ))}
            </div>
          </div>
        </>
      ) : (
        <>
          <div className="w-full max-w-2xl flex flex-col justify-start mb-20">
            {chat.map((msg, i) => (
              <div key={i} className={`flex mb-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] text-base leading-relaxed ${msg.role === 'user' ? 'text-white text-right' : 'text-gray-300 text-left'}`}>
                  {msg.content}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
        </>
      )}

      <div className="fixed bottom-0 left-0 right-0 p-4 bg-gray-950 flex justify-center">
        <div className="w-full max-w-2xl flex items-center gap-2">
          <input type="text" className="flex-1 bg-gray-800 text-white p-3 rounded-full placeholder-gray-400 outline-none"placeholder="Ask a question about the Nigerian Constitution..."value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSearch()}/>
          <button onClick={handleSearch} className="bg-gray-700 hover:bg-gray-600 p-3 rounded-full text-white">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l4.478-1.791a1 1 0 01.424 0l4.478 1.791a1 1 0 001.17-1.409l-7-14z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}