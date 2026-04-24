import { useState, useEffect, useRef } from 'react'

export default function InfoTip({ content, below = false }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    if (!open) return
    const close = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [open])

  return (
    <span className="relative inline-flex items-center" ref={ref}>
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); setOpen(v => !v) }}
        className="w-3.5 h-3.5 rounded-full bg-muted-foreground/20 text-muted-foreground text-[9px] font-bold flex items-center justify-center hover:bg-muted-foreground/30 transition-colors leading-none cursor-pointer"
        aria-label="More information"
      >?</button>
      {open && (
        <div className={`absolute z-50 ${below ? 'top-full mt-2' : 'bottom-full mb-2'} left-1/2 -translate-x-1/2 w-72 rounded-lg border bg-white text-gray-800 shadow-lg p-3 text-xs leading-relaxed whitespace-normal`}>
          {content}
        </div>
      )}
    </span>
  )
}
