interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  onClick?: () => void;
  hoverable?: boolean;
}

export default function Card({ children, className = '', title, subtitle, actions, onClick, hoverable }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-surface-700 bg-surface-800/80 backdrop-blur-sm ${hoverable ? 'cursor-pointer transition-all hover:border-primary-500/50 hover:shadow-lg hover:shadow-primary-500/5' : ''} ${className}`}
      onClick={onClick}
    >
      {(title || actions) && (
        <div className="flex items-center justify-between border-b border-surface-700 px-5 py-4">
          <div>
            {title && <h3 className="text-sm font-semibold text-surface-100">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs text-surface-400">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}
