// Langue d'affichage : le texte français sert de clé, traductions dans traductions.js.
// t('Bonjour {nom}', { nom }) ; tn(n, '{n} collaborateur', '{n} collaborateurs').
import { createContext, useContext } from 'react'
import DICO from './traductions.js'

export const LANGUES = { fr: 'Français', en: 'English', de: 'Deutsch', es: 'Español', it: 'Italiano' }
const ORDRE = ['en', 'de', 'es', 'it']
const LOCALES = { fr: 'fr-FR', en: 'en-GB', de: 'de-DE', es: 'es-ES', it: 'it-IT' }
const CLE_STOCKAGE = 'rheurope.langue'

export function langueInitiale() {
  try {
    const memo = localStorage.getItem(CLE_STOCKAGE)
    if (memo && LANGUES[memo]) return memo
  } catch { /* stockage indisponible : on continue */ }
  const nav = (navigator.language || 'fr').slice(0, 2).toLowerCase()
  return LANGUES[nav] ? nav : 'fr'
}

export function memoriserLangue(langue) {
  try { localStorage.setItem(CLE_STOCKAGE, langue) } catch { /* sans effet */ }
}

export function creerOutils(langue) {
  const i = ORDRE.indexOf(langue)
  const locale = LOCALES[langue] || 'fr-FR'
  const t = (texte, params) => {
    let s = i >= 0 ? (DICO[texte]?.[i] || texte) : texte
    if (params) s = s.replace(/\{(\w+)\}/g, (m, k) => (params[k] ?? m))
    return s
  }
  const nombre = (n) => Number(n || 0).toLocaleString(locale)
  // Pluriel : en français 0 et 1 sont au singulier, dans les autres langues seul 1 l'est.
  const tn = (n, singulier, pluriel, params) =>
    t((langue === 'fr' ? n > 1 : n !== 1) ? pluriel : singulier, { n: nombre(n), ...params })
  const nomRef = (e) => (e ? (langue !== 'fr' && e.traductions?.[langue]) || e.libelle : '')
  const ref = (refs, type, code) => {
    if (!code) return ''
    const e = (refs?.[type] || []).find((x) => x.code === code)
    return e ? nomRef(e) : code
  }
  const date = (iso) => {
    if (!iso) return ''
    const [a, m, j] = String(iso).slice(0, 10).split('-').map(Number)
    if (!a || !m || !j) return iso
    return new Intl.DateTimeFormat(locale, { day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date(a, m - 1, j))
  }
  const dateHeure = (iso) => {
    if (!iso) return ''
    const d = new Date(iso)
    return isNaN(d) ? iso : d.toLocaleString(locale, { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  }
  return { langue, locale, t, tn, nombre, nomRef, ref, date, dateHeure }
}

export const ContexteLangue = createContext(creerOutils('fr'))
export const useT = () => useContext(ContexteLangue)
