import axios from 'axios';

// Create a configured axios instance
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

// A variable to hold the token retrieval function injected by the Auth0Provider hook wrapper
let getToken: (() => Promise<string>) | null = null;

export const setAuthTokenGetter = (getter: () => Promise<string>) => {
  getToken = getter;
};

// Add a request interceptor to inject the token
api.interceptors.request.use(
  async (config) => {
    if (getToken) {
      try {
        const token = await getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      } catch (e) {
        console.error("Failed to acquire token:", e);
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
