import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, requete } from '../api.js'
import { Badge, Bandeau, Bouton, Champ, Chargement, EnTetePage, Icone, Modale, Statut } from '../composants.jsx'
import { useT } from '../i18n.js'
import { naviguer, nomComplet } from '../outils.js'

const VIDE = {
  nom: '', prenom: '', matricule: '', sexe: '', email: '', date_naissance: '', date_debut: '', date_fin: '',
  type_contrat: '', service: '', etablissement: '', poste: '', manager_id: '',
}
const ORDRE = ['nom', 'prenom', 'sexe', 'date_naissance', 'matricule', 'email', 'etablissement', 'service', 'poste',
  'manager_id', 'type_contrat', 'date_debut', 'date_fin']
const LIBELLES = {
  nom: 'Nom', prenom: 'Prénom', sexe: 'Sexe', date_naissance: 'Date de naissance', matricule: 'Matricule',
  email: 'Adresse e-mail Accor', etablissement: 'Établissement', service: 'Service', poste: 'Poste', manager_id: 'Manager',
  type_contrat: 'Type de contrat', date_debut: 'Date de début de contrat', date_fin: 'Date de fin de contrat',
  statut: 'Statut', date_sortie: 'Date de sortie', motif_sortie: 'Motif de sortie', commentaire_sortie: 'Commentaire de sortie',
}
const ACTIONS = {
  creation: ['Création', 'info'], modification: ['Modification', 'neutre'], desactivation: ['Désactivation', 'danger'],
  sortie_programmee: ['Sortie programmée', 'alerte'], desactivation_auto: ['Désactivation automatique', 'danger'],
  reactivation: ['Réactivation', 'succes'],
}

// Liste déroulante d'un référentiel : valeurs actives + valeur actuelle si elle a été désactivée.
function Liste({ id, valeur, elements, onChange, onBlur, erreur, vide, format }) {
  const { t, nomRef } = useT()
  const visibles = elements.filter((e) => e.actif !== false || e.code === valeur)
  return (
    <select id={id} value={valeur} onChange={(e) => onChange(e.target.value)} onBlur={onBlur}
      aria-invalid={!!erreur} aria-describedby={erreur ? `${id}-erreur` : undefined} aria-required="true">
      <option value="">{vide || t('Sélectionner…')}</option>
      {visibles.map((e) => (
        <option key={e.code} value={e.code}>{format ? format(e) : nomRef(e)}{e.actif === false ? ` (${t('désactivé')})` : ''}</option>
      ))}
    </select>
  )
}

