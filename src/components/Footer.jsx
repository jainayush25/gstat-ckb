import { useState } from 'react'
import { Mail, MapPin, Bell } from 'lucide-react'

const links = [
  { label: 'Understanding GSTAT Jurisdiction', href: '/gstat-jurisdiction' },
  { label: 'Procedural Requirements', href: '/procedural-requirements' },
  { label: 'Appeal Process Guidelines', href: '/appeal-process' },
  { label: 'Blog & Insights', href: '/blog' },
  { label: 'Contact Us', href: '/contact' },
]

export default function Footer() {
  const [email, setEmail] = useState('')
  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 bg-brand-600 rounded-lg flex items-center justify-center"><span className="text-white font-bold text-sm">CKB</span></div>
              <span className="font-semibold text-white">CKB Law</span>
            </div>
            <p className="text-sm text-gray-400 leading-relaxed mb-4">Full-service law firm with specialized expertise in GST and tax litigation across 14 cities in India.</p>
            <div className="flex items-center gap-2 text-sm text-gray-400"><MapPin className="w-4 h-4 text-brand-400 shrink-0" /><span>14 Cities across India</span></div>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">GSTAT Resources</h4>
            <ul className="space-y-2.5">{links.map(l => <li key={l.label}><a href={l.href} className="text-sm text-gray-400 hover:text-brand-300 transition-colors">{l.label}</a></li>)}</ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Stay Updated</h4>
            <p className="text-sm text-gray-400 mb-4">Get the latest on Indirect Tax law and GSTAT developments</p>
            <div className="flex gap-2 mb-5">
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Your email address" className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-500" />
              <button className="px-3 py-2 bg-brand-600 rounded-lg hover:bg-brand-700 transition-colors"><Bell className="w-4 h-4 text-white" /></button>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-400"><Mail className="w-4 h-4 text-brand-400 shrink-0" /><a href="mailto:gstat@ckb.com" className="hover:text-brand-300 transition-colors">gstat@ckb.com</a></div>
          </div>
        </div>
        <div className="border-t border-gray-800 mt-10 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-gray-500">
          <p>© 2025 CKB Attorneys. All rights reserved.</p>
          <p>gstat.ckb.com</p>
        </div>
      </div>
    </footer>
  )
}
