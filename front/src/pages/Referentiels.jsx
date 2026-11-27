import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import { Bandeau, Bouton, EnTetePage, Icone } from '../composants.jsx'
import { LANGUES, useT } from '../i18n.js'

const ORDRE = ['etablissements', 'services', 'postes', 'types_contrat', 'sexes', 'pays', 'motifs_sortie']
const TITRES = {
  etablissements: 'Établissements', services: 'Services', postes: 'Postes', types_contrat: 'Types de contrat',
  sexes: 'Sexe', pays: 'Pays', motifs_sortie: 'Motifs de sortie',
}
const AUTRES_LANGUES = ['en', 'de', 'es', 'it']
// Les noms d'établissements sont des noms propres : pas de traduction.
const TRADUISIBLE = (type) => type !== 'etablissements'

export default function Referentiels({ refs, chargerRefs, notifier }) {
  const { t, nomRef } = useT()
  const [type, setType] = useState('etablissements')
  const [lignes, setLignes] = useState([])
  const [erreurs, setErreurs] = useState([])
  const [enCours, setEnCours] = useState(false)
  const fichier = useRef(null)

  const copie = (liste) => (liste || []).map((e) => ({ ...e, traductions: { ...(e.traductions || {}) } }))
  useEffect(() => { setLignes(copie(refs[type])); setErreurs([]) }, [type, refs])

  const modifie = JSON.stringify(lignes) !== JSON.stringify(copie(refs[type]))
  const changer = (i, champ, valeur) => setLignes(lignes.map((l, j) => (j === i ? { ...l, [champ]: valeur } : l)))
  const changerTrad = (i, lang, valeur) => setLignes(lignes.map((l, j) => (j === i ? { ...l, traductions: { ...l.traductions, [lang]: valeur } } : l)))
  const ajouter = () => setLignes([...lignes, {
    _nouveau: true, code: '', libelle: '', actif: true, traductions: {},
    ...(type === 'etablissements' ? { pays: '' } : {}), ...(type === 'postes' ? { sans_manager: false } : {}),
    ...(type === 'types_contrat' ? { date_fin_requise: true } : {}),
  }])

  const enregistrer = async () => {
    setEnCours(true); setErreurs([])
    try {
      await api(`referentiels/${type}`, { method: 'PUT', body: { elements: lignes } })
      await chargerRefs()
      notifier(t('Référentiel « {nom} » enregistré.', { nom: t(TITRES[type]) }))
    } catch (e) { setErreurs(e.corps?.details || [e.message]) }
    finally { setEnCours(false) }
  }

  const importer = async (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    const donnees = new FormData()
    donnees.append('fichier', f)
    setEnCours(true); setErreurs([])
    try {
      const r = await api('referentiels/etablissements/import', { method: 'POST', body: donnees })
      await chargerRefs()
      notifier(t('Import terminé : {ajoutes} ajouté(s), {maj} mis à jour.', { ajoutes: r.ajoutes, maj: r.mis_a_jour }))
    } catch (err) { setErreurs(err.corps?.details || [err.message]) }
    finally { setEnCours(false); e.target.value = '' }
  }

  return (
    <>
      <EnTetePage titre={t('Référentiels')} sousTitre={t("Listes déroulantes standardisées à l'échelle européenne")} />
      <div className="onglets" role="tablist" aria-label={t('Référentiels')}>
        {ORDRE.map((x) => (
          <button key={x} type="button" role="tab" aria-selected={type === x} className={type === x ? 'actif' : ''}
            onClick={() => { if (!modifie || window.confirm(t('Abandonner les modifications non enregistrées ?'))) setType(x) }}>
            {t(TITRES[x])}<span className="onglet-nb">{(refs[x] || []).length}</span>
          </button>
        ))}
      </div>
      <section className="carte carte-tableau" role="tabpanel">
        <div className="tableau-entete">
          <p className="discret">{t('Un code utilisé par des collaborateurs ne peut pas être supprimé : décochez « Actif » pour ne plus le proposer.')}
            {TRADUISIBLE(type) && <> {t("Libellé de référence en français (exports) ; une traduction vide affiche le libellé français.")}</>}</p>
          {type === 'etablissements' && (
            <>
              <input ref={fichier} type="file" accept=".xlsx,.csv" hidden onChange={importer} />
              <Bouton variante="secondaire" icone="importer" onClick={() => fichier.current?.click()} disabled={enCours}>
                {t('Importer (Excel / CSV)')}</Bouton>
            </>
          )}
        </div>
        {type === 'etablissements' && <p className="discret aide-import">{t('Import : colonnes')} <code>code</code>, <code>nom</code>, <code>pays</code> {t('(code ISO ou nom). Les codes existants sont mis à jour.')}</p>}
        {erreurs.length > 0 && <Bandeau ton="danger" titre={t('Non enregistré')}><ul className="liste-erreurs">{erreurs.map((e) => <li key={e}>{e}</li>)}</ul></Bandeau>}
        <div className="defilement-tableau">
          <table className="tableau tableau-edition">
            <thead>
              <tr>
                <th scope="col">{t('Code')}</th><th scope="col">{t('Libellé')} {TRADUISIBLE(type) && '(FR)'}</th>
                {TRADUISIBLE(type) && AUTRES_LANGUES.map((l) => <th key={l} scope="col" title={LANGUES[l]}>{l.toUpperCase()}</th>)}
                {type === 'etablissements' && <th scope="col">{t('Pays')}</th>}
                {type === 'postes' && <th scope="col">{t('Manager facultatif')}</th>}
                {type === 'types_contrat' && <th scope="col">{t('Date de fin obligatoire')}</th>}
                <th scope="col">{t('Actif')}</th><th scope="col"><span className="visuellement-cache">{t('Retirer')}</span></th>
              </tr>
            </thead>
            <tbody>
              {lignes.map((l, i) => (
                <tr key={i} className={l.actif ? '' : 'ligne-inactive'}>
                  <td><input type="text" aria-label={t('Code')} className="mono" value={l.code} readOnly={!l._nouveau}
                    title={l._nouveau ? undefined : t('Code enregistré : non modifiable')}
                    onChange={(e) => changer(i, 'code', e.target.value.toUpperCase())} maxLength={20} /></td>
                  <td className="col-libelle"><input type="text" aria-label={t('Libellé')} value={l.libelle} onChange={(e) => changer(i, 'libelle', e.target.value)} maxLength={120} /></td>
                  {TRADUISIBLE(type) && AUTRES_LANGUES.map((lang) => (
                    <td key={lang} className="col-traduction">
                      <input type="text" lang={lang} aria-label={`${t('Libellé')} — ${LANGUES[lang]}`} value={l.traductions?.[lang] || ''}
                        placeholder={l.libelle} onChange={(e) => changerTrad(i, lang, e.target.value)} maxLength={120} />
                    </td>
                  ))}
                  {type === 'etablissements' && (
                    <td><select aria-label={t('Pays')} value={l.pays} onChange={(e) => changer(i, 'pays', e.target.value)}>
                      <option value="">—</option>
                      {refs.pays.map((p) => <option key={p.code} value={p.code}>{nomRef(p)}</option>)}
                    </select></td>
                  )}
                  {type === 'postes' && <td className="centre"><input type="checkbox" aria-label={t('Manager facultatif')} checked={!!l.sans_manager} onChange={(e) => changer(i, 'sans_manager', e.target.checked)} /></td>}
                  {type === 'types_contrat' && <td className="centre"><input type="checkbox" aria-label={t('Date de fin obligatoire')} checked={!!l.date_fin_requise} onChange={(e) => changer(i, 'date_fin_requise', e.target.checked)} /></td>}
                  <td className="centre"><input type="checkbox" aria-label={t('Actif')} checked={!!l.actif} onChange={(e) => changer(i, 'actif', e.target.checked)} /></td>
                  <td className="centre">
                    <button type="button" className="bouton-icone" aria-label={t('Retirer {code}', { code: l.code || t('la ligne') })}
                      onClick={() => setLignes(lignes.filter((_, j) => j !== i))}><Icone nom="corbeille" taille={16} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="barre-enregistrer">
          <Bouton variante="secondaire" icone="plus" onClick={ajouter}>{t('Ajouter une ligne')}</Bouton>
          <span className="espace" />
          {modifie && <span className="discret">{t('Modifications non enregistrées')}</span>}
          <Bouton variante="secondaire" onClick={() => setLignes(copie(refs[type]))} disabled={!modifie}>{t('Annuler')}</Bouton>
          <Bouton icone="valide" chargement={enCours} disabled={!modifie} onClick={enregistrer}>{t('Enregistrer')}</Bouton>
        </div>
      </section>
    </>
  )
}
