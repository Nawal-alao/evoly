import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import ContenuRiche from '../components/ContenuRiche'
import { Check, Bookmark } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useNotification } from '../context/NotificationContext'
import api from '../api/axios'

const CLASSES_LABEL = {
  '6EME': 'Sixième', '5EME': 'Cinquième', '4EME': 'Quatrième',
  '3EME': 'Troisième', '2ND': 'Seconde', '1ERE': 'Première', 'TLE': 'Terminale',
}

export default function CoursDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const { notifier } = useNotification()
  const [cours, setCours] = useState(null)
  const [activeSeq, setActiveSeq] = useState(null)
  const [termine, setTermine] = useState(false)
  const [loadingTermine, setLoadingTermine] = useState(false)
  const [favori, setFavori] = useState(false)
  const [loadingFavori, setLoadingFavori] = useState(false)
  const observerRef = useRef(null)
  const debounceRef = useRef(null)
  const activeSeqRef = useRef(null)
  const readyForObserver = useRef(false)

  const isEleve = user?.classe_scolaire !== undefined

  useEffect(() => {
    api.get(`pedagogie/cours/${id}/`).then(r => {
      setCours(r.data)
      setTermine(r.data.termine)
      setFavori(r.data.favori)
      if (r.data.sequences?.length) {
        const hash = window.location.hash.replace('#sequence-', '')
        const fromHash = r.data.sequences.find(s => String(s.id) === hash)
        if (fromHash) {
          setActiveSeq(fromHash.id)
          setTimeout(() => {
            const el = document.getElementById(`sequence-${fromHash.id}`)
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
            readyForObserver.current = true
          }, 400)
        } else if (isEleve) {
          api.get(`pedagogie/cours/${id}/progression/`).then(res => {
            if (res.data.sequence_id) {
              const saved = r.data.sequences.find(s => s.id === res.data.sequence_id)
              if (saved) {
                setActiveSeq(saved.id)
                setTimeout(() => {
                  const el = document.getElementById(`sequence-${saved.id}`)
                  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
                  readyForObserver.current = true
                }, 400)
              } else {
                setActiveSeq(r.data.sequences[0].id)
                readyForObserver.current = true
              }
            } else {
              setActiveSeq(r.data.sequences[0].id)
              readyForObserver.current = true
            }
          }).catch(() => {
            setActiveSeq(r.data.sequences[0].id)
          })
        } else {
          setActiveSeq(r.data.sequences[0].id)
          readyForObserver.current = true
        }
      }
    })
  }, [id, isEleve])

  // IntersectionObserver : synchronise activeSeq avec la séquence visible
  useEffect(() => {
    if (!cours?.sequences?.length) return

    const handleIntersect = (entries) => {
      if (!readyForObserver.current) return
      for (const entry of entries) {
        if (entry.isIntersecting) {
          const id = entry.target.id.replace('sequence-', '')
          setActiveSeq(Number(id))
        }
      }
    }

    observerRef.current = new IntersectionObserver(handleIntersect, {
      rootMargin: '-20% 0px -60% 0px',
      threshold: 0,
    })

    const timer = setTimeout(() => {
      cours.sequences.forEach(seq => {
        const el = document.getElementById(`sequence-${seq.id}`)
        if (el) observerRef.current.observe(el)
      })
    }, 300)

    return () => {
      clearTimeout(timer)
      if (observerRef.current) observerRef.current.disconnect()
    }
  }, [cours])

  // Met à jour le hash URL quand activeSeq change
  useEffect(() => {
    if (activeSeq) {
      const hash = `#sequence-${activeSeq}`
      if (window.location.hash !== hash) {
        history.replaceState(null, '', hash)
      }
    }
  }, [activeSeq])

  // Sauvegarde la position de lecture (debounce 1s + flush forcé au démontage)
  useEffect(() => {
    if (!activeSeq || !isEleve) return

    activeSeqRef.current = activeSeq

    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      api.post(`pedagogie/cours/${id}/progression/`, { sequence_id: activeSeq }).catch(() => {})
    }, 1000)

    return () => {
      clearTimeout(debounceRef.current)
      if (activeSeqRef.current) {
        api.post(`pedagogie/cours/${id}/progression/`, { sequence_id: activeSeqRef.current }).catch(() => {})
      }
    }
  }, [activeSeq, id, isEleve])

  const scrollToSeq = useCallback((seqId) => {
    setActiveSeq(seqId)
    const el = document.getElementById(`sequence-${seqId}`)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [])

  const toggleTermine = () => {
    setLoadingTermine(true)
    api.post(`pedagogie/cours/${id}/terminer/`).then(r => {
      setTermine(r.data.termine)
      if (r.data.termine) {
        notifier('Cours marqué comme terminé, bravo !', 'success')
      } else {
        notifier('Cours retiré de tes cours terminés.', 'info')
      }
    }).catch(() => {
      notifier('Une erreur est survenue, réessaie dans un instant.', 'error')
    }).finally(() => setLoadingTermine(false))
  }

  const toggleFavori = () => {
    setLoadingFavori(true)
    api.post(`pedagogie/cours/${id}/favori/`).then(r => {
      setFavori(r.data.favori)
      if (r.data.favori) {
        notifier('Ajouté à tes favoris.', 'success')
      } else {
        notifier('Retiré de tes favoris.', 'info')
      }
    }).catch(() => {
      notifier('Une erreur est survenue, réessaie dans un instant.', 'error')
    }).finally(() => setLoadingFavori(false))
  }

  if (!cours) return <main><div className="etat-vide"><p>Chargement…</p></div></main>

  const sequences = cours.sequences || []
  const classeLabel = CLASSES_LABEL[cours.classe_scolaire] || cours.classe_scolaire

  return (
    <main>
      <p className="fil-ariane">
        <Link to="/cours">Mes cours</Link> / {classeLabel} / {cours.titre}
      </p>

      <div className="entete-page">
        <p className="eyebrow">{classeLabel}</p>
        <div className="ligne-titre-cours">
          <h1>{cours.titre}</h1>
          {isEleve && (
            <div className="actions-cours">
              <button
                type="button"
                className={`bouton-favori${favori ? ' actif' : ''}`}
                onClick={toggleFavori}
                disabled={loadingFavori}
                aria-label={favori ? 'Retirer des favoris' : 'Ajouter aux favoris'}
              >
                <Bookmark size={16} fill={favori ? 'currentColor' : 'none'} />
              </button>
              <button
                type="button"
                className={`bouton-terminer ${termine ? 'actif' : ''}`}
                onClick={toggleTermine}
                disabled={loadingTermine}
              >
                {termine ? (
                  <span className="badge badge-termine"><Check size={14} strokeWidth={3} /> Terminé</span>
                ) : (
                  <><Check size={16} /> Marquer comme terminé</>
                )}
              </button>
            </div>
          )}
        </div>
        {cours.description && <p className="texte-doux">{cours.description}</p>}
      </div>

      {sequences.length > 0 ? (
        <div className="mise-en-page-cours">
          <nav className="sommaire-sequences">
            <div className="sommaire-titre">Contenu du cours</div>
            {termine !== undefined && (
              <div className="sommaire-badge">
                {termine ? (
                  <span className="badge badge-termine"><Check size={12} strokeWidth={3} /> Terminé</span>
                ) : activeSeq ? (
                  <span className="badge badge-inactif">
                    Séquence {sequences.find(s => s.id === activeSeq)?.ordre || '…'} en cours
                  </span>
                ) : (
                  <span className="badge badge-inactif">En cours</span>
                )}
              </div>
            )}
            {sequences.map((seq, idx) => (
              <a key={seq.id} href={`#sequence-${seq.id}`}
                className={`sommaire-item${activeSeq === seq.id ? ' actif' : ''}`}
                onClick={(e) => { e.preventDefault(); scrollToSeq(seq.id) }}>
                <span className="sommaire-num">{idx + 1}</span>
                <span>{seq.titre}</span>
              </a>
            ))}
          </nav>
          <div className="cours-contenu-colonne">
            {sequences.map((seq, idx) => (
              <article key={seq.id} className="sequence" id={`sequence-${seq.id}`}>
                <h3>Séquence {seq.ordre}</h3>
                <h2>{seq.titre}</h2>
                <ContenuRiche contenu={seq.contenu} className="contenu-sequence" />
              </article>
            ))}
          </div>
        </div>
      ) : (
        <div className="carte">
          <div className="etat-vide">
            <p>Le contenu de ce cours arrive bientôt.</p>
          </div>
        </div>
      )}
    </main>
  )
}
