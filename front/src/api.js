// Appels à l'API de l'application : toujours à partir de BASE_URL (= /RHEUROPE/).
const BASE = import.meta.env.BASE_URL + 'api/'

export class ErreurApi extends Error {
  constructor(message, statut, corps) {
    super(message)
    this.statut = statut
    this.corps = corps || {}
  }
}

// Langue envoyée au serveur (messages d'erreur et libellés calculés dans la bonne langue).
let langueCourante = 'fr'
export const definirLangueApi = (langue) => { langueCourante = langue }

export async function api(chemin, { method = 'GET', body } = {}) {
  const options = { method, headers: { Accept: 'application/json', 'X-Langue': langueCourante } }
  if (body instanceof FormData) options.body = body
  else if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(body)
  }
  let r
  try {
    r = await fetch(BASE + chemin, options)
  } catch {
    throw new ErreurApi({
      fr: 'Serveur injoignable : vérifiez votre connexion.', en: 'Server unreachable: check your connection.',
      de: 'Server nicht erreichbar: Verbindung prüfen.', es: 'Servidor inaccesible: compruebe su conexión.',
      it: 'Server non raggiungibile: verificare la connessione.',
    }[langueCourante], 0)
  }
  const corps = await r.json().catch(() => ({}))
  if (!r.ok) throw new ErreurApi(corps.error || `Erreur ${r.status}`, r.status, corps)
  return corps
}

export const urlApi = (chemin) => BASE + chemin + (chemin.includes('?') ? '&' : '?') + 'langue=' + langueCourante

export function requete(params) {
  const q = new URLSearchParams()
  Object.entries(params || {}).forEach(([k, v]) => {
    if (Array.isArray(v)) { if (v.length) q.set(k, v.join(',')) }
    else if (v !== undefined && v !== null && v !== '') q.set(k, v)
  })
  const s = q.toString()
  return s ? '?' + s : ''
}
