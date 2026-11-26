// Appels à l'API de l'application : toujours à partir de BASE_URL (= /RHEUROPE/).
const BASE = import.meta.env.BASE_URL + 'api/'

export class ErreurApi extends Error {
  constructor(message, statut, corps) {
    super(message)
    this.statut = statut
    this.corps = corps || {}
  }
}

export async function api(chemin, { method = 'GET', body } = {}) {
  const options = { method, headers: { Accept: 'application/json' } }
  if (body instanceof FormData) options.body = body
  else if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(body)
  }
  let r
  try {
    r = await fetch(BASE + chemin, options)
  } catch {
    throw new ErreurApi('Serveur injoignable : vérifiez votre connexion.', 0)
  }
  const corps = await r.json().catch(() => ({}))
  if (!r.ok) throw new ErreurApi(corps.error || `Erreur ${r.status}`, r.status, corps)
  return corps
}

export const urlApi = (chemin) => BASE + chemin

export function requete(params) {
  const q = new URLSearchParams()
  Object.entries(params || {}).forEach(([k, v]) => {
    if (Array.isArray(v)) { if (v.length) q.set(k, v.join(',')) }
    else if (v !== undefined && v !== null && v !== '') q.set(k, v)
  })
  const s = q.toString()
  return s ? '?' + s : ''
}
