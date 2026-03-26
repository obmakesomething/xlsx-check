interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  className?: string;
}

const variants: Record<string, string> = {
  default: 'bg-surface-700 text-surface-200',
  success: 'bg-green-900/60 text-green-300',
  warning: 'bg-yellow-900/60 text-yellow-300',
  error: 'bg-red-900/60 text-red-300',
  info: 'bg-blue-900/60 text-blue-300',
};

export default function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
}
