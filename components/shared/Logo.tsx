export function Logo({ className }: { className?: string }) {
  return (
    <div className={className ?? 'flex items-center gap-2'}>
      <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
        <rect width="32" height="32" rx="8" fill="url(#pulse-grad)" />
        <path d="M6 17h4l3-8 6 16 3-8h4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        <defs>
          <linearGradient id="pulse-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop stopColor="#5b8cff" />
            <stop offset="1" stopColor="#2fd47a" />
          </linearGradient>
        </defs>
      </svg>
      <span className="text-base font-semibold tracking-tight text-base-50">Pulse</span>
    </div>
  );
}
