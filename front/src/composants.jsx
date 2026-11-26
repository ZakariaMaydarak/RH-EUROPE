import { useEffect, useRef } from 'react'

// Icônes SVG (tracés au trait, style Lucide) — jamais d'emoji comme icône.
const TRACES = {
  tableau: <><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></>,
  equipe: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></>,
  ajout: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M19 8v6M22 11h-6" /></>,
  recherche: <><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></>,
  telecharger: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10 5 5 5-5" /><path d="M12 15V3" /></>,
  importer: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m17 8-5-5-5 5" /><path d="M12 3v12" /></>,
  qualite: <><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="m9 12 2 2 4-4" /></>,
  liste: <><path d="M8 6h13M8 12h13M8 18h13" /><path d="M3 6h.01M3 12h.01M3 18h.01" /></>,
  utilisateurs: <><circle cx="12" cy="8" r="4" /><path d="M6 21v-1a6 6 0 0 1 12 0v1" /><path d="m19 3 2 2-2 2" /></>,
  historique: <><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /><path d="M12 7v5l4 2" /></>,
  reglages: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></>,
  retour: <path d="m15 18-6-6 6-6" />,
  suivant: <path d="m9 18 6-6-6-6" />,
  haut: <path d="m18 15-6-6-6 6" />,
  bas: <path d="m6 9 6 6 6-6" />,
  tri: <><path d="m7 15 5 5 5-5" /><path d="m7 9 5-5 5 5" /></>,
  fermer: <><path d="M18 6 6 18" /><path d="m6 6 12 12" /></>,
  valide: <path d="M20 6 9 17l-5-5" />,
  alerte: <><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /><path d="M12 9v4M12 17h.01" /></>,
  erreur: <><circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" /></>,
  info: <><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></>,
  calendrier: <><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></>,
  sortie: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="m16 17 5-5-5-5" /><path d="M21 12H9" /></>,
  reactiver: <><path d="M3 12a9 9 0 0 1 15-6.7L21 8" /><path d="M21 3v5h-5" /><path d="M21 12a9 9 0 0 1-15 6.7L3 16" /><path d="M3 21v-5h5" /></>,
  corbeille: <><path d="M3 6h18" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" /><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></>,
  generer: <><path d="m12 3-1.9 5.8L4 10.6l4.9 3.6L7.2 20 12 16.6 16.8 20l-1.7-5.8 4.9-3.6-6.1-1.8z" /></>,
  hotel: <><path d="M3 21h18" /><path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16" /><path d="M9 7h1M14 7h1M9 11h1M14 11h1M9 15h1M14 15h1" /><path d="M10 21v-3h4v3" /></>,
  plus: <><path d="M12 5v14M5 12h14" /></>,
  crayon: <><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" /></>,
  menu: <><path d="M4 6h16M4 12h16M4 18h16" /></>,
  arrivee: <><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" /><path d="m10 17 5-5-5-5" /><path d="M15 12H3" /></>,
  sablier: <><path d="M5 22h14M5 2h14" /><path d="M17 22v-4.2a2 2 0 0 0-.6-1.4L12 12l-4.4 4.4a2 2 0 0 0-.6 1.4V22" /><path d="M7 2v4.2a2 2 0 0 0 .6 1.4L12 12l4.4-4.4a2 2 0 0 0 .6-1.4V2" /></>,
  inactif: <><circle cx="12" cy="12" r="10" /><path d="m4.9 4.9 14.2 14.2" /></>,
  actif: <><path d="M22 11.1V12a10 10 0 1 1-5.9-9.1" /><path d="m22 4-10 10-3-3" /></>,
}

export function Icone({ nom, taille = 18, className = '' }) {
  return (
    <svg className={`icone ${className}`} width={taille} height={taille} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      {TRACES[nom] || TRACES.info}
    </svg>
  )
}

export function Badge({ ton = 'neutre', children, icone }) {
  return <span className={`badge badge-${ton}`}>{icone && <Icone nom={icone} taille={13} />}{children}</span>
}

export function Statut({ statut }) {
  return statut === 'actif'
    ? <Badge ton="succes" icone="actif">Actif</Badge>
    : <Badge ton="neutre" icone="inactif">Inactif</Badge>
}

export function Champ({ id, label, requis, erreur, aide, children, large }) {
  return (
    <div className={`champ ${erreur ? 'champ-erreur' : ''} ${large ? 'champ-large' : ''}`}>
      <label htmlFor={id}>{label}{requis && <span className="requis" aria-hidden="true"> *</span>}</label>
      {children}
      {erreur
        ? <p className="message-erreur" id={`${id}-erreur`} role="alert"><Icone nom="erreur" taille={14} />{erreur}</p>
        : aide ? <p className="aide" id={`${id}-aide`}>{aide}</p> : null}
    </div>
  )
}

