import { useState, useEffect, useRef } from 'react';
import { aiAPI } from '../api';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, User, Sparkles, RefreshCw } from 'lucide-react';

export default function Chatbot({ projectId, onProjectUpdate }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (projectId) {
      aiAPI.chatHistory(projectId).then(({ data }) => setMessages(data)).catch(() => {});
    }
  }, [projectId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return;
    const userMsg = { role: 'user', content: text, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const { data } = await aiAPI.chat(text, projectId);
      setMessages((prev) => [...prev, data]);
      if (data.fields_updated?.length && onProjectUpdate) {
        onProjectUpdate();
      }
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.', created_at: new Date().toISOString() }]);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    "What's the project status?",
    "Add deliverable: Final validation report",
    "Add risk: Supply chain delay category Logistics",
    "Add inventory: PCB boards required 100 available 20",
    "Add wbs 2.6 Compliance Testing 14 days under 2.0",
    "Add machine: Test Jig Station health 88",
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-280px)] min-h-[500px]">
      <div className="mb-3 flex items-center justify-between text-sm text-gray-500">
        <span>You can ask questions or modify charter, WBS, inventory, risks, and maintenance via chat.</span>
        {onProjectUpdate && (
          <button onClick={onProjectUpdate} className="flex items-center gap-1 text-primary-600 hover:underline">
            <RefreshCw className="w-3 h-3" /> Refresh project data
          </button>
        )}
      </div>
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="bg-primary-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-8 h-8 text-primary-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">AI Project Assistant</h3>
            <p className="text-gray-500 mb-6 max-w-lg mx-auto">
              Ask about status, risks, budget, or tell me to add/update items — e.g. &quot;Add deliverable: User manual&quot; or &quot;Add risk: Chipset shortage&quot;.
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-2xl mx-auto">
              {suggestions.map((s) => (
                <button key={s} onClick={() => sendMessage(s)} className="text-sm bg-gray-100 hover:bg-primary-50 hover:text-primary-700 px-3 py-1.5 rounded-full transition-colors">{s}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="bg-primary-100 p-2 rounded-lg h-fit"><Bot className="w-4 h-4 text-primary-600" /></div>
            )}
            <div className={`max-w-[80%] rounded-xl px-4 py-3 ${msg.role === 'user' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
              {msg.fields_updated?.length > 0 && (
                <p className="text-xs text-accent-700 bg-accent-50 rounded px-2 py-1 mb-2">Project updated — refresh tabs to see changes</p>
              )}
              {msg.role === 'assistant' ? (
                <div className="chat-message text-sm prose prose-sm max-w-none"><ReactMarkdown>{msg.content}</ReactMarkdown></div>
              ) : (
                <p className="text-sm">{msg.content}</p>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="bg-gray-200 p-2 rounded-lg h-fit"><User className="w-4 h-4 text-gray-600" /></div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="bg-primary-100 p-2 rounded-lg"><Bot className="w-4 h-4 text-primary-600" /></div>
            <div className="bg-gray-100 rounded-xl px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={(e) => { e.preventDefault(); sendMessage(input); }} className="flex gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question or say: Add deliverable / risk / material / wbs task / machine..."
            className="input-field flex-1"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()} className="btn-primary px-4">
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