function ChoixManager({ valeur, resume, onChoix, exclure, etablissement, erreur, facultatif, onBlur }) {
  const { t } = useT()
  const [ouvert, setOuvert] = useState(false)
  const [q, setQ] = useState('')
  const [resultats, setResultats] = useState([])
  const [actif, setActif] = useState(-1)
  const conteneur = useRef(null)

  useEffect(() => {
    if (!ouvert) return
    const minuteur = setTimeout(() => {
      api('managers' + requete({ q, exclure, etablissement })).then((r) => { setResultats(r); setActif(-1) }).catch(() => setResultats([]))
    }, 200)
    return () => clearTimeout(minuteur)
  }, [q, ouvert, exclure, etablissement])

  useEffect(() => {
    const clic = (e) => { if (conteneur.current && !conteneur.current.contains(e.target)) { setOuvert(false) } }
    document.addEventListener('mousedown', clic)
    return () => document.removeEventListener('mousedown', clic)
  }, [])

  const choisir = (m) => { onChoix(m); setOuvert(false); setQ('') }

  if (valeur && resume && !ouvert) {
    return (
      <div className="manager-choisi">
        <span className="avatar petit" aria-hidden="true">{(resume.prenom || '?')[0]}{(resume.nom || '')[0]}</span>
        <span className="personne-texte">
          <strong>{nomComplet(resume)}</strong>
          <span>{resume.matricule} · {resume.etablissement}{resume.statut !== 'actif' ? ` · ${t('inactif')}` : ''}</span>
        </span>
        <button type="button" className="bouton bouton-lien" onClick={() => setOuvert(true)}>{t('Changer')}</button>
        {facultatif && <button type="button" className="bouton bouton-lien" onClick={() => onChoix(null)}>{t('Retirer')}</button>}
      </div>
    )
  }
  return (
    <div className="combo" ref={conteneur}>
      <input id="manager_id" type="text" role="combobox" aria-expanded={ouvert} aria-controls="manager-liste"
        aria-autocomplete="list" aria-invalid={!!erreur} aria-describedby={erreur ? 'manager_id-erreur' : 'manager_id-aide'}
        aria-activedescendant={actif >= 0 ? `manager-${actif}` : undefined}
        placeholder={t('Rechercher par nom, prénom ou matricule…')} value={q} autoComplete="off"
        onFocus={() => setOuvert(true)} onChange={(e) => { setQ(e.target.value); setOuvert(true) }} onBlur={onBlur}
        onKeyDown={(e) => {
          if (e.key === 'ArrowDown') { e.preventDefault(); setActif((a) => Math.min(a + 1, resultats.length - 1)) }
          if (e.key === 'ArrowUp') { e.preventDefault(); setActif((a) => Math.max(a - 1, 0)) }
          if (e.key === 'Enter' && actif >= 0) { e.preventDefault(); choisir(resultats[actif]) }
          if (e.key === 'Escape') setOuvert(false)
        }} />
      {ouvert && (
        <ul className="combo-liste" id="manager-liste" role="listbox">
          {resultats.length === 0 && <li className="combo-vide">{t('Aucun collaborateur actif trouvé.')}</li>}
          {resultats.map((m, i) => (
            <li key={m.id} id={`manager-${i}`} role="option" aria-selected={i === actif}
              className={i === actif ? 'actif' : ''} onMouseDown={(e) => { e.preventDefault(); choisir(m) }}>
              <strong>{nomComplet(m)}</strong>
              <span>{m.poste} · {m.etablissement} · {m.matricule}</span>
            </li>
          ))}
        </ul>
      )}
      {valeur && resume && <button type="button" className="bouton bouton-lien" onClick={() => setOuvert(false)}>{t('Garder {nom}', { nom: nomComplet(resume) })}</button>}
    </div>
  )
}

