// Petites fonctions partagées : dates, libellés des référentiels, recherche.

export function dateFr(iso) {
  if (!iso) return ''
  const [a, m, j] = String(iso).slice(0, 10).split('-')
  return a && m && j ? `${j}/${m}/${a}` : iso
}

export function dateHeureFr(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d)) return iso
  return d.toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export function joursAvant(iso, aujourdhui) {
  if (!iso) return null
  const a = new Date(String(aujourdhui).slice(0, 10) + 'T00:00:00')
  const b = new Date(String(iso).slice(0, 10) + 'T00:00:00')
  return Math.round((b - a) / 86400000)
}

export const sansAccents = (t) => String(t || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

export function libelle(refs, type, code) {
  if (!code) return ''
  const e = (refs?.[type] || []).find((x) => x.code === code)
  return e ? e.libelle : code
}

export function nomComplet(c) {
  return c ? `${c.prenom || ''} ${c.nom || ''}`.trim() : ''
}

export function pluriel(n, singulier, pluriel_) {
  return `${n.toLocaleString('fr-FR')} ${n > 1 ? (pluriel_ || singulier + 's') : singulier}`
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
