import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'
import { Bandeau, Chargement, EnTetePage, Icone, Statut, Vide } from '../composants.jsx'
import { useT } from '../i18n.js'
import { naviguer, sansAccents } from '../outils.js'

const COLONNES = [
  { cle: 'matricule', titre: 'Matricule' },
  { cle: 'nom', titre: 'Nom' },
  { cle: 'prenom', titre: 'Prénom' },
  { cle: 'statut', titre: 'Statut' },
  { cle: 'poste', titre: 'Poste', ref: 'postes' },
  { cle: 'service', titre: 'Service', ref: 'services' },
  { cle: 'etablissement', titre: 'Établissement' },
  { cle: 'type_contrat', titre: 'Contrat', ref: 'types_contrat' },
  { cle: 'date_debut', titre: 'Début', date: true },
  { cle: 'date_fin', titre: 'Fin', date: true },
]
const FILTRES = [
  { cle: 'statut', titre: 'Statut' },
  { cle: 'etablissement', titre: 'Établissement', ref: 'etablissements' },
  { cle: 'service', titre: 'Service', ref: 'services' },
  { cle: 'type_contrat', titre: 'Type de contrat', ref: 'types_contrat' },
  { cle: 'poste', titre: 'Poste', ref: 'postes' },
  { cle: 'sexe', titre: 'Sexe', ref: 'sexes' },
]
const PAR_PAGE = 25

