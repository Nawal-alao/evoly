import React, { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import DOMPurify from 'dompurify'
import loadKatex from '../utils/katexLoader'
import api from '../api/axios'
import ContenuRiche from '../components/ContenuRiche'

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
  return <div ref={ref} />
}

function LigneCorrection({ reponse }) {
  return (
    <div className="reponse-ligne">
      <div className={`puce ${reponse.correct ? 'puce-correct' : 'puce-incorrect'}`}>
        {reponse.correct ? '✓' : '✗'}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontWeight: 600, marginBottom: 4 }}>
          {reponse.question?.notion}
        </p>
        <p style={{ marginBottom: 4 }}>
          Ta réponse : <strong><KaTeXText text={reponse.reponse_donnee || '—'} /></strong>
        </p>
        {!reponse.correct && (
          <p style={{ color: 'var(--couleur-succes)', marginBottom: 0 }}>
            Bonne réponse : <strong><KaTeXText text={reponse.question?.bonne_reponse || '—'} /></strong>
          </p>
        )}
      </div>
    </div>
  )
}

export default function ResultatDetail() {
  const { id } = useParams()
  const [resultat, setResultat] = useState(null)

  useEffect(() => {
    api.get(`evaluations/resultats/${id}/`).then(r => setResultat(r.data))
  }, [id])

  if (!resultat) return <main><div className="etat-vide"><p>Chargement…</p></div></main>

  const note = Number(resultat.note)
  const reponses = resultat.reponses || []
  const exercicesGroupes = resultat.examen?.exercices_groupes || []

  const reponsesParQuestion = {}
  reponses.forEach(r => { reponsesParQuestion[r.question?.id] = r })

  const questionsGroupeesIds = new Set(
    exercicesGroupes.flatMap(ex => (ex.etapes || []).map(e => e.id))
  )

  const reponsesStandalone = reponses.filter(r => !questionsGroupeesIds.has(r.question?.id))

  let compteur = 0

  return (
    <main>
      <p className="fil-ariane">
        <Link to="/examens">Mes examens</Link> / Résultat
      </p>

      <div className="resultat-hero">
        <div className="note-geante">{note.toFixed(1)}</div>
        <div className="note-sur">/ 20</div>
      </div>

      <div className="entete-page">
        <p className="eyebrow">{resultat.examen?.matiere?.nom}</p>
        <h1>{resultat.examen?.titre}</h1>
      </div>

      <div className="carte">
        {exercicesGroupes.map(ex => (
          <div key={ex.id} className="exercice-groupe-bloc correction-groupe">
            <div className="exercice-groupe-enonce">
              <ContenuRiche contenu={ex.enonce_principal} className="contenu-exercice-groupe" />
            </div>

            {(ex.etapes || []).map((etape, idx) => {
              compteur++
              const rep = reponsesParQuestion[etape.id]
              if (!rep) return null
              return (
                <div key={etape.id} className="etape-cordection">
                  <p className="numero-etape-correction">Étape {idx + 1}</p>
                  <LigneCorrection reponse={rep} />
                </div>
              )
            })}
          </div>
        ))}

        {reponsesStandalone.map((r) => {
          compteur++
          return <LigneCorrection key={r.id} reponse={r} />
        })}
      </div>

      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <Link to="/examens" className="btn btn-secondaire">Retour aux examens</Link>
      </div>
    </main>
  )
}
