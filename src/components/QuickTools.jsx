import { Calculator, Clock, MapPin, ArrowRight } from 'lucide-react'
const tools = [
  { icon: Calculator, title: 'Pre-Deposit Calculator', desc: 'Calculate mandatory pre-deposit amounts for your GSTAT appeal', href: '/pre-deposit-calculator', color: 'bg-brand-50 text-brand-700' },
  { icon: Clock, title: 'Timeline Calculator', desc: 'Find your appeal filing deadlines under Section 112', href: '/timeline-calculator', color: 'bg-amber-50 text-amber-700' },
  { icon: MapPin, title: 'Jurisdiction Search', desc: 'Identify your GSTAT bench based on location', href: '/jurisdiction-search', color: 'bg-violet-50 text-violet-700' },
]
export default function QuickTools() {
  return (
    <section className="py-12 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8"><span className="text-xs font-semibold uppercase tracking-wider text-brand-600">Popular Tools</span><h2 className="text-2xl font-bold text-gray-900 mt-1">Quick Tools</h2><p className="text-gray-500 text-sm mt-1">Access our most popular calculators and search tools</p></div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">{tools.map((t) => { const Icon = t.icon; return (<a key={t.title} href={t.href} className="bg-white rounded-xl p-6 border border-gray-100 hover:shadow-lg hover:border-brand-200 transition-all group"><div className={`w-11 h-11 rounded-xl ${t.color} flex items-center justify-center mb-4`}><Icon className="w-5 h-5" /></div><h3 className="font-semibold text-gray-900 mb-1 group-hover:text-brand-700">{t.title}</h3><p className="text-gray-500 text-sm leading-relaxed mb-4">{t.desc}</p><span className="text-xs text-brand-600 font-semibold flex items-center gap-1">Use Tool <ArrowRight className="w-3 h-3" /></span></a>) })}</div>
      </div>
    </section>
  )
}
