import React, { useEffect, useRef, useState, useCallback } from 'react'

/*
  Champ de réponse mathématique WYSIWYG basé sur MathLive.

  - vrai éditeur mathématique : les structures (\frac{}, coordonnées,
    vecteurs...) sont insérées comme des champs éditables vides dans
    lesquels l'élève clique et tape.
  - la barre d'outils compose des structures ; le clavier mathématique
    intégré de MathLive complète la saisie au touché.
  - la valeur soumise est exportée en LaTeX (élève invisible).
*/

const OUTILS = [
  { id: 'frac',   label: 'a/b',     titre: 'Fraction',         latex: '\\frac{#0}{#1}' },
  { id: 'sqrt',   label: '√x',      titre: 'Racine carrée',    latex: '\\sqrt{#0}' },
  { id: 'puiss',  label: 'x²',      titre: 'Puissance',        latex: '{{{#0}}^{#1}}' },
  { id: 'indice', label: 'x_i',     titre: 'Indice',           latex: '{#0}_{#1}' },
  { id: 'vec',    label: 'AB→',     titre: 'Vecteur',          latex: '\\vec{#0}' },
  { id: 'tuple',  label: '(x;y;z)', titre: 'Coordonnées (x;y;z)', latex: '\\left({#0};{#1};{#2}\\right)' },
  { id: 'somme',  label: 'Σ',       titre: 'Somme',            latex: '\\sum_{#0}^{#1}{#2}' },
  { id: 'integ',  label: '∫',       titre: 'Intégrale',        latex: '\\int_{#0}^{#1}{#2}' },
  { id: 'point',  label: 'A( )',    titre: 'Point A',          latex: 'A\\left({#0}\\right)' },
  { id: 'fois',   label: '×',       titre: 'Multiplier',       latex: '\\times' },
  { id: 'fracL',  label: '÷',       titre: 'Diviser',          latex: '\\div' },
  { id: 'egal',   label: '=',       titre: 'Égal',             latex: '=' },
  { id: 'approx', label: '≈',       titre: 'Approximativement', latex: '\\approx' },
  { id: 'inf',    label: '→',       titre: 'Flèche',           latex: '\\to' },
]

export default function ChampReponseMath({ value, onChange, placeholder }) {
  const conteneurRef = useRef(null)
  const champRef = useRef(null)
  const [pret, setPret] = useState(false)
  const ignoreSynchro = useRef(false)

  useEffect(() => {
    let annule = false
    const conteneur = conteneurRef.current
    if (!conteneur) return undefined

    let mathField = null

    async function charger() {
      await Promise.all([
        import('mathlive'),
        import('mathlive/fonts.css'),
        import('mathlive/static.css'),
      ])
      if (annule || !conteneurRef.current) return

      mathField = document.createElement('math-field')
      mathField.setAttribute('style', 'width:100%; height:100%;')
      mathField.virtualKeyboardMode = 'onfocus'
      mathField.value = value || ''
      mathField.placeholder = placeholder || ''
      conteneurRef.current.appendChild(mathField)
      champRef.current = mathField
      setPret(true)

      mathField.addEventListener('input', () => {
        ignoreSynchro.current = true
        if (onChange) onChange(mathField.value)
      })
    }

    charger()
    return () => {
      annule = true
      if (mathField && mathField.parentNode) mathField.parentNode.removeChild(mathField)
      champRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Synchro depuis la source externe (ex: reset) sans écraser la frappe
  useEffect(() => {
    const mf = champRef.current
    if (!mf) return
    if (ignoreSynchro.current) {
      ignoreSynchro.current = false
      return
    }
    if (mf.value !== value) mf.setValue(value || '')
  }, [value])

  const inserer = useCallback((latex) => {
    const mf = champRef.current
    if (!mf) return
    mf.executeCommand('insert', latex)
    mf.focus()
  }, [])

  return (
    <div className="rep-math">
      <div className="rep-math-ruban" role="toolbar" aria-label="Barre d'outils mathématiques">
        {OUTILS.map(outil => (
          <button
            key={outil.id}
            type="button"
            className="rep-math-outil"
            title={outil.titre}
            aria-label={outil.titre}
            disabled={!pret}
            onClick={() => inserer(outil.latex)}
          >
            {outil.label}
          </button>
        ))}
      </div>
      <div className="rep-math-zone-ml" ref={conteneurRef} />
    </div>
  )
}
