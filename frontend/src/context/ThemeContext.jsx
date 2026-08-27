import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const ThemeContext = createContext()

const CLE_THEME = 'theme'

function lireThemeInitial() {
  const sauvegarde = localStorage.getItem(CLE_THEME)
  if (sauvegarde === 'sombre' || sauvegarde === 'clair') return sauvegarde
  if (window.matchMedia?.('(prefers-color-scheme: dark)').matches) return 'sombre'
  return 'clair'
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(lireThemeInitial)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem(CLE_THEME, theme)
  }, [theme])

  useEffect(() => {
    const media = window.matchMedia?.('(prefers-color-scheme: dark)')
    if (!media) return

    const handler = (e) => {
      if (!localStorage.getItem(CLE_THEME)) {
        setTheme(e.matches ? 'sombre' : 'clair')
      }
    }
    media.addEventListener('change', handler)
    return () => media.removeEventListener('change', handler)
  }, [])

  useEffect(() => {
    const handler = (e) => {
      if (e.key === CLE_THEME && (e.newValue === 'sombre' || e.newValue === 'clair')) {
        setTheme(e.newValue)
        document.documentElement.dataset.theme = e.newValue
      }
    }
    window.addEventListener('storage', handler)
    return () => window.removeEventListener('storage', handler)
  }, [])

  const basculer = useCallback(() => {
    setTheme((prev) => (prev === 'clair' ? 'sombre' : 'clair'))
  }, [])

  return (
    <ThemeContext.Provider value={{ theme, basculer }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme doit être utilisé dans un ThemeProvider')
  return ctx
}
