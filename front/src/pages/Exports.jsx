import { useEffect, useState } from 'react'
import { api, requete, urlApi } from '../api.js'
import { Bandeau, EnTetePage, Icone } from '../composants.jsx'
import { useT } from '../i18n.js'

function Choix({ titre, options, valeurs, onChange }) {
  const { t } = useT()
  const basculer = (code) => onChange(valeurs.includes(code) ? valeurs.filter((v) => v !== code) : [...valeurs, code])
  return (
    <fieldset className="choix">
      <legend>{titre}{valeurs.length > 0 && <button type="button" className="bouton bouton-lien" onClick={() => onChange([])}>{t('Tout')}</button>}</legend>
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
  const { t, tn, nomRef } = useT()
  const [f, setF] = useState({ pays: [], etablissement: [], service: [], type_contrat: [], statut: [] })
  const [apercu, setApercu] = useState(null)
  const params = requete(f)

  useEffect(() => { api('export/apercu' + params).then(setApercu).catch(() => setApercu(null)) }, [params])

  const options = (liste) => liste.map((e) => ({ code: e.code, libelle: nomRef(e) }))
  const pays = refs.pays.filter((p) => refs.etablissements.some((e) => e.pays === p.code))
  const etablissements = refs.etablissements.filter((e) => !f.pays.length || f.pays.includes(e.pays))
  const telecharger = (format) => {
    window.location.href = urlApi('export' + requete({ ...f, format }))
    notifier(t('Export {format} en cours de téléchargement.', { format: format.toUpperCase() }))
  }

  return (
    <>
      <EnTetePage titre={t('Exports')} sousTitre={t("Fichier standardisé de tous les collaborateurs européens, pour l'alimentation des systèmes internes")} />
      <section className="carte">
        <h2 className="carte-titre"><Icone nom="liste" />{t('Filtres')}</h2>
        <p className="discret">{t('Aucune case cochée dans un groupe = pas de filtre sur ce critère.')}</p>
        <Choix titre={t('Pays')} options={options(pays)} valeurs={f.pays} onChange={(v) => setF({ ...f, pays: v, etablissement: [] })} />
        <Choix titre={t('Établissement')} options={etablissements.map((e) => ({ code: e.code, libelle: `${e.code} — ${nomRef(e)}` }))}
          valeurs={f.etablissement} onChange={(v) => setF({ ...f, etablissement: v })} />
        <Choix titre={t('Service')} options={options(refs.services)} valeurs={f.service} onChange={(v) => setF({ ...f, service: v })} />
        <Choix titre={t('Type de contrat')} options={options(refs.types_contrat)} valeurs={f.type_contrat} onChange={(v) => setF({ ...f, type_contrat: v })} />
        <Choix titre={t('Statut')} options={[{ code: 'actif', libelle: t('Actifs') }, { code: 'inactif', libelle: t('Inactifs') }]}
          valeurs={f.statut} onChange={(v) => setF({ ...f, statut: v })} />
      </section>
      <section className="carte export-actions">
        <p aria-live="polite"><strong>{apercu ? tn(apercu.nb, '{n} collaborateur', '{n} collaborateurs') : '…'}</strong> {t("dans l'export")}</p>
        <div className="entete-actions">
          <button type="button" className="bouton bouton-primaire" disabled={!apercu?.nb} onClick={() => telecharger('xlsx')}>
            <Icone nom="telecharger" />{t('Exporter en Excel')}</button>
          <button type="button" className="bouton bouton-secondaire" disabled={!apercu?.nb} onClick={() => telecharger('csv')}>
            <Icone nom="telecharger" />{t('Exporter en CSV')}</button>
        </div>
      </section>
      <Bandeau ton="info" titre={t('Format standard')}>
        {t("Colonnes fixes ({n}) avec codes et libellés des référentiels, en français quelle que soit la langue d'affichage. CSV : UTF-8, séparateur « ; », dates AAAA-MM-JJ. Chaque export est tracé dans l'historique. Fichier contenant des données personnelles : usage interne uniquement (RGPD).", { n: apercu?.colonnes?.length || 27 })}
      </Bandeau>
      {apercu?.colonnes && <p className="colonnes-export">{apercu.colonnes.map((c) => <code key={c}>{c}</code>)}</p>}
    </>
  )
}
