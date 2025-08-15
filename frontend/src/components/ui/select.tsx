import * as React from 'react'

type Option = { value: string; label: string }

export function Select({
  value, onChange, options, className=''
}: { value?: string; onChange?: (v:string)=>void; options: Option[]; className?: string }){
  return (
    <select
      value={value}
      onChange={(e)=>onChange && onChange(e.target.value)}
      className={`w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500 ${className}`}
    >
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  )
}
