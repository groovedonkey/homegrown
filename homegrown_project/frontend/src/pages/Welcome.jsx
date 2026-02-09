import { useEffect, useMemo, useState } from 'react'
import { BookOpen, ChevronRight, Loader2 } from 'lucide-react'
import { api, API_ORIGIN } from '../lib/api'

export default function Welcome({ onSelectEnrollment }) {
  const [instructors, setInstructors] = useState([])
  const [courses, setCourses] = useState([])
  const [selectedInstructorId, setSelectedInstructorId] = useState('')
  const [selectedCourseId, setSelectedCourseId] = useState('')
  const [intro, setIntro] = useState('')
  const [isIntroLoading, setIsIntroLoading] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
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

  return (
    <div className="min-h-screen bg-linear-to-br from-zinc-950 via-zinc-950 to-emerald-950 text-zinc-100">
      <div className="mx-auto max-w-3xl px-4 sm:px-6 py-8 sm:py-14">

        {/* Header */}
        <div className="text-center">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/15 border border-emerald-500/20">
            <BookOpen size={26} className="text-emerald-300" />
          </div>
          <h1 className="mt-4 text-3xl sm:text-4xl font-bold tracking-tight">Homegrown</h1>
          <p className="mt-2 text-sm sm:text-base text-emerald-200/60">Choose your instructor and course to get started.</p>
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200 text-center">
            {error}
          </div>
        )}

        {/* Instructor Selection */}
        <div className="mt-10">
          <label className="block text-xs font-semibold uppercase tracking-wider text-emerald-200/70">
            Instructor {isLoading && <Loader2 size={14} className="inline animate-spin ml-2" />}
          </label>
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
            className="mt-2 w-full rounded-xl bg-zinc-900/80 border border-white/10 px-4 py-3 text-base text-zinc-100 outline-none focus:ring-2 focus:ring-emerald-500/40 transition-shadow"
            disabled={isLoading}
          >
            {instructors.map((i) => (
              <option key={i.agent_id} value={String(i.agent_id)}>
                {i.agent_name || 'Unnamed Instructor'}
              </option>
            ))}
          </select>
        </div>

        {/* Instructor Card */}
        {(isIntroLoading || intro || selectedInstructor) && (
          <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 shadow-xl shadow-emerald-900/10 overflow-hidden">
            <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 p-6">
              {selectedInstructor?.avatar_url && (
                <img
                  src={`${API_ORIGIN}${selectedInstructor.avatar_url}`}
                  alt={selectedInstructor.agent_name || 'Instructor avatar'}
                  className="h-44 w-44 sm:h-48 sm:w-48 rounded-2xl border-2 border-emerald-500/20 bg-zinc-950/30 object-cover shrink-0 shadow-lg shadow-emerald-900/20"
                  loading="lazy"
                />
              )}
              <div className="min-w-0 text-center sm:text-left">
                <h2 className="text-xl font-bold text-emerald-100">
                  {selectedInstructor?.agent_name || 'Select an Instructor'}
                </h2>
                <div className="mt-3 text-sm text-emerald-100/80 leading-relaxed whitespace-pre-wrap">
                  {isIntroLoading ? (
                    <span className="text-emerald-200/50 italic">Loading introduction…</span>
                  ) : (
                    intro
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Course Selection */}
        <div className="mt-8">
          <label className="block text-xs font-semibold uppercase tracking-wider text-emerald-200/70">Course</label>
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
            className="mt-2 w-full rounded-xl bg-zinc-900/80 border border-white/10 px-4 py-3 text-base text-zinc-100 outline-none focus:ring-2 focus:ring-emerald-500/40 transition-shadow"
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
        </div>

        {/* Enter Classroom Button */}
        <button
          onClick={async () => {
            if (!selectedInstructorId || !selectedCourseId) return
            setIsLoading(true)
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
              setIsLoading(false)
            }
          }}
          disabled={!selectedInstructorId || !selectedCourseId || isLoading}
          className="mt-6 w-full rounded-xl bg-emerald-600 hover:bg-emerald-500 transition-colors px-4 py-4 text-base font-semibold text-white shadow-lg shadow-emerald-900/30 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          Enter Classroom
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  )
}
