import { useEffect, useState } from 'react'

// Toujours construire les URL de l'API à partir de BASE_URL (= /RHEUROPE/).
const API = import.meta.env.BASE_URL + 'api/'

async function api(chemin, options) {
  const r = await fetch(API + chemin, { headers: { 'Content-Type': 'application/json' }, ...options })
  const corps = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(corps.error || `Erreur ${r.status}`)
  return corps
}

export default function App() {
  const [moi, setMoi] = useState(null)
  const [notes, setNotes] = useState([])
  const [texte, setTexte] = useState('')
  const [erreur, setErreur] = useState(null)

  const charger = () => api('notes').then(setNotes).catch(e => setErreur(e.message))
  useEffect(() => { api('me').then(setMoi).catch(e => setErreur(e.message)); charger() }, [])

  const ajouter = async (e) => {
    e.preventDefault()
    try { await api('notes', { method: 'POST', body: JSON.stringify({ texte }) }); setTexte(''); charger() }
    catch (err) { setErreur(err.message) }
  }

  return (
    <main className="page">
      <a className="retour" href="/">← Retour au portail</a>
      <h1>HR EUROPE</h1>
      {moi && <p className="muted">Connecté : {moi.nom} — rôle {moi.role}</p>}
      {erreur && <p className="erreur">{erreur}</p>}
      <form onSubmit={ajouter} className="ligne">
        <input value={texte} onChange={e => setTexte(e.target.value)} placeholder="Nouvelle note" />
        <button type="submit">Ajouter</button>
      </form>
      <ul>{notes.map((n, i) => <li key={i}>{n.texte} <span className="muted">— {n.par}</span></li>)}</ul>
    </main>
  )
}
