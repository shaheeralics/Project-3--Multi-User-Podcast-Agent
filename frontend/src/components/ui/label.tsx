import * as React from 'react'
export function Label({children, className=''}){
  return <label className={`block text-sm text-slate-300 mb-1 ${className}`}>{children}</label>
}
