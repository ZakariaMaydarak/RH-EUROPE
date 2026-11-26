import { useEffect, useState } from 'react'
import { api, requete } from '../api.js'
import { Badge, Bandeau, Chargement, EnTetePage, Icone, Vide } from '../composants.jsx'
import { dateHeureFr } from '../outils.js'

const TONS = {
  creation: 'info', modification: 'neutre', desactivation: 'danger', sortie_programmee: 'alerte',
  desactivation_auto: 'danger', reactivation: 'succes', effacement: 'danger', export: 'info',
}

export default function Historique({ admin }) {
  const [action, setAction] = useState('')
  const [q, setQ] = useState('')
  const [donnees, setDonnees] = useState(null)
  const [erreur, setErreur] = useState(null)
  const [deplie, setDeplie] = useState(null)

  useEffect(() => {
    const t = setTimeout(() => {
      api('historique' + requete({ action, q })).then(setDonnees).catch((e) => setErreur(e.message))
    }, 250)
    return () => clearTimeout(t)
  }, [action, q])

  return (
    <>
      <EnTetePage titre="Historique" sousTitre={admin ? 'Toutes les actions : créations, modifications, sorties, administration, exports'
        : 'Créations, modifications et sorties des collaborateurs de vos établissements'} />
      <div className="carte barre-outils">
        <div className="recherche">
          <Icone nom="recherche" />
          <label htmlFor="h-q" className="visuellement-cache">Rechercher</label>
          <input id="h-q" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Collaborateur, matricule, utilisateur…" />
        </div>
        <div className="filtres">
          <div className="filtre">
            <label htmlFor="h-action">Action</label>
            <select id="h-action" value={action} onChange={(e) => setAction(e.target.value)}>
              <option value="">Toutes</option>
              {donnees && Object.entries(donnees.actions).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
        </div>
      </div>
      {erreur && <Bandeau ton="danger">{erreur}</Bandeau>}
      {!donnees && !erreur && <Chargement />}
      {donnees && (
        <section className="carte carte-tableau">
          {donnees.entrees.length === 0 ? <Vide icone="historique" titre="Aucune action trouvée" /> : (
            <div className="defilement-tableau">
              <table className="tableau">
                <thead><tr><th scope="col">Date</th><th scope="col">Action</th><th scope="col">Collaborateur / objet</th><th scope="col">Par</th><th scope="col">Détail</th></tr></thead>
                <tbody>
                  {donnees.entrees.map((e, i) => (
                    <tr key={i}>
                      <td className="nowrap">{dateHeureFr(e.le)}</td>
                      <td><Badge ton={TONS[e.action] || 'neutre'}>{donnees.actions[e.action] || e.action}</Badge></td>
                      <td>{e.collaborateur_id && e.action !== 'effacement'
                        ? <><a href={`#/collaborateurs/${e.collaborateur_id}`}>{e.nom_complet}</a><span className="discret"> · {e.matricule} · {e.etablissement}</span></>
                        : e.nom_complet || <span className="discret">—</span>}</td>
                      <td>{e.par_nom || e.par}</td>
                      <td>
                        {e.detail}
                        {e.changements?.length > 0 && e.action !== 'creation' && (
                          deplie === i
                            ? <ul className="changements">{e.changements.map((c) => <li key={c.champ}><strong>{c.libelle}</strong> : <s>{c.avant || 'vide'}</s> → {c.apres || 'vide'}</li>)}</ul>
                            : <button type="button" className="bouton bouton-lien" onClick={() => setDeplie(i)}>
                              {e.changements.length} champ{e.changements.length > 1 ? 's' : ''} modifié{e.changements.length > 1 ? 's' : ''}</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </>
  )
}
