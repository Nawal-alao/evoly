import React, { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useNotification } from '../context/NotificationContext'
import ChampMotDePasse from '../components/ChampMotDePasse'

const CLASSES = [
  { value: '6EME', label: 'Sixième' },
  { value: '5EME', label: 'Cinquième' },
  { value: '4EME', label: 'Quatrième' },
  { value: '3EME', label: 'Troisième' },
  { value: '2ND',  label: 'Seconde' },
  { value: '1ERE', label: 'Première' },
  { value: 'TLE',  label: 'Terminale' },
]

const SERIES = [
  { value: 'AUCUNE', label: 'Aucune (collège)' },
  { value: 'A', label: 'Série A' },
  { value: 'B', label: 'Série B' },
  { value: 'C', label: 'Série C' },
  { value: 'D', label: 'Série D' },
]

function FieldErrors({ errors }) {
  if (!errors) return null
  const msgs = Array.isArray(errors) ? errors : [errors]
  return <p className="champ-erreur">{msgs.join(' ')}</p>
}

export default function InscriptionEleve() {
  const { inscriptionEleve, user } = useAuth()
  const { notifier } = useNotification()

  const [form, setForm] = useState({
    prenom: '', nom: '', age: '',
    classe_scolaire: '6EME', serie: 'AUCUNE',
    username: '', password: '',
  })
  const [erreurs, setErreurs] = useState({})
  const [nonFieldError, setNonFieldError] = useState('')
  const [sending, setSending] = useState(false)

  if (user) {
    const isEleve = user.classe_scolaire !== undefined
    return <Navigate to={isEleve ? '/dashboard/eleve' : '/dashboard/mentor'} replace />
  }

  const set = (field) => (e) => {
    setForm((f) => ({ ...f, [field]: e.target.value }))
    setErreurs((er) => ({ ...er, [field]: undefined }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErreurs({})
    setNonFieldError('')
    setSending(true)
    try {
      const prenom = await inscriptionEleve({
        ...form,
        age: Number(form.age),
      })
      notifier(`Bienvenue sur Évoly, ${prenom} ! Ton compte a été créé.`, 'success')
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
        <p className="eyebrow">Rejoindre Évoly</p>
        <h1>Créer mon compte élève</h1>
        <p className="sous-titre">Quelques informations pour personnaliser tes cours dès le départ.</p>

        <div className="carte-auth">
          <form onSubmit={handleSubmit} noValidate>
            {nonFieldError && <p className="champ-erreur">{nonFieldError}</p>}

            <label htmlFor="prenom">Prénom</label>
            <input id="prenom" type="text" required value={form.prenom} onChange={set('prenom')} />
            <FieldErrors errors={erreurs.prenom} />

            <label htmlFor="nom">Nom</label>
            <input id="nom" type="text" required value={form.nom} onChange={set('nom')} />
            <FieldErrors errors={erreurs.nom} />

            <label htmlFor="age">Âge</label>
            <input id="age" type="number" min="8" max="25" required value={form.age} onChange={set('age')} />
            <FieldErrors errors={erreurs.age} />

            <label htmlFor="classe_scolaire">Classe</label>
            <select id="classe_scolaire" value={form.classe_scolaire} onChange={set('classe_scolaire')}>
              {CLASSES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
            <FieldErrors errors={erreurs.classe_scolaire} />

            <label htmlFor="serie">Série</label>
            <select id="serie" value={form.serie} onChange={set('serie')}>
              {SERIES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
            <FieldErrors errors={erreurs.serie} />

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
