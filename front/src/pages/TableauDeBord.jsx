import { useEffect, useState } from 'react'
import { api, requete } from '../api.js'
import { Bandeau, Barres, Chargement, EnTetePage, Icone, Vide } from '../composants.jsx'
import { useT } from '../i18n.js'
import { joursAvant, naviguer } from '../outils.js'

function Kpi({ libelle, valeur, detail, icone, ton, lien }) {
  const { nombre } = useT()
  const contenu = (
    <>
      <span className={`kpi-icone kpi-${ton}`}><Icone nom={icone} taille={20} /></span>
      <span className="kpi-texte">
        <span className="kpi-libelle">{libelle}</span>
        <span className="kpi-valeur">{nombre(valeur)}</span>
        {detail && <span className="kpi-detail">{detail}</span>}
      </span>
    </>
  )
  return lien ? <a className="carte kpi" href={lien}>{contenu}</a> : <div className="carte kpi">{contenu}</div>
}

function ListeEcheances({ titre, icone, elements, vide, aujourdhui, mode }) {
  const { t, tn, date } = useT()
  return (
    <section className="carte">
      <h2 className="carte-titre"><Icone nom={icone} />{titre}</h2>
      {elements.length === 0 ? <p className="discret">{vide}</p> : (
        <ul className="liste-personnes">
          {elements.map((p) => {
            const j = joursAvant(p.date, aujourdhui)
            const quand = mode === 'arrivee'
              ? (j > 0 ? tn(j, 'Arrive dans {n} jour', 'Arrive dans {n} jours') : j === 0 ? t("Arrivé(e) aujourd'hui") : tn(-j, 'Arrivé(e) il y a {n} jour', 'Arrivé(e) il y a {n} jours'))
              : (j === 0 ? t("Aujourd'hui") : tn(j, 'Dans {n} jour', 'Dans {n} jours'))
            return (
              <li key={p.id}>
                <a href={`#/collaborateurs/${p.id}`}>
                  <span className="avatar petit" aria-hidden="true">{(p.prenom || '?').slice(0, 1)}{(p.nom || '').slice(0, 1)}</span>
                  <span className="personne-texte">
                    <strong>{p.prenom} {p.nom}</strong>
                    <span>{p.poste} · {p.type_contrat} · {p.etablissement}</span>
                  </span>
                  <span className={`echeance ${mode !== 'arrivee' && j <= 7 ? 'urgent' : ''}`}>
                    <strong>{date(p.date)}</strong><span>{quand}</span>
                  </span>
                </a>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}

// « Nom, Prénom » (annuaire) → Prénom ; sinon le premier mot.
function prenomDe(nom) {
  const s = String(nom || '').trim()
  if (s.includes(',')) return s.split(',')[1].trim().split(' ')[0]
  return s.split(' ')[0]
}

export default function TableauDeBord({ moi, refs, admin }) {
  const { t, tn, nomRef } = useT()
  const etablissements = admin ? refs.etablissements : refs.etablissements.filter((e) => moi.sites.includes(e.code))
  const [etab, setEtab] = useState('')
  const [donnees, setDonnees] = useState(null)
  const [erreur, setErreur] = useState(null)

  useEffect(() => {
    setDonnees(null)
    api('tableau-de-bord' + requete({ etablissement: etab })).then(setDonnees).catch((e) => setErreur(e.message))
  }, [etab])

  const filtre = (cle, valeur) => naviguer(`/collaborateurs${requete({ statut: 'actif', etablissement: etab, [cle]: valeur })}`)
  const titreEtab = etab ? nomRef(etablissements.find((e) => e.code === etab)) : (admin ? t('Tous les établissements européens') : t('Vos établissements'))
  const f = donnees?.fenetres

  return (
    <>
      <EnTetePage
        titre={t('Bonjour {prenom}', { prenom: prenomDe(moi.nom) })}
        sousTitre={t('Effectifs — {perimetre}', { perimetre: titreEtab })}
        actions={<>
          {etablissements.length > 1 && (
            <div className="select-compact">
              <label htmlFor="tdb-etab" className="visuellement-cache">{t('Établissement')}</label>
              <Icone nom="hotel" taille={16} />
              <select id="tdb-etab" value={etab} onChange={(e) => setEtab(e.target.value)}>
                <option value="">{t('Tous les établissements')}</option>
                {etablissements.map((e) => <option key={e.code} value={e.code}>{e.code} — {nomRef(e)}</option>)}
              </select>
            </div>
          )}
          <a className="bouton bouton-primaire" href="#/collaborateurs/nouveau"><Icone nom="plus" />{t('Ajouter un collaborateur')}</a>
        </>}
      />
      {erreur && <Bandeau ton="danger">{erreur}</Bandeau>}
      {!donnees && !erreur && <Chargement />}
      {donnees && etablissements.length === 0 && (
        <Bandeau ton="alerte" titre={admin ? t('Aucun établissement') : t('Aucun établissement attribué')}>
          {admin ? <>{t('Commencez par créer ou importer les établissements dans')} <a href="#/referentiels">{t('Référentiels')}</a>.</>
            : t("Demandez à un administrateur HR EUROPE de vous rattacher à vos établissements.")}
        </Bandeau>
      )}
      {donnees && (
        <>
          <div className="grille-kpi">
            <Kpi libelle={t('Collaborateurs actifs')} valeur={donnees.compteurs.actifs} icone="actif" ton="succes"
              lien={`#/collaborateurs${requete({ statut: 'actif', etablissement: etab })}`} />
            <Kpi libelle={t('Collaborateurs inactifs')} valeur={donnees.compteurs.inactifs} icone="inactif" ton="neutre"
              lien={`#/collaborateurs${requete({ statut: 'inactif', etablissement: etab })}`} />
            <Kpi libelle={t('Nouvelles arrivées')} valeur={donnees.compteurs.arrivees} icone="arrivee" ton="info"
              detail={t('{n} derniers jours', { n: f.arrivees }) + (donnees.compteurs.arrivees_a_venir ? ' · ' + t('{n} à venir', { n: donnees.compteurs.arrivees_a_venir }) : '')} />
            <Kpi libelle={t('Prochains départs')} valeur={donnees.compteurs.departs} icone="sortie" ton="alerte"
              detail={t('{n} prochains jours', { n: f.departs })} />
            <Kpi libelle={t('Contrats à échéance')} valeur={donnees.compteurs.echeances} icone="sablier" ton="danger"
              detail={t('{n} prochains jours', { n: f.echeances })} />
          </div>

          {donnees.compteurs.total === 0 ? (
            <div className="carte">
              <Vide icone="equipe" titre={t('Aucun collaborateur pour le moment')}>
                <p>{t('Créez la première fiche pour alimenter le référentiel.')}</p>
                <a className="bouton bouton-primaire" href="#/collaborateurs/nouveau"><Icone nom="plus" />{t('Ajouter un collaborateur')}</a>
              </Vide>
            </div>
          ) : (
            <>
              <div className="grille-3">
                <ListeEcheances titre={t('Contrats arrivant à échéance')} icone="sablier" elements={donnees.listes.echeances}
                  vide={tn(f.echeances, 'Aucun contrat à durée déterminée ne se termine dans les {n} prochains jours.', 'Aucun contrat à durée déterminée ne se termine dans les {n} prochains jours.')}
                  aujourdhui={donnees.aujourd_hui} />
                <ListeEcheances titre={t('Prochains départs')} icone="sortie" elements={donnees.listes.departs}
                  vide={t('Aucun départ prévu dans les {n} prochains jours.', { n: f.departs })} aujourdhui={donnees.aujourd_hui} />
                <ListeEcheances titre={t('Nouvelles arrivées')} icone="arrivee" elements={donnees.listes.arrivees}
                  vide={t('Aucune arrivée récente ou à venir.')} aujourdhui={donnees.aujourd_hui} mode="arrivee" />
              </div>
              <h2 className="titre-section">{t('Répartition des effectifs actifs')}</h2>
              <div className="grille-3">
                <section className="carte"><h3 className="carte-titre">{t('Par service')}</h3>
                  <Barres donnees={donnees.repartition.service} onClic={(d) => filtre('service', d.code)} /></section>
                <section className="carte"><h3 className="carte-titre">{t('Par sexe')}</h3>
                  <Barres donnees={donnees.repartition.sexe} onClic={(d) => filtre('sexe', d.code)} /></section>
                <section className="carte"><h3 className="carte-titre">{t('Par type de contrat')}</h3>
                  <Barres donnees={donnees.repartition.type_contrat} onClic={(d) => filtre('type_contrat', d.code)} /></section>
              </div>
              {!etab && donnees.par_etablissement.length > 1 && (
                <section className="carte">
                  <h3 className="carte-titre"><Icone nom="hotel" />{t('Par établissement')}</h3>
                  <Barres donnees={donnees.par_etablissement.map((e) => ({ ...e, libelle: `${e.code} — ${e.libelle}` }))}
                    onClic={(d) => setEtab(d.code)} />
                </section>
              )}
            </>
          )}
        </>
      )}
    </>
  )
}
