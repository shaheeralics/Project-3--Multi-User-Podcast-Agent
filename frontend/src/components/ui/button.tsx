import * as React from 'react'

export function Button(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { className = '', ...rest } = props
  return (
    <button
      className={`px-4 py-2 rounded-2xl bg-brand-500 hover:bg-brand-400 active:scale-[0.99] transition text-white font-medium shadow-soft disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
      {...rest}
    />
  )
}