export default function Collaborateurs({ refs, params, moi, admin }) {
  const { t, tn, ref, nomRef, date, locale } = useT()
  const [liste, setListe] = useState(null)
  const [erreur, setErreur] = useState(null)
  const [texte, setTexte] = useState(params.q || '')
  const [filtres, setFiltres] = useState(() => ({
    statut: params.statut ?? 'actif', etablissement: params.etablissement || '', service: params.service || '',
    type_contrat: params.type_contrat || '', poste: params.poste || '', sexe: params.sexe || '',
  }))
  const [tri, setTri] = useState({ cle: 'nom', sens: 1 })
  const [page, setPage] = useState(1)

  useEffect(() => { api('collaborateurs').then(setListe).catch((e) => setErreur(e.message)) }, [])
  useEffect(() => { setPage(1) }, [texte, filtres, tri])

  const valeurAffichee = (c, col) => col.ref ? ref(refs, col.ref, c[col.cle]) : c[col.cle] || ''

  const resultat = useMemo(() => {
    if (!liste) return []
    const mots = sansAccents(texte).split(/\s+/).filter(Boolean)
    const res = liste.filter((c) => {
      for (const f of FILTRES) if (filtres[f.cle] && c[f.cle] !== filtres[f.cle]) return false
      if (!mots.length) return true
      const cible = sansAccents([c.matricule, c.nom, c.prenom, c.email, c.manager_nom, c.etablissement,
        ref(refs, 'postes', c.poste), ref(refs, 'services', c.service)].join(' '))
      return mots.every((m) => cible.includes(m))
    })
    const col = COLONNES.find((x) => x.cle === tri.cle)
    return res.sort((a, b) => tri.sens * String(valeurAffichee(a, col)).localeCompare(String(valeurAffichee(b, col)), locale, { numeric: true })
      || String(a.prenom).localeCompare(String(b.prenom), locale))
  }, [liste, texte, filtres, tri, refs, locale])

  const optionsFiltre = (f) => {
    if (f.cle === 'statut') return [{ code: 'actif', libelle: t('Actifs') }, { code: 'inactif', libelle: t('Inactifs') }]
    const presents = new Set((liste || []).map((c) => c[f.cle]))
    return refs[f.ref].filter((e) => presents.has(e.code))
      .map((e) => ({ code: e.code, libelle: f.cle === 'etablissement' ? `${e.code} — ${nomRef(e)}` : nomRef(e) }))
  }
  const nbFiltres = Object.entries(filtres).filter(([k, v]) => v && k !== 'statut').length + (texte ? 1 : 0)
  const pages = Math.max(1, Math.ceil(resultat.length / PAR_PAGE))
  const visibles = resultat.slice((page - 1) * PAR_PAGE, page * PAR_PAGE)
  const trier = (cle) => setTri((x) => ({ cle, sens: x.cle === cle ? -x.sens : 1 }))

  return (
    <>
      <EnTetePage
        titre={t('Collaborateurs')}
        sousTitre={admin ? t('Tous les établissements européens') : t('Vos établissements : {liste}', { liste: moi.sites.join(', ') || t('aucun') })}
        actions={<a className="bouton bouton-primaire" href="#/collaborateurs/nouveau"><Icone nom="plus" />{t('Ajouter un collaborateur')}</a>}
      />
      {erreur && <Bandeau ton="danger">{erreur}</Bandeau>}
      <div className="carte barre-outils">
        <div className="recherche">
          <Icone nom="recherche" />
          <label htmlFor="recherche" className="visuellement-cache">{t('Rechercher un collaborateur')}</label>
          <input id="recherche" type="search" value={texte} onChange={(e) => setTexte(e.target.value)}
            placeholder={t('Nom, prénom, matricule, e-mail, poste…')} autoComplete="off" />
        </div>
        <div className="filtres">
          {FILTRES.map((f) => (
            <div className="filtre" key={f.cle}>
              <label htmlFor={`f-${f.cle}`}>{t(f.titre)}</label>
              <select id={`f-${f.cle}`} value={filtres[f.cle]} onChange={(e) => setFiltres({ ...filtres, [f.cle]: e.target.value })}>
                <option value="">{t('Tous')}</option>
                {optionsFiltre(f).map((o) => <option key={o.code} value={o.code}>{o.libelle}</option>)}
              </select>
            </div>
          ))}
          {nbFiltres > 0 && (
            <button type="button" className="bouton bouton-lien" onClick={() => {
              setTexte(''); setFiltres({ statut: filtres.statut, etablissement: '', service: '', type_contrat: '', poste: '', sexe: '' })
            }}><Icone nom="fermer" taille={16} />{t('Effacer les filtres')}</button>
          )}
        </div>
      </div>

      {!liste && !erreur && <Chargement />}
      {liste && (
        <section className="carte carte-tableau">
          <div className="tableau-entete">
            <p aria-live="polite"><strong>{tn(resultat.length, '{n} collaborateur', '{n} collaborateurs')}</strong>
              {resultat.length !== liste.length && <span className="discret"> {t('sur {n}', { n: liste.length })}</span>}</p>
          </div>
          {resultat.length === 0 ? (
            <Vide icone="recherche" titre={liste.length ? t('Aucun résultat') : t('Aucun collaborateur')}>
              {liste.length ? t('Modifiez la recherche ou les filtres.') : <a className="bouton bouton-primaire" href="#/collaborateurs/nouveau"><Icone nom="plus" />{t('Ajouter un collaborateur')}</a>}
            </Vide>
          ) : (
            <div className="defilement-tableau">
              <table className="tableau tableau-cliquable">
                <thead>
                  <tr>
                    {COLONNES.map((col) => (
                      <th key={col.cle} scope="col" aria-sort={tri.cle === col.cle ? (tri.sens > 0 ? 'ascending' : 'descending') : 'none'}>
                        <button type="button" className="tri" onClick={() => trier(col.cle)}>
                          {t(col.titre)}<Icone nom={tri.cle === col.cle ? (tri.sens > 0 ? 'haut' : 'bas') : 'tri'} taille={14} />
                        </button>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {visibles.map((c) => (
                    <tr key={c.id} tabIndex={0} onClick={() => naviguer(`/collaborateurs/${c.id}`)}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); naviguer(`/collaborateurs/${c.id}`) } }}
                      aria-label={t('Ouvrir la fiche de {nom}', { nom: `${c.prenom} ${c.nom}` })}>
                      {COLONNES.map((col) => (
                        <td key={col.cle} className={col.cle === 'nom' ? 'fort' : col.cle === 'matricule' ? 'mono' : ''}>
                          {col.cle === 'statut' ? <Statut statut={c.statut} />
                            : col.date ? date(c[col.cle]) || <span className="discret">—</span>
                              : valeurAffichee(c, col)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {pages > 1 && (
            <nav className="pagination" aria-label={t('Pagination')}>
              <button type="button" className="bouton bouton-secondaire" disabled={page === 1} onClick={() => setPage(page - 1)}>
                <Icone nom="retour" taille={16} />{t('Précédent')}</button>
              <span>{t('Page {page} / {total}', { page, total: pages })}</span>
              <button type="button" className="bouton bouton-secondaire" disabled={page === pages} onClick={() => setPage(page + 1)}>
                {t('Suivant')}<Icone nom="suivant" taille={16} /></button>
            </nav>
          )}
        </section>
      )}
    </>
  )
}
