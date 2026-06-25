import { useState } from 'react'
import { X, Zap } from 'lucide-react'
const updates = ['Snapshot of GSTAT E-Appeal filing process','GSTAT Advisory - Higher court exemption or correction of pre deposit amount','Court fees - GSTAT Advisory regarding online payment on portal','GSTAT extends ease of filing appeals procedure till 31 December 2026','Formation of Benches for hearing appeals - Categories and week days specified']
export default function NewsTicker() {
  const [visible, setVisible] = useState(true)
  if (!visible) return null
  const text = [...updates, ...updates].join('  •  ')
  return (
    <div className="bg-brand-700 text-white flex items-center overflow-hidden h-9">
      <div className="shrink-0 flex items-center gap-1.5 bg-brand-900 px-3 h-full text-xs font-semibold tracking-wider uppercase"><Zap className="w-3 h-3 text-brand-200" /><span>Latest</span></div>
      <div className="flex-1 overflow-hidden"><div className="whitespace-nowrap ticker-animation text-sm text-brand-100 inline-block">{text}</div></div>
      <button onClick={() => setVisible(false)} className="shrink-0 px-3 h-full hover:bg-brand-600 transition-colors"><X className="w-3.5 h-3.5" /></button>
    </div>
  )
}
