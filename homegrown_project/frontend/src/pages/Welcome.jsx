import { useEffect, useMemo, useState } from 'react'
import { BookOpen, ChevronRight, Loader2 } from 'lucide-react'
import { api } from '../lib/api'

function EnrollmentOption({ enrollment }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="min-w-0">
        <div className="text-sm font-semibold text-emerald-100 truncate">
          {enrollment.course_title || 'Untitled Course'}
        </div>
        <div className="text-xs text-emerald-200/70 truncate">
          {enrollment.agent_name ? `${enrollment.agent_name} • ` : ''}
          {typeof enrollment.current_module_index === 'number' ? `Module ${enrollment.current_module_index + 1}` : 'Module ?'}
          {typeof enrollment.total_modules === 'number' ? ` / ${enrollment.total_modules}` : ''}
        </div>
      </div>
      <ChevronRight size={18} className="text-emerald-300/80" />
    </div>
  )
}

export default function Welcome({ onSelectEnrollment }) {
  const [enrollments, setEnrollments] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  const lastEnrollmentKey = 'homegrown:last_enrollment_id'

  const selected = useMemo(
    () => enrollments.find((e) => String(e.enrollment_id) === String(selectedId)) || null,
    [enrollments, selectedId],
  )

  useEffect(() => {
    let cancelled = false

    async function load() {
      setIsLoading(true)
      setError(null)
      try {
        const res = await api.get('/enrollments')
        if (cancelled) return
        const list = res.data || []
        setEnrollments(list)

        if (list.length > 0) {
          let preferredId = String(list[0].enrollment_id)
          try {
            const stored = localStorage.getItem(lastEnrollmentKey)
            if (stored && list.some((e) => String(e.enrollment_id) === String(stored))) {
              preferredId = String(stored)
            }
          } catch {
            // ignore
          }
          setSelectedId(preferredId)
        }
      } catch {
        if (cancelled) return
        setError('Could not load enrollments. Is the backend running?')
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="min-h-screen bg-linear-to-br from-zinc-950 via-zinc-950 to-emerald-950 text-zinc-100">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <div className="flex items-center gap-3">
          <div className="h-11 w-11 rounded-xl bg-emerald-500/15 border border-emerald-500/20 flex items-center justify-center">
            <BookOpen size={20} className="text-emerald-300" />
          </div>
          <div>
            <div className="text-2xl font-bold tracking-tight">Homegrown</div>
            <div className="text-sm text-emerald-200/70">Choose a course to enter your workspace.</div>
          </div>
        </div>

        <div className="mt-10 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-white/10 bg-white/5 shadow-xl shadow-emerald-900/10 overflow-hidden">
            <div className="p-5 border-b border-white/10">
              <div className="text-sm font-semibold text-emerald-100">Welcome</div>
              <div className="text-xs text-emerald-200/70 mt-1">
                This is a local prototype. No login yet — pick an enrollment and start learning.
              </div>
            </div>
            <div className="p-5 text-sm text-zinc-200/90 leading-relaxed">
              <div className="rounded-xl border border-emerald-500/15 bg-emerald-500/5 p-4">
                <div className="text-emerald-200 font-semibold">What you can do</div>
                <div className="mt-2 text-xs text-emerald-100/70">
                  Chat with your tutor, track module objectives, upload files for grading, and keep personal notes saved to your device.
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 shadow-xl shadow-emerald-900/10 overflow-hidden">
            <div className="p-5 border-b border-white/10 flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-emerald-100">Your Enrollments</div>
                <div className="text-xs text-emerald-200/70 mt-1">Select a course to open your workspace.</div>
              </div>
              {isLoading && <Loader2 size={18} className="animate-spin text-emerald-300" />}
            </div>

            <div className="p-5">
              {error && (
                <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-200">
                  {error}
                </div>
              )}

              <label className="block text-xs text-emerald-200/70">Enrollment</label>
              <select
                value={selectedId}
                onChange={(e) => setSelectedId(e.target.value)}
                className="mt-2 w-full rounded-xl bg-zinc-950/40 border border-white/10 px-3 py-2 text-sm text-zinc-100 outline-none focus:ring-2 focus:ring-emerald-500/40"
                disabled={isLoading}
              >
                {enrollments.map((e) => (
                  <option key={e.enrollment_id} value={String(e.enrollment_id)}>
                    {(e.course_title || 'Untitled Course') + (e.agent_name ? ` — ${e.agent_name}` : '')}
                  </option>
                ))}
              </select>

              <div className="mt-4 rounded-xl border border-white/10 bg-zinc-950/30 p-4">
                {selected ? (
                  <EnrollmentOption enrollment={selected} />
                ) : (
                  <div className="text-xs text-zinc-400">No enrollment selected.</div>
                )}
              </div>

              <button
                onClick={() => {
                  if (!selected) return
                  try {
                    localStorage.setItem(lastEnrollmentKey, String(selected.enrollment_id))
                  } catch {
                    // ignore
                  }
                  onSelectEnrollment(selected)
                }}
                disabled={!selected || isLoading}
                className="mt-4 w-full rounded-xl bg-emerald-500/20 border border-emerald-500/30 hover:bg-emerald-500/25 transition-colors px-4 py-3 text-sm font-semibold text-emerald-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Enter Workspace
              </button>

              <div className="mt-3 text-[11px] text-emerald-200/60">
                Tip: If you don’t see any enrollments, run the backend seed script and refresh.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
