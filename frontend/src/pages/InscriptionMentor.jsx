import React, { useState, useEffect } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useNotification } from '../context/NotificationContext'
import api from '../api/axios'
import ChampMotDePasse from '../components/ChampMotDePasse'

function FieldErrors({ errors }) {
  if (!errors) return null
  const msgs = Array.isArray(errors) ? errors : [errors]
  return <p className="champ-erreur">{msgs.join(' ')}</p>
}

export default function InscriptionMentor() {
  const { inscriptionMentor, user } = useAuth()
  const { notifier } = useNotification()

  const [form, setForm] = useState({
    prenom: '', nom: '', bio: '',
    username: '', password: '',
  })
  const [matieresIds, setMatieresIds] = useState([])
  const [matieresDispos, setMatieresDispos] = useState([])
  const [erreurs, setErreurs] = useState({})
  const [nonFieldError, setNonFieldError] = useState('')
  const [sending, setSending] = useState(false)

  useEffect(() => {
    api.get('pedagogie/matieres/')
      .then(({ data }) => setMatieresDispos(data))
      .catch(() => {})
  }, [])

  if (user) {
    const isEleve = user.classe_scolaire !== undefined
    return <Navigate to={isEleve ? '/dashboard/eleve' : '/dashboard/mentor'} replace />
  }

  const set = (field) => (e) => {
    setForm((f) => ({ ...f, [field]: e.target.value }))
    setErreurs((er) => ({ ...er, [field]: undefined }))
  }

  const toggleMatiere = (id) => {
    setMatieresIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
    setErreurs((er) => ({ ...er, matieres: undefined }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErreurs({})
    setNonFieldError('')
    setSending(true)
    try {
      const prenom = await inscriptionMentor({ ...form, matieres: matieresIds })
      notifier(`Bienvenue sur Évoly, ${prenom} ! Ton profil mentor est prêt.`, 'success')
    } catch (err) {
      const data = err.response?.data
      if (data) {
        if (data.non_field_errors) {
          const msg = Array.isArray(data.non_field_errors) ? data.non_field_errors.join(' ') : data.non_field_errors
          setNonFieldError(msg)
          notifier(msg, 'error')
        }
        const fieldErrors = {}
        for (const [key, val] of Object.entries(data)) {
          if (key === 'non_field_errors') continue
          fieldErrors[key] = Array.isArray(val) ? val.join(' ') : String(val)
        }
        setErreurs(fieldErrors)
        if (Object.keys(fieldErrors).length === 0 && !data.detail) {
          setNonFieldError("Une erreur est survenue. Vérifie les champs.")
          notifier("Une erreur est survenue, réessaie dans un instant.", 'error')
        }
      } else {
        setNonFieldError("Impossible de contacter le serveur. Réessaie.")
        notifier("Une erreur est survenue, réessaie dans un instant.", 'error')
      }
    } finally {
      setSending(false)
    }
  }

  return (
    <main>
      <div className="conteneur-auth">
        <p className="eyebrow">Devenir mentor</p>
        <h1>Créer mon compte mentor</h1>
        <p className="sous-titre">Accompagne des élèves dans les matières que tu maîtrises.</p>

        <div className="carte-auth">
          <form onSubmit={handleSubmit} noValidate>
            {nonFieldError && <p className="champ-erreur">{nonFieldError}</p>}

            <label htmlFor="prenom">Prénom</label>
            <input id="prenom" type="text" required value={form.prenom} onChange={set('prenom')} />
            <FieldErrors errors={erreurs.prenom} />

            <label htmlFor="nom">Nom</label>
            <input id="nom" type="text" required value={form.nom} onChange={set('nom')} />
            <FieldErrors errors={erreurs.nom} />

            <label htmlFor="bio">Bio</label>
            <textarea id="bio" rows="3" value={form.bio} onChange={set('bio')}
              placeholder="Décris ton parcours et tes spécialités…"
            />
            <FieldErrors errors={erreurs.bio} />

            <fieldset className="champ-group">
              <legend>Matières enseignées</legend>
              {matieresDispos.length === 0 && (
                <p className="texte-doux" style={{fontSize:'0.85rem',margin:'0 0 8px'}}>Chargement…</p>
              )}
              <div className="cases-matieres">
                {matieresDispos.map((m) => (
                  <label key={m.id} className="case-matiere">
                    <input
                      type="checkbox"
                      checked={matieresIds.includes(m.id)}
                      onChange={() => toggleMatiere(m.id)}
                    />
                    <span>{m.nom}</span>
                  </label>
                ))}
              </div>
              <FieldErrors errors={erreurs.matieres} />
            </fieldset>

            <div className="separateur-ou">Identifiants de connexion</div>

            <label htmlFor="username">Nom d'utilisateur</label>
            <input id="username" type="text" required autoComplete="username" value={form.username} onChange={set('username')} />
            <FieldErrors errors={erreurs.username} />

            <label htmlFor="password">Mot de passe</label>
            <ChampMotDePasse id="password" required autoComplete="new-password" value={form.password} onChange={set('password')} />
            <FieldErrors errors={erreurs.password} />

            <button type="submit" className="btn btn-primaire" disabled={sending}>
              {sending ? 'Création…' : 'Créer mon compte'}
            </button>
          </form>

          <p className="lien-bas-de-carte">
            Déjà inscrit ? <Link to="/connexion">Se connecter</Link>
          </p>
        </div>
      </div>
    </main>
  )
}
