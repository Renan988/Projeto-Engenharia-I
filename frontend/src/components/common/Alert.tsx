import type { ReactNode } from 'react'

interface AlertProps {
  type?: 'error' | 'warning' | 'info' | 'success'
  message: ReactNode
  onClose?: () => void
}

export function Alert({ type = 'error', message, onClose }: AlertProps) {
  const styles = {
    error: {
      bg: '#fef2f2',
      border: '#f87171',
      text: '#991b1b',
    },
    warning: {
      bg: '#fffbeb',
      border: '#fcd34d',
      text: '#92400e',
    },
    info: {
      bg: '#eff6ff',
      border: '#93c5fd',
      text: '#1e40af',
    },
    success: {
      bg: '#f0fdf4',
      border: '#86efac',
      text: '#166534',
    },
  }[type]

  return (
    <div
      role="alert"
      style={{
        backgroundColor: styles.bg,
        border: `1px solid ${styles.border}`,
        color: styles.text,
        padding: '0.75rem 1rem',
        borderRadius: '6px',
        marginBottom: '1rem',
        fontSize: '0.875rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '0.5rem',
      }}
    >
      <div style={{ flex: 1 }}>{message}</div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          aria-label="Fechar alerta"
          style={{
            background: 'none',
            border: 'none',
            color: 'inherit',
            cursor: 'pointer',
            fontWeight: 'bold',
            padding: '0 4px',
          }}
        >
          ×
        </button>
      )}
    </div>
  )
}
