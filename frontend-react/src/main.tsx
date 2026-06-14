import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Auth0Provider } from '@auth0/auth0-react'
import './index.css'
import App from './App.tsx'

const domain = import.meta.env.VITE_AUTH0_DOMAIN || "dev-k05s7ohpn7hhcrxg.us.auth0.com";
const clientId = import.meta.env.VITE_AUTH0_CLIENT_ID || "kIhQb16gH2imFhq7OMwB7Ss6GYk2xwgX";
const audience = import.meta.env.VITE_AUTH0_AUDIENCE || "https://api.airecruiter.local";

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: audience,
        scope: "openid profile email"
      }}
    >
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </Auth0Provider>
  </StrictMode>,
)
