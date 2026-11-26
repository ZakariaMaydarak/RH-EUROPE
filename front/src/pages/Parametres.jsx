import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { Bandeau, Bouton, Champ, Chargement, EnTetePage, Icone } from '../composants.jsx'
import { dateHeureFr } from '../outils.js'

function exemple(modele, largeur, depart) {
  const an = new Date().getFullYear()
  return (modele || '').toUpperCase().replace('{PAYS}', 'FR').replace('{ETAB}', 'H1234')
    .replace('{AAAA}', String(an)).replace('{AA}', String(an % 100).padStart(2, '0'))
    .replace('{N}', String(depart || 1).padStart(Number(largeur) || 6, '0'))
}

export default function Parametres({ notifier }) {
  const [v, setV] = useState(null)
  const [erreurs, setErreurs] = useState({})
  const [enCours, setEnCours] = useState(false)
  const [auto, setAuto] = useState(null)

  const chargerAuto = () => api('automatisation').then(setAuto).catch(() => {})
  useEffect(() => {
    api('parametres').then((p) => setV({ domaines: p.domaines_email.join(', '), ...p.matricule })).catch((e) => setErreurs({ general: e.message }))
    chargerAuto()
  }, [])

  if (!v) return erreurs.general ? <Bandeau ton="danger">{erreurs.general}</Bandeau> : <Chargement />

  const enregistrer = async () => {
    setEnCours(true); setErreurs({})
    try {
      await api('parametres', { method: 'PUT', body: {
        domaines_email: v.domaines.split(/[,;\s]+/).filter(Boolean),
        matricule: { modele: v.modele, largeur: Number(v.largeur), depart: Number(v.depart) },
      } })
      notifier('Paramètres enregistrés.')
    } catch (e) { setErreurs(e.corps?.erreurs || { general: e.message }) }
    finally { setEnCours(false) }
  }
  const lancer = async () => {
    try { const r = await api('automatisation/lancer', { method: 'POST' }); notifier(`${r.desactives} collaborateur(s) désactivé(s).`); chargerAuto() }
    catch (e) { notifier(e.message, 'alerte') }
  }

  return (
    <>
      <EnTetePage titre="Paramètres" sousTitre="Règles de contrôle et de numérotation" />
      {erreurs.general && <Bandeau ton="danger">{erreurs.general}</Bandeau>}
      <section className="carte">
        <h2 className="carte-titre">Adresses e-mail</h2>
        <Champ id="p-domaines" label="Domaines autorisés" requis erreur={erreurs.domaines_email}
          aide="Séparés par des virgules. Les sous-domaines sont acceptés (ex. accor.com autorise fr.accor.com).">
          <input id="p-domaines" type="text" value={v.domaines} onChange={(e) => setV({ ...v, domaines: e.target.value })} />
        </Champ>
      </section>
      <section className="carte">
        <h2 className="carte-titre">Génération des matricules</h2>
        <div className="grille-champs">
          <Champ id="p-modele" label="Modèle" requis erreur={erreurs.modele}
            aide="Repères : {PAYS} code pays de l'établissement, {ETAB} code établissement, {AAAA} / {AA} année, {N} numéro séquentiel.">
            <input id="p-modele" className="mono" type="text" value={v.modele} onChange={(e) => setV({ ...v, modele: e.target.value.toUpperCase() })} />
          </Champ>
          <Champ id="p-largeur" label="Nombre de chiffres du numéro" requis erreur={erreurs.largeur}>
            <input id="p-largeur" type="number" min={3} max={12} value={v.largeur} onChange={(e) => setV({ ...v, largeur: e.target.value })} />
          </Champ>
          <Champ id="p-depart" label="Premier numéro" requis erreur={erreurs.depart} aide="Utile pour reprendre après une numérotation existante.">
            <input id="p-depart" type="number" min={1} value={v.depart} onChange={(e) => setV({ ...v, depart: e.target.value })} />
          </Champ>
        </div>
        <p className="exemple">Exemple : <code>{exemple(v.modele, v.largeur, v.depart)}</code>
          <span className="discret"> — chaque numéro généré est réservé, et un matricule déjà utilisé est automatiquement sauté.</span></p>
        <div className="barre-enregistrer"><span className="espace" />
          <Bouton icone="valide" chargement={enCours} onClick={enregistrer}>Enregistrer</Bouton></div>
      </section>
      <section className="carte">
        <h2 className="carte-titre"><Icone nom="sablier" />Désactivation automatique</h2>
        <p>Chaque jour à <strong>{auto?.heure || '01:05'}</strong> (heure de Paris), les collaborateurs actifs dont la date de fin de contrat
          est dépassée passent au statut inactif (motif « Fin de contrat » sauf motif déjà renseigné). Un rattrapage a lieu au démarrage du serveur.</p>
        {auto && (
          <p className="discret">
            {auto.active ? 'Planification active.' : 'Planification inactive sur ce serveur.'}{' '}
            {auto.dernier_passage ? `Dernier passage : ${dateHeureFr(auto.dernier_passage.le)} — ${auto.dernier_passage.desactives} désactivation(s).` : 'Aucun passage enregistré.'}
          </p>
        )}
        <Bouton variante="secondaire" icone="reactiver" onClick={lancer}>Lancer maintenant</Bouton>
      </section>
    </>
  )
}
