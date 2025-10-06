import type { AppProps } from 'next/app'
import '../src/styles/globals.css'

// Custom App component to apply global styles and wrap all pages
export default function MyApp({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />
}


