import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger'
  isLoading?: boolean
  children: ReactNode
}

export function Button({
  variant = 'primary',
  isLoading = false,
  children,
  disabled,
  style,
  ...rest
}: ButtonProps) {
  const baseColors = {
    primary: {
      bg: '#2563eb',
      color: '#ffffff',
      hover: '#1d4ed8',
    },
    secondary: {
      bg: '#e5e7eb',
      color: '#1f2937',
      hover: '#d1d5db',
    },
    danger: {
      bg: '#dc2626',
      color: '#ffffff',
      hover: '#b91c1c',
    },
  }[variant]

  return (
    <button
      disabled={disabled || isLoading}
      style={{
        padding: '0.625rem 1.25rem',
        borderRadius: '6px',
        fontSize: '0.9375rem',
        fontWeight: 600,
        cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
        opacity: disabled || isLoading ? 0.7 : 1,
        backgroundColor: baseColors.bg,
        color: baseColors.color,
        border: 'none',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.5rem',
        transition: 'background-color 0.15s ease',
        ...style,
      }}
      {...rest}
    >
      {isLoading ? (
        <>
          <span
            style={{
              display: 'inline-block',
              width: '14px',
              height: '14px',
              border: '2px solid currentColor',
              borderRightColor: 'transparent',
              borderRadius: '50%',
              animation: 'spin 0.75s linear infinite',
            }}
          />
          <span>Carregando...</span>
        </>
      ) : (
        children
      )}
    </button>
  )
}
