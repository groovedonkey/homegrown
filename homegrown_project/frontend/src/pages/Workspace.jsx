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
  User,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Circle,
} from 'lucide-react'
import { api } from '../lib/api'

function cx(...args) {
  return args.filter(Boolean).join(' ')
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="inline-flex items-center gap-1.5 rounded-2xl rounded-bl-none bg-zinc-900 border border-white/8 px-4 py-3">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400/70 animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400/70 animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400/70 animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  )
}

function McqQuizBlock({ enrollmentId, block, onSend }) {
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const submit = async () => {
    if (isSubmitting) return
    setIsSubmitting(true)
    try {
      const res = await api.post('/quiz/submit', {
        enrollment_id: enrollmentId,
        quiz_id: block.quiz_id,
        answers: (block.questions || []).map((q) => ({
          question_id: q.id,
          answer_id: answers[q.id] || '',
        })),
      })
      setResult(res.data)
    } catch {
      setResult({ error: 'Could not submit quiz. Is the backend running?' })
    } finally {
      setIsSubmitting(false)
    }
  }

  const scoreLine = () => {
    if (!result || result.error) return null
    const passText =
      typeof result.passed === 'boolean'
        ? result.passed
          ? 'Pass'
          : 'Try again'
        : ''
    return `${result.score}/${result.total}${passText ? ` · ${passText}` : ''}`
  }

  const allAnswered = (block.questions || []).every((q) => answers[q.id])

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-emerald-100">
        <BookOpen size={14} className="text-emerald-400" />
        {block.title || 'Quiz'}
      </div>

      {(block.questions || []).map((q, idx) => {
        const questionResult = result && !result.error && Array.isArray(result.results)
          ? result.results.find((x) => x.question_id === q.id)
          : null

        return (
          <div key={q.id || idx} className="rounded-xl border border-white/8 bg-zinc-950/50 p-3.5">
            <div className="text-sm text-zinc-200 mb-3">
              <span className="text-emerald-400/70 font-semibold mr-2">Q{idx + 1}.</span>
              {q.prompt}
            </div>
            <div className="space-y-2">
              {(q.options || []).map((opt) => {
                const isSelected = String(answers[q.id] || '') === String(opt.id)
                const optResult = questionResult
                  ? result.results.find((x) => x.question_id === q.id)
                  : null
                const isCorrectOpt = optResult && isSelected && optResult.is_correct
                const isWrongOpt = optResult && isSelected && !optResult.is_correct

                return (
                  <label
                    key={opt.id}
                    className={cx(
                      'flex items-center gap-2.5 rounded-lg px-3 py-2 cursor-pointer transition-colors text-sm',
                      result
                        ? isCorrectOpt
                          ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-100'
                          : isWrongOpt
                            ? 'bg-red-500/10 border border-red-500/20 text-red-200'
                            : 'border border-transparent text-zinc-400'
                        : isSelected
                          ? 'bg-emerald-500/10 border border-emerald-500/25 text-emerald-100'
                          : 'border border-transparent text-zinc-300 hover:bg-white/5',
                    )}
                  >
                    <input
                      type="radio"
                      name={q.id}
                      value={opt.id}
                      checked={isSelected}
                      onChange={() => !result && setAnswers((prev) => ({ ...prev, [q.id]: opt.id }))}
                      className="sr-only"
                    />
                    <span className={cx(
                      'shrink-0 h-4 w-4 rounded-full border flex items-center justify-center',
                      isSelected ? 'border-emerald-400 bg-emerald-500/20' : 'border-zinc-600'
                    )}>
                      {isSelected && <span className="h-2 w-2 rounded-full bg-emerald-400" />}
                    </span>
                    {opt.text}
                    {isCorrectOpt && <CheckCircle2 size={14} className="ml-auto text-emerald-400" />}
                    {isWrongOpt && <XCircle size={14} className="ml-auto text-red-400" />}
                  </label>
                )
              })}
            </div>
          </div>
        )
      })}

      <div className="flex items-center gap-3 pt-1">
        {!result ? (
          <button
            onClick={submit}
            disabled={isSubmitting || !allAnswered}
            className="rounded-xl bg-emerald-600 hover:bg-emerald-500 transition-colors px-4 py-2 text-xs font-semibold text-white disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isSubmitting && <Loader2 size={13} className="animate-spin" />}
            {isSubmitting ? 'Submitting…' : 'Submit Quiz'}
          </button>
        ) : (
          <button
            onClick={() => onSend?.('continue')}
            className="rounded-xl bg-emerald-600 hover:bg-emerald-500 transition-colors px-4 py-2 text-xs font-semibold text-white flex items-center gap-2"
          >
            Continue Lesson
          </button>
        )}
        {result?.error ? (
          <div className="text-xs text-red-300">{result.error}</div>
        ) : result ? (
          <div className="text-xs font-semibold text-emerald-300">{scoreLine()}</div>
        ) : null}
      </div>
    </div>
  )
}

