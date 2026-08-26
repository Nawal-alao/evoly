import React, { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'

export default function ChampMotDePasse({ id, value, onChange, autoComplete, required, className }) {
  const [visible, setVisible] = useState(false)

  return (
    <div className={`champ-mdp-wrapper ${className || ''}`}>
      <input
        id={id}
        type={visible ? 'text' : 'password'}
        required={required}
        autoComplete={autoComplete}
        value={value}
        onChange={onChange}
      />
      <button
        type="button"
        className="bouton-toggle-mdp"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
        tabIndex={-1}
      >
        {visible ? <EyeOff size={18} /> : <Eye size={18} />}
      </button>
    </div>
  )
}
