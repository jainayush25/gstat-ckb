import { ArrowRight } from 'lucide-react'
const timeline = [{year:'2017',text:'Section 109 of CGST Act constitutes GSTAT'},{year:'2023',text:'Finance Act, 2023 - Sections 149 & 150 substituted S109 & S110'},{year:'Jul 2024',text:'Constitution of Principal Bench and State Benches'},{year:'Apr 2025',text:'GSTAT (Procedure) Rules, 2025 notified'},{year:'Sep 2025',text:'Appeal filing opens'},{year:'Jun 2026',text:'Final deadline for all pending appeals'}]
export default function GSTATGuide() {
  return (
    <section className="py-12 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-10"><span className="text-xs font-semibold uppercase tracking-wider text-brand-600">Educational Resource</span><h2 className="text-2xl font-bold text-gray-900 mt-1">Understanding the GST Appellate Tribunal</h2></div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 border border-gray-100"><h3 className="text-lg font-semibold text-brand-700 mb-3">What is GSTAT?</h3><p className="text-gray-600 text-sm leading-relaxed mb-4">The GSTAT has been constituted under Section 109 of the CGST Act, 2017. It serves as the <strong>second level of appeal</strong> in the GST dispute resolution mechanism.</p><div className="bg-brand-50 rounded-lg p-4 border border-brand-100"><p className="text-xs font-semibold text-brand-700 mb-1">Key Development</p><p className="text-xs text-brand-600">The GSTAT (Procedure) Rules, 2025 were notified in April 2025.</p></div></div>
          <div className="bg-white rounded-xl p-6 border border-gray-100"><h3 className="text-lg font-semibold text-brand-700 mb-3">Jurisdiction & Powers</h3><div className="space-y-3"><div className="bg-gray-50 rounded-lg p-3"><p className="text-xs font-semibold text-gray-800 mb-1">Principal Bench (New Delhi)</p><p className="text-xs text-gray-500">Presided by President, Judicial Member, and two Technical Members.</p></div><div className="bg-gray-50 rounded-lg p-3"><p className="text-xs font-semibold text-gray-800 mb-1">State Benches</p><p className="text-xs text-gray-500">Two Judicial Members and two Technical Members. Handle all other appeals.</p></div></div></div>
        </div>
        <div className="bg-white rounded-xl p-6 border border-gray-100"><h3 className="text-lg font-semibold text-gray-900 mb-5">Important Dates</h3><div className="relative"><div className="absolute left-16 top-0 bottom-0 w-0.5 bg-brand-100" /><div className="space-y-4">{timeline.map((item, i) => (<div key={i} className="flex gap-4 items-start"><div className="w-14 text-right shrink-0"><span className="text-xs font-bold text-brand-600">{item.year}</span></div><div className="w-3 h-3 rounded-full bg-brand-500 shrink-0 mt-0.5 relative z-10" /><p className="text-sm text-gray-600">{item.text}</p></div>))}</div></div><div className="mt-6"><a href="/filing-timelines" className="text-sm text-brand-600 font-medium flex items-center gap-1">View Filing Timelines <ArrowRight className="w-4 h-4" /></a></div></div>
      </div>
    </section>
  )
}