function NotesPanel({ enrollmentId }) {
  const storageKey = `homegrown:notes:${enrollmentId}`
  const [notes, setNotes] = useState(() => {
    try {
      return localStorage.getItem(storageKey) || ''
    } catch {
      return ''
    }
  })
  const [saved, setSaved] = useState(false)

  const save = () => {
    try {
      localStorage.setItem(storageKey, notes)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {
      // ignore
    }
  }

  return (
    <div className="rounded-2xl border border-white/8 bg-zinc-900/50 overflow-hidden">
      <div className="px-5 py-4 border-b border-white/8 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText size={15} className="text-emerald-400" />
          <span className="text-sm font-semibold text-zinc-100">Notes</span>
        </div>
        <button
          onClick={save}
          className={cx(
            'inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all',
            saved
              ? 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-300'
              : 'border border-white/10 bg-zinc-800/60 text-zinc-300 hover:bg-zinc-700/60'
          )}
        >
          {saved ? <CheckCircle2 size={13} /> : <Save size={13} />}
          {saved ? 'Saved!' : 'Save'}
        </button>
      </div>
      <div className="p-5">
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Write notes here… (saved to this device)"
          className="w-full min-h-40 rounded-xl bg-zinc-950/60 border border-white/8 p-3 text-sm text-zinc-200 placeholder:text-zinc-600 outline-none focus:ring-2 focus:ring-emerald-500/40 resize-none"
        />
        <p className="mt-2 text-[11px] text-zinc-600">
          Saved locally in your browser.
        </p>
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
    <div className="rounded-2xl border border-white/8 bg-zinc-900/50 overflow-hidden">
      <div className="px-5 py-4 border-b border-white/8 flex items-center gap-2">
        <Upload size={15} className="text-emerald-400" />
        <span className="text-sm font-semibold text-zinc-100">Upload Files</span>
        {isUploading && <Loader2 size={14} className="ml-auto animate-spin text-emerald-400" />}
      </div>

      <div className="p-5">
        <div className="flex items-center gap-2">
          <label className="flex-1 rounded-xl border border-dashed border-white/10 bg-zinc-950/40 px-3 py-2.5 text-xs text-zinc-400 cursor-pointer hover:border-emerald-500/30 hover:text-zinc-200 transition-colors truncate">
            <input
              type="file"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            {file ? (
              <span className="text-zinc-200 font-medium">{file.name}</span>
            ) : (
              <span>Choose a file…</span>
            )}
          </label>
          <button
            onClick={upload}
            disabled={!file || isUploading}
            className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 transition-colors px-3.5 py-2.5 text-xs font-semibold text-white disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Paperclip size={13} />
            Upload
          </button>
        </div>

        {error && (
          <div className="mt-3 rounded-xl border border-red-500/20 bg-red-500/8 px-3 py-2.5 text-xs text-red-300">
            {error}
          </div>
        )}

        {result?.ok && (
          <div className="mt-3 rounded-xl border border-emerald-500/20 bg-emerald-500/8 px-3 py-2.5 text-xs text-emerald-300 flex items-center gap-2">
            <CheckCircle2 size={13} />
            Uploaded <span className="font-semibold">{result.filename}</span>
          </div>
        )}

        <p className="mt-3 text-[11px] text-zinc-600">
          Files are stored on the server and logged to chat history.
        </p>
      </div>
    </div>
  )
}

export default function Workspace({ enrollment, onBack }) {
  const [messages, setMessages] = useState([])
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
    let cancelled = false

    async function loadHistory() {
      try {
        const res = await api.get('/chat/history', {
          params: { enrollment_id: enrollment.enrollment_id, limit: 100 },
        })

        if (cancelled) return

        const items = res.data?.items || []
        if (items.length > 0) {
          const mapped = items.map((i) => {
            if (i.sender === 'agent') {
              try {
                const parsed = JSON.parse(i.content)
                if (parsed && Array.isArray(parsed.blocks)) {
                  return { sender: 'agent', blocks: parsed.blocks }
                }
              } catch {
                // ignore
              }
            }
            return { sender: i.sender, blocks: [{ type: 'markdown', text: i.content }] }
          })
          setMessages(mapped)
          return
        }
      } catch {
        if (cancelled) return
      }

      setMessages([
        {
          sender: 'agent',
          blocks: [{ type: 'markdown', text: `Welcome back! You're in **${enrollment.course_title || 'your course'}**. Let's get started.` }],
        },
      ])
    }

    loadHistory()
    return () => {
      cancelled = true
    }
  }, [enrollment.enrollment_id, enrollment.course_title])

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
  }, [messages, isLoading])

  const courseLabel = useMemo(() => {
    const parts = []
    if (enrollment.agent_name) parts.push(enrollment.agent_name)
    if (enrollment.course_title) parts.push(enrollment.course_title)
    return parts.join(' · ') || 'Homegrown'
  }, [enrollment])

  const resetSession = async () => {
    if (isLoading) return
    setIsLoading(true)
    try {
      await api.post('/chat/reset', null, {
        params: { enrollment_id: enrollment.enrollment_id },
      })
      setInput('')
      setMessages([
        {
          sender: 'system',
          blocks: [{ type: 'markdown', text: `Session reset. Say hello when you're ready to start fresh.` }],
        },
      ])

      setWorkspace((prev) => ({
        ...prev,
        status: 'In Progress',
        moduleIndex: 0,
      }))
    } catch {
      setMessages((prev) => [
        ...prev,
        { sender: 'system', blocks: [{ type: 'markdown', text: 'Could not reset. Is the backend running?' }] },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const sendChat = async (rawMsg) => {
    const msg = (rawMsg || '').trim()
    if (!msg || isLoading) return

    setMessages((prev) => [...prev, { sender: 'student', blocks: [{ type: 'markdown', text: msg }] }])
    setIsLoading(true)

    try {
      const res = await api.post('/chat', {
        enrollment_id: enrollment.enrollment_id,
        message: msg,
      })

      const blocks = res.data?.blocks || [{ type: 'markdown', text: '' }]
      setMessages((prev) => [...prev, { sender: 'agent', blocks }])

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
        { sender: 'system', blocks: [{ type: 'markdown', text: 'Connection error. Is the backend running?' }] },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const sendMessage = async () => {
    const msg = input.trim()
    if (!msg || isLoading) return
    setInput('')
    await sendChat(msg)
  }

  const progressPercent = workspace.totalModules
    ? Math.round(((workspace.moduleIndex) / workspace.totalModules) * 100)
    : null

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 overflow-y-auto" style={{ background: 'radial-gradient(ellipse 80% 40% at 50% -5%, rgba(16,185,129,0.08) 0%, transparent 60%), #09090b' }}>
      {/* ── Header ── */}
      <div className="sticky top-0 z-10 border-b border-white/8 bg-zinc-950/90 backdrop-blur-md">
        <div className="flex items-center gap-3 px-4 py-3">
          <button
            onClick={onBack}
            className="h-9 w-9 rounded-xl border border-white/10 bg-zinc-900/60 hover:bg-zinc-800/60 flex items-center justify-center transition-colors shrink-0"
            title="Back"
          >
            <ArrowLeft size={16} className="text-zinc-300" />
          </button>

          <div className="h-9 w-9 rounded-xl bg-emerald-500/15 border border-emerald-500/20 flex items-center justify-center shrink-0">
            <Bot size={18} className="text-emerald-400" />
          </div>

          <div className="min-w-0 flex-1">
            <div className="text-sm font-semibold text-zinc-100 truncate">{courseLabel}</div>
            <div className="text-[11px] text-zinc-500 truncate">
              {workspace.title}
              {typeof workspace.moduleIndex === 'number' && workspace.totalModules
                ? ` · Module ${workspace.moduleIndex + 1} / ${workspace.totalModules}`
                : ''}
            </div>
          </div>

          <button
            onClick={resetSession}
            disabled={isLoading}
            className="ml-auto rounded-xl border border-white/10 bg-zinc-900/60 hover:bg-zinc-800/60 px-3 py-2 text-xs text-zinc-400 hover:text-zinc-200 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 transition-colors shrink-0"
            title="Start over with a clean chat history"
          >
            <RotateCcw size={13} />
            <span className="hidden sm:inline">Start Fresh</span>
          </button>
        </div>
      </div>

      {/* ── Chat ── */}
      <div className="flex flex-col" style={{ minHeight: 'calc(100vh - 57px)' }}>
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6 space-y-4" style={{ maxHeight: '65vh', minHeight: '300px' }}>
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={cx('flex items-end gap-2.5', m.sender === 'student' ? 'flex-row-reverse' : 'flex-row')}
            >
              {/* Avatar */}
              {m.sender !== 'student' && (
                <div className={cx(
                  'shrink-0 h-7 w-7 rounded-full flex items-center justify-center mb-0.5',
                  m.sender === 'system' ? 'bg-zinc-800 border border-white/8' : 'bg-emerald-500/20 border border-emerald-500/20'
                )}>
                  {m.sender === 'system' ? (
                    <Circle size={12} className="text-zinc-500" />
                  ) : (
                    <Bot size={14} className="text-emerald-400" />
                  )}
                </div>
              )}
              {m.sender === 'student' && (
                <div className="shrink-0 h-7 w-7 rounded-full bg-zinc-700/60 border border-white/8 flex items-center justify-center mb-0.5">
                  <User size={14} className="text-zinc-300" />
                </div>
              )}

              <div
                className={cx(
                  'max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
                  m.sender === 'student'
                    ? 'bg-emerald-600/25 border border-emerald-500/25 text-emerald-50 rounded-br-sm'
                    : m.sender === 'system'
                      ? 'bg-zinc-900/80 border border-white/8 text-zinc-400 italic rounded-bl-sm'
                      : 'bg-zinc-900 border border-white/8 text-zinc-200 rounded-bl-sm',
                )}
              >
                {(m.blocks || []).map((b, bi) => {
                  if (b.type === 'mcq_quiz') {
                    return (
                      <div key={bi} className={bi === 0 ? '' : 'mt-3'}>
                        <McqQuizBlock enrollmentId={enrollment.enrollment_id} block={b} onSend={sendChat} />
                      </div>
                    )
                  }
                  return (
                    <div key={bi} className={bi > 0 ? 'mt-2' : ''}>
                      <ReactMarkdown>{b.text || ''}</ReactMarkdown>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}

          {isLoading && <TypingIndicator />}
        </div>

        {/* Input */}
        <div className="border-t border-white/8 bg-zinc-950/60 px-4 py-4 backdrop-blur-sm">
          <div className="mx-auto max-w-3xl">
            <div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-zinc-900/80 px-3 py-2 focus-within:ring-2 focus-within:ring-emerald-500/40 focus-within:border-emerald-500/30 transition-all">
              <button className="p-1.5 text-zinc-500 hover:text-zinc-300 transition-colors mb-0.5" title="Attach">
                <Paperclip size={17} />
              </button>
              <textarea
                value={input}
                onChange={(e) => {
                  setInput(e.target.value)
                  e.target.style.height = 'auto'
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    sendMessage()
                  }
                }}
                placeholder="Message your instructor… (Enter to send)"
                rows={1}
                className="flex-1 bg-transparent outline-none text-sm text-zinc-100 placeholder:text-zinc-600 resize-none py-1.5 max-h-30"
                disabled={isLoading}
                style={{ minHeight: '36px' }}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="p-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors mb-0.5 shrink-0"
                title="Send"
              >
                <Send size={15} className="text-white" />
              </button>
            </div>
            <p className="mt-1.5 text-center text-[11px] text-zinc-700">Shift+Enter for newline</p>
          </div>
        </div>

        {/* ── Below-chat sections ── */}
        <div className="mx-auto w-full max-w-5xl px-4 sm:px-6 py-8 space-y-6">
          {/* Module info */}
          <div className="rounded-2xl border border-white/8 bg-zinc-900/50 overflow-hidden">
            <div className="px-6 py-5 border-b border-white/8">
              <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-emerald-400/70 mb-3">
                <BookOpen size={12} />
                Current Module
              </div>
              <div className="flex items-start justify-between gap-4">
                <h2 className="text-xl font-bold text-zinc-100">{workspace.title}</h2>
                {workspace.status && (
                  <span className={cx(
                    'shrink-0 rounded-full px-2.5 py-1 text-[11px] font-semibold',
                    workspace.status === 'Complete'
                      ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/25'
                      : 'bg-zinc-800 text-zinc-400 border border-white/8'
                  )}>
                    {workspace.status}
                  </span>
                )}
              </div>

              {/* Progress bar */}
              {progressPercent !== null && (
                <div className="mt-3">
                  <div className="flex items-center justify-between text-[11px] text-zinc-500 mb-1.5">
                    <span>Progress</span>
                    <span>Module {workspace.moduleIndex + 1} of {workspace.totalModules}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all duration-500"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="px-6 py-5">
              <div className="rounded-xl border border-emerald-500/15 bg-emerald-500/5 p-4">
                <div className="text-[11px] uppercase tracking-widest font-bold text-emerald-400/70 mb-2">Objective</div>
                <p className="text-sm text-zinc-300 leading-relaxed">{workspace.objective}</p>
              </div>
            </div>
          </div>

          {/* Upload & Notes */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <UploadPanel enrollmentId={enrollment.enrollment_id} />
            <NotesPanel key={enrollment.enrollment_id} enrollmentId={enrollment.enrollment_id} />
          </div>
        </div>
      </div>
    </div>
  )
}
