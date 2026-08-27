import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { AuthProvider } from './context/AuthContext'
import { NotificationProvider } from './context/NotificationContext'
import Layout from './components/Layout'
import RouteProtegee from './components/RouteProtegee'

const Home = React.lazy(() => import('./pages/Home'))
const Connexion = React.lazy(() => import('./pages/Connexion'))
const InscriptionEleve = React.lazy(() => import('./pages/InscriptionEleve'))
const InscriptionMentor = React.lazy(() => import('./pages/InscriptionMentor'))
const DashboardEleve = React.lazy(() => import('./pages/DashboardEleve'))
const DashboardMentor = React.lazy(() => import('./pages/DashboardMentor'))
const CoursList = React.lazy(() => import('./pages/CoursList'))
const CoursDetail = React.lazy(() => import('./pages/CoursDetail'))
const ExamensList = React.lazy(() => import('./pages/ExamensList'))
const PasserExamen = React.lazy(() => import('./pages/PasserExamen'))
const ResultatDetail = React.lazy(() => import('./pages/ResultatDetail'))
const Mentors = React.lazy(() => import('./pages/Mentors'))
const Profil = React.lazy(() => import('./pages/Profil'))
const Abonnement = React.lazy(() => import('./pages/Abonnement'))
const Communaute = React.lazy(() => import('./pages/Communaute'))
const GroupeDetail = React.lazy(() => import('./pages/GroupeDetail'))
const Conversations = React.lazy(() => import('./pages/Conversations'))
const ConversationDetail = React.lazy(() => import('./pages/ConversationDetail'))

export default function App() {
  return (
    <ThemeProvider>
    <NotificationProvider>
      <AuthProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/connexion" element={<Connexion />} />
            <Route path="/inscription/eleve" element={<InscriptionEleve />} />
            <Route path="/inscription/mentor" element={<InscriptionMentor />} />

            <Route path="/dashboard/eleve" element={<RouteProtegee><DashboardEleve /></RouteProtegee>} />
            <Route path="/dashboard/mentor" element={<RouteProtegee><DashboardMentor /></RouteProtegee>} />
            <Route path="/cours" element={<RouteProtegee><CoursList /></RouteProtegee>} />
            <Route path="/cours/favoris" element={<RouteProtegee><CoursList /></RouteProtegee>} />
            <Route path="/cours/:id" element={<RouteProtegee><CoursDetail /></RouteProtegee>} />
            <Route path="/examens" element={<RouteProtegee><ExamensList /></RouteProtegee>} />
            <Route path="/examens/:id/passer" element={<RouteProtegee><PasserExamen /></RouteProtegee>} />
            <Route path="/resultats/:id" element={<RouteProtegee><ResultatDetail /></RouteProtegee>} />
            <Route path="/mentors" element={<RouteProtegee><Mentors /></RouteProtegee>} />
            <Route path="/profil" element={<RouteProtegee><Profil /></RouteProtegee>} />
            <Route path="/profil/eleve" element={<RouteProtegee><Profil /></RouteProtegee>} />
            <Route path="/profil/mentor" element={<RouteProtegee><Profil /></RouteProtegee>} />
            <Route path="/abonnement" element={<RouteProtegee><Abonnement /></RouteProtegee>} />
            <Route path="/communaute" element={<RouteProtegee><Communaute /></RouteProtegee>} />
            <Route path="/communaute/:id" element={<RouteProtegee><GroupeDetail /></RouteProtegee>} />
            <Route path="/conversations" element={<RouteProtegee><Conversations /></RouteProtegee>} />
            <Route path="/conversations/:id" element={<RouteProtegee><ConversationDetail /></RouteProtegee>} />
          </Route>
        </Routes>
      </AuthProvider>
    </NotificationProvider>
    </ThemeProvider>
  )
}
