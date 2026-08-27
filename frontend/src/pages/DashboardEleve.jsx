import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Bookmark, Users, CreditCard, CalendarDays, Trophy, BookOpen, FileText, MessageCircle, GraduationCap, Play, TrendingUp } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useNotification } from '../context/NotificationContext'
import api from '../api/axios'
import useCompteurAnime from '../hooks/useCompteurAnime'
import Squelette from '../components/Squelette'
import ChargementFluide from '../components/ChargementFluide'

const CLASSES_LABEL = {
  '6EME': 'Sixième', '5EME': 'Cinquième', '4EME': 'Quatrième',
  '3EME': 'Troisième', '2ND': 'Seconde', '1ERE': 'Première', 'TLE': 'Terminale',
}

const MESSAGES_MOTIVANTS = [
  'Chaque leçon te rapproche de ton objectif. Continue comme ça !',
  'La régularité est la clé. Tu es sur la bonne voie.',
  'Chaque examen passé est un pas de plus vers la réussite.',
  'Ton investissement aujourd\'hui construit ton avenir demain.',
  'Les résultats viennent avec le travail. Continue à fournir des efforts.',
]

const raccourcis = [
  { to: '/cours', icon: BookOpen, label: 'Mes cours', desc: 'Reprends là où tu en étais' },
  { to: '/examens', icon: FileText, label: 'Passer un examen', desc: 'Teste tes connaissances' },
  { to: '/conversations', icon: MessageCircle, label: 'Messages', desc: 'Échange avec tes mentors' },
  { to: '/communaute', icon: GraduationCap, label: 'Communauté', desc: 'Rejoins ton groupe d\'étude' },
]

function Etoiles({ note, noteCible, estActive, suiviId, onNoter }) {
  const [etoileCliquee, setEtoileCliquee] = useState(null)
  const [enCours, setEnCours] = useState(false)

  const gererClic = useCallback(async (valeur) => {
    if (enCours) return
    setEtoileCliquee(valeur)
    setEnCours(true)
    try {
      await onNoter(suiviId, valeur)
    } finally {
      setEnCours(false)
      setTimeout(() => setEtoileCliquee(null), 250)
    }
  }, [enCours, suiviId, onNoter])

  return (
    <span className="notation-mentor" style={{ opacity: enCours ? 0.6 : 1, pointerEvents: enCours ? 'none' : 'auto' }}>
      {[1, 2, 3, 4, 5].map(i => {
        const remplie = etoileCliquee !== null
          ? i <= etoileCliquee
          : (noteCible !== null && i <= noteCible)
        return (
          <button
            key={i}
            type="button"
            className={`etoile-noter${remplie ? ' remplie' : ''}${etoileCliquee === i ? ' etoile-pulse' : ''}`}
            onClick={() => gererClic(i)}
            disabled={enCours}
            title={`Noter ${i}/5`}
          >
            ★
          </button>
        )
      })}
    </span>
  )
}

