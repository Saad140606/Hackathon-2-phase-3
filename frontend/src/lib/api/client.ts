import axios from 'axios';

const apiClient = axios.create({
  // Always use the deployed Hugging Face Space backend for API calls
  baseURL: 'https://saad146-todo-phase-3.hf.space',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

export default apiClient;
