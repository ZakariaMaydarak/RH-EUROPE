// Petites fonctions partagées. Dates, nombres et libellés traduits : voir i18n.js (useT).

export function joursAvant(iso, aujourdhui) {
  if (!iso) return null
  const a = new Date(String(aujourdhui).slice(0, 10) + 'T00:00:00')
  const b = new Date(String(iso).slice(0, 10) + 'T00:00:00')
  return Math.round((b - a) / 86400000)
}

export const sansAccents = (t) => String(t || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

export function nomComplet(c) {
  return c ? `${c.prenom || ''} ${c.nom || ''}`.trim() : ''
}

// Navigation par l'ancre (#/route?param=valeur) : liens partageables, retour arrière du navigateur.
export function lireRoute() {
  const brut = window.location.hash.replace(/^#/, '') || '/tableau-de-bord'
  const [chemin, q] = brut.split('?')
  return { chemin, parties: chemin.split('/').filter(Boolean), params: Object.fromEntries(new URLSearchParams(q || '')) }
}

export function naviguer(chemin) {
  window.location.hash = chemin
}
