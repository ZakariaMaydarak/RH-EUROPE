import { useEffect, useState } from 'react'
import { api, requete } from '../api.js'
import { Badge, Bandeau, Chargement, EnTetePage, Icone, Vide } from '../composants.jsx'
import { useT } from '../i18n.js'

const TONS = {
  creation: 'info', modification: 'neutre', desactivation: 'danger', sortie_programmee: 'alerte',
  desactivation_auto: 'danger', reactivation: 'succes', effacement: 'danger', export: 'info',
}
const CHAMPS = {
  nom: 'Nom', prenom: 'Prénom', sexe: 'Sexe', date_naissance: 'Date de naissance', matricule: 'Matricule',
  email: 'Adresse e-mail Accor', etablissement: 'Établissement', service: 'Service', poste: 'Poste', manager_id: 'Manager',
  type_contrat: 'Type de contrat', date_debut: 'Date de début de contrat', date_fin: 'Date de fin de contrat',
  statut: 'Statut', date_sortie: 'Date de sortie', motif_sortie: 'Motif de sortie', commentaire_sortie: 'Commentaire de sortie',
}

export default function Historique({ admin }) {
  const { t, tn, dateHeure } = useT()
  const [action, setAction] = useState('')
  const [q, setQ] = useState('')
  const [donnees, setDonnees] = useState(null)
  const [erreur, setErreur] = useState(null)
  const [deplie, setDeplie] = useState(null)

  useEffect(() => {
    const minuteur = setTimeout(() => {
      api('historique' + requete({ action, q })).then(setDonnees).catch((e) => setErreur(e.message))
    }, 250)
    return () => clearTimeout(minuteur)
  }, [action, q])

  return (
    <>
      <EnTetePage titre={t('Historique')} sousTitre={admin ? t('Toutes les actions : créations, modifications, sorties, administration, exports')
        : t('Créations, modifications et sorties des collaborateurs de vos établissements')} />
      <div className="carte barre-outils">
        <div className="recherche">
          <Icone nom="recherche" />
          <label htmlFor="h-q" className="visuellement-cache">{t('Rechercher')}</label>
          <input id="h-q" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('Collaborateur, matricule, utilisateur…')} />
        </div>
        <div className="filtres">
          <div className="filtre">
            <label htmlFor="h-action">{t('Action')}</label>
            <select id="h-action" value={action} onChange={(e) => setAction(e.target.value)}>
              <option value="">{t('Toutes')}</option>
              {donnees && Object.entries(donnees.actions).map(([k, v]) => <option key={k} value={k}>{t(v)}</option>)}
            </select>
          </div>
        </div>
      </div>
      {erreur && <Bandeau ton="danger">{erreur}</Bandeau>}
      {!donnees && !erreur && <Chargement />}
      {donnees && (
        <section className="carte carte-tableau">
          {donnees.entrees.length === 0 ? <Vide icone="historique" titre={t('Aucune action trouvée')} /> : (
            <div className="defilement-tableau">
              <table className="tableau">
                <thead><tr><th scope="col">{t('Date')}</th><th scope="col">{t('Action')}</th><th scope="col">{t('Collaborateur / objet')}</th><th scope="col">{t('Par')}</th><th scope="col">{t('Détail')}</th></tr></thead>
                <tbody>
                  {donnees.entrees.map((e, i) => (
                    <tr key={i}>
                      <td className="nowrap">{dateHeure(e.le)}</td>
                      <td><Badge ton={TONS[e.action] || 'neutre'}>{t(donnees.actions[e.action] || e.action)}</Badge></td>
                      <td>{e.collaborateur_id && e.action !== 'effacement'
                        ? <><a href={`#/collaborateurs/${e.collaborateur_id}`}>{e.nom_complet}</a><span className="discret"> · {e.matricule} · {e.etablissement}</span></>
                        : e.nom_complet || <span className="discret">—</span>}</td>
                      <td>{e.par === 'automatisation' ? t('Désactivation automatique') : (e.par_nom || e.par)}</td>
                      <td>
                        {e.detail}
                        {e.changements?.length > 0 && e.action !== 'creation' && (
                          deplie === i
                            ? <ul className="changements">{e.changements.map((c) => <li key={c.champ}><strong>{t(CHAMPS[c.champ] || c.libelle)}</strong> : <s>{c.avant || t('vide')}</s> → {c.apres || t('vide')}</li>)}</ul>
                            : <button type="button" className="bouton bouton-lien" onClick={() => setDeplie(i)}>
                              {tn(e.changements.length, '{n} champ modifié', '{n} champs modifiés')}</button>
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
