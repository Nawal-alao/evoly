import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import DOMPurify from 'dompurify'
import loadKatex from '../utils/katexLoader'
import { useNotification } from '../context/NotificationContext'
import api from '../api/axios'
import ContenuRiche from '../components/ContenuRiche'
import ChampReponseMath from '../components/ChampReponseMath'

const KATEX_DELIMITERS = {
  delimiters: [
    { left: '$$', right: '$$', display: true },
    { left: '$', right: '$', display: false },
    { left: '\\(', right: '\\)', display: false },
    { left: '\\[', right: '\\]', display: true },
  ],
  throwOnError: false,
}

function KaTeXText({ text }) {
  const ref = useRef(null)
  useEffect(() => {
    if (ref.current) {
      loadKatex().then(renderMathInElement => {
        if (ref.current) renderMathInElement(ref.current, KATEX_DELIMITERS)
      })
    }
  }, [text])
  return <span ref={ref}>{text}</span>
}

function EnonceAvecMath({ html }) {
  const ref = useRef(null)
  useEffect(() => {
    if (ref.current) {
      ref.current.innerHTML = DOMPurify.sanitize(html)
      loadKatex().then(renderMathInElement => {
        if (ref.current) renderMathInElement(ref.current, KATEX_DELIMITERS)
      })
    }
  }, [html])
  return <div className="enonce" ref={ref} />
}

function BadgeEtape({ idx, total }) {
  return (
    <span className="badge-etape">
      Étape {idx + 1} / {total}
    </span>
  )
}

