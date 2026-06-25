import { Users, ArrowRight } from 'lucide-react'
export default function TeamCTA() {
  return (
    <section className="py-14 bg-gradient-to-r from-brand-700 to-brand-600">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 bg-white/15 rounded-2xl mb-5"><Users className="w-7 h-7 text-white" /></div>
        <h2 className="text-3xl font-bold text-white mt-2 mb-3">Meet Our GSTAT Team</h2>
        <p className="text-brand-100 max-w-xl mx-auto text-base mb-8">Our experienced team of GSTAT specialists is ready to assist you.</p>
        <a href="/meet-our-team" className="inline-flex items-center gap-2 px-6 py-3 bg-white text-brand-700 rounded-xl font-semibold text-sm hover:bg-brand-50">Meet Our GSTAT Team <ArrowRight className="w-4 h-4" /></a>
      </div>
    </section>
  )
}
