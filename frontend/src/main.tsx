import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './auth'
import { ThemeProvider } from './ThemeProvider'
import './index.css'
// Iron Editorial faces (C2.0): bundled but not yet applied to any surface.
import './fonts'

const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, retry: 1 } } })
// ThemeProvider sits inside AuthProvider because the resolved theme is role-aware
// (trainee dark / coach light); AuthProvider hydrates the user synchronously, so the
// theme is correct on first paint.
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={queryClient}><BrowserRouter><AuthProvider><ThemeProvider><App/></ThemeProvider></AuthProvider></BrowserRouter></QueryClientProvider></React.StrictMode>)
