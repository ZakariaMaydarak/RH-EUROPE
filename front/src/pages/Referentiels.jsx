import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import { Bandeau, Bouton, EnTetePage, Icone } from '../composants.jsx'

const ORDRE = ['etablissements', 'services', 'postes', 'types_contrat', 'sexes', 'pays', 'motifs_sortie']
const TITRES = {
  etablissements: 'Établissements', services: 'Services', postes: 'Postes', types_contrat: 'Types de contrat',
  sexes: 'Sexe', pays: 'Pays', motifs_sortie: 'Motifs de sortie',
}

export default function Referentiels({ refs, chargerRefs, notifier }) {
  const [type, setType] = useState('etablissements')
  const [lignes, setLignes] = useState([])
  const [erreurs, setErreurs] = useState([])
  const [enCours, setEnCours] = useState(false)
  const fichier = useRef(null)

  useEffect(() => {
    setLignes((refs[type] || []).map((e) => ({ ...e })))
    setErreurs([])
  }, [type, refs])

  const modifie = JSON.stringify(lignes) !== JSON.stringify(refs[type] || [])
  const changer = (i, champ, valeur) => setLignes(lignes.map((l, j) => (j === i ? { ...l, [champ]: valeur } : l)))
  const ajouter = () => setLignes([...lignes, {
    _nouveau: true, code: '', libelle: '', actif: true,
    ...(type === 'etablissements' ? { pays: '' } : {}), ...(type === 'postes' ? { sans_manager: false } : {}),
    ...(type === 'types_contrat' ? { date_fin_requise: true } : {}),
  }])

  const enregistrer = async () => {
    setEnCours(true); setErreurs([])
    try {
      await api(`referentiels/${type}`, { method: 'PUT', body: { elements: lignes } })
      await chargerRefs()
      notifier(`Référentiel « ${TITRES[type]} » enregistré.`)
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
      notifier(`Import terminé : ${r.ajoutes} ajouté(s), ${r.mis_a_jour} mis à jour.`)
    } catch (err) { setErreurs(err.corps?.details || [err.message]) }
    finally { setEnCours(false); e.target.value = '' }
  }

  return (
    <>
      <EnTetePage titre="Référentiels" sousTitre="Listes déroulantes standardisées à l'échelle européenne" />
      <div className="onglets" role="tablist" aria-label="Référentiels">
        {ORDRE.map((t) => (
          <button key={t} type="button" role="tab" aria-selected={type === t} className={type === t ? 'actif' : ''}
            onClick={() => { if (!modifie || window.confirm('Abandonner les modifications non enregistrées ?')) setType(t) }}>
            {TITRES[t]}<span className="onglet-nb">{(refs[t] || []).length}</span>
          </button>
        ))}
      </div>
      <section className="carte carte-tableau" role="tabpanel">
        <div className="tableau-entete">
          <p className="discret">Un code utilisé par des collaborateurs ne peut pas être supprimé : décochez « Actif » pour ne plus le proposer.</p>
          {type === 'etablissements' && (
            <>
              <input ref={fichier} type="file" accept=".xlsx,.csv" hidden onChange={importer} />
              <Bouton variante="secondaire" icone="importer" onClick={() => fichier.current?.click()} disabled={enCours}>
                Importer (Excel / CSV)</Bouton>
            </>
          )}
        </div>
        {type === 'etablissements' && <p className="discret aide-import">Import : colonnes <code>code</code>, <code>nom</code>, <code>pays</code> (code ISO ou nom). Les codes existants sont mis à jour.</p>}
        {erreurs.length > 0 && <Bandeau ton="danger" titre="Non enregistré"><ul className="liste-erreurs">{erreurs.map((e) => <li key={e}>{e}</li>)}</ul></Bandeau>}
        <div className="defilement-tableau">
          <table className="tableau tableau-edition">
            <thead>
              <tr>
                <th scope="col">Code</th><th scope="col">Libellé</th>
                {type === 'etablissements' && <th scope="col">Pays</th>}
                {type === 'postes' && <th scope="col">Manager facultatif</th>}
                {type === 'types_contrat' && <th scope="col">Date de fin obligatoire</th>}
                <th scope="col">Actif</th><th scope="col"><span className="visuellement-cache">Retirer</span></th>
              </tr>
            </thead>
            <tbody>
              {lignes.map((l, i) => {
                return (
                  <tr key={i} className={l.actif ? '' : 'ligne-inactive'}>
                    <td><input type="text" aria-label="Code" className="mono" value={l.code} readOnly={!l._nouveau}
                      title={l._nouveau ? undefined : 'Code enregistré : non modifiable'}
                      onChange={(e) => changer(i, 'code', e.target.value.toUpperCase())} maxLength={20} /></td>
                    <td className="col-libelle"><input type="text" aria-label="Libellé" value={l.libelle} onChange={(e) => changer(i, 'libelle', e.target.value)} maxLength={120} /></td>
                    {type === 'etablissements' && (
                      <td><select aria-label="Pays" value={l.pays} onChange={(e) => changer(i, 'pays', e.target.value)}>
                        <option value="">—</option>
                        {refs.pays.map((p) => <option key={p.code} value={p.code}>{p.libelle}</option>)}
                      </select></td>
                    )}
                    {type === 'postes' && <td className="centre"><input type="checkbox" aria-label="Manager facultatif" checked={!!l.sans_manager} onChange={(e) => changer(i, 'sans_manager', e.target.checked)} /></td>}
                    {type === 'types_contrat' && <td className="centre"><input type="checkbox" aria-label="Date de fin obligatoire" checked={!!l.date_fin_requise} onChange={(e) => changer(i, 'date_fin_requise', e.target.checked)} /></td>}
                    <td className="centre"><input type="checkbox" aria-label="Actif" checked={!!l.actif} onChange={(e) => changer(i, 'actif', e.target.checked)} /></td>
                    <td className="centre">
                      <button type="button" className="bouton-icone" aria-label={`Retirer ${l.code || 'la ligne'}`}
                        onClick={() => setLignes(lignes.filter((_, j) => j !== i))}><Icone nom="corbeille" taille={16} /></button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <div className="barre-enregistrer">
          <Bouton variante="secondaire" icone="plus" onClick={ajouter}>Ajouter une ligne</Bouton>
          <span className="espace" />
          {modifie && <span className="discret">Modifications non enregistrées</span>}
          <Bouton variante="secondaire" onClick={() => setLignes((refs[type] || []).map((e) => ({ ...e })))} disabled={!modifie}>Annuler</Bouton>
          <Bouton icone="valide" chargement={enCours} disabled={!modifie} onClick={enregistrer}>Enregistrer</Bouton>
        </div>
      </section>
    </>
  )
}
