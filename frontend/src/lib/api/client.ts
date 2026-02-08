import axios from 'axios';

const apiClient = axios.create({
  // Always use the deployed Hugging Face Space backend for API calls
  baseURL: 'https://saad146-todo-phase-3.hf.space',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

// Log the resolved API base at runtime so deployed builds can be verified
if (typeof window !== 'undefined') {
  // eslint-disable-next-line no-console
  console.log('API_BASE:', apiClient.defaults.baseURL);
}

export default apiClient;
