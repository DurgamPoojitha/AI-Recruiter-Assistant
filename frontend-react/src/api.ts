import axios from 'axios';

// Create a configured axios instance
// Configurable via VITE_API_BASE_URL (AWS Production ALB/EC2 URL) with localhost fallback
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000',
});
