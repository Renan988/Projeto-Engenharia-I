import type { InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
}

export function Input({ label, id, error, style, ...rest }: InputProps) {
  const inputId = id || rest.name

  return (
    <div style={{ marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
      <label
        htmlFor={inputId}
        style={{
          fontSize: '0.875rem',
          fontWeight: 600,
          color: 'var(--text-color, #1f2937)',
          textAlign: 'left',
        }}
      >
        {label}
      </label>
      <input
        id={inputId}
        style={{
          padding: '0.625rem 0.75rem',
          borderRadius: '6px',
          border: error ? '1px solid #ef4444' : '1px solid #d1d5db',
          fontSize: '1rem',
          outline: 'none',
          backgroundColor: '#fff',
          color: '#111827',
          transition: 'border-color 0.15s ease-in-out',
          ...style,
        }}
        {...rest}
      />
      {error && (
        <span
          role="alert"
          style={{
            fontSize: '0.75rem',
            color: '#dc2626',
            textAlign: 'left',
          }}
        >
          {error}
        </span>
      )}
    </div>
  )
}