export default function Fiche({ id, moi, refs, admin, notifier }) {
  const { t, tn, ref, nomRef, date, dateHeure, langue } = useT()
  const nouveau = id === 'nouveau'
  const etabsAutorises = admin ? refs.etablissements : refs.etablissements.filter((e) => moi.sites.includes(e.code))
  const [form, setForm] = useState(null)
  const [original, setOriginal] = useState(null)
  const [details, setDetails] = useState(null)      // {collaborateur, manager, equipe, historique}
  const [manager, setManager] = useState(null)
  const [touches, setTouches] = useState({})
  const [tentative, setTentative] = useState(false)
  const [controle, setControle] = useState({ erreurs: {}, alertes: [] })
  const [erreur, setErreur] = useState(null)
  const [enCours, setEnCours] = useState(false)
  const [modale, setModale] = useState(null)
  const numero = useRef(0)

  const charger = useCallback(() => {
    if (nouveau) {
      const f = { ...VIDE, etablissement: etabsAutorises.length === 1 ? etabsAutorises[0].code : '' }
      setForm(f); setOriginal(f); setDetails(null); setManager(null)
      return
    }
    api(`collaborateurs/${id}`).then((d) => {
      const f = Object.fromEntries(Object.keys(VIDE).map((k) => [k, d.collaborateur[k] || '']))
      setForm(f); setOriginal(f); setDetails(d); setManager(d.manager); setTouches({}); setTentative(false)
    }).catch((e) => setErreur(e.message))
  }, [id, nouveau])
  useEffect(() => { charger() }, [charger])

  // Contrôles serveur (unicité Europe, cohérence, doublons) à chaque modification
  // et à chaque changement de langue (messages traduits par le serveur).
  useEffect(() => {
    if (!form) return
    const n = ++numero.current
    const minuteur = setTimeout(() => {
      api('collaborateurs/verifier', { method: 'POST', body: { collaborateur: form, id: nouveau ? null : id } })
        .then((r) => { if (n === numero.current) setControle(r) }).catch(() => {})
    }, 300)
    return () => clearTimeout(minuteur)
  }, [form, id, nouveau, langue])

  const modifie = useMemo(() => form && original && JSON.stringify(form) !== JSON.stringify(original), [form, original])
  useEffect(() => {
    if (!modifie) return
    const avertir = (e) => { e.preventDefault(); e.returnValue = '' }
    window.addEventListener('beforeunload', avertir)
    return () => window.removeEventListener('beforeunload', avertir)
  }, [modifie])

  if (erreur && !form) return <Bandeau ton="danger" titre={t('Fiche indisponible')}>{erreur}</Bandeau>
  if (!form) return <Chargement />

  const c = details?.collaborateur
  const changer = (champ, valeur) => setForm((f) => ({ ...f, [champ]: valeur }))
  const toucher = (champ) => () => setTouches((x) => ({ ...x, [champ]: true }))
  const erreurDe = (champ) => (touches[champ] || tentative) ? controle.erreurs[champ] : null
  const typeContrat = refs.types_contrat.find((x) => x.code === form.type_contrat)
  const poste = refs.postes.find((p) => p.code === form.poste)
  const finRequise = !!typeContrat?.date_fin_requise
  const managerFacultatif = !!poste?.sans_manager
  const erreursBloquantes = ORDRE.filter((k) => controle.erreurs[k])
  const doublon = controle.alertes.find((a) => a.type === 'doublon')
  const autresAlertes = controle.alertes.filter((a) => a.type !== 'doublon')
  const lecture = (champ) => ({
    id: champ, value: form[champ], onBlur: toucher(champ),
    'aria-invalid': !!erreurDe(champ), 'aria-required': true,
    'aria-describedby': erreurDe(champ) ? `${champ}-erreur` : `${champ}-aide`,
  })
  const statutTexte = (s) => (s === 'actif' ? t('actif') : t('inactif'))

  const enregistrer = async (confirmerDoublon = false) => {
    setTentative(true)
    if (erreursBloquantes.length) {
      document.getElementById(erreursBloquantes[0])?.focus()
      return
    }
    setEnCours(true)
    try {
      const corps = { collaborateur: form, confirmer_doublon: confirmerDoublon }
      if (nouveau) {
        const r = await api('collaborateurs', { method: 'POST', body: corps })
        setOriginal(form)
        notifier(t('Fiche de {nom} créée.', { nom: nomComplet(r.collaborateur) }))
        naviguer(`/collaborateurs/${r.collaborateur.id}`)
      } else {
        const r = await api(`collaborateurs/${id}`, { method: 'PUT', body: corps })
        notifier(r.changements ? t('Modifications enregistrées.') : t('Aucune modification à enregistrer.'), r.changements ? 'succes' : 'info')
        charger()
      }
      setModale(null)
    } catch (e) {
      if (e.statut === 409) setModale('doublon')
      else if (e.corps?.erreurs) { setControle({ erreurs: e.corps.erreurs, alertes: e.corps.alertes || [] }); notifier(e.message, 'alerte') }
      else notifier(e.message, 'alerte')
    } finally { setEnCours(false) }
  }

  const genererMatricule = async () => {
    try {
      const r = await api('matricule/generer', { method: 'POST', body: { etablissement: form.etablissement } })
      changer('matricule', r.matricule)
      setTouches((x) => ({ ...x, matricule: true }))
      notifier(t('Matricule {m} généré.', { m: r.matricule }))
    } catch (e) { notifier(e.message, 'alerte') }
  }

  const annuler = () => {
    if (modifie && !window.confirm(t('Abandonner les modifications non enregistrées ?'))) return
    if (nouveau) naviguer('/collaborateurs')
    else { setForm(original); setManager(details?.manager); setTouches({}); setTentative(false) }
  }

  const titre = nouveau ? t('Nouveau collaborateur') : nomComplet(c)
  const formatEtab = (e) => `${e.code} — ${nomRef(e)}`

  return (
    <>
      <EnTetePage
        retour={{ href: '#/collaborateurs', texte: t('Collaborateurs') }}
        titre={<>{titre}{c && <span className="titre-badge"><Statut statut={c.statut} /></span>}</>}
        sousTitre={c ? `${c.matricule} · ${ref(refs, 'postes', c.poste)} · ${c.etablissement} — ${ref(refs, 'etablissements', c.etablissement)}`
          : t('Tous les champs marqués * sont obligatoires.')}
        actions={c && (c.statut === 'actif'
          ? <Bouton variante="secondaire" icone="sortie" onClick={() => setModale('desactiver')} disabled={modifie}
            title={modifie ? t("Enregistrez d'abord les modifications") : undefined}>{t('Désactiver')}</Bouton>
          : <Bouton variante="secondaire" icone="reactiver" onClick={() => setModale('reactiver')} disabled={modifie}>{t('Réactiver')}</Bouton>)}
      />

      {c && c.statut !== 'actif' && (
        <Bandeau ton="alerte" titre={t('Collaborateur inactif depuis le {date}', { date: date(c.date_sortie) })}>
          {t('Motif : {motif}', { motif: ref(refs, 'motifs_sortie', c.motif_sortie) || '—' })}{c.commentaire_sortie ? ` — ${c.commentaire_sortie}` : ''}.{' '}
          {t('La fiche reste consultable et corrigeable ; utilisez « Réactiver » en cas de prolongation ou de retour.')}
        </Bandeau>
      )}
      {c && c.statut === 'actif' && c.motif_sortie && (
        <Bandeau ton="info" titre={t('Sortie programmée le {date}', { date: date(c.date_fin) })}>
          {t('Motif : {motif}', { motif: ref(refs, 'motifs_sortie', c.motif_sortie) })}. {t('Le collaborateur sera désactivé automatiquement le lendemain.')}
        </Bandeau>
      )}

      <div className="fiche-grille">
        <form className="fiche-formulaire" noValidate onSubmit={(e) => { e.preventDefault(); enregistrer() }}>
          {tentative && erreursBloquantes.length > 0 && (
            <div className="bandeau bandeau-danger" role="alert">
              <Icone nom="erreur" />
              <div>
                <strong>{tn(erreursBloquantes.length, 'Enregistrement impossible : {n} erreur à corriger', 'Enregistrement impossible : {n} erreurs à corriger')}</strong>
                <ul className="liste-erreurs">
                  {erreursBloquantes.map((k) => (
                    <li key={k}><a href={`#${k}`} onClick={(e) => { e.preventDefault(); document.getElementById(k)?.focus() }}>
                      {t(LIBELLES[k])} — {controle.erreurs[k]}</a></li>
                  ))}
                </ul>
              </div>
            </div>
          )}
          {doublon && (
            <div className="bandeau bandeau-alerte" role="status">
              <Icone nom="alerte" />
              <div>
                <strong>{doublon.message}</strong>
                <ul className="liste-erreurs">
                  {doublon.collaborateurs.map((d) => (
                    <li key={d.id}>{admin || moi.sites.includes(d.etablissement)
                      ? <a href={`#/collaborateurs/${d.id}`} target="_blank" rel="noreferrer">{d.prenom} {d.nom}</a>
                      : <>{d.prenom} {d.nom}</>} — {d.matricule} · {d.etablissement} · {statutTexte(d.statut)}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
          {autresAlertes.map((a) => <Bandeau key={a.type} ton="info">{a.message}</Bandeau>)}

          <section className="carte">
            <h2 className="carte-titre"><Icone nom="utilisateurs" />{t('Identité')}</h2>
            <div className="grille-champs">
              <Champ id="nom" label={t('Nom')} requis erreur={erreurDe('nom')} aide={t('Enregistré en majuscules.')}>
                <input type="text" {...lecture('nom')} autoComplete="off" maxLength={80} onChange={(e) => changer('nom', e.target.value)} />
              </Champ>
              <Champ id="prenom" label={t('Prénom')} requis erreur={erreurDe('prenom')}>
                <input type="text" {...lecture('prenom')} autoComplete="off" maxLength={80} onChange={(e) => changer('prenom', e.target.value)} />
              </Champ>
              <Champ id="sexe" label={t('Sexe')} requis erreur={erreurDe('sexe')}>
                <Liste id="sexe" valeur={form.sexe} elements={refs.sexes} erreur={erreurDe('sexe')} onBlur={toucher('sexe')} onChange={(v) => changer('sexe', v)} />
              </Champ>
              <Champ id="date_naissance" label={t('Date de naissance')} requis erreur={erreurDe('date_naissance')}>
                <input type="date" {...lecture('date_naissance')} max={moi.aujourd_hui} onChange={(e) => changer('date_naissance', e.target.value)} />
              </Champ>
              <Champ id="matricule" label={t('Matricule')} requis erreur={erreurDe('matricule')}
                aide={t('Unique en Europe. Sans matricule existant, générez-en un.')}>
                <div className="champ-avec-bouton">
                  <input type="text" {...lecture('matricule')} className="mono" autoComplete="off" maxLength={20}
                    onChange={(e) => changer('matricule', e.target.value.toUpperCase())} />
                  <Bouton variante="secondaire" icone="generer" onClick={genererMatricule}
                    disabled={!!form.matricule && !controle.erreurs.matricule}
                    title={form.matricule ? t('Videz le champ pour générer un nouveau matricule') : undefined}>{t('Générer un matricule')}</Bouton>
                </div>
              </Champ>
              <Champ id="email" label={t('Adresse e-mail Accor')} requis erreur={erreurDe('email')}
                aide={t('Adresse nominative du collaborateur (ex. prenom.nom@accor.com), unique en Europe.')}>
                <input type="email" {...lecture('email')} autoComplete="off" inputMode="email" onChange={(e) => changer('email', e.target.value.trim())} />
              </Champ>
            </div>
          </section>

          <section className="carte">
            <h2 className="carte-titre"><Icone nom="hotel" />{t('Affectation')}</h2>
            <div className="grille-champs">
              <Champ id="etablissement" label={t('Établissement')} requis erreur={erreurDe('etablissement')}>
                <Liste id="etablissement" valeur={form.etablissement} elements={etabsAutorises} format={formatEtab}
                  erreur={erreurDe('etablissement')} onBlur={toucher('etablissement')} onChange={(v) => changer('etablissement', v)} />
              </Champ>
              <Champ id="service" label={t('Service')} requis erreur={erreurDe('service')}>
                <Liste id="service" valeur={form.service} elements={refs.services} erreur={erreurDe('service')} onBlur={toucher('service')} onChange={(v) => changer('service', v)} />
              </Champ>
              <Champ id="poste" label={t('Poste')} requis erreur={erreurDe('poste')}>
                <Liste id="poste" valeur={form.poste} elements={refs.postes} erreur={erreurDe('poste')} onBlur={toucher('poste')} onChange={(v) => changer('poste', v)} />
              </Champ>
              <Champ id="manager_id" label={t('Manager')} requis={!managerFacultatif} erreur={erreurDe('manager_id')}
                aide={managerFacultatif ? t('Facultatif pour ce poste.') : t('Collaborateur actif existant dans la base (tous établissements).')}>
                <ChoixManager valeur={form.manager_id} resume={manager} exclure={nouveau ? '' : id} etablissement={form.etablissement}
                  erreur={erreurDe('manager_id')} facultatif={managerFacultatif} onBlur={toucher('manager_id')}
                  onChoix={(m) => { setManager(m); changer('manager_id', m ? m.id : ''); setTouches((x) => ({ ...x, manager_id: true })) }} />
              </Champ>
            </div>
          </section>

          <section className="carte">
            <h2 className="carte-titre"><Icone nom="calendrier" />{t('Contrat')}</h2>
            <div className="grille-champs">
              <Champ id="type_contrat" label={t('Type de contrat')} requis erreur={erreurDe('type_contrat')}>
                <Liste id="type_contrat" valeur={form.type_contrat} elements={refs.types_contrat} erreur={erreurDe('type_contrat')}
                  onBlur={toucher('type_contrat')} onChange={(v) => changer('type_contrat', v)} />
              </Champ>
              <Champ id="date_debut" label={t('Date de début de contrat')} requis erreur={erreurDe('date_debut')}>
                <input type="date" {...lecture('date_debut')} onChange={(e) => changer('date_debut', e.target.value)} />
              </Champ>
              <Champ id="date_fin" label={t('Date de fin de contrat')} requis={finRequise} erreur={erreurDe('date_fin')}
                aide={finRequise ? t('Obligatoire pour ce type de contrat.') : t('Facultative pour ce contrat : à renseigner seulement en cas de départ prévu.')}>
                <input type="date" {...lecture('date_fin')} aria-required={finRequise} min={form.date_debut || undefined}
                  onChange={(e) => changer('date_fin', e.target.value)} />
              </Champ>
            </div>
          </section>

          <div className="barre-enregistrer">
            <span className="discret">{modifie ? t('Modifications non enregistrées') : nouveau ? '' : t('Aucune modification')}</span>
            <Bouton variante="secondaire" onClick={annuler} disabled={!modifie && !nouveau}>{t('Annuler')}</Bouton>
            <Bouton type="submit" icone="valide" chargement={enCours} disabled={!nouveau && !modifie}>
              {nouveau ? t('Créer la fiche') : t('Enregistrer')}
            </Bouton>
          </div>
        </form>

        {c && (
          <aside className="fiche-cote">
            <section className="carte">
              <h2 className="carte-titre">{t('Informations')}</h2>
              <dl className="infos">
                <dt>{t('Créée le')}</dt><dd>{dateHeure(c.cree_le)}<span>{c.cree_par}</span></dd>
                <dt>{t('Modifiée le')}</dt><dd>{dateHeure(c.modifie_le)}<span>{c.modifie_par === 'automatisation' ? t('Désactivation automatique') : c.modifie_par}</span></dd>
              </dl>
            </section>
            {details.equipe.length > 0 && (
              <section className="carte">
                <h2 className="carte-titre"><Icone nom="equipe" />{t('Équipe managée ({n})', { n: details.equipe.length })}</h2>
                <ul className="liste-simple">
                  {details.equipe.map((m) => <li key={m.id}><a href={`#/collaborateurs/${m.id}`}>{nomComplet(m)}</a><span>{m.etablissement}</span></li>)}
                </ul>
              </section>
            )}
            <section className="carte">
              <h2 className="carte-titre"><Icone nom="historique" />{t('Historique')}</h2>
              <ol className="chronologie">
                {details.historique.map((h, i) => {
                  const [lib, ton] = ACTIONS[h.action] || [h.action, 'neutre']
                  return (
                    <li key={i}>
                      <div className="chrono-entete"><Badge ton={ton}>{t(lib)}</Badge><span>{dateHeure(h.le)}</span></div>
                      <p className="chrono-par">{t('par {nom}', { nom: h.par === 'automatisation' ? t('Désactivation automatique') : (h.par_nom || h.par) })}</p>
                      {h.action !== 'creation' && h.changements?.length > 0 && (
                        <ul className="changements">
                          {h.changements.map((ch) => (
                            <li key={ch.champ}><strong>{t(LIBELLES[ch.champ] || ch.libelle)}</strong> : <s>{ch.avant || t('vide')}</s> → {ch.apres || t('vide')}</li>
                          ))}
                        </ul>
                      )}
                    </li>
                  )
                })}
              </ol>
            </section>
            {admin && (
              <section className="carte zone-danger">
                <h2 className="carte-titre">{t('Effacement RGPD')}</h2>
                <p className="discret">{t("À réserver aux demandes d'effacement ou à l'expiration des durées de conservation. Privilégiez la désactivation, qui conserve l'historique.")}</p>
                <Bouton variante="danger" icone="corbeille" onClick={() => setModale('effacer')}>{t('Effacer définitivement')}</Bouton>
              </section>
            )}
          </aside>
        )}
      </div>

      {modale === 'doublon' && (
        <Modale titre={t('Doublon potentiel')} onFermer={() => setModale(null)} actions={<>
          <Bouton variante="secondaire" onClick={() => setModale(null)}>{t('Revenir à la fiche')}</Bouton>
          <Bouton chargement={enCours} onClick={() => enregistrer(true)}>{t("Il s'agit d'une autre personne : enregistrer")}</Bouton>
        </>}>
          <p>{t('Un collaborateur portant les mêmes nom, prénom et date de naissance existe déjà :')}</p>
          <ul className="liste-erreurs">
            {(doublon?.collaborateurs || []).map((d) => <li key={d.id}>{d.prenom} {d.nom} — {d.matricule} · {d.etablissement} · {statutTexte(d.statut)}</li>)}
          </ul>
          <p className="discret">{t("S'il s'agit de la même personne (retour, mutation), ouvrez plutôt sa fiche existante et réactivez-la ou modifiez son établissement.")}</p>
        </Modale>
      )}
      {modale === 'desactiver' && <ModaleSortie c={c} refs={refs} moi={moi} onFermer={() => setModale(null)}
        onFait={(r) => { setModale(null); notifier(r.programme ? t('Sortie programmée le {date}.', { date: date(r.collaborateur.date_fin) }) : t('Collaborateur désactivé.')); charger() }} />}
      {modale === 'reactiver' && <ModaleReactivation c={c} refs={refs} moi={moi} onFermer={() => setModale(null)}
        onFait={() => { setModale(null); notifier(t('Collaborateur réactivé.')); charger() }} />}
      {modale === 'effacer' && <ModaleEffacement c={c} onFermer={() => setModale(null)}
        onFait={() => { setModale(null); notifier(t('Données du collaborateur effacées.')); naviguer('/collaborateurs') }} />}
    </>
  )
}

function ModaleSortie({ c, refs, moi, onFermer, onFait }) {
  const { t } = useT()
  const [v, setV] = useState({ date_sortie: moi.aujourd_hui, motif_sortie: '', commentaire: '' })
  const [erreurs, setErreurs] = useState({})
  const [enCours, setEnCours] = useState(false)
  const futur = v.date_sortie > moi.aujourd_hui
  const valider = async () => {
    if (!v.motif_sortie) { setErreurs({ motif_sortie: t('Choisissez un motif de sortie.') }); return }
    setEnCours(true)
    try { onFait(await api(`collaborateurs/${c.id}/desactiver`, { method: 'POST', body: v })) }
    catch (e) { setErreurs(e.corps?.erreurs || { general: e.message }) }
    finally { setEnCours(false) }
  }
  return (
    <Modale titre={t('Désactiver {nom}', { nom: nomComplet(c) })} onFermer={onFermer} actions={<>
      <Bouton variante="secondaire" onClick={onFermer}>{t('Annuler')}</Bouton>
      <Bouton variante="danger" icone="sortie" chargement={enCours} onClick={valider}>{futur ? t('Programmer la sortie') : t('Désactiver')}</Bouton>
    </>}>
      <p className="discret">{t('La fiche est conservée avec son historique. Le collaborateur pourra être réactivé.')}</p>
      {erreurs.general && <Bandeau ton="danger">{erreurs.general}</Bandeau>}
      <Champ id="date_sortie" label={t("Dernier jour dans l'établissement")} requis erreur={erreurs.date_sortie}
        aide={futur ? t("Date future : le collaborateur reste actif jusqu'à cette date, puis est désactivé automatiquement.") : undefined}>
        <input id="date_sortie" type="date" value={v.date_sortie} min={c.date_debut} onChange={(e) => setV({ ...v, date_sortie: e.target.value })} />
      </Champ>
      <Champ id="motif_sortie" label={t('Motif de sortie')} requis erreur={erreurs.motif_sortie}>
        <Liste id="motif_sortie" valeur={v.motif_sortie} elements={refs.motifs_sortie} erreur={erreurs.motif_sortie}
          onChange={(x) => setV({ ...v, motif_sortie: x })} />
      </Champ>
      <Champ id="commentaire" label={t('Commentaire (facultatif)')}>
        <textarea id="commentaire" rows={2} maxLength={300} value={v.commentaire} onChange={(e) => setV({ ...v, commentaire: e.target.value })} />
      </Champ>
    </Modale>
  )
}

function ModaleReactivation({ c, refs, moi, onFermer, onFait }) {
  const { t } = useT()
  const [v, setV] = useState({ type_contrat: c.type_contrat, date_debut: c.date_debut, date_fin: '' })
  const [erreurs, setErreurs] = useState({})
  const [enCours, setEnCours] = useState(false)
  const tc = refs.types_contrat.find((x) => x.code === v.type_contrat)
  const valider = async () => {
    setEnCours(true)
    try { await api(`collaborateurs/${c.id}/reactiver`, { method: 'POST', body: v }); onFait() }
    catch (e) { setErreurs(e.corps?.erreurs || { general: e.message }) }
    finally { setEnCours(false) }
  }
  return (
    <Modale titre={t('Réactiver {nom}', { nom: nomComplet(c) })} onFermer={onFermer} actions={<>
      <Bouton variante="secondaire" onClick={onFermer}>{t('Annuler')}</Bouton>
      <Bouton icone="reactiver" chargement={enCours} onClick={valider}>{t('Réactiver')}</Bouton>
    </>}>
      <p className="discret">{t("Prolongation de contrat ou retour dans l'entreprise : indiquez le nouveau contrat.")}</p>
      {erreurs.general && <Bandeau ton="danger">{erreurs.general}</Bandeau>}
      {Object.entries(erreurs).filter(([k]) => !['general', 'type_contrat', 'date_debut', 'date_fin'].includes(k)).map(([k, m]) =>
        <Bandeau key={k} ton="danger">{m}</Bandeau>)}
      <Champ id="r-type" label={t('Type de contrat')} requis erreur={erreurs.type_contrat}>
        <Liste id="r-type" valeur={v.type_contrat} elements={refs.types_contrat} onChange={(x) => setV({ ...v, type_contrat: x })} />
      </Champ>
      <Champ id="r-debut" label={t('Date de début de contrat')} requis erreur={erreurs.date_debut}
        aide={t("Conservez la date d'origine pour une prolongation ; indiquez la date de retour sinon.")}>
        <input id="r-debut" type="date" value={v.date_debut} onChange={(e) => setV({ ...v, date_debut: e.target.value })} />
      </Champ>
      <Champ id="r-fin" label={t('Nouvelle date de fin de contrat')} requis={!!tc?.date_fin_requise} erreur={erreurs.date_fin}
        aide={tc?.date_fin_requise ? t('Obligatoire pour ce type de contrat.') : t('Laisser vide pour un contrat sans date de fin.')}>
        <input id="r-fin" type="date" value={v.date_fin} min={moi.aujourd_hui} onChange={(e) => setV({ ...v, date_fin: e.target.value })} />
      </Champ>
    </Modale>
  )
}

function ModaleEffacement({ c, onFermer, onFait }) {
  const { t } = useT()
  const [saisie, setSaisie] = useState('')
  const [erreur, setErreur] = useState(null)
  const [enCours, setEnCours] = useState(false)
  const valider = async () => {
    setEnCours(true)
    try { await api(`collaborateurs/${c.id}`, { method: 'DELETE', body: { confirmation: saisie } }); onFait() }
    catch (e) { setErreur(e.message) }
    finally { setEnCours(false) }
  }
  return (
    <Modale titre={t('Effacer définitivement')} onFermer={onFermer} actions={<>
      <Bouton variante="secondaire" onClick={onFermer}>{t('Annuler')}</Bouton>
      <Bouton variante="danger" icone="corbeille" chargement={enCours} disabled={saisie !== 'EFFACER'} onClick={valider}>{t('Effacer')}</Bouton>
    </>}>
      <Bandeau ton="danger" titre={t('Action irréversible')}>
        {t("La fiche de {nom} ({matricule}) sera supprimée et son historique anonymisé. Seule la trace de l'effacement sera conservée.", { nom: nomComplet(c), matricule: c.matricule })}
      </Bandeau>
      {erreur && <Bandeau ton="danger">{erreur}</Bandeau>}
      <Champ id="confirmation" label={t('Pour confirmer, saisissez EFFACER')}>
        <input id="confirmation" type="text" value={saisie} autoComplete="off" onChange={(e) => setSaisie(e.target.value)} />
      </Champ>
    </Modale>
  )
}
