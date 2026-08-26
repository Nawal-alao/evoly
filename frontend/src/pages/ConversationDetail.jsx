import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Send, ArrowLeft, MoreHorizontal, Copy, Paperclip, X } from 'lucide-react'
import { createPortal } from 'react-dom'
import { useAuth } from '../context/AuthContext'
import { useNotification } from '../context/NotificationContext'
import api from '../api/axios'
import AvatarInitiales from '../components/AvatarInitiales'

const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')

function mediaUrl(path) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${API_BASE}${path}`
}

function formaterDateSep(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const ajd = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const hier = new Date(ajd)
  hier.setDate(hier.getDate() - 1)
  const msgJour = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  if (msgJour.getTime() === ajd.getTime()) return "Aujourd'hui"
  if (msgJour.getTime() === hier.getTime()) return 'Hier'
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })
}

function formaterHeure(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

function grouperMessages(messages) {
  const groupes = []
  messages.forEach(m => {
    const derniere = groupes[groupes.length - 1]
    if (
      derniere &&
      derniere.auteurId === m.auteur?.id &&
      !m.image &&
      !derniere.messages[derniere.messages.length - 1].image &&
      (new Date(m.date_envoi) - new Date(derniere.messages[derniere.messages.length - 1].date_envoi)) < 5 * 60 * 1000
    ) {
      derniere.messages.push(m)
    } else {
      groupes.push({ auteurId: m.auteur?.id, messages: [m] })
    }
  })
  return groupes
}

function estMien(message, user) {
  return message.auteur?.id === user?.id || message.auteur?.username === user?.username
}

function CheckIcon({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 11" fill="none" xmlns="http://www.w3.org/2000/svg" className="conv-check-icon">
      <path d="M1.5 5.5L4.5 8.5L11 2" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function DoubleCheckIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 18 11" fill="none" xmlns="http://www.w3.org/2000/svg" className="conv-check-icon">
      <path d="M1.5 5.5L4.5 8.5L11 2" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M5.5 5.5L8.5 8.5L15 2" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function BulleMessage({ contenu, image, bullClass, tailClass, footer, onImageClick }) {
  const texteRef = useRef(null)
  const [expanded, setExpanded] = useState(false)
  const [isLong, setIsLong] = useState(false)

  useEffect(() => {
    const el = texteRef.current
    if (!el) return
    const full = el.scrollHeight
    const lh = parseFloat(getComputedStyle(el).lineHeight) || 22
    if (full > lh * 4.5 + 4) {
      setIsLong(true)
    }
  }, [contenu])

  const tronque = isLong && !expanded
  const hasImage = !!image

  return (
    <div className="conv-bulle-collapsible">
      <div className={`conv-bulle ${bullClass}${tailClass ? ` ${tailClass}` : ''}${tronque ? ' conv-bulle-tronquee' : ''}`}>
        {hasImage && (
          <img
            src={image}
            alt="Image envoyée"
            className="conv-bulle-image"
            onClick={() => onImageClick?.(image)}
          />
        )}
        {contenu && (
          <p ref={texteRef} className={`conv-texte${tronque ? ' conv-texte-tronque' : ''}`}>
            {contenu}
          </p>
        )}
        {footer && <div className="conv-bulle-footer">{footer}</div>}
      </div>
      {isLong && (
        <button type="button" className="conv-voir-plus" onClick={() => setExpanded(e => !e)}>
          {expanded ? 'Voir moins' : 'Voir plus'}
        </button>
      )}
    </div>
  )
}

function MenuContextuel({ x, y, texte, onCopier, onFermer }) {
  const ref = useRef(null)
  const [pos, setPos] = useState({ x, y })
  useEffect(() => {
    if (!ref.current) return
    const rect = ref.current.getBoundingClientRect()
    const vw = window.innerWidth
    const vh = window.innerHeight
    setPos({
      x: Math.min(x, vw - rect.width - 8),
      y: Math.min(y, vh - rect.height - 8),
    })
  }, [x, y])
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) onFermer() }
    document.addEventListener('mousedown', handler)
    document.addEventListener('touchstart', handler)
    return () => {
      document.removeEventListener('mousedown', handler)
      document.removeEventListener('touchstart', handler)
    }
  }, [onFermer])

  const style = { position: 'fixed', top: pos.y, left: pos.x, zIndex: 10000 }
  return createPortal(
    <div ref={ref} className="ctx-menu" style={style}>
      <button type="button" className="ctx-menu-item" onClick={() => onCopier(texte)}>
        <Copy size={14} strokeWidth={2} />
        <span>Copier</span>
      </button>
    </div>,
    document.body
  )
}

function ModalImage({ src, onFermer }) {
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onFermer() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onFermer])

  return createPortal(
    <div className="modal-image-overlay" onClick={onFermer}>
      <button type="button" className="modal-image-close" onClick={onFermer} aria-label="Fermer">
        <X size={24} strokeWidth={2} />
      </button>
      <img src={src} alt="Image en plein écran" className="modal-image-img" onClick={(e) => e.stopPropagation()} />
    </div>,
    document.body
  )
}

export default function ConversationDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { notifier } = useNotification()

  const [suivi, setSuivi] = useState(null)
  const [messages, setMessages] = useState([])
  const [contenu, setContenu] = useState('')
  const [sending, setSending] = useState(false)
  const [premierNonLu, setPremierNonLu] = useState(null)
  const [marqueLus, setMarqueLus] = useState(false)
  const [menuCtx, setMenuCtx] = useState(null)
  const [newMsgCount, setNewMsgCount] = useState(0)

  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [modalImage, setModalImage] = useState(null)

  const scrollRef = useRef(null)
  const textareaRef = useRef(null)
  const bottomRef = useRef(null)
  const fileInputRef = useRef(null)
  const scrollEstEnBas = useRef(true)

  const ajusterHauteur = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 140) + 'px'
  }, [])

  useEffect(() => { ajusterHauteur() }, [contenu, ajusterHauteur])

  useEffect(() => {
    let ignore = false
    api.get(`communaute/conversations/${id}/`).then(r => {
      if (ignore) return
      setSuivi(r.data)
      const msgs = r.data.messages || []
      setMessages(msgs)
      const premiersNonLus = msgs.find(m => !m.lu && !estMien(m, user))
      if (premiersNonLus) setPremierNonLu(premiersNonLus.id)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'instant' }), 60)
      setTimeout(() => {
        if (!ignore) {
          api.post(`communaute/conversations/${id}/`).then(() => { if (!ignore) setMarqueLus(true) })
        }
      }, 1500)
    })
    return () => { ignore = true }
  }, [id, user])

  useEffect(() => {
    const zone = scrollRef.current
    if (!zone) return
    const handler = () => {
      scrollEstEnBas.current = zone.scrollHeight - zone.scrollTop - zone.clientHeight < 80
      if (scrollEstEnBas.current) setNewMsgCount(0)
    }
    zone.addEventListener('scroll', handler, { passive: true })
    return () => zone.removeEventListener('scroll', handler)
  }, [])

  useEffect(() => {
    if (scrollEstEnBas.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    } else if (messages.length > 0) {
      const der = messages[messages.length - 1]
      if (estMien(der, user)) {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
      } else {
        setNewMsgCount(c => c + 1)
      }
    }
  }, [messages, user])

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      notifier('Seules les images sont acceptées.', 'error')
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      notifier('Image trop lourde (max 5 Mo).', 'error')
      return
    }
    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
  }

  const annulerImage = () => {
    if (imagePreview) URL.revokeObjectURL(imagePreview)
    setImageFile(null)
    setImagePreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSend = useCallback((e) => {
    e.preventDefault()
    const txt = contenu.trim()
    if ((!txt && !imageFile) || sending) return
    setSending(true)

    const formData = new FormData()
    if (txt) formData.append('contenu', txt)
    if (imageFile) formData.append('image', imageFile)

    api.post(`communaute/conversations/${id}/envoyer/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => {
      setMessages(prev => [...prev, r.data])
      setContenu('')
      annulerImage()
      if (textareaRef.current) textareaRef.current.style.height = 'auto'
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    }).catch(() => {
      notifier("Une erreur est survenue, réessaie dans un instant.", 'error')
    }).finally(() => setSending(false))
  }, [contenu, imageFile, sending, id, notifier])

  const copierMessage = useCallback((texte) => {
    navigator.clipboard.writeText(texte).then(() => {
      notifier('Message copié.', 'info')
    }).catch(() => {
      notifier('Impossible de copier.', 'error')
    })
    setMenuCtx(null)
  }, [notifier])

  const roleInterlocuteur = user?.classe_scolaire !== undefined ? 'mentor' : 'eleve'

  if (!suivi) {
    return (
      <main className="conv-loading">
        <div className="etat-vide"><p>Chargement…</p></div>
      </main>
    )
  }

  const groupes = grouperMessages(messages)
  const affichage = []
  let derniereDate = null

  groupes.forEach((groupe, gi) => {
    const premierMsg = groupe.messages[0]
    const dMsg = new Date(premierMsg.date_envoi).toDateString()

    if (dMsg !== derniereDate) {
      affichage.push({ type: 'date', key: `date-${gi}`, iso: premierMsg.date_envoi })
      derniereDate = dMsg
    }

    const estMienGroupe = estMien(premierMsg, user)
    const prenom = estMienGroupe ? (user?.prenom || '') : (suivi.interlocuteur_prenom || '')
    const nomA = estMienGroupe ? (user?.nom || '') : (suivi.interlocuteur?.split(' ').slice(1).join(' ') || '')
    const role = estMienGroupe ? (user?.classe_scolaire !== undefined ? 'eleve' : 'mentor') : roleInterlocuteur

    groupe.messages.forEach((m, mi) => {
      if (premierNonLu && !marqueLus && m.id === premierNonLu) {
        affichage.push({ type: 'nouveaux', key: 'sep-nouveaux' })
      }
      affichage.push({
        type: 'message',
        message: m,
        estMien: estMienGroupe,
        prenom,
        nom: nomA,
        role,
        premierDuGroupe: mi === 0,
        dernierDuGroupe: mi === groupe.messages.length - 1,
        cleGroupe: `groupe-${gi}`,
      })
    })
  })

  const canSend = contenu.trim() || imageFile

  return (
    <main className="conv-page">
      <div className="conv-header">
        <button type="button" className="conv-retour" onClick={() => navigate('/conversations')} aria-label="Retour aux conversations">
          <ArrowLeft size={20} strokeWidth={2} />
        </button>
        <AvatarInitiales prenom={suivi.interlocuteur_prenom} nom={suivi.interlocuteur?.split(' ').slice(1).join(' ')} taille={36} role={roleInterlocuteur} />
        <div className="conv-header-info">
          <span className="conv-header-nom">{suivi.interlocuteur}</span>
          <span className="conv-header-meta">
            <span className="matiere-tag">{suivi.matiere}</span>
            <span className="conv-header-sous">{suivi.sous_texte}</span>
          </span>
        </div>
      </div>

      <div className="conv-messages" ref={scrollRef}>
        <div className="conv-messages-inner">
          {affichage.length > 0 ? affichage.map(item => {
            if (item.type === 'date') {
              return (
                <div key={item.key} className="conv-sep-date">
                  <span className="conv-sep-date-ligne" />
                  <span className="conv-sep-date-texte">{formaterDateSep(item.iso)}</span>
                  <span className="conv-sep-date-ligne" />
                </div>
              )
            }
            if (item.type === 'nouveaux') {
              return (
                <div key={item.key} className="conv-sep-nouveaux">
                  <span className="conv-sep-nouveaux-ligne" />
                  <span className="conv-sep-nouveaux-texte">Nouveaux messages</span>
                  <span className="conv-sep-nouveaux-ligne" />
                </div>
              )
            }

            const m = item.message
            const showHeader = item.premierDuGroupe
            const bullClass = item.estMien ? 'conv-bulle-mien' : 'conv-bulle-autre'
            const rowClass = item.estMien ? 'conv-row-mien' : 'conv-row-autre'
            const contentClass = item.estMien ? 'conv-content-mien' : 'conv-content-autre'

            return (
              <div key={m.id} className={`conv-row ${rowClass} ${showHeader ? 'conv-row-premier' : 'conv-row-suite'}`}>
                {!item.estMien && (
                  <div className="conv-avatar-col">
                    {showHeader ? (
                      <AvatarInitiales prenom={item.prenom} nom={item.nom} taille={32} role={item.role} />
                    ) : (
                      <div style={{ width: 32, flexShrink: 0 }} />
                    )}
                  </div>
                )}

                <div className={`conv-content ${contentClass}`}>
                  {showHeader && !item.estMien && (
                    <div className="conv-msg-header">
                      <span className="conv-msg-auteur">{item.prenom}</span>
                    </div>
                  )}

                  <div className="conv-bulle-wrap">
                    <BulleMessage
                      contenu={m.contenu}
                      image={mediaUrl(m.image)}
                      bullClass={bullClass}
                      tailClass={item.dernierDuGroupe ? (item.estMien ? 'conv-bulle-tail-mien' : 'conv-bulle-tail-autre') : ''}
                      onImageClick={setModalImage}
                      footer={item.estMien ? (
                        <>
                          <span className="conv-msg-time">{formaterHeure(m.date_envoi)}</span>
                          {m.lu ? <DoubleCheckIcon size={16} /> : <CheckIcon size={14} />}
                        </>
                      ) : null}
                    />

                    <button
                      type="button"
                      className="conv-more-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        setMenuCtx(menuCtx?.id === m.id ? null : { id: m.id, x: e.clientX, y: e.clientY, texte: m.contenu })
                      }}
                      aria-label="Plus d'options"
                    >
                      <MoreHorizontal size={14} strokeWidth={2} />
                    </button>
                  </div>
                </div>

                {item.estMien && (
                  <div className="conv-avatar-col conv-avatar-col-mien">
                    {showHeader ? (
                      <AvatarInitiales prenom={item.prenom} nom={item.nom} taille={32} role={item.role} />
                    ) : (
                      <div style={{ width: 32, flexShrink: 0 }} />
                    )}
                  </div>
                )}
              </div>
            )
          }) : (
            <div className="etat-vide">
              <p>Aucun message pour le moment. Lance la conversation !</p>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {newMsgCount > 0 && (
          <button type="button" className="conv-scroll-bottom" onClick={() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); setNewMsgCount(0) }}>
            ↓ {newMsgCount} nouveau{newMsgCount > 1 ? 'x' : ''}
          </button>
        )}
      </div>

      <div className="conv-input-zone">
        {imagePreview && (
          <div className="conv-image-preview">
            <img src={imagePreview} alt="Aperçu" className="conv-image-preview-img" />
            <button type="button" className="conv-image-preview-annuler" onClick={annulerImage} aria-label="Annuler l'image">
              <X size={16} strokeWidth={2.5} />
            </button>
          </div>
        )}

        <form className="conv-input-form" onSubmit={handleSend}>
          <input
            type="file"
            ref={fileInputRef}
            accept="image/*"
            capture="environment"
            onChange={handleFileSelect}
            className="conv-file-input"
          />
          <button
            type="button"
            className="conv-attach-btn"
            onClick={() => fileInputRef.current?.click()}
            aria-label="Joindre une photo"
          >
            <Paperclip size={20} strokeWidth={2} />
          </button>

          <textarea
            ref={textareaRef}
            className="conv-textarea"
            placeholder={imageFile ? 'Ajoute un message (optionnel)…' : 'Écris ton message...'}
            rows={1}
            value={contenu}
            onChange={e => setContenu(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend(e)
              }
            }}
          />
          <button type="submit" className="conv-send" disabled={sending || !canSend} aria-label="Envoyer">
            <Send size={18} strokeWidth={2} />
          </button>
        </form>
      </div>

      {menuCtx && (
        <MenuContextuel x={menuCtx.x} y={menuCtx.y} texte={menuCtx.texte} onCopier={copierMessage} onFermer={() => setMenuCtx(null)} />
      )}

      {modalImage && <ModalImage src={modalImage} onFermer={() => setModalImage(null)} />}
    </main>
  )
}
