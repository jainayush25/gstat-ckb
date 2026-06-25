import { useState } from 'react'
import { Search, Menu, X, ChevronDown, LogIn } from 'lucide-react'

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [insightsOpen, setInsightsOpen] = useState(false)
  const [resourcesOpen, setResourcesOpen] = useState(false)
  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <a href="/" className="flex items-center gap-3 shrink-0">
            <div className="w-9 h-9 bg-brand-700 rounded-lg flex items-center justify-center"><span className="text-white font-bold text-sm tracking-wide">CKB</span></div>
            <span className="text-gray-900 font-semibold text-base hidden sm:block">CKB Law</span>
          </a>
          <div className="hidden md:flex items-center gap-1">
            <div className="relative" onMouseEnter={() => setInsightsOpen(true)} onMouseLeave={() => setInsightsOpen(false)}>
              <button className="flex items-center gap-1 px-3 py-2 text-sm text-gray-700 rounded-md hover:bg-gray-100">Insights <ChevronDown className="w-3.5 h-3.5" /></button>
              {insightsOpen && <div className="absolute top-full left-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-100 py-1 z-50"><a href="/news-and-orders" className="block px-4 py-2 text-sm text-gray-700 hover:bg-brand-50">Notifications</a><a href="/blog" className="block px-4 py-2 text-sm text-gray-700 hover:bg-brand-50">Articles</a></div>}
            </div>
            <div className="relative" onMouseEnter={() => setResourcesOpen(true)} onMouseLeave={() => setResourcesOpen(false)}>
              <button className="flex items-center gap-1 px-3 py-2 text-sm text-gray-700 rounded-md hover:bg-gray-100">Resources <ChevronDown className="w-3.5 h-3.5" /></button>
              {resourcesOpen && <div className="absolute top-full left-0 mt-1 w-52 bg-white rounded-lg shadow-lg border border-gray-100 py-1 z-50"><a href="/pre-deposit-calculator" className="block px-4 py-2 text-sm text-gray-700 hover:bg-brand-50">Pre-Deposit Calculator</a><a href="/timeline-calculator" className="block px-4 py-2 text-sm text-gray-700 hover:bg-brand-50">Timeline Calculator</a><a href="/jurisdiction-search" className="block px-4 py-2 text-sm text-gray-700 hover:bg-brand-50">Jurisdiction Search</a></div>}
            </div>
            <a href="/gstat-benches" className="px-3 py-2 text-sm text-gray-700 rounded-md hover:bg-gray-100">Benches</a>
            <a href="/faq" className="px-3 py-2 text-sm text-gray-700 rounded-md hover:bg-gray-100">FAQ</a>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setSearchOpen(!searchOpen)} className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 rounded-md hover:bg-gray-100"><Search className="w-4 h-4" /><span className="hidden sm:inline">Search</span></button>
            <a href="/meet-our-team" className="hidden md:inline-flex items-center px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700">Meet our team</a>
            <a href="/login" className="hidden md:flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 rounded-md hover:bg-gray-100"><LogIn className="w-4 h-4" /> Login</a>
            <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden p-2 text-gray-600 rounded-md hover:bg-gray-100">{menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}</button>
          </div>
        </div>
        {searchOpen && <div className="pb-3"><input autoFocus type="text" placeholder="Search updates, orders, articles..." className="w-full px-4 py-2.5 text-sm border border-brand-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-400" /></div>}
      </div>
      {menuOpen && <div className="md:hidden border-t border-gray-100 bg-white"><div className="px-4 py-3 space-y-1"><a href="/news-and-orders" className="block px-3 py-2 text-sm text-gray-700 rounded-md hover:bg-brand-50">Notifications</a><a href="/blog" className="block px-3 py-2 text-sm text-gray-700 rounded-md hover:bg-brand-50">Articles</a><a href="/gstat-benches" className="block px-3 py-2 text-sm text-gray-700 rounded-md hover:bg-brand-50">Benches</a><a href="/faq" className="block px-3 py-2 text-sm text-gray-700 rounded-md hover:bg-brand-50">FAQ</a><a href="/meet-our-team" className="block px-3 py-2 text-sm text-brand-700 font-medium rounded-md hover:bg-brand-50">Meet our team</a></div></div>}
    </nav>
  )
}
