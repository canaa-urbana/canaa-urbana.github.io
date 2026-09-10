import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import 'maplibre-gl/dist/maplibre-gl.css'
import './styles/ardosia.css'
import './styles/app.css'
import App from './App'
import { TemaProvider } from './lib/theme'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <TemaProvider>
      <App />
    </TemaProvider>
  </StrictMode>,
)
