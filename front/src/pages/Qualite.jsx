import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { Bandeau, Chargement, EnTetePage, Icone, Statut } from '../composants.jsx'
import { useT } from '../i18n.js'

export default function Qualite() {
  const { t } = useT()
  const [donnees, setDonnees] = useState(null)
  const [erreur, setErreur] = useState(null)
  const [ouvert, setOuvert] = useState(null)
  useEffect(() => { api('qualite').then(setDonnees).catch((e) => setErreur(e.message)) }, [])

  if (erreur) return <Bandeau ton="danger">{erreur}</Bandeau>
  if (!donnees) return <Chargement />
  const taux = donnees.total_collaborateurs ? Math.round((donnees.fiches_conformes / donnees.total_collaborateurs) * 100) : 100

  return (
    <>
      <EnTetePage titre={t('Qualité des données')} sousTitre={t("Contrôles de complétude et de cohérence sur toute l'Europe")} />
      <div className="grille-kpi">
        <div className="carte kpi">
          <span className={`kpi-icone kpi-${taux >= 95 ? 'succes' : taux >= 80 ? 'alerte' : 'danger'}`}><Icone nom="qualite" taille={20} /></span>
          <span className="kpi-texte"><span className="kpi-libelle">{t('Fiches sans anomalie')}</span>
            <span className="kpi-valeur">{taux} %</span>
            <span className="kpi-detail">{t('{n} sur {total}', { n: donnees.fiches_conformes, total: donnees.total_collaborateurs })}</span></span>
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
                  <thead><tr><th scope="col">{t('Matricule')}</th><th scope="col">{t('Collaborateur')}</th><th scope="col">{t('Établissement')}</th><th scope="col">{t('Statut')}</th><th scope="col">{t('Détail')}</th></tr></thead>
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
                {ctl.nb > ctl.elements.length && <p className="discret">{t('{n} premiers éléments affichés.', { n: ctl.elements.length })}</p>}
              </div>
            )}
          </section>
        ))}
      </div>
    </>
  )
}
