import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, definirLangueApi } from './api.js'
import { Bandeau, Chargement, Icone } from './composants.jsx'
import { ContexteLangue, LANGUES, creerOutils, langueInitiale, memoriserLangue } from './i18n.js'
import { lireRoute } from './outils.js'
import TableauDeBord from './pages/TableauDeBord.jsx'
import Collaborateurs from './pages/Collaborateurs.jsx'
import Fiche from './pages/Fiche.jsx'
import Qualite from './pages/Qualite.jsx'
import Exports from './pages/Exports.jsx'
import Referentiels from './pages/Referentiels.jsx'
import Utilisateurs from './pages/Utilisateurs.jsx'
import Historique from './pages/Historique.jsx'
import Parametres from './pages/Parametres.jsx'

const NAVIGATION = [
  { section: 'Pilotage' },
  { route: 'tableau-de-bord', libelle: 'Tableau de bord', icone: 'tableau' },
  { route: 'collaborateurs', libelle: 'Collaborateurs', icone: 'equipe' },
  { route: 'historique', libelle: 'Historique', icone: 'historique' },
  { section: 'Administration', admin: true },
  { route: 'qualite', libelle: 'Qualité des données', icone: 'qualite', admin: true },
  { route: 'exports', libelle: 'Exports', icone: 'telecharger', admin: true },
  { route: 'referentiels', libelle: 'Référentiels', icone: 'liste', admin: true },
  { route: 'utilisateurs', libelle: 'Utilisateurs et droits', icone: 'utilisateurs', admin: true },
  { route: 'parametres', libelle: 'Paramètres', icone: 'reglages', admin: true },
]

// Sélecteur de langue : dans la barre du haut, donc présent sur toutes les pages.
function ChoixLangue({ langue, onChange, t }) {
  return (
    <div className="choix-langue">
      <Icone nom="globe" taille={16} />
      <label htmlFor="choix-langue" className="visuellement-cache">{t('Langue')}</label>
      <select id="choix-langue" value={langue} onChange={(e) => onChange(e.target.value)} title={t('Langue')}>
        {Object.entries(LANGUES).map(([code, nom]) => <option key={code} value={code} lang={code}>{nom}</option>)}
      </select>
    </div>
  )
}

