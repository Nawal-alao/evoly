import React, { Suspense, useState, useEffect } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { Sun, Moon } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { useNotification, ConteneurNotifications } from '../context/NotificationContext'
import EntreePage from './EntreePage'
import MenuCompte from './MenuCompte'

const HAMBURGER = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="3" y1="6" x2="21" y2="6" />
    <line x1="3" y1="12" x2="21" y2="12" />
    <line x1="3" y1="18" x2="21" y2="18" />
  </svg>
)

export default function Layout() {
  const { user, userType, loading, logout } = useAuth()
  const { theme, basculer } = useTheme()
  const { notifications, notifier, retirer } = useNotification()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOuvert, setMenuOuvert] = useState(false)

  useEffect(() => {
    setMenuOuvert(false)
  }, [location.pathname])

  const handleLogout = () => {
    logout()
    notifier("Tu es déconnecté. À bientôt !", 'info')
    navigate('/')
  }

  const profilPath = userType === 'mentor' ? '/profil/mentor' : '/profil/eleve'

  return (
    <>
      <header className="entete">
        <div className="entete-conteneur">
          <div className="entete-gauche">
            <Link to="/" className="logo">Évoly<span>.</span></Link>

            <nav className={`nav-liens${menuOuvert ? ' ouvert' : ''}`}>
              {!loading && (
                <>
                  {user ? (
                    <>
                      {/* Liens directs d'usage fréquent */}
                      {userType === 'eleve' ? (
                        <>
                          <Link to="/dashboard/eleve" onClick={() => setMenuOuvert(false)}>Tableau de bord</Link>
                          <Link to="/cours" onClick={() => setMenuOuvert(false)}>Cours</Link>
                          <Link to="/examens" onClick={() => setMenuOuvert(false)}>Examens</Link>
                          <Link to="/mentors" onClick={() => setMenuOuvert(false)}>Mentors</Link>
                          <Link to="/conversations" onClick={() => setMenuOuvert(false)}>Messages</Link>
                          <Link to="/communaute" onClick={() => setMenuOuvert(false)}>Communauté</Link>
                        </>
                      ) : (
                        <>
                          <Link to="/dashboard/mentor" onClick={() => setMenuOuvert(false)}>Tableau de bord</Link>
                          <Link to="/cours" onClick={() => setMenuOuvert(false)}>Cours</Link>
                          <Link to="/conversations" onClick={() => setMenuOuvert(false)}>Messages</Link>
                          <Link to="/communaute" onClick={() => setMenuOuvert(false)}>Communauté</Link>
                        </>
                      )}

                      {/* Section compte intégrée au menu mobile uniquement */}
                      <div className="nav-mobile-uniquement">
                        <div className="nav-mobile-separateur" />
                        <Link to={profilPath} onClick={() => setMenuOuvert(false)}>Mon profil</Link>
                        {userType === 'eleve' && (
                          <Link to="/abonnement" onClick={() => setMenuOuvert(false)}>Abonnement</Link>
                        )}
                        <div className="nav-mobile-actions">
                          <button
                            type="button"
                            className="btn btn-secondaire"
                            onClick={() => {
                              setMenuOuvert(false)
                              handleLogout()
                            }}
                          >
                            Se déconnecter
                          </button>
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <Link to="/cours" onClick={() => setMenuOuvert(false)}>Cours</Link>
                      <Link to="/mentors" onClick={() => setMenuOuvert(false)}>Mentors</Link>

                      <div className="nav-actions">
                        <Link to="/connexion" className="btn btn-secondaire" onClick={() => setMenuOuvert(false)}>Se connecter</Link>
                        <Link to="/inscription/eleve" className="btn btn-primaire" onClick={() => setMenuOuvert(false)}>Commencer</Link>
                      </div>
                    </>
                  )}
                </>
              )}
            </nav>
          </div>

          <div className="entete-droite">
            <button
              className="bouton-theme"
              onClick={basculer}
              aria-label={theme === 'clair' ? 'Passer en mode sombre' : 'Passer en mode clair'}
            >
              {theme === 'clair' ? <Moon size={18} /> : <Sun size={18} />}
            </button>

            {!loading && (
              user ? (
                <div className="desktop-uniquement">
                  <MenuCompte user={user} userType={userType} onLogout={handleLogout} />
                </div>
              ) : (
                <div className="nav-actions desktop-uniquement">
                  <Link to="/connexion" className="btn btn-secondaire">Se connecter</Link>
                  <Link to="/inscription/eleve" className="btn btn-primaire">Commencer</Link>
                </div>
              )
            )}

            <button
              className="bouton-menu-mobile"
              aria-label={menuOuvert ? 'Fermer le menu' : 'Ouvrir le menu'}
              aria-expanded={String(menuOuvert)}
              onClick={() => setMenuOuvert(prev => !prev)}
            >
              {HAMBURGER}
            </button>
          </div>
        </div>
      </header>

      <ConteneurNotifications notifications={notifications} onRetirer={retirer} />

      <EntreePage key={location.pathname}>
        <Suspense fallback={
          <main>
            <div className="etat-vide" style={{ minHeight: '40vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
              <div className="squelette" style={{ width: 180, height: 20, borderRadius: 8 }} />
              <div className="squelette" style={{ width: 140, height: 14, borderRadius: 8 }} />
            </div>
          </main>
        }>
          <Outlet />
        </Suspense>
      </EntreePage>

      {!/^\/conversations\/\d+$/.test(location.pathname) && (
        <footer>
          <p>© {new Date().getFullYear()} Évoly — Plateforme éducative béninoise.</p>
        </footer>
      )}
    </>
  )
}
