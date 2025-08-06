  'use client';
  import { useState, useRef, useEffect } from 'react';

  const intros = [
    "Do you want to know more about the Nigerian Constitution?",
    "Are you curious about your legal rights?",
    "Looking to understand how the Nigerian government works?",
    "Explore the laws that shape Nigeria.",
  ]

  export default function Home() {
    const [question, setQuestion] = useState('');
    const [chat, setChat] = useState<{ role: 'user' | 'ai', content: string }[]>([]);
    const [loading, setLoading] = useState(false);
    const chatEndRef = useRef<HTMLDivElement>(null);
    const [currentIntroIndex, setCurrentIntroIndex] = useState(0);
    const [displayText, setDisplayText] = useState('');
    const [isDeleting, setIsDeleting] = useState(false);

    useEffect(() => {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chat]);
  
    useEffect(() => {
      const current = intros[currentIntroIndex];
      let updatedText = isDeleting
        ? current.substring(0, displayText.length - 1)
        : current.substring(0, displayText.length + 1);
  
      const typingSpeed = isDeleting ? 50 : Math.floor(Math.random() * (150 - 80 + 1)) + 80;
      let timer;

      if (!isDeleting && updatedText === current) {
        timer = setTimeout(() => setIsDeleting(true), 2000);
      } else if (isDeleting && updatedText === '') {
        timer = setTimeout(() => {
          setIsDeleting(false);
          setCurrentIntroIndex((prev) => (prev + 1) % intros.length);
        },500);
      } else {
        timer = setTimeout(() => {
          setDisplayText(updatedText);
        }, typingSpeed);
      }
      return () => clearTimeout(timer);
    }, [displayText, isDeleting, currentIntroIndex, intros]);
  
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
      <div className="flex flex-col min-h-screen bg-gray-900 text-gray-100 font-sans">
        <main className="flex-1 overflow-y-auto w-full max-w-3xl mx-auto p-4 flex flex-col pt-8 pb-20">
          {showInitialScreen ? (
            <div className="flex flex-col flex-grow items-center justify-center text-center px-4">
              <h1 className="text-5xl font-extrabold mb-4 animate-fade-in">Hello, citizen!</h1>
              <h2 className="text-xl text-gray-400 mb-8 max-w-xl min-h-[80px]">
                <span>{displayText}<span className="border-r-2 border-gray-400 animate-pulse ml-1" /></span>
              </h2>
              <div className="flex gap-5">
              {["What is the Constitution?", "Who makes the laws?", "What are my rights?"].map((text, i) => (
                  <button key={i} onClick={() => { setQuestion(text); setTimeout(() => handleSearch(), 100);
                    }}
                    className="flex items-center gap-2 text-sm px-4 py-3 rounded-xl bg-gray-800 hover:bg-gray-700 transition-colors duration-200 text-gray-300">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2a10 10 0 100 20 10 10 0 000-20z" />
                    </svg>
                    {text}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex-1 w-full max-w-3xl mx-auto pt-8 pb-20">
              {chat.map((msg, i) => (
                <div key={i} className={`flex mb-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'ai' && (
                    <div className="w-8 h-8 rounded-full bg-blue-500 mr-2 flex-shrink-0 flex items-center justify-center text-white font-bold">
                    </div>
                  )}
                  <div
                    className={`max-w-[70%] px-4 py-2 rounded-xl text-sm break-words whitespace-pre-wrap shadow-sm ${
                      msg.role === 'user'
                        ? 'bg-blue-500 text-white rounded-br-none'
                        : 'bg-gray-800 text-gray-200 rounded-bl-none'
                    }`}>
                    {msg.content}
                    {msg.role === 'ai' && msg.content === 'Generating......'}
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
          )}
        </main>

        <footer className="fixed bottom-0 left-0 right-0 p-4 bg-gray-900 border-t border-gray-700 flex justify-center z-10">
          <div className="w-full max-w-3xl flex items-center gap-2">
            <input type="text" className="flex-1 bg-gray-800 text-white p-3 rounded-full placeholder-gray-400 outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200" placeholder="Ask a question about the Nigerian Constitution..." value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSearch()}/>
            <button onClick={handleSearch} className="bg-blue-600 hover:bg-blue-500 p-3 rounded-full text-white transition-colors duration-200 disabled:bg-gray-600"disabled={loading || !question.trim()}>
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l4.478-1.791a1 1 0 01.424 0l4.478 1.791a1 1 0 001.17-1.409l-7-14z" />
              </svg>
            </button>
          </div>
        </footer>
      </div>
    );
  }