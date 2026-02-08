import axios from 'axios';

const apiClient = axios.create({
  // Use `NEXT_PUBLIC_API_URL` when provided (Vercel env var). Fall back to
  // the deployed Hugging Face Space backend so the sites remain connected.
  baseURL:
    process.env.NEXT_PUBLIC_API_URL || "https://saad146-phase-3.hf.space",
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

// Log the resolved API base at runtime so deployed builds can be verified
if (typeof window !== 'undefined') {
 
  console.log('API_BASE:', apiClient.defaults.baseURL);
}

export default apiClient;
