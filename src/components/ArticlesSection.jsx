import { ArrowRight, Clock } from 'lucide-react'
const articles = [
  { title: 'GSTAT Jurisdiction Search: How to Determine the Correct Bench', date: 'Mar 18, 2026', readTime: '6 min', href: '/blog/gstat-jurisdiction', category: 'GSTAT Procedures' },
  { title: 'Understanding Pre-Deposit Requirements for Filing GSTAT Appeals', date: 'Mar 18, 2026', readTime: '4 min', href: '/blog/pre-deposit', category: 'GSTAT Procedures' },
  { title: 'Single Bench vs Division Bench: GSTAT Composition Guide 2026', date: 'Feb 3, 2026', readTime: '8 min', href: '/blog/bench-guide', category: 'GSTAT Procedures' },
]
export default function ArticlesSection() {
  return (
    <section className="py-12 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8"><div><span className="text-xs font-semibold uppercase tracking-wider text-brand-600">Articles</span><h2 className="text-2xl font-bold text-gray-900 mt-1">Articles & Insights</h2></div><a href="/blog" className="hidden sm:flex items-center gap-1 text-sm text-brand-600 font-medium">View all <ArrowRight className="w-4 h-4" /></a></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">{articles.map((a, i) => (<a key={i} href={a.href} className="group border border-gray-100 rounded-xl overflow-hidden hover:shadow-md transition-all"><div className="h-36 bg-gradient-to-br from-brand-600 to-brand-800 flex items-center justify-center p-6"><h3 className="text-white text-sm font-semibold text-center leading-snug">{a.title}</h3></div><div className="p-5"><span className="inline-block bg-brand-50 text-brand-700 text-xs font-medium px-2.5 py-0.5 rounded-full mb-3">{a.category}</span><div className="flex items-center justify-between text-xs text-gray-400 mt-3"><span>{a.date}</span><span className="flex items-center gap-1"><Clock className="w-3 h-3" />{a.readTime}</span></div></div></a>))}</div>
      </div>
    </section>
  )
}
