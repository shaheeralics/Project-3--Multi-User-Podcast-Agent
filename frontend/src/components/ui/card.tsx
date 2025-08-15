import * as React from 'react'

export function Card({children, className=''}: {children: React.ReactNode, className?: string}){
  return <div className={`card ${className}`}>{children}</div>
}
export function CardHeader({children}:{children:React.ReactNode}){ return <div className="p-5 border-b border-slate-800">{children}</div>}
export function CardContent({children}:{children:React.ReactNode}){ return <div className="p-5">{children}</div>}
export function CardTitle({children}:{children:React.ReactNode}){ return <div className="text-lg font-semibold">{children}</div>}
