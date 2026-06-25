import { useState } from 'react'
import { FileText, ChevronLeft, ChevronRight, Search, ArrowRight } from 'lucide-react'
const items = [
  { date: '19 Jun 2026', title: 'Snapshot of GSTAT E-Appeal filing process', excerpt: 'A snapshot for the entire appeal filing process for detailed understanding and seamless filing.' },
  { date: '15 Jun 2026', title: 'GSTAT Advisory - Higher court exemption or correction of pre deposit amount', excerpt: 'This advisory explains how to review and proceed when the pre-deposit amount is auto-populated from the GSTN portal.' },
  { date: '15 Jun 2026', title: 'Court fees - GSTAT Advisory regarding online payment on portal', excerpt: 'Taxpayers informed that where online payment of court fees has been made but payment status is not reflected.' },
  { date: '14 May 2026', title: 'GSTAT extends ease of filing appeals procedure till 31 December 2026', excerpt: 'GSTAT extends ease of filling appeal submission till 31 December 2026.' },
  { date: '07 May 2026', title: 'GSTAT Principal Bench also empowered to hear appeals as the National Appellate Authority', excerpt: 'GSTAT Principal Bench empowered to hear appeals as the National Appellate Authority.' },
]
export default function WhatsNew() {
  const [start, setStart] = useState(0)
  const visible = items.slice(start, start + 3)
  return (
    <section className="py-12 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div><div className="flex items-center gap-2 mb-1"><span className="w-1.5 h-1.5 bg-brand-500 rounded-full inline-block" /><span className="text-xs font-semibold uppercase tracking-wider text-brand-600">Latest developments</span></div><h2 className="text-2xl font-bold text-gray-900">What's New in GSTAT</h2><p className="text-gray-500 text-sm mt-1">The most recent notifications, circulars and updates.</p></div>
          <div className="flex items-center gap-3"><div className="relative"><Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" /><input type="text" placeholder="Search..." className="pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg w-64 focus:outline-none focus:ring-2 focus:ring-brand-300" /></div><a href="/news-and-orders" className="flex items-center gap-1 text-sm text-brand-600 font-medium whitespace-nowrap">View all <ArrowRight className="w-3.5 h-3.5" /></a></div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">{visible.map((item, i) => (<div key={i} className="border border-gray-100 rounded-xl p-5 hover:shadow-md hover:border-brand-200 transition-all cursor-pointer group"><div className="flex items-start justify-between mb-3"><span className="text-xs text-gray-400">{item.date}</span><FileText className="w-4 h-4 text-brand-400" /></div><h3 className="text-sm font-semibold text-gray-900 mb-2 leading-snug group-hover:text-brand-700">{item.title}</h3><p className="text-xs text-gray-500 leading-relaxed mb-4 line-clamp-3">{item.excerpt}</p><button className="text-xs text-brand-600 font-medium flex items-center gap-1">Open PDF <ArrowRight className="w-3 h-3" /></button></div>))}</div>
        <div className="flex justify-center gap-2 mt-6"><button onClick={() => setStart(Math.max(0, start - 1))} disabled={start === 0} className="p-2 rounded-full border border-gray-200 disabled:opacity-30 hover:bg-brand-50"><ChevronLeft className="w-4 h-4 text-gray-600" /></button><button onClick={() => setStart(Math.min(items.length - 3, start + 1))} disabled={start >= items.length - 3} className="p-2 rounded-full border border-gray-200 disabled:opacity-30 hover:bg-brand-50"><ChevronRight className="w-4 h-4 text-gray-600" /></button></div>
      </div>
    </section>
  )
}
