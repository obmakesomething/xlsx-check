import { MessageSquare, Bell } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';

interface HeaderProps {
  title?: string;
}

export default function Header({ title }: HeaderProps) {
  const { toggleCopilot } = useUIStore();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-surface-700 bg-surface-900/80 px-6 backdrop-blur-md">
      <div>
        {title && <h1 className="text-lg font-semibold text-surface-100">{title}</h1>}
      </div>
      <div className="flex items-center gap-2">
        <button className="relative rounded-lg p-2 text-surface-400 hover:bg-surface-800 hover:text-surface-200">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-primary-500" />
        </button>
        <button
          onClick={toggleCopilot}
          className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
        >
          <MessageSquare className="h-4 w-4" />
          <span>AI 코파일럿</span>
        </button>
      </div>
    </header>
  );
}
