import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base = URL de l'app dans le portail (/RHEUROPE/) : obligatoire.
// En dev (npm run dev), les appels /RHEUROPE/api partent vers le portail local
// lancé par outils/lancer-en-local.ps1 (port 8000).
export default defineConfig({
  base: '/RHEUROPE/',
  plugins: [react()],
  server: {
    proxy: { '/RHEUROPE/api': 'http://localhost:8000' },
  },
})
