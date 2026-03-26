import { InboxIcon } from 'lucide-react';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export default function EmptyState({ icon, title, description, action, className = '' }: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-16 text-center ${className}`}>
      <div className="mb-4 text-surface-500">
        {icon || <InboxIcon className="h-12 w-12" />}
      </div>
      <h3 className="text-lg font-medium text-surface-300">{title}</h3>
      {description && <p className="mt-2 max-w-md text-sm text-surface-500">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
