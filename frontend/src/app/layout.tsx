import type { Metadata } from 'next'
import '../index.css'

export const metadata: Metadata = {
  title: 'Intech Sistemas - Controle de Fluxo de SPEDs',
  description: 'Sistema de gestão e rastreabilidade de SPEDs fiscais',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body style={{ margin: 0, padding: 0 }}>{children}</body>
    </html>
  )
}
