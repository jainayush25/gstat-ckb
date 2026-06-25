import { Download, Eye, FileText } from 'lucide-react'
const resources = [
  { title: 'GSTAT Procedure Rules 2025', type: 'Procedure Rules', desc: 'Complete procedural rules for GST Appellate Tribunal proceedings' },
  { title: 'GSTAT User Advisory', type: 'Guide', desc: 'Official user advisory and guidelines for GSTAT e-filing' },
  { title: 'GSTAT Cases Category', type: 'Guide', desc: 'Classification and categorization of GSTAT cases' },
  { title: 'GST APL-05 - Appeal to GSTAT', type: 'Form', desc: 'Main appeal form under Section 112' },
  { title: 'GST APL-06 - Cross-Objections', type: 'Form', desc: 'Form for filing cross-objections within 45 days' },
  { title: 'GST APL-07 - Condonation of Delay', type: 'Form', desc: 'Application for condonation of delay under Section 112(3)' },
]
const typeColors = { 'Procedure Rules': 'bg-brand-50 text-brand-700', 'Guide': 'bg-amber-50 text-amber-700', 'Form': 'bg-violet-50 text-violet-700' }
export default function ResourcesSection() {
  return (
    <section className="py-12 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8"><h2 className="text-2xl font-bold text-gray-900">Downloadable Resources</h2><p className="text-gray-500 text-sm mt-1">Essential forms, templates, and guides for GSTAT appeals</p></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">{resources.map((r, i) => (<div key={i} className="border border-gray-100 rounded-xl p-5 hover:shadow-md hover:border-brand-100 transition-all"><div className="flex items-start justify-between mb-3"><div className="w-9 h-9 bg-gray-50 rounded-lg flex items-center justify-center"><FileText className="w-4 h-4 text-brand-600" /></div><span className={`text-xs font-medium px-2 py-0.5 rounded-full ${typeColors[r.type] || 'bg-gray-50 text-gray-600'}`}>{r.type}</span></div><h3 className="font-semibold text-gray-900 text-sm mb-1.5">{r.title}</h3><p className="text-xs text-gray-500 mb-4 leading-relaxed line-clamp-2">{r.desc}</p><p className="text-xs text-gray-400 mb-3">PDF Document</p><div className="flex gap-2"><button className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 border border-gray-200 rounded-lg text-xs font-medium text-gray-600 hover:bg-gray-50"><Eye className="w-3 h-3" /> View</button><button className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 bg-brand-600 text-white rounded-lg text-xs font-medium hover:bg-brand-700"><Download className="w-3 h-3" /> Download</button></div></div>))}</div>
        <p className="text-xs text-gray-400 text-center mt-6"><strong>Note:</strong> All resources are for reference only. Always verify with official GSTAT website.</p>
      </div>
    </section>
  )
}
