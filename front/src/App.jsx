import { useCallback, useEffect, useState } from 'react'
import { api } from './api.js'
import { Bandeau, Chargement, Icone } from './composants.jsx'
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

export default function App() {
  const [route, setRoute] = useState(lireRoute())
  const [moi, setMoi] = useState(null)
  const [refs, setRefs] = useState(null)
  const [erreur, setErreur] = useState(null)
  const [menuOuvert, setMenuOuvert] = useState(false)
  const [notification, setNotification] = useState(null)

  useEffect(() => {
    const changer = () => { setRoute(lireRoute()); setMenuOuvert(false); window.scrollTo(0, 0) }
    window.addEventListener('hashchange', changer)
    return () => window.removeEventListener('hashchange', changer)
  }, [])

  const chargerRefs = useCallback(() => api('referentiels').then((r) => setRefs(r.referentiels)), [])

  useEffect(() => {
    api('me').then((m) => {
      setMoi(m)
      if (m.role !== 'aucun') chargerRefs().catch((e) => setErreur(e.message))
    }).catch((e) => setErreur(e.message))
  }, [chargerRefs])

  const notifier = useCallback((texte, ton = 'succes') => {
    setNotification({ texte, ton, cle: Date.now() })
  }, [])
  useEffect(() => {
    if (!notification) return
    const t = setTimeout(() => setNotification(null), 4500)
    return () => clearTimeout(t)
  }, [notification])

  if (erreur) return <div className="page-seule"><Bandeau ton="danger" titre="Impossible de charger l'application">{erreur}</Bandeau></div>
  if (!moi) return <div className="page-seule"><Chargement /></div>
  if (moi.role === 'aucun') {
    return (
      <div className="page-seule">
        <a className="lien-retour" href="/"><Icone nom="retour" taille={16} />Retour au portail</a>
        <h1>HR EUROPE</h1>
        <Bandeau ton="alerte" titre="Aucun droit attribué">
          Votre compte ({moi.email}) n'a pas encore de profil dans HR EUROPE. Demandez à un administrateur de
          l'application de vous attribuer le profil « Directeur d'hôtel » avec vos établissements.
        </Bandeau>
      </div>
    )
  }
  if (!refs) return <div className="page-seule"><Chargement /></div>

  const admin = moi.role === 'admin'
  const [premier, second] = route.parties
  const contexte = { moi, refs, admin, notifier, chargerRefs, params: route.params }
  const interdit = <Bandeau ton="danger" titre="Accès réservé">Cette page est réservée aux administrateurs.</Bandeau>

  let page
  if (premier === 'collaborateurs' && second) page = <Fiche key={second} id={second} {...contexte} />
  else if (premier === 'collaborateurs') page = <Collaborateurs {...contexte} />
  else if (premier === 'historique') page = <Historique {...contexte} />
  else if (premier === 'qualite') page = admin ? <Qualite {...contexte} /> : interdit
  else if (premier === 'exports') page = admin ? <Exports {...contexte} /> : interdit
  else if (premier === 'referentiels') page = admin ? <Referentiels {...contexte} /> : interdit
  else if (premier === 'utilisateurs') page = admin ? <Utilisateurs {...contexte} /> : interdit
  else if (premier === 'parametres') page = admin ? <Parametres {...contexte} /> : interdit
  else page = <TableauDeBord {...contexte} />

  const actif = premier || 'tableau-de-bord'
  const nbEtab = admin ? refs.etablissements.length : moi.sites.length

  return (
    <div className="coquille">
      <a className="aller-contenu" href="#contenu" onClick={(e) => { e.preventDefault(); document.getElementById('contenu')?.focus() }}>Aller au contenu</a>
      <header className="barre-haut">
        <button type="button" className="bouton-menu" aria-label="Ouvrir le menu" aria-expanded={menuOuvert}
          onClick={() => setMenuOuvert(!menuOuvert)}><Icone nom={menuOuvert ? 'fermer' : 'menu'} /></button>
        <a className="marque" href="#/tableau-de-bord">
          <span className="marque-logo" aria-hidden="true">RH</span>
          <span className="marque-texte"><strong>HR EUROPE</strong><span>Employee Master Data</span></span>
        </a>
        <div className="barre-haut-droite">
          <a className="lien-portail" href="/"><Icone nom="retour" taille={16} /><span>Portail</span></a>
          <div className="utilisateur" title={moi.email}>
            <span className="avatar" aria-hidden="true">{(moi.nom || moi.email).slice(0, 1).toUpperCase()}</span>
            <span className="utilisateur-texte">
              <strong>{moi.nom}</strong>
              <span>{admin ? 'Administrateur · Europe' : `Directeur d'hôtel · ${nbEtab} établissement${nbEtab > 1 ? 's' : ''}`}</span>
            </span>
          </div>
        </div>
      </header>
      <nav className={`navigation ${menuOuvert ? 'ouverte' : ''}`} aria-label="Navigation principale">
        <ul>
          {NAVIGATION.filter((n) => !n.admin || admin).map((n) => n.section
            ? <li key={n.section} className="nav-section">{n.section}</li>
            : (
              <li key={n.route}>
                <a href={`#/${n.route}`} className={actif === n.route ? 'actif' : ''} aria-current={actif === n.route ? 'page' : undefined}>
                  <Icone nom={n.icone} />{n.libelle}
                </a>
              </li>
            ))}
        </ul>
        <a className="nav-ajout" href="#/collaborateurs/nouveau"><Icone nom="plus" />Ajouter un collaborateur</a>
      </nav>
      {menuOuvert && <div className="voile" onClick={() => setMenuOuvert(false)} />}
      <main id="contenu" className="contenu" tabIndex={-1}>{page}</main>
      {notification && (
        <div key={notification.cle} className={`notification notification-${notification.ton}`} role="status" aria-live="polite">
          <Icone nom={notification.ton === 'succes' ? 'valide' : 'alerte'} />{notification.texte}
        </div>
      )}
    </div>
  )
}
