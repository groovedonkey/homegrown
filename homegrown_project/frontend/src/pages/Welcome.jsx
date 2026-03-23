import { useEffect, useMemo, useState } from 'react'
import { BookOpen, ChevronRight, Loader2, GraduationCap, Sparkles } from 'lucide-react'
import { api, API_ORIGIN } from '../lib/api'

export default function Welcome({ onSelectEnrollment }) {
  const [instructors, setInstructors] = useState([])
  const [courses, setCourses] = useState([])
  const [selectedInstructorId, setSelectedInstructorId] = useState('')
  const [selectedCourseId, setSelectedCourseId] = useState('')
  const [intro, setIntro] = useState('')
  const [isIntroLoading, setIsIntroLoading] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isEntering, setIsEntering] = useState(false)
  const [error, setError] = useState(null)

  const lastInstructorKey = 'homegrown:last_instructor_id'
  const lastCourseKey = 'homegrown:last_course_id'

  const selectedInstructor = useMemo(
    () => instructors.find((i) => String(i.agent_id) === String(selectedInstructorId)) || null,
    [instructors, selectedInstructorId],
  )

  const selectedCourse = useMemo(
    () => courses.find((c) => String(c.course_id) === String(selectedCourseId)) || null,
    [courses, selectedCourseId],
  )

  useEffect(() => {
    let cancelled = false

    async function load() {
      setIsLoading(true)
      setError(null)
      try {
        const res = await api.get('/instructors')
        if (cancelled) return
        const list = res.data || []
        setInstructors(list)

        if (list.length > 0) {
          let preferredId = String(list[0].agent_id)
          try {
            const stored = localStorage.getItem(lastInstructorKey)
            if (stored && list.some((i) => String(i.agent_id) === String(stored))) {
              preferredId = String(stored)
            }
          } catch {
            // ignore
          }
          setSelectedInstructorId(preferredId)
        }
      } catch {
        if (cancelled) return
        setError('Could not load instructors. Is the backend running?')
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function loadCourses() {
      if (!selectedInstructorId) {
        setCourses([])
        setSelectedCourseId('')
        setIntro('')
        return
      }

      setIsLoading(true)
      setError(null)
      try {
        const res = await api.get(`/instructors/${selectedInstructorId}/courses`)
        if (cancelled) return
        const list = res.data || []
        setCourses(list)

        if (list.length > 0) {
          let preferredCourse = String(list[0].course_id)
          try {
            const stored = localStorage.getItem(lastCourseKey)
            if (stored && list.some((c) => String(c.course_id) === String(stored))) {
              preferredCourse = String(stored)
            }
          } catch {
            // ignore
          }
          setSelectedCourseId(preferredCourse)
        } else {
          setSelectedCourseId('')
        }
      } catch {
        if (cancelled) return
        setError('Could not load courses for that instructor.')
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    loadCourses()
    return () => {
      cancelled = true
    }
  }, [selectedInstructorId])

  useEffect(() => {
    let cancelled = false

    async function loadIntro() {
      if (!selectedInstructorId) {
        setIntro('')
        return
      }

      setIsIntroLoading(true)
      try {
        const res = await api.get(`/instructors/${selectedInstructorId}/intro`)
        if (cancelled) return
        setIntro(res.data?.intro || '')
      } catch {
        if (cancelled) return
        setIntro('')
      } finally {
        if (!cancelled) setIsIntroLoading(false)
      }
    }

    loadIntro()
    return () => {
      cancelled = true
    }
  }, [selectedInstructorId])

  const canEnter = !!(selectedInstructorId && selectedCourseId && !isLoading && !isEntering)

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100" style={{ background: 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(16,185,129,0.12) 0%, transparent 70%), linear-gradient(to bottom right, #09090b, #09090b, #052e16)' }}>
      <div className="mx-auto max-w-2xl px-4 sm:px-6 py-10 sm:py-16">

        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/25 shadow-lg shadow-emerald-900/30 mb-5">
            <BookOpen size={28} className="text-emerald-400" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-b from-zinc-100 to-zinc-400 bg-clip-text text-transparent">
            Homegrown
          </h1>
          <p className="mt-3 text-sm sm:text-base text-zinc-400">
            Your personal AI-powered learning studio
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300 flex items-center gap-2">
            <span className="shrink-0 h-1.5 w-1.5 rounded-full bg-red-400"></span>
            {error}
          </div>
        )}

        {/* Selection Card */}
        <div className="rounded-2xl border border-white/8 bg-white/[0.03] shadow-2xl shadow-black/40 overflow-hidden">
          <div className="p-6 sm:p-8 space-y-6">

            {/* Instructor */}
            <div>
              <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-emerald-400/80 mb-2.5">
                <GraduationCap size={13} />
                Instructor
                {isLoading && <Loader2 size={13} className="animate-spin ml-1 text-emerald-500/60" />}
              </label>
              <div className="relative">
                <select
                  value={selectedInstructorId}
                  onChange={(e) => {
                    const next = e.target.value
                    setSelectedInstructorId(next)
                    setSelectedCourseId('')
                    setIntro('')
                    try {
                      localStorage.setItem(lastInstructorKey, String(next))
                    } catch {
                      // ignore
                    }
                  }}
                  className="w-full appearance-none rounded-xl bg-zinc-900 border border-white/10 px-4 py-3 text-sm text-zinc-100 outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all disabled:opacity-40 disabled:cursor-not-allowed pr-10"
                  disabled={isLoading}
                >
                  {instructors.map((i) => (
                    <option key={i.agent_id} value={String(i.agent_id)}>
                      {i.agent_name || 'Unnamed Instructor'}
                    </option>
                  ))}
                </select>
                <ChevronRight size={15} className="absolute right-3 top-1/2 -translate-y-1/2 rotate-90 text-zinc-500 pointer-events-none" />
              </div>
            </div>

            {/* Instructor Card */}
            {(isIntroLoading || intro || selectedInstructor) && (
              <div className="rounded-xl border border-white/8 bg-zinc-900/60 overflow-hidden">
                <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5 p-5">
                  {selectedInstructor?.avatar_url ? (
                    <img
                      src={`${API_ORIGIN}${selectedInstructor.avatar_url}`}
                      alt={selectedInstructor.agent_name || 'Instructor avatar'}
                      className="h-20 w-20 sm:h-24 sm:w-24 rounded-xl border border-emerald-500/20 bg-zinc-950/50 object-cover shrink-0"
                      loading="lazy"
                    />
                  ) : (
                    <div className="h-20 w-20 sm:h-24 sm:w-24 rounded-xl border border-white/10 bg-zinc-800/60 flex items-center justify-center shrink-0">
                      <GraduationCap size={32} className="text-zinc-500" />
                    </div>
                  )}
                  <div className="min-w-0 text-center sm:text-left">
                    <div className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-emerald-400/70 mb-1">
                      <Sparkles size={10} />
                      AI Instructor
                    </div>
                    <h2 className="text-lg font-bold text-zinc-100">
                      {selectedInstructor?.agent_name || 'Select an Instructor'}
                    </h2>
                    <p className="mt-2 text-sm text-zinc-400 leading-relaxed whitespace-pre-wrap">
                      {isIntroLoading ? (
                        <span className="italic text-zinc-500">Loading introduction…</span>
                      ) : (
                        intro
                      )}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Course */}
            <div>
              <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-emerald-400/80 mb-2.5">
                <BookOpen size={13} />
                Course
              </label>
              <div className="relative">
                <select
                  value={selectedCourseId}
                  onChange={(e) => {
                    const next = e.target.value
                    setSelectedCourseId(next)
                    try {
                      localStorage.setItem(lastCourseKey, String(next))
                    } catch {
                      // ignore
                    }
                  }}
                  className="w-full appearance-none rounded-xl bg-zinc-900 border border-white/10 px-4 py-3 text-sm text-zinc-100 outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all disabled:opacity-40 disabled:cursor-not-allowed pr-10"
                  disabled={isLoading || !selectedInstructorId}
                >
                  {courses.length === 0 && (
                    <option value="">No courses available</option>
                  )}
                  {courses.map((c) => (
                    <option key={c.course_id} value={String(c.course_id)}>
                      {c.course_title || 'Untitled Course'}
                    </option>
                  ))}
                </select>
                <ChevronRight size={15} className="absolute right-3 top-1/2 -translate-y-1/2 rotate-90 text-zinc-500 pointer-events-none" />
              </div>
              {selectedCourse && (
                <p className="mt-2 text-xs text-zinc-500">{selectedCourse.course_description}</p>
              )}
            </div>
          </div>

          {/* CTA */}
          <div className="px-6 sm:px-8 pb-6 sm:pb-8">
            <button
              onClick={async () => {
                if (!canEnter) return
                setIsEntering(true)
                setError(null)
                try {
                  const res = await api.post('/classroom/enter', null, {
                    params: {
                      agent_id: selectedInstructorId,
                      course_id: selectedCourseId,
                    },
                  })
                  onSelectEnrollment(res.data)
                } catch {
                  setError('Could not enter classroom.')
                } finally {
                  setIsEntering(false)
                }
              }}
              disabled={!canEnter}
              className="w-full rounded-xl bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 transition-colors px-5 py-3.5 text-sm font-semibold text-white shadow-lg shadow-emerald-900/40 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isEntering ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Entering…
                </>
              ) : (
                <>
                  Enter Classroom
                  <ChevronRight size={16} />
                </>
              )}
            </button>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-zinc-600">
          Powered by Homegrown AI
        </p>
      </div>
    </div>
  )
}
