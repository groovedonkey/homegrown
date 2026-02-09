import axios from 'axios'

const useNetlifyProxy =
  import.meta.env.VITE_USE_NETLIFY_PROXY === '1'

export const API_BASE_URL = useNetlifyProxy
  ? '/api'
  : import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

export const API_ORIGIN = useNetlifyProxy
  ? ''
  : import.meta.env.VITE_API_BASE_URL?.replace(/\/api\/?$/, '') || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
})
