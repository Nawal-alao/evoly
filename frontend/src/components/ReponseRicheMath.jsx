import React, { useRef, useEffect } from 'react'

/*
  Rendu d'une valeur qui peut être du LaTeX brut ou du texte simple.

  - Détecte si la chaîne contient du LaTeX (commande précédée de "\",
    ou encadrée de $...$).
  - Si oui, la rend mathématiquement via KaTeX.
  - Sinon, l'affiche telle quelle.
*/

const PATTERN_LATEX = /[\\$]/

export default function ReponseRicheMath({ value, fallback = '' }) {
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    let annule = false

    const brut = (typeof value === 'string' ? value : '').trim()
    if (!brut) {
      el.textContent = fallback
      return undefined
    }

    // Détecte du LaTeX : commande "\" ou encadrement "$...$"
    if (!PATTERN_LATEX.test(brut)) {
      el.textContent = brut
      return undefined
    }

    // Normalise les délimiteurs $, \( \), \[ \]
    let latex = brut
    const strictPairs = [
      ['$$', '$$'],
      ['$', '$'],
      ['\\(', '\\)'],
      ['\\[', '\\]'],
    ]
    for (const [g, d] of strictPairs) {
      if (latex.startsWith(g) && latex.endsWith(d) && latex.length > g.length + d.length) {
        latex = latex.slice(g.length, d.length === 0 ? undefined : -d.length)
        break
      }
    }

    Promise.all([import('katex/dist/katex.min.css'), import('katex')])
      .then(([, { default: katex }]) => {
        if (annule) return
        try {
          el.innerHTML = katex.renderToString(latex, { throwOnError: false, displayMode: false })
        } catch {
          el.textContent = brut
        }
      })
      .catch(() => {
        if (!annule) el.textContent = brut
      })

    return () => { annule = true }
  }, [value, fallback])

  return <span ref={ref} />
}
