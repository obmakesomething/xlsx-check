import { BookOpen, Tag, Clock } from 'lucide-react';
import type { KnowledgeEntry } from '../../types/copilot';
import { formatRelativeTime } from '../../utils/formatters';
import Badge from '../shared/Badge';

interface KnowledgeCardProps {
  entry: KnowledgeEntry;
  onClick?: () => void;
}

const categoryColors: Record<string, string> = {
  design: 'bg-blue-900/30 text-blue-300',
  debugging: 'bg-red-900/30 text-red-300',
  certification: 'bg-yellow-900/30 text-yellow-300',
  component: 'bg-emerald-900/30 text-emerald-300',
  manufacturing: 'bg-purple-900/30 text-purple-300',
  experience: 'bg-orange-900/30 text-orange-300',
};

export default function KnowledgeCard({ entry, onClick }: KnowledgeCardProps) {
  return (
    <div
      onClick={onClick}
      className="cursor-pointer rounded-xl border border-surface-700 bg-surface-800/80 p-5 transition-all hover:border-primary-500/50 hover:shadow-lg"
    >
      <div className="mb-2 flex items-start justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-primary-400" />
          <h3 className="text-sm font-semibold text-surface-100">{entry.title}</h3>
        </div>
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${categoryColors[entry.category] || 'bg-surface-700 text-surface-300'}`}>
          {entry.category}
        </span>
      </div>

      <p className="mb-3 text-xs text-surface-400 line-clamp-3 leading-relaxed">{entry.content}</p>

      <div className="flex items-center justify-between">
        <div className="flex flex-wrap gap-1">
          {entry.tags.slice(0, 4).map((tag) => (
            <span key={tag} className="inline-flex items-center gap-0.5 rounded bg-surface-700 px-1.5 py-0.5 text-xs text-surface-400">
              <Tag className="h-2.5 w-2.5" />
              {tag}
            </span>
          ))}
        </div>
        <span className="flex items-center gap-1 text-xs text-surface-500">
          <Clock className="h-3 w-3" />
          {formatRelativeTime(entry.created_at)}
        </span>
      </div>

      <div className="mt-2 text-xs text-surface-500">
        출처: {entry.source}
      </div>
    </div>
  );
}
