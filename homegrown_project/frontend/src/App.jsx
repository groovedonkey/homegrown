import { useState } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { Send, Paperclip, BookOpen, Bot } from 'lucide-react'

function App() {
  const [messages, setMessages] = useState([
    { sender: 'agent', text: "Welcome! Please type 'Hello Tera' to begin." }
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  
  // This state controls the Right Panel (The Workspace)
  const [workspace, setWorkspace] = useState({
    title: "Module 1: Income vs Expenses",
    objective: "Categorize the transaction list below.",
    status: "In Progress"
  })

  const sendMessage = async () => {
    if (!input.trim()) return;

    // 1. Add User Message immediately
    const newMsg = { sender: 'student', text: input }
    setMessages(prev => [...prev, newMsg])
    setInput("")
    setIsLoading(true)

    try {
      // 2. Call the Backend
      // Note: enrollment_id is hardcoded to 1 for this test
      const response = await axios.post('http://127.0.0.1:8000/api/chat', {
        enrollment_id: 2, 
        message: input
      })

      // 3. Handle Agent Response
      const agentText = response.data.agent_response
      setMessages(prev => [...prev, { sender: 'agent', text: agentText }])

      // 4. Update Workspace if the backend sent an update
      if (response.data.workspace_update) {
        setWorkspace(prev => ({
          ...prev,
          ...response.data.workspace_update
        }))
      }

    } catch (error) {
      console.error("Error talking to Daisy:", error)
      setMessages(prev => [...prev, { sender: 'system', text: "⚠️ Connection Error: Is the backend running?" }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-stone-50 text-stone-800 font-sans overflow-hidden">
      
      {/* LEFT PANEL: Chat Interface (40% Width) */}
      <div className="w-2/5 flex flex-col border-r border-stone-300 bg-white shadow-xl z-10">
        
        {/* Header */}
        <div className="p-4 border-b border-stone-200 bg-green-50 flex items-center gap-3">
          <div className="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center text-white shadow-sm">
            <Bot size={24} />
          </div>
          <div>
            <h2 className="font-bold text-lg text-green-900">Daisy Dollars</h2>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <p className="text-xs text-green-700 font-medium uppercase tracking-wide">Online • Finance 101</p>
            </div>
          </div>
        </div>

        {/* Chat Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-stone-50">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.sender === 'student' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] p-4 rounded-2xl shadow-sm text-sm leading-relaxed ${
                msg.sender === 'student' 
                  ? 'bg-stone-800 text-white rounded-br-none' 
                  : 'bg-white border border-stone-200 text-stone-700 rounded-bl-none'
              }`}>
                {/* We use ReactMarkdown so Daisy can use bold text or lists */}
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
               <div className="bg-stone-200 text-stone-500 px-4 py-2 rounded-full text-xs animate-pulse">
                 Daisy is thinking...
               </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-stone-200">
          <div className="flex items-center gap-2 bg-stone-100 p-2 rounded-xl border border-stone-200 focus-within:ring-2 focus-within:ring-green-500 transition-all">
            <button className="p-2 text-stone-400 hover:text-green-600 transition-colors"><Paperclip size={20}/></button>
            <input 
              className="flex-1 bg-transparent outline-none text-stone-700 placeholder-stone-400"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              disabled={isLoading}
            />
            <button 
              onClick={sendMessage} 
              disabled={isLoading}
              className={`p-2 rounded-lg text-white transition-all ${
                input.trim() ? 'bg-green-600 hover:bg-green-700 shadow-md' : 'bg-stone-300'
              }`}
            >
              <Send size={18}/>
            </button>
          </div>
        </div>
      </div>

      {/* RIGHT PANEL: The Workspace (60% Width) */}
      <div className="w-3/5 flex flex-col bg-stone-100 p-6 overflow-y-auto">
        <div className="max-w-3xl mx-auto w-full">
            
            {/* Module Card */}
            <div className="bg-white rounded-2xl shadow-sm border border-stone-200 p-8 mb-6">
              <div className="flex items-center gap-2 mb-6 text-stone-400">
                <BookOpen size={18}/>
                <span className="uppercase tracking-widest text-xs font-bold">Current Module</span>
              </div>
              
              <h1 className="text-3xl font-serif font-bold text-stone-800 mb-4">{workspace.title}</h1>
              
              <div className="bg-orange-50 border-l-4 border-orange-400 p-4 rounded-r-lg">
                <h3 className="font-bold text-orange-800 text-sm mb-1 uppercase">Objective</h3>
                <p className="text-orange-900">{workspace.objective}</p>
              </div>
            </div>

            {/* Interactive Content Placeholder */}
            <div className="bg-white rounded-2xl shadow-sm border border-stone-200 p-8 min-h-[400px] flex flex-col items-center justify-center text-stone-400 border-dashed border-2">
                <p>Interactive Worksheet Content Will Load Here</p>
                <span className="text-xs mt-2">(Spreadsheet / Code Editor / Canvas)</span>
            </div>

        </div>
      </div>

    </div>
  )
}

export default App