import React, { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, User, Sparkles, LogOut } from 'lucide-react'
import AvatarInitiales from './AvatarInitiales'

export default function MenuCompte({ user, userType, onLogout }) {
  const [ouvert, setOuvert] = useState(false)
  const menuRef = useRef(null)

  // Ferme le menu au clic en dehors ou sur Échap
  useEffect(() => {
    if (!ouvert) return

    const handleClickExterieur = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setOuvert(false)
      }
    }

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setOuvert(false)
      }
    }

    document.addEventListener('pointerdown', handleClickExterieur)
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('pointerdown', handleClickExterieur)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [ouvert])

  if (!user) return null

  const prenom = user.prenom || (userType === 'mentor' ? 'Mentor' : 'Élève')
  const profilPath = userType === 'mentor' ? '/profil/mentor' : '/profil/eleve'

  return (
    <div className="menu-compte-conteneur" ref={menuRef}>
      <button
        type="button"
        className={`menu-compte-declencheur ${ouvert ? 'ouvert' : ''}`}
        onClick={() => setOuvert(prev => !prev)}
        aria-expanded={ouvert}
        aria-haspopup="true"
        aria-label={`Menu de compte de ${prenom}`}
      >
        <AvatarInitiales
          prenom={user.prenom}
          nom={user.nom}
          taille={32}
          role={userType}
        />
        <span className="menu-compte-prenom">{prenom}</span>
        <ChevronDown size={15} className={`menu-compte-chevron ${ouvert ? 'rotation' : ''}`} />
      </button>

      {ouvert && (
        <div className="menu-compte-dropdown" role="menu">
          <Link
            to={profilPath}
            className="menu-compte-item"
            role="menuitem"
            onClick={() => setOuvert(false)}
          >
            <User size={16} />
            <span>Mon profil</span>
          </Link>

          {userType === 'eleve' && (
            <Link
              to="/abonnement"
              className="menu-compte-item"
              role="menuitem"
              onClick={() => setOuvert(false)}
            >
              <Sparkles size={16} />
              <span>Abonnement</span>
            </Link>
          )}

          <div className="menu-compte-separateur" role="separator" />

          <button
            type="button"
            className="menu-compte-item menu-compte-item--deconnexion"
            role="menuitem"
            onClick={() => {
              setOuvert(false)
              onLogout?.()
            }}
          >
            <LogOut size={16} />
            <span>Se déconnecter</span>
          </button>
        </div>
      )}
    </div>
  )
}
