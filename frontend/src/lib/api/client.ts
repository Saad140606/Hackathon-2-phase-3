import axios from 'axios';

const apiClient = axios.create({
  // Use environment variable in production; fallback to deployed Space for safety
  baseURL:
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    'https://saad146-todo-phase-3.hf.space',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

export default apiClient;
