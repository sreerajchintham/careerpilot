import type { AppProps } from 'next/app'
import '../src/styles/globals.css'
import { AuthProvider } from '../contexts/AuthContext'
import { Toaster } from 'react-hot-toast'

// Custom App component to apply global styles and wrap all pages
export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <Component {...pageProps} />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
        }}
      />
    </AuthProvider>
  )
}


