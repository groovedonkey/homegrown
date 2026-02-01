import { useEffect, useState } from 'react'
import Welcome from './pages/Welcome.jsx'
import Workspace from './pages/Workspace.jsx'

function getRoute() {
  const hash = window.location.hash || '#/'
  if (hash.startsWith('#/workspace')) return 'workspace'
  return 'welcome'
}

export default function App() {
  const [route, setRoute] = useState(getRoute())
  const [selectedEnrollment, setSelectedEnrollment] = useState(null)

  useEffect(() => {
    const onHashChange = () => setRoute(getRoute())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const goWelcome = () => {
    window.location.hash = '#/'
  }

  const goWorkspace = (enrollment) => {
    setSelectedEnrollment(enrollment)
    window.location.hash = '#/workspace'
  }

  if (route === 'workspace' && selectedEnrollment) {
    return <Workspace enrollment={selectedEnrollment} onBack={goWelcome} />
  }

  return <Welcome onSelectEnrollment={goWorkspace} />
}