export default function PasserExamen() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { notifier } = useNotification()
  const [examen, setExamen] = useState(null)
  const [questions, setQuestions] = useState([])
  const [exercicesGroupes, setExercicesGroupes] = useState([])
  const [reponses, setReponses] = useState({})
  const [sending, setSending] = useState(false)
  const [actifId, setActifId] = useState(null)
  const [contextesOuverts, setContextesOuverts] = useState({})

  useEffect(() => {
    api.get(`evaluations/examens/${id}/passer/`).then(r => {
      setExamen(r.data.examen)
      setQuestions(r.data.questions)
      setExercicesGroupes(r.data.examen.exercices_groupes || [])
    })
  }, [id])

  const editeurMath = !!examen?.editeur_math_effectif

  const valeurVide = (v) => v === undefined || v === null || String(v).trim() === ''

  const setReponse = (qId, value) => {
    setReponses(prev => {
      const suivant = { ...prev, [qId]: value }
      if (valeurVide(suivant[qId])) {
        const { [qId]: _, ...reste } = suivant
        return reste
      }
      return suivant
    })
  }

  // Liste plate de toutes les questions (étapes de groupes + questions indépendantes)
  const toutesLesQuestions = [
    ...exercicesGroupes.flatMap(ex => ex.etapes || []),
    ...questions,
  ]
  const totalQuestions = toutesLesQuestions.length

  const estRepondue = (qId) => !valeurVide(reponses[qId])

  const defilerVers = useCallback((qId) => {
    const el = document.getElementById(`question-${qId}`)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [])

  const basculerContexte = (groupeId) => {
    setContextesOuverts(prev => ({ ...prev, [groupeId]: !prev[groupeId] }))
  }

  const renduChamp = (q) => {
    if (q.type_question === 'QCM' && q.choix_reponses) {
      return q.choix_reponses.map((choix, ci) => (
        <div key={ci} className="choix-reponse">
          <input type="radio" id={`q${q.id}-c${ci}`} name={`q${q.id}`}
            value={choix} required
            checked={reponses[q.id] === choix}
            onFocus={() => setActifId(q.id)}
            onChange={() => setReponse(q.id, choix)} />
          <label htmlFor={`q${q.id}-c${ci}`}><KaTeXText text={choix} /></label>
        </div>
      ))
    }
    if (editeurMath) {
      return (
        <ChampReponseMath
          value={reponses[q.id] || ''}
          onChange={(v) => setReponse(q.id, v)}
          placeholder="Ta réponse…"
        />
      )
    }
    return (
      <input type="text" placeholder="Ta réponse" required
        value={reponses[q.id] || ''}
        onFocus={() => setActifId(q.id)}
        onChange={(e) => setReponse(q.id, e.target.value)} />
    )
  }

  const renduCarteQuestion = ({ q, isEtape, idx, totalEtapes, compteur }) => (
    <div key={q.id} id={`question-${q.id}`} className="carte-question"
      data-repondue={estRepondue(q.id) ? 'oui' : 'non'}
      onFocusCapture={() => setActifId(q.id)}>
      <div className="carte-question-entete">
        {isEtape
          ? <BadgeEtape idx={idx} total={totalEtapes} />
          : <span className="badge-question">Question {compteur} / {totalQuestions}</span>}
        <span className={`etat-reponse ${estRepondue(q.id) ? 'vue' : 'vide'}`}>
          {estRepondue(q.id) ? 'Répondu' : 'À répondre'}
        </span>
      </div>
      <EnonceAvecMath html={q.enonce} />
      {renduChamp(q)}
    </div>
  )

  const renduContexteDesktop = (ex) => (
    <aside className="contexte-cadre">
      <p className="contexte-titre">Contexte de l'exercice</p>
      <ContenuRiche contenu={ex.enonce_principal} className="contenu-exercice-groupe" />
    </aside>
  )

  const renduContexteMobile = (ex) => {
    const ouvert = !!contextesOuverts[ex.id]
    return (
      <div className={`contexte-accordion${ouvert ? ' ouvert' : ''}`}>
        <button type="button" className="contexte-accordion-entete" onClick={() => basculerContexte(ex.id)} aria-expanded={ouvert}>
          <span>Contexte de l'exercice</span>
          <span className="contexte-chevron">{ouvert ? '−' : '+'}</span>
        </button>
        {ouvert && (
          <div className="contexte-accordion-corps">
            <ContenuRiche contenu={ex.enonce_principal} className="contenu-exercice-groupe" />
          </div>
        )}
      </div>
    )
  }

  if (!examen) return <main><div className="etat-vide"><p>Chargement…</p></div></main>

  let compteur = 0

  const handleSubmit = (e) => {
    e.preventDefault()
    setSending(true)
    const payload = {
      reponses: toutesLesQuestions.map(q => ({
        question_id: q.id,
        reponse: reponses[q.id] || '',
      })),
    }
    api.post(`evaluations/examens/${id}/soumettre/`, payload).then(r => {
      notifier('Examen soumis avec succès !', 'success')
      navigate(`/resultats/${r.data.id}`)
    }).catch(() => {
      setSending(false)
      notifier("L'envoi de tes réponses a échoué, réessaie.", 'error')
    })
  }

  const statutQuestion = (q) => {
    if (estRepondue(q.id)) return 'repondue'
    if (actifId === q.id) return 'encours'
    return 'restante'
  }

  return (
    <main className="page-passer-examen">
      <p className="fil-ariane">
        <Link to="/examens">Mes examens</Link> / {examen.matiere?.nom}
      </p>

      <div className="entete-page">
        <p className="eyebrow">{examen.matiere?.nom}</p>
        <h1>{examen.titre}</h1>
        <p className="texte-doux">
          {totalQuestions} question{totalQuestions > 1 ? 's' : ''} — réponds du mieux que tu peux, tu peux revenir en arrière avant de valider.
        </p>
      </div>

      {/* Barre de progression : puces numérotées */}
      <div className="progression-examen" role="tablist" aria-label="Progression de l'examen">
        {toutesLesQuestions.map((q, i) => (
          <button
            key={q.id}
            type="button"
            className={`puce-progression ${statutQuestion(q)}`}
            title={`Question ${i + 1}${estRepondue(q.id) ? ' — répondu' : ''}`}
            aria-label={`Question ${i + 1}`}
            onClick={() => defilerVers(q.id)}
          >
            {i + 1}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        {exercicesGroupes.map(ex => {
          const etapes = ex.etapes || []
          return (
            <section key={ex.id} className="exercice-groupe-bloc">
              {/* Mobile : accordéon rétractable du contexte */}
              <div className="contexte-mobile-uniquement">
                {renduContexteMobile(ex)}
              </div>

              <div className="exercice-groupe-split">
                {/* Desktop : panneau sticky gauche */}
                <div className="contexte-desktop-uniquement">
                  {renduContexteDesktop(ex)}
                </div>

                {/* Droite : cartes d'étapes défilantes */}
                <div className="etapes-colonne">
                  {etapes.map((etape, idx) => {
                    compteur++
                    return renduCarteQuestion({
                      q: etape, isEtape: true, idx,
                      totalEtapes: etapes.length, compteur,
                    })
                  })}
                </div>
              </div>
            </section>
          )
        })}

        {/* Questions indépendantes (sans groupe) */}
        <div className="questions-independantes">
          {questions.map((q) => {
            compteur++
            return renduCarteQuestion({ q, isEtape: false, idx: 0, totalEtapes: 0, compteur })
          })}
        </div>

        <div className="barre-actions-examen">
          <button type="submit" className="btn btn-primaire" disabled={sending}>
            {sending ? 'Envoi…' : 'Valider mes réponses'}
          </button>
        </div>
      </form>
    </main>
  )
}
