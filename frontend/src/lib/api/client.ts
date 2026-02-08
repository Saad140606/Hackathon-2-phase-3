import axios from 'axios';

const apiClient = axios.create({
  // Always use the deployed Hugging Face Space backend for API calls
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

// Log the resolved API base at runtime so deployed builds can be verified
if (typeof window !== 'undefined') {
 
  console.log('API_BASE:', apiClient.defaults.baseURL);
}

export default apiClient;