export function Bouton({ variante = 'primaire', icone, children, chargement, disabled, type = 'button', ...props }) {
  return (
    <button type={type} className={`bouton bouton-${variante}`} disabled={chargement || disabled} aria-busy={chargement || undefined} {...props}>
      {chargement ? <span className="rond-chargement" aria-hidden="true" /> : icone && <Icone nom={icone} />}
      {children}
    </button>
  )
}

export function Modale({ titre, onFermer, children, actions, large }) {
  const ref = useRef(null)
  useEffect(() => {
    const precedent = document.activeElement
    const premier = ref.current?.querySelector('input, select, textarea, button:not(.modale-fermer)')
    premier?.focus()
    const clavier = (e) => {
      if (e.key === 'Escape') onFermer()
      if (e.key === 'Tab' && ref.current) {   // garde le focus dans la fenêtre
        const f = [...ref.current.querySelectorAll('button, input, select, textarea, a[href]')].filter((x) => !x.disabled)
        if (!f.length) return
        if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus() }
        else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus() }
      }
    }
    document.addEventListener('keydown', clavier)
    document.body.classList.add('sans-defilement')
    return () => {
      document.removeEventListener('keydown', clavier)
      document.body.classList.remove('sans-defilement')
      precedent?.focus?.()
    }
  }, [onFermer])
  return (
    <div className="modale-fond" onMouseDown={(e) => e.target === e.currentTarget && onFermer()}>
      <div className={`modale ${large ? 'modale-large' : ''}`} role="dialog" aria-modal="true" aria-labelledby="modale-titre" ref={ref}>
        <div className="modale-entete">
          <h2 id="modale-titre">{titre}</h2>
          <button type="button" className="modale-fermer" onClick={onFermer} aria-label="Fermer"><Icone nom="fermer" /></button>
        </div>
        <div className="modale-corps">{children}</div>
        {actions && <div className="modale-actions">{actions}</div>}
      </div>
    </div>
  )
}

export function Chargement({ texte = 'Chargement…' }) {
  return <div className="chargement" role="status"><span className="rond-chargement" aria-hidden="true" />{texte}</div>
}

export function Vide({ icone = 'info', titre, children }) {
  return (
    <div className="vide">
      <span className="vide-icone"><Icone nom={icone} taille={22} /></span>
      <p className="vide-titre">{titre}</p>
      {children && <div className="vide-texte">{children}</div>}
    </div>
  )
}

export function Bandeau({ ton = 'info', titre, children }) {
  const icone = { info: 'info', alerte: 'alerte', danger: 'erreur', succes: 'valide' }[ton]
  return (
    <div className={`bandeau bandeau-${ton}`} role={ton === 'danger' ? 'alert' : 'status'}>
      <Icone nom={icone} />
      <div>{titre && <strong>{titre}</strong>}{children && <div>{children}</div>}</div>
    </div>
  )
}

export function EnTetePage({ titre, sousTitre, actions, retour }) {
  return (
    <div className="entete-page">
      <div>
        {retour && <a className="lien-retour" href={retour.href}><Icone nom="retour" taille={16} />{retour.texte}</a>}
        <h1>{titre}</h1>
        {sousTitre && <p className="sous-titre">{sousTitre}</p>}
      </div>
      {actions && <div className="entete-actions">{actions}</div>}
    </div>
  )
}

// Barres horizontales (répartitions) : valeur et part affichées en texte, pas seulement en couleur.
export function Barres({ donnees, total, onClic }) {
  if (!donnees?.length) return <p className="discret">Aucune donnée.</p>
  const max = Math.max(...donnees.map((d) => d.nb), 1)
  const somme = total || donnees.reduce((s, d) => s + d.nb, 0)
  return (
    <ul className="barres">
      {donnees.map((d) => (
        <li key={d.code || d.libelle}>
          <button type="button" className="barre-ligne" onClick={onClic ? () => onClic(d) : undefined} disabled={!onClic}>
            <span className="barre-libelle">{d.libelle}</span>
            <span className="barre-piste"><span className="barre-valeur" style={{ width: `${(d.nb / max) * 100}%` }} /></span>
            <span className="barre-nb">{d.nb}<span className="barre-part">{somme ? Math.round((d.nb / somme) * 100) : 0} %</span></span>
          </button>
        </li>
      ))}
    </ul>
  )
}
