import { ArrowRight, Calculator, BookOpen } from 'lucide-react'
export default function Hero() {
  return (
    <section className="relative bg-gradient-to-br from-brand-800 via-brand-700 to-brand-600 text-white overflow-hidden">
      <div className="absolute inset-0 opacity-10"><div className="absolute top-0 right-0 w-96 h-96 bg-white rounded-full -translate-y-1/2 translate-x-1/2" /></div>
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
        <div className="inline-flex items-center gap-2 bg-white/15 backdrop-blur-sm border border-white/20 rounded-full px-4 py-1.5 mb-6"><div className="w-1.5 h-1.5 bg-brand-300 rounded-full animate-pulse" /><span className="text-sm text-white/90 font-medium">Independent resource by CKB</span></div>
        <div className="max-w-3xl">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight mb-4">GST Appellate <br /><span className="text-brand-200">Tribunal</span></h1>
          <p className="text-xl text-brand-100 mb-4 font-medium">A new era in tax dispute resolution</p>
          <p className="text-brand-200 text-base lg:text-lg mb-10 max-w-xl leading-relaxed">Track notifications, plan pre-deposits, find the right bench and follow significant orders, all curated by our GSTAT practice.</p>
          <div className="flex flex-wrap gap-3 mb-16">
            <a href="/news-and-orders" className="flex items-center gap-2 px-5 py-3 bg-white/15 border border-white/30 rounded-xl text-white text-sm font-medium hover:bg-white/25">Latest developments <ArrowRight className="w-4 h-4" /></a>
            <a href="/pre-deposit-calculator" className="flex items-center gap-2 px-5 py-3 bg-white text-brand-800 rounded-xl text-sm font-semibold hover:bg-brand-50"><Calculator className="w-4 h-4" /> Pre-deposit calculator</a>
            <a href="/blog" className="flex items-center gap-2 px-5 py-3 bg-white/15 border border-white/30 rounded-xl text-white text-sm font-medium hover:bg-white/25"><BookOpen className="w-4 h-4" /> Articles</a>
          </div>
          <div className="flex flex-wrap gap-10">{[{v:'31',l:'State Benches'},{v:'14',l:'CKB Offices'},{v:'2025',l:'Procedure Rules'}].map(s => <div key={s.l}><div className="text-3xl font-extrabold">{s.v}</div><div className="text-brand-200 text-sm mt-0.5">{s.l}</div></div>)}</div>
        </div>
      </div>
    </section>
  )
}