export default function App() {
  const [langue, setLangue] = useState(langueInitiale)
  const outils = useMemo(() => creerOutils(langue), [langue])
  const { t } = outils
  const [route, setRoute] = useState(lireRoute())
  const [moi, setMoi] = useState(null)
  const [refs, setRefs] = useState(null)
  const [erreur, setErreur] = useState(null)
  const [menuOuvert, setMenuOuvert] = useState(false)
  const [notification, setNotification] = useState(null)

  definirLangueApi(langue)
  useEffect(() => {
    document.documentElement.lang = langue
    document.title = `HR EUROPE — ${t('Portail Adagio')}`
  }, [langue, t])

  const changerLangue = useCallback((nouvelle) => {
    if (!LANGUES[nouvelle]) return
    definirLangueApi(nouvelle)
    memoriserLangue(nouvelle)
    setLangue(nouvelle)
    api('me/langue', { method: 'PUT', body: { langue: nouvelle } }).catch(() => {})   // mémorisée aussi côté serveur
  }, [])

  useEffect(() => {
    const changer = () => { setRoute(lireRoute()); setMenuOuvert(false); window.scrollTo(0, 0) }
    window.addEventListener('hashchange', changer)
    return () => window.removeEventListener('hashchange', changer)
  }, [])

  const chargerRefs = useCallback(() => api('referentiels').then((r) => setRefs(r.referentiels)), [])

  useEffect(() => {
    api('me').then((m) => {
      setMoi(m)
      // Langue choisie sur un autre poste : elle prime sur celle du navigateur.
      if (m.langue && LANGUES[m.langue]) { definirLangueApi(m.langue); memoriserLangue(m.langue); setLangue(m.langue) }
      if (m.role !== 'aucun') chargerRefs().catch((e) => setErreur(e.message))
    }).catch((e) => setErreur(e.message))
  }, [chargerRefs])

  const notifier = useCallback((texte, ton = 'succes') => {
    setNotification({ texte, ton, cle: Date.now() })
  }, [])
  useEffect(() => {
    if (!notification) return
    const minuteur = setTimeout(() => setNotification(null), 4500)
    return () => clearTimeout(minuteur)
  }, [notification])

  const choix = <ChoixLangue langue={langue} onChange={changerLangue} t={t} />
  const pageSeule = (contenu) => (
    <ContexteLangue.Provider value={outils}>
      <div className="page-seule">
        <div className="page-seule-haut">
          <a className="lien-retour" href="/"><Icone nom="retour" taille={16} />{t('Retour au portail')}</a>
          {choix}
        </div>
        {contenu}
      </div>
    </ContexteLangue.Provider>
  )

  if (erreur) return pageSeule(<Bandeau ton="danger" titre={t("Impossible de charger l'application")}>{erreur}</Bandeau>)
  if (!moi) return pageSeule(<Chargement />)
  if (moi.role === 'aucun') {
    return pageSeule(<>
      <h1>HR EUROPE</h1>
      <Bandeau ton="alerte" titre={t('Aucun droit attribué')}>
        {t("Votre compte ({email}) n'a pas encore de profil dans HR EUROPE. Demandez à un administrateur de l'application de vous attribuer le profil « Directeur d'hôtel » avec vos établissements.", { email: moi.email })}
      </Bandeau>
    </>)
  }
  if (!refs) return pageSeule(<Chargement />)

  const admin = moi.role === 'admin'
  const [premier, second] = route.parties
  const contexte = { moi, refs, admin, notifier, chargerRefs, params: route.params }
  const interdit = <Bandeau ton="danger" titre={t('Accès réservé')}>{t('Cette page est réservée aux administrateurs.')}</Bandeau>

  let page
  // La fiche garde sa saisie en cours lors d'un changement de langue ; les autres pages
  // sont rechargées (clé = langue) pour obtenir les textes calculés par le serveur.
  if (premier === 'collaborateurs' && second) page = <Fiche key={second} id={second} {...contexte} />
  else if (premier === 'collaborateurs') page = <Collaborateurs key={langue} {...contexte} />
  else if (premier === 'historique') page = <Historique key={langue} {...contexte} />
  else if (premier === 'qualite') page = admin ? <Qualite key={langue} {...contexte} /> : interdit
  else if (premier === 'exports') page = admin ? <Exports key={langue} {...contexte} /> : interdit
  else if (premier === 'referentiels') page = admin ? <Referentiels {...contexte} /> : interdit
  else if (premier === 'utilisateurs') page = admin ? <Utilisateurs key={langue} {...contexte} /> : interdit
  else if (premier === 'parametres') page = admin ? <Parametres key={langue} {...contexte} /> : interdit
  else page = <TableauDeBord key={langue} {...contexte} />

  const actif = premier || 'tableau-de-bord'
  const nbEtab = admin ? refs.etablissements.length : moi.sites.length

  return (
    <ContexteLangue.Provider value={outils}>
      <div className="coquille">
        <a className="aller-contenu" href="#contenu" onClick={(e) => { e.preventDefault(); document.getElementById('contenu')?.focus() }}>{t('Aller au contenu')}</a>
        <header className="barre-haut">
          <button type="button" className="bouton-menu" aria-label={t('Ouvrir le menu')} aria-expanded={menuOuvert}
            onClick={() => setMenuOuvert(!menuOuvert)}><Icone nom={menuOuvert ? 'fermer' : 'menu'} /></button>
          <a className="marque" href="#/tableau-de-bord">
            <span className="marque-logo" aria-hidden="true">RH</span>
            <span className="marque-texte"><strong>HR EUROPE</strong><span>Employee Master Data</span></span>
          </a>
          <div className="barre-haut-droite">
            {choix}
            <a className="lien-portail" href="/" aria-label={t('Portail')}><Icone nom="retour" taille={16} /><span>{t('Portail')}</span></a>
            <div className="utilisateur" title={moi.email}>
              <span className="avatar" aria-hidden="true">{(moi.nom || moi.email).slice(0, 1).toUpperCase()}</span>
              <span className="utilisateur-texte">
                <strong>{moi.nom}</strong>
                <span>{admin ? t('Administrateur · Europe') : outils.tn(nbEtab, "Directeur d'hôtel · {n} établissement", "Directeur d'hôtel · {n} établissements")}</span>
              </span>
            </div>
          </div>
        </header>
        <nav className={`navigation ${menuOuvert ? 'ouverte' : ''}`} aria-label={t('Navigation principale')}>
          <ul>
            {NAVIGATION.filter((n) => !n.admin || admin).map((n) => n.section
              ? <li key={n.section} className="nav-section">{t(n.section)}</li>
              : (
                <li key={n.route}>
                  <a href={`#/${n.route}`} className={actif === n.route ? 'actif' : ''} aria-current={actif === n.route ? 'page' : undefined}>
                    <Icone nom={n.icone} />{t(n.libelle)}
                  </a>
                </li>
              ))}
          </ul>
          <a className="nav-ajout" href="#/collaborateurs/nouveau"><Icone nom="plus" />{t('Ajouter un collaborateur')}</a>
        </nav>
        {menuOuvert && <div className="voile" onClick={() => setMenuOuvert(false)} />}
        <main id="contenu" className="contenu" tabIndex={-1}>{page}</main>
        {notification && (
          <div key={notification.cle} className={`notification notification-${notification.ton}`} role="status" aria-live="polite">
            <Icone nom={notification.ton === 'succes' ? 'valide' : 'alerte'} />{notification.texte}
          </div>
        )}
      </div>
    </ContexteLangue.Provider>
  )
}
