import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'
import { Badge, Bandeau, Bouton, Champ, Chargement, EnTetePage, Icone, Modale, Vide } from '../composants.jsx'
import { useT } from '../i18n.js'
import { sansAccents } from '../outils.js'

function Edition({ utilisateur, roles, refs, onFermer, onFait }) {
  const { t, tn, nomRef } = useT()
  const [v, setV] = useState(utilisateur || { email: '', name: '', role: 'gm', sites: [] })
  const [q, setQ] = useState('')
  const [erreur, setErreur] = useState(null)
  const [enCours, setEnCours] = useState(false)
  const filtres = refs.etablissements.filter((e) => sansAccents(`${e.code} ${e.libelle}`).includes(sansAccents(q)))
  const basculer = (code) => setV({ ...v, sites: v.sites.includes(code) ? v.sites.filter((s) => s !== code) : [...v.sites, code] })
  const valider = async () => {
    setEnCours(true); setErreur(null)
    try { await api('utilisateurs', { method: 'PUT', body: v }); onFait() }
    catch (e) { setErreur(e.message) } finally { setEnCours(false) }
  }
  return (
    <Modale large titre={utilisateur ? t('Droits de {email}', { email: utilisateur.email }) : t('Ajouter un utilisateur')} onFermer={onFermer} actions={<>
      <Bouton variante="secondaire" onClick={onFermer}>{t('Annuler')}</Bouton>
      <Bouton icone="valide" chargement={enCours} onClick={valider}>{t('Enregistrer')}</Bouton>
    </>}>
      {erreur && <Bandeau ton="danger">{erreur}</Bandeau>}
      <div className="grille-champs">
        <Champ id="u-email" label={t('Adresse e-mail (compte Microsoft Adagio)')} requis>
          <input id="u-email" type="email" value={v.email} readOnly={!!utilisateur} onChange={(e) => setV({ ...v, email: e.target.value.trim() })} />
        </Champ>
        <Champ id="u-nom" label={t('Nom affiché')}>
          <input id="u-nom" type="text" value={v.name || ''} onChange={(e) => setV({ ...v, name: e.target.value })} />
        </Champ>
        <Champ id="u-role" label={t('Profil')} requis>
          <select id="u-role" value={v.role} onChange={(e) => setV({ ...v, role: e.target.value })}>
            {Object.entries(roles).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </select>
        </Champ>
      </div>
      {v.role === 'gm' && (
        <fieldset className="choix">
          <legend>{tn(v.sites.length, 'Établissements ({n} sélectionné)', 'Établissements ({n} sélectionnés)')}</legend>
          <input type="search" aria-label={t('Filtrer les établissements')} placeholder={t('Filtrer…')} value={q} onChange={(e) => setQ(e.target.value)} />
          <div className="liste-cases">
            {filtres.map((e) => (
              <label key={e.code} className="case">
                <input type="checkbox" checked={v.sites.includes(e.code)} onChange={() => basculer(e.code)} />
                <span className="mono">{e.code}</span> {nomRef(e)}
              </label>
            ))}
            {filtres.length === 0 && <p className="discret">{t('Aucun établissement.')}</p>}
          </div>
        </fieldset>
      )}
      <Bandeau ton="info">{t("L'utilisateur doit aussi disposer de l'App Role App.RHEUROPE, attribué dans Azure par l'administrateur du portail.")}</Bandeau>
    </Modale>
  )
}

export default function Utilisateurs({ refs, moi, notifier }) {
  const { t, dateHeure } = useT()
  const [donnees, setDonnees] = useState(null)
  const [erreur, setErreur] = useState(null)
  const [edition, setEdition] = useState(null)   // null | 'nouveau' | utilisateur
  const charger = useCallback(() => api('utilisateurs').then(setDonnees).catch((e) => setErreur(e.message)), [])
  useEffect(() => { charger() }, [charger])

  const retirer = async (u) => {
    if (!window.confirm(t("Retirer l'accès de {email} à HR EUROPE ?", { email: u.email }))) return
    try { await api(`utilisateurs/${encodeURIComponent(u.email)}`, { method: 'DELETE' }); notifier(t('Accès retiré.')); charger() }
    catch (e) { notifier(e.message, 'alerte') }
  }

  if (erreur) return <Bandeau ton="danger">{erreur}</Bandeau>
  if (!donnees) return <Chargement />
  const tons = { admin: 'info', gm: 'succes', aucun: 'neutre' }

  return (
    <>
      <EnTetePage titre={t('Utilisateurs et droits')} sousTitre={t('Profil et établissements de chaque utilisateur de HR EUROPE')}
        actions={<Bouton icone="plus" onClick={() => setEdition('nouveau')}>{t('Ajouter un utilisateur')}</Bouton>} />
      <Bandeau ton="info">
        {t("À la première connexion : un administrateur du portail devient administrateur ; une adresse d'hôtel (hXXXX@…) devient directeur de l'hôtel HXXXX ; les autres comptes n'ont aucun accès tant qu'un profil ne leur est pas attribué ici.")}
      </Bandeau>
      <section className="carte carte-tableau">
        {donnees.utilisateurs.length === 0 ? <Vide icone="utilisateurs" titre={t('Aucun utilisateur enregistré')} /> : (
          <div className="defilement-tableau">
            <table className="tableau">
              <thead><tr><th scope="col">{t('Utilisateur')}</th><th scope="col">{t('Profil')}</th><th scope="col">{t('Établissements')}</th><th scope="col">{t('Mis à jour')}</th><th scope="col"><span className="visuellement-cache">{t('Actions')}</span></th></tr></thead>
              <tbody>
                {donnees.utilisateurs.map((u) => (
                  <tr key={u.email}>
                    <td><strong>{u.name || u.email}</strong><div className="discret">{u.email}</div></td>
                    <td><Badge ton={tons[u.role] || 'neutre'}>{donnees.roles[u.role] || u.role}</Badge></td>
                    <td>{u.role === 'admin' ? <span className="discret">{t('Tous')}</span> : (u.sites || []).join(', ') || <span className="discret">—</span>}</td>
                    <td className="nowrap">{dateHeure(u.updated_at)}<div className="discret">{u.source === 'auto' ? t('automatique') : t('manuel')}</div></td>
                    <td className="actions-ligne">
                      <button type="button" className="bouton-icone" aria-label={t('Modifier {email}', { email: u.email })} onClick={() => setEdition({ ...u, sites: u.sites || [] })}><Icone nom="crayon" taille={16} /></button>
                      {u.email !== moi.email && <button type="button" className="bouton-icone" aria-label={t('Retirer {code}', { code: u.email })} onClick={() => retirer(u)}><Icone nom="corbeille" taille={16} /></button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      {edition && <Edition utilisateur={edition === 'nouveau' ? null : edition} roles={donnees.roles} refs={refs}
        onFermer={() => setEdition(null)} onFait={() => { setEdition(null); notifier(t('Droits enregistrés.')); charger() }} />}
    </>
  )
}
