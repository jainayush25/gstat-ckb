import Navbar from '../components/Navbar'
import NewsTicker from '../components/NewsTicker'
import WhatsNew from '../components/WhatsNew'
import Hero from '../components/Hero'
import QuickTools from '../components/QuickTools'
import ArticlesSection from '../components/ArticlesSection'
import GSTATGuide from '../components/GSTATGuide'
import ResourcesSection from '../components/ResourcesSection'
import TeamCTA from '../components/TeamCTA'
import Footer from '../components/Footer'

export default function Home() {
  return (
    <div className="min-h-screen bg-white font-sans">
      <Navbar />
      <NewsTicker />
      <WhatsNew />
      <Hero />
      <QuickTools />
      <ArticlesSection />
      <GSTATGuide />
      <ResourcesSection />
      <TeamCTA />
      <Footer />
    </div>
  )
}
