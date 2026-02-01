import { useEffect, useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import {
  Bot,
  BookOpen,
  Loader2,
  Paperclip,
  Send,
  Upload,
  FileText,
  Save,
  ArrowLeft,
} from 'lucide-react'
import { api } from '../lib/api'

function cx(...args) {
  return args.filter(Boolean).join(' ')
}

function NotesPanel({ enrollmentId }) {
  const storageKey = `homegrown:notes:${enrollmentId}`
  const [notes, setNotes] = useState(() => {
    try {
      const existing = localStorage.getItem(storageKey)
      return existing || ''
    } catch {
      return ''
    }
  })

  const save = () => {
    try {
      localStorage.setItem(storageKey, notes)
    } catch {
      // ignore
    }
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText size={16} className="text-emerald-300" />
          <div className="text-sm font-semibold text-emerald-100">Notes</div>
        </div>
        <button
          onClick={save}
          className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-zinc-950/40 px-3 py-1.5 text-xs text-zinc-200 hover:bg-zinc-950/60"
        >
          <Save size={14} />
          Save
        </button>
      </div>
      <div className="p-4">
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Write notes here… (saved to this device)"
          className="w-full min-h-45 rounded-xl bg-zinc-950/40 border border-white/10 p-3 text-sm text-zinc-100 outline-none focus:ring-2 focus:ring-emerald-500/40"
        />
        <div className="mt-2 text-[11px] text-emerald-200/60">
          Notes are saved locally in your browser (localStorage).
        </div>
      </div>
    </div>
  )
}

function UploadPanel({ enrollmentId, onUploaded }) {
  const [file, setFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const upload = async () => {
    if (!file) return
    setIsUploading(true)
    setError(null)
    setResult(null)

    try {
      const form = new FormData()
      form.append('enrollment_id', String(enrollmentId))
      form.append('file', file)

      const res = await api.post('/uploads', form)
      setResult(res.data)
      onUploaded?.(res.data)
      setFile(null)
    } catch {
      setError('Upload failed. Check backend logs.')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden">
      <div className="p-4 border-b border-white/10 flex items-center gap-2">
        <Upload size={16} className="text-emerald-300" />
        <div className="text-sm font-semibold text-emerald-100">Upload Files</div>
        {isUploading && <Loader2 size={16} className="ml-auto animate-spin text-emerald-300" />}
      </div>

      <div className="p-4">
        <div className="flex items-center gap-2">
          <label className="flex-1 rounded-xl border border-white/10 bg-zinc-950/40 px-3 py-2 text-xs text-zinc-200 cursor-pointer hover:bg-zinc-950/60">
            <input
              type="file"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            {file ? file.name : 'Choose a file…'}
          </label>
          <button
            onClick={upload}
            disabled={!file || isUploading}
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-500/20 border border-emerald-500/30 hover:bg-emerald-500/25 transition-colors px-4 py-2 text-xs font-semibold text-emerald-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Paperclip size={14} />
            Upload
          </button>
        </div>

        {error && (
          <div className="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-200">
            {error}
          </div>
        )}

        {result?.ok && (
          <div className="mt-3 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 text-xs text-emerald-100">
            Uploaded <span className="font-semibold">{result.filename}</span>
          </div>
        )}

        <div className="mt-2 text-[11px] text-emerald-200/60">
          Uploaded files are stored on the server (local dev) and logged to chat history.
        </div>
      </div>
    </div>
  )
}

export default function Workspace({ enrollment, onBack }) {
  const [messages, setMessages] = useState([
    {
      sender: 'agent',
      text: `Welcome! You’re in ${enrollment.course_title || 'your course'}. Say hello to begin.`,
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const [workspace, setWorkspace] = useState(() => ({
    title: enrollment.current_module_title || 'Current Module',
    objective: enrollment.current_module_objective || 'Objective will appear here.',
    status: 'In Progress',
    moduleIndex: enrollment.current_module_index ?? 0,
    totalModules: enrollment.total_modules ?? null,
  }))

  const scrollRef = useRef(null)

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
  }, [messages, isLoading])

  const courseLabel = useMemo(() => {
    const parts = []
    if (enrollment.agent_name) parts.push(enrollment.agent_name)
    if (enrollment.course_title) parts.push(enrollment.course_title)
    return parts.join(' • ') || 'Homegrown'
  }, [enrollment])

  const sendMessage = async () => {
    const msg = input.trim()
    if (!msg || isLoading) return

    setMessages((prev) => [...prev, { sender: 'student', text: msg }])
    setInput('')
    setIsLoading(true)

    try {
      const res = await api.post('/chat', {
        enrollment_id: enrollment.enrollment_id,
        message: msg,
      })

      const agentText = res.data?.agent_response || ''
      setMessages((prev) => [...prev, { sender: 'agent', text: agentText }])

      if (res.data?.workspace_update) {
        setWorkspace((prev) => ({
          ...prev,
          status: res.data.workspace_update.status || prev.status,
          title: res.data.workspace_update.next_module || prev.title,
          objective: res.data.workspace_update.objective || prev.objective,
          moduleIndex: typeof prev.moduleIndex === 'number' ? prev.moduleIndex + 1 : prev.moduleIndex,
        }))
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { sender: 'system', text: 'Connection error. Is the backend running?' },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="h-screen bg-linear-to-br from-zinc-950 via-zinc-950 to-emerald-950 text-zinc-100 overflow-hidden">
      <div className="h-full flex">
        <div className="w-105 max-w-[45vw] border-r border-white/10 bg-zinc-950/20 backdrop-blur">
          <div className="p-4 border-b border-white/10 flex items-center gap-3">
            <button
              onClick={onBack}
              className="h-10 w-10 rounded-xl border border-white/10 bg-zinc-950/40 hover:bg-zinc-950/60 flex items-center justify-center"
              title="Back"
            >
              <ArrowLeft size={18} className="text-emerald-200" />
            </button>
            <div className="h-10 w-10 rounded-xl bg-emerald-500/15 border border-emerald-500/20 flex items-center justify-center">
              <Bot size={20} className="text-emerald-300" />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-bold text-emerald-100 truncate">{courseLabel}</div>
              <div className="text-xs text-emerald-200/60 truncate">
                Enrollment #{enrollment.enrollment_id}
              </div>
            </div>
          </div>

          <div ref={scrollRef} className="h-[calc(100vh-160px)] overflow-y-auto px-4 py-5 space-y-4">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={cx('flex', m.sender === 'student' ? 'justify-end' : 'justify-start')}
              >
                <div
                  className={cx(
                    'max-w-[85%] rounded-2xl border px-4 py-3 text-sm leading-relaxed',
                    m.sender === 'student'
                      ? 'bg-emerald-500/15 border-emerald-500/20 text-emerald-50 rounded-br-none'
                      : m.sender === 'system'
                        ? 'bg-red-500/10 border-red-500/20 text-red-200'
                        : 'bg-white/5 border-white/10 text-zinc-100 rounded-bl-none',
                  )}
                >
                  <ReactMarkdown>{m.text}</ReactMarkdown>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="inline-flex items-center gap-2 rounded-full bg-white/5 border border-white/10 px-4 py-2 text-xs text-emerald-200/70">
                  <Loader2 size={14} className="animate-spin" />
                  Thinking…
                </div>
              </div>
            )}
          </div>

          <div className="p-4 border-t border-white/10">
            <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-zinc-950/40 px-3 py-2 focus-within:ring-2 focus-within:ring-emerald-500/40">
              <button className="p-2 text-emerald-200/60 hover:text-emerald-200" title="Attach">
                <Paperclip size={18} />
              </button>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Type a message…"
                className="flex-1 bg-transparent outline-none text-sm text-zinc-100 placeholder:text-zinc-500"
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="p-2 rounded-xl bg-emerald-500/20 border border-emerald-500/30 hover:bg-emerald-500/25 disabled:opacity-50"
                title="Send"
              >
                <Send size={18} className="text-emerald-100" />
              </button>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-5xl px-6 py-8 space-y-6">
            <div className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden">
              <div className="p-6 border-b border-white/10 flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 text-emerald-200/70">
                    <BookOpen size={16} />
                    <span className="text-xs uppercase tracking-widest font-bold">Current Module</span>
                  </div>
                  <div className="mt-2 text-2xl font-bold text-zinc-100 truncate">{workspace.title}</div>
                  <div className="mt-1 text-xs text-emerald-200/60">
                    {typeof workspace.moduleIndex === 'number' ? `Module ${workspace.moduleIndex + 1}` : ''}
                    {typeof workspace.totalModules === 'number' ? ` / ${workspace.totalModules}` : ''}
                    {workspace.status ? ` • ${workspace.status}` : ''}
                  </div>
                </div>
              </div>

              <div className="p-6">
                <div className="rounded-xl border border-emerald-500/15 bg-emerald-500/5 p-4">
                  <div className="text-xs uppercase tracking-widest font-bold text-emerald-200/70">Objective</div>
                  <div className="mt-2 text-sm text-emerald-50">{workspace.objective}</div>
                </div>

                <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <UploadPanel enrollmentId={enrollment.enrollment_id} />
                  <NotesPanel key={enrollment.enrollment_id} enrollmentId={enrollment.enrollment_id} />
                </div>

                <div className="mt-6 rounded-xl border border-white/10 bg-zinc-950/30 p-5 text-sm text-zinc-200/90">
                  <div className="font-semibold text-emerald-100">Workspace</div>
                  <div className="mt-2 text-xs text-emerald-200/60">
                    This area is where interactive content (editors, worksheets, grading results) will live.
                  </div>
                </div>
              </div>
            </div>

            <div className="text-[11px] text-emerald-200/50">
              Dark mode prototype • Styling and layout can be expanded later.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
