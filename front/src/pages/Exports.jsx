import { useEffect, useState } from 'react'
import { api, requete, urlApi } from '../api.js'
import { Bandeau, EnTetePage, Icone } from '../composants.jsx'
import { pluriel } from '../outils.js'

function Choix({ titre, options, valeurs, onChange }) {
  const basculer = (code) => onChange(valeurs.includes(code) ? valeurs.filter((v) => v !== code) : [...valeurs, code])
  return (
    <fieldset className="choix">
      <legend>{titre}{valeurs.length > 0 && <button type="button" className="bouton bouton-lien" onClick={() => onChange([])}>Tout</button>}</legend>
      <div className="puces">
        {options.map((o) => (
          <label key={o.code} className={`puce ${valeurs.includes(o.code) ? 'cochee' : ''}`}>
            <input type="checkbox" checked={valeurs.includes(o.code)} onChange={() => basculer(o.code)} />
            {o.libelle}
          </label>
        ))}
      </div>
    </fieldset>
  )
}

export default function Exports({ refs, notifier }) {
  const [f, setF] = useState({ pays: [], etablissement: [], service: [], type_contrat: [], statut: [] })
  const [apercu, setApercu] = useState(null)
  const params = requete(f)

  useEffect(() => { api('export/apercu' + params).then(setApercu).catch(() => setApercu(null)) }, [params])

  const pays = refs.pays.filter((p) => refs.etablissements.some((e) => e.pays === p.code))
  const etablissements = refs.etablissements.filter((e) => !f.pays.length || f.pays.includes(e.pays))
  const telecharger = (format) => {
    window.location.href = urlApi('export' + requete({ ...f, format }))
    notifier(`Export ${format.toUpperCase()} en cours de téléchargement.`)
  }

  return (
    <>
      <EnTetePage titre="Exports" sousTitre="Fichier standardisé de tous les collaborateurs européens, pour l'alimentation des systèmes internes" />
      <section className="carte">
        <h2 className="carte-titre"><Icone nom="liste" />Filtres</h2>
        <p className="discret">Aucune case cochée dans un groupe = pas de filtre sur ce critère.</p>
        <Choix titre="Pays" options={pays} valeurs={f.pays} onChange={(v) => setF({ ...f, pays: v, etablissement: [] })} />
        <Choix titre="Établissement" options={etablissements.map((e) => ({ code: e.code, libelle: `${e.code} — ${e.libelle}` }))}
          valeurs={f.etablissement} onChange={(v) => setF({ ...f, etablissement: v })} />
        <Choix titre="Service" options={refs.services} valeurs={f.service} onChange={(v) => setF({ ...f, service: v })} />
        <Choix titre="Type de contrat" options={refs.types_contrat} valeurs={f.type_contrat} onChange={(v) => setF({ ...f, type_contrat: v })} />
        <Choix titre="Statut" options={[{ code: 'actif', libelle: 'Actifs' }, { code: 'inactif', libelle: 'Inactifs' }]}
          valeurs={f.statut} onChange={(v) => setF({ ...f, statut: v })} />
      </section>
      <section className="carte export-actions">
        <p aria-live="polite"><strong>{apercu ? pluriel(apercu.nb, 'collaborateur') : '…'}</strong> dans l'export</p>
        <div className="entete-actions">
          <button type="button" className="bouton bouton-primaire" disabled={!apercu?.nb} onClick={() => telecharger('xlsx')}>
            <Icone nom="telecharger" />Exporter en Excel</button>
          <button type="button" className="bouton bouton-secondaire" disabled={!apercu?.nb} onClick={() => telecharger('csv')}>
            <Icone nom="telecharger" />Exporter en CSV</button>
        </div>
      </section>
      <Bandeau ton="info" titre="Format standard">
        Colonnes fixes ({apercu?.colonnes?.length || 27}) avec codes et libellés des référentiels. CSV : UTF-8, séparateur « ; »,
        dates AAAA-MM-JJ. Chaque export est tracé dans l'historique. Fichier contenant des données personnelles : usage interne uniquement (RGPD).
      </Bandeau>
      {apercu?.colonnes && <p className="colonnes-export">{apercu.colonnes.map((c) => <code key={c}>{c}</code>)}</p>}
    </>
  )
}
