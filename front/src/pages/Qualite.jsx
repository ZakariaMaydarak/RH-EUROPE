import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { Bandeau, Chargement, EnTetePage, Icone, Statut } from '../composants.jsx'

export default function Qualite() {
  const [donnees, setDonnees] = useState(null)
  const [erreur, setErreur] = useState(null)
  const [ouvert, setOuvert] = useState(null)
  useEffect(() => { api('qualite').then(setDonnees).catch((e) => setErreur(e.message)) }, [])

  if (erreur) return <Bandeau ton="danger">{erreur}</Bandeau>
  if (!donnees) return <Chargement />
  const taux = donnees.total_collaborateurs ? Math.round((donnees.fiches_conformes / donnees.total_collaborateurs) * 100) : 100

  return (
    <>
      <EnTetePage titre="Qualité des données" sousTitre="Contrôles de complétude et de cohérence sur toute l'Europe" />
      <div className="grille-kpi">
        <div className="carte kpi">
          <span className={`kpi-icone kpi-${taux >= 95 ? 'succes' : taux >= 80 ? 'alerte' : 'danger'}`}><Icone nom="qualite" taille={20} /></span>
          <span className="kpi-texte"><span className="kpi-libelle">Fiches sans anomalie</span>
            <span className="kpi-valeur">{taux} %</span>
            <span className="kpi-detail">{donnees.fiches_conformes} sur {donnees.total_collaborateurs}</span></span>
        </div>
      </div>
      <div className="liste-controles">
        {donnees.controles.map((ctl) => (
          <section className="carte controle" key={ctl.code}>
            <button type="button" className="controle-entete" aria-expanded={ouvert === ctl.code}
              onClick={() => setOuvert(ouvert === ctl.code ? null : ctl.code)} disabled={!ctl.nb}>
              <span className={`pastille ${ctl.nb ? 'pastille-alerte' : 'pastille-succes'}`}>
                <Icone nom={ctl.nb ? 'alerte' : 'valide'} taille={16} /></span>
              <span className="controle-libelle">{ctl.libelle}</span>
              <span className="controle-nb">{ctl.nb}</span>
              {ctl.nb > 0 && <Icone nom={ouvert === ctl.code ? 'haut' : 'bas'} />}
            </button>
            {ouvert === ctl.code && (
              <div className="defilement-tableau">
                <table className="tableau">
                  <thead><tr><th scope="col">Matricule</th><th scope="col">Collaborateur</th><th scope="col">Établissement</th><th scope="col">Statut</th><th scope="col">Détail</th></tr></thead>
                  <tbody>
                    {ctl.elements.map((x, i) => (
                      <tr key={x.id + i}>
                        <td className="mono">{x.matricule || '—'}</td>
                        <td><a href={`#/collaborateurs/${x.id}`}>{x.prenom} {x.nom}</a></td>
                        <td>{x.etablissement}</td>
                        <td><Statut statut={x.statut} /></td>
                        <td>{x.detail}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {ctl.nb > ctl.elements.length && <p className="discret">{ctl.elements.length} premiers éléments affichés.</p>}
              </div>
            )}
          </section>
        ))}
      </div>
    </>
  )
}