export default function DashboardEleve() {
  const { user } = useAuth()
  const { notifier } = useNotification()
  const [suivis, setSuivis] = useState([])
  const [progressions, setProgressions] = useState([])
  const [abonnement, setAbonnement] = useState(null)
  const [derniereActivite, setDerniereActivite] = useState(null)
  const [loading, setLoading] = useState(true)
  const [matieresHistorique, setMatieresHistorique] = useState([])
  const [matiereSelectee, setMatiereSelectee] = useState(null)
  const [historiquePoints, setHistoriquePoints] = useState([])
  const [loadingHistorique, setLoadingHistorique] = useState(false)
  const [Recharts, setRecharts] = useState(null)
  const [reducedMotion, setReducedMotion] = useState(false)

  const messageMotivant = useMemo(() =>
    MESSAGES_MOTIVANTS[Math.floor(Math.random() * MESSAGES_MOTIVANTS.length)], []
  )

  useEffect(() => {
    Promise.all([
      api.get('comptes/mes-suivis/').then(r => setSuivis(r.data)),
      api.get('evaluations/progressions/').then(r => setProgressions(r.data)),
      api.get('abonnements/mon-abonnement/').then(r => setAbonnement(r.data.abonnement_actif)),
      api.get('pedagogie/cours/derriere-activite/').then(r => {
        if (r.data && r.data.cours_id) setDerniereActivite(r.data)
      }),
    ]).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    import('recharts').then(setRecharts)
    setReducedMotion(window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  }, [])

  useEffect(() => {
    api.get('evaluations/progression/historique/')
      .then(r => {
        setMatieresHistorique(r.data.matieres)
        if (r.data.matieres.length > 0) {
          setMatiereSelectee(r.data.matieres[0].id)
        }
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (matiereSelectee === null) return
    setLoadingHistorique(true)
    api.get(`evaluations/progression/historique/?matiere=${matiereSelectee}`)
      .then(r => setHistoriquePoints(r.data.points))
      .catch(() => setHistoriquePoints([]))
      .finally(() => setLoadingHistorique(false))
  }, [matiereSelectee])

  const noter = useCallback(async (suiviId, note) => {
    try {
      await api.post(`comptes/suivis/${suiviId}/noter/`, { note })
      setSuivis(prev => prev.map(s => s.id === suiviId ? { ...s, note_evaluation: note } : s))
      notifier('Note enregistrée', 'success')
    } catch {
      notifier('Erreur lors de l\'enregistrement de la note', 'error')
    }
  }, [notifier])

  const mentorsAnime = useCompteurAnime(suivis.length)
  const membresMois = useMemo(() => {
    if (!user?.date_inscription) return null
    return new Date(user.date_inscription).toLocaleDateString('fr-FR', { month: 'short', year: 'numeric' })
  }, [user?.date_inscription])

  if (!user) return null
  const classeLabel = CLASSES_LABEL[user.classe_scolaire] || user.classe_scolaire

  return (
    <main>
      <div className="entete-dashboard">
        <div className="entete-dashboard-texte">
          <p className="eyebrow">Tableau de bord</p>
          <h1>Salut {user.prenom} 👋</h1>
          <p className="texte-doux">{classeLabel}{user.serie !== 'AUCUNE' ? ` · Série ${user.serie}` : ''}</p>
        </div>
        <div className="encart-motivant">
          <Trophy size={28} strokeWidth={1.5} />
          <p>{messageMotivant}</p>
        </div>
      </div>

      <ChargementFluide
        isLoading={loading}
        squelette={
          <>
            <div className="grille-stats">
              {Array.from({ length: 3 }, (_, i) => (
                <div key={i} className="stat-carte">
                  <div className="stat-carte-haut">
                    <Squelette largeur={42} hauteur={42} arrondi="50%" />
                    <Squelette largeur={80} hauteur={32} />
                  </div>
                  <Squelette largeur="55%" hauteur={14} style={{ marginTop: 6 }} />
                  <Squelette largeur="80%" hauteur={12} style={{ marginTop: 4 }} />
                </div>
              ))}
            </div>
            <div className="section-titre"><h2>Mes mentors</h2></div>
            <div className="carte" style={{ marginBottom: 40 }}>
              {Array.from({ length: 3 }, (_, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', borderBottom: i < 2 ? '1px solid var(--couleur-bordure)' : 'none' }}>
                  <div>
                    <Squelette largeur={140} hauteur={16} style={{ marginBottom: 4 }} />
                    <Squelette largeur={100} hauteur={12} />
                  </div>
                  <Squelette largeur={80} hauteur={32} arrondi="var(--rayon-petit)" />
                </div>
              ))}
            </div>
            <div className="section-titre"><h2>Ma progression</h2></div>
            <div className="carte" style={{ marginBottom: 40 }}>
              {Array.from({ length: 3 }, (_, i) => (
                <div key={i} className="ligne-progression">
                  <div style={{ flex: 1 }}>
                    <Squelette largeur={120} hauteur={16} style={{ marginBottom: 8 }} />
                    <div className="barre-progression-conteneur">
                      <Squelette largeur="100%" hauteur={8} arrondi="999px" />
                    </div>
                  </div>
                  <Squelette largeur={40} hauteur={20} />
                </div>
              ))}
            </div>
            <div className="carte-reprendre-lecture">
              <div className="reprendre-lecture-texte">
                <Squelette largeur={120} hauteur={12} style={{ marginBottom: 6 }} />
                <Squelette largeur={180} hauteur={18} style={{ marginBottom: 4 }} />
                <Squelette largeur={220} hauteur={12} />
              </div>
              <Squelette largeur={100} hauteur={38} arrondi="var(--rayon-petit)" />
            </div>
          </>
        }
      >
        <div className="grille-stats">
          <div className="stat-carte">
            <div className="stat-carte-haut">
              <div className="stat-carte-icon bleu">
                <Users size={20} strokeWidth={2} />
              </div>
              <div className="valeur">{mentorsAnime}</div>
            </div>
            <div className="label">Mentor{mentorsAnime > 1 ? 's' : ''} suivi{mentorsAnime > 1 ? 's' : ''}</div>
            <p className="stat-carte-desc">Accompagnement personnalisé matière par matière</p>
          </div>
          <div className="stat-carte">
            <div className="stat-carte-haut">
              <div className="stat-carte-icon accent">
                <CreditCard size={20} strokeWidth={2} />
              </div>
              <div className="valeur">{abonnement ? 'Actif' : 'Inactif'}</div>
            </div>
            <div className="label">Statut de l'abonnement</div>
            <p className="stat-carte-desc">{abonnement ? `Formule ${abonnement.formule}` : 'Souscris pour débloquer les mentors'}</p>
          </div>
          <div className="stat-carte">
            <div className="stat-carte-haut">
              <div className="stat-carte-icon vert">
                <CalendarDays size={20} strokeWidth={2} />
              </div>
              <div className="valeur">{membresMois || '—'}</div>
            </div>
            <div className="label">Membre depuis</div>
            <p className="stat-carte-desc">Rejoins la communauté des élèves béninois</p>
          </div>
        </div>

        <div className="section-titre">
          <h2>Mes mentors</h2>
          <Link to="/mentors">Trouver un mentor →</Link>
        </div>
        <div className="carte" style={{ marginBottom: 40 }}>
          {suivis.length > 0 ? (
            <ul className="liste-simple">
              {suivis.map(s => (
                <li key={s.id}>
                  <div>
                    <strong>{s.mentor_name}</strong>
                    <span className="texte-doux"> — {s.matiere_nom}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16, minWidth: 0, flexWrap: 'wrap' }}>
                    <Etoiles note={s.note_evaluation} noteCible={s.note_evaluation} estActive suiviId={s.id} onNoter={noter} />
                    <Link to={`/conversations/${s.id}`} className="btn btn-primaire" style={{ flexShrink: 0 }}>Écrire</Link>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="etat-vide">
              <p>Tu ne suis encore aucun mentor.</p>
              <Link to="/mentors" className="btn btn-primaire">Trouver un mentor</Link>
            </div>
          )}
        </div>

        <div className="section-titre">
          <h2>Ma progression</h2>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <Link to="/cours/favoris" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <Bookmark size={14} /> Favoris
            </Link>
            <Link to="/cours">Voir tous les cours →</Link>
          </div>
        </div>
        <div className="carte" style={{ marginBottom: 40 }}>
          {progressions.length > 0 ? (
            progressions.map(p => (
              <div key={p.id} className="ligne-progression">
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="matiere-nom">{p.matiere_nom}</div>
                  <div className="barre-progression-conteneur">
                    <div className="barre-progression" style={{ width: `${p.niveau_maitrise}%` }} />
                  </div>
                </div>
                <div className="pourcentage">{Math.round(p.niveau_maitrise)}%</div>
              </div>
            ))
          ) : (
            <div className="etat-vide">
              <div className="etat-vide-icone">
                <GraduationCap size={40} strokeWidth={1.2} />
              </div>
              <p>Tu n'as pas encore de progression enregistrée.</p>
              <p className="texte-doux" style={{ fontSize: '0.9rem', marginTop: -12 }}>
                Passe ton premier examen pour commencer à suivre ton évolution.
              </p>
              <Link to="/examens" className="btn btn-primaire">Voir les examens disponibles</Link>
            </div>
          )}
        </div>

        {matieresHistorique.length > 0 && (
          <div style={{ marginBottom: 40 }}>
            <div className="section-titre">
              <h2 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <TrendingUp size={22} strokeWidth={2} />
                Évolution de ma progression
              </h2>
            </div>
            <div className="carte">
              <div className="evolution-selecteur">
                <label htmlFor="select-matiere-evolution">Matière</label>
                <select
                  id="select-matiere-evolution"
                  value={matiereSelectee ?? ''}
                  onChange={e => setMatiereSelectee(Number(e.target.value))}
                >
                  {matieresHistorique.map(m => (
                    <option key={m.id} value={m.id}>{m.nom}</option>
                  ))}
                </select>
              </div>

              {loadingHistorique ? (
                <div style={{ padding: '24px 0' }}>
                  <Squelette largeur="100%" hauteur={220} arrondi="var(--rayon-petit)" />
                </div>
              ) : historiquePoints.length < 2 ? (
                <div className="etat-vide" style={{ padding: '32px 0' }}>
                  <p>Passe encore quelques examens dans cette matière pour voir ta progression se dessiner ici.</p>
                </div>
              ) : Recharts ? (
                <div className="evolution-graphique">
                  <Recharts.ResponsiveContainer width="100%" height={280}>
                    <Recharts.LineChart
                      data={historiquePoints.map(p => {
                        const d = new Date(p.date_snapshot)
                        return {
                          jourCourt: d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }),
                          jourLong: d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }),
                          niveau: Number(p.niveau_maitrise),
                        }
                      })}
                      margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
                    >
                      <Recharts.CartesianGrid strokeDasharray="3 3" stroke="var(--couleur-bordure)" />
                      <Recharts.XAxis
                        dataKey="jourCourt"
                        tick={{ fontSize: 12, fill: 'var(--couleur-texte-doux)' }}
                        tickLine={false}
                        axisLine={{ stroke: 'var(--couleur-bordure)' }}
                        minTickGap={24}
                      />
                      <Recharts.YAxis
                        domain={[0, 100]}
                        tick={{ fontSize: 12, fill: 'var(--couleur-texte-doux)' }}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={v => `${v}%`}
                        width={44}
                      />
                      <Recharts.Tooltip
                        contentStyle={{
                          background: 'var(--couleur-fond-carte)',
                          border: '1px solid var(--couleur-bordure)',
                          borderRadius: 'var(--rayon-petit)',
                          fontSize: '0.85rem',
                          color: 'var(--couleur-texte)',
                        }}
                        formatter={v => [`${v}%`, 'Maîtrise']}
                        labelFormatter={(_, payload) => payload[0]?.payload?.jourLong ?? ''}
                      />
                      <Recharts.Line
                        type="monotone"
                        dataKey="niveau"
                        stroke="var(--couleur-accent)"
                        strokeWidth={2.5}
                        dot={{ r: 4, fill: 'var(--couleur-accent)', strokeWidth: 0 }}
                        activeDot={{ r: 6, fill: 'var(--couleur-accent)' }}
                        isAnimationActive={!reducedMotion}
                      />
                    </Recharts.LineChart>
                  </Recharts.ResponsiveContainer>
                </div>
              ) : (
                <div style={{ padding: '24px 0' }}>
                  <Squelette largeur="100%" hauteur={220} arrondi="var(--rayon-petit)" />
                </div>
              )}
            </div>
          </div>
        )}
      </ChargementFluide>

      {derniereActivite && (
        <div className="carte-reprendre-lecture">
          <div className="reprendre-lecture-texte">
            <p className="reprendre-lecture-label">Reprends ta lecture</p>
            <p className="reprendre-lecture-cours">{derniereActivite.titre}</p>
            <p className="reprendre-lecture-detail">
              {derniereActivite.matiere_nom} — Séquence {derniereActivite.ordre} : {derniereActivite.titre_sequence}
            </p>
          </div>
          <Link
            to={`/cours/${derniereActivite.cours_id}#sequence-${derniereActivite.sequence_id}`}
            className="btn btn-primaire reprendre-lecture-btn"
          >
            <Play size={16} fill="currentColor" /> Continuer
          </Link>
        </div>
      )}

      <div className="raccourcis-dashboard">
        {raccourcis.map(r => (
          <Link key={r.to} to={r.to} className="raccourci-carte">
            <div className="raccourci-icon">
              <r.icon size={22} strokeWidth={1.8} />
            </div>
            <div>
              <p className="raccourci-label">{r.label}</p>
              <p className="raccourci-desc">{r.desc}</p>
            </div>
          </Link>
        ))}
      </div>

      <div className="section-titre"><h2>Mon abonnement</h2></div>
      <div className="carte">
        {abonnement ? (
          <>
            <p><span className="badge badge-actif">Actif</span></p>
            <p className="texte-doux" style={{ marginTop: 12 }}>
              Formule {abonnement.formule} — expire le {new Date(abonnement.date_fin).toLocaleDateString('fr-FR')}
            </p>
            <Link to="/abonnement" className="btn btn-secondaire" style={{ marginTop: 12 }}>Gérer mon abonnement</Link>
          </>
        ) : (
          <div className="etat-vide">
            <p>Tu n'as pas d'abonnement actif. Souscris pour débloquer les mentors et l'accès complet aux cours.</p>
            <Link to="/abonnement" className="btn btn-primaire">Souscrire maintenant</Link>
          </div>
        )}
      </div>
    </main>
  )
}
