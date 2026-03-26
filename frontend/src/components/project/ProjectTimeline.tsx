import { Calendar, CheckCircle, Clock, AlertTriangle, Circle } from 'lucide-react';
import type { TimelineEvent } from '../../types/project';
import { formatDate } from '../../utils/formatters';
import Badge from '../shared/Badge';

interface ProjectTimelineProps {
  events: TimelineEvent[];
}

const statusConfig: Record<string, { icon: React.ElementType; color: string; badge: 'success' | 'info' | 'warning' | 'error' }> = {
  completed: { icon: CheckCircle, color: 'text-green-400', badge: 'success' },
  in_progress: { icon: Clock, color: 'text-blue-400', badge: 'info' },
  pending: { icon: Circle, color: 'text-surface-500', badge: 'default' as never },
  delayed: { icon: AlertTriangle, color: 'text-red-400', badge: 'error' },
};

const statusLabels: Record<string, string> = {
  completed: '완료',
  in_progress: '진행 중',
  pending: '대기',
  delayed: '지연',
};

export default function ProjectTimeline({ events }: ProjectTimelineProps) {
  if (events.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-surface-600 text-sm text-surface-500">
        타임라인이 아직 생성되지 않았습니다.
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {events.map((event, index) => {
        const config = statusConfig[event.status] || statusConfig.pending;
        const Icon = config.icon;
        const isLast = index === events.length - 1;

        return (
          <div key={event.id} className="flex gap-4">
            {/* Timeline line */}
            <div className="flex flex-col items-center">
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 ${
                event.status === 'completed'
                  ? 'border-green-500 bg-green-500/20'
                  : event.status === 'in_progress'
                  ? 'border-blue-500 bg-blue-500/20'
                  : event.status === 'delayed'
                  ? 'border-red-500 bg-red-500/20'
                  : 'border-surface-600 bg-surface-800'
              }`}>
                <Icon className={`h-4 w-4 ${config.color}`} />
              </div>
              {!isLast && <div className="w-0.5 flex-1 bg-surface-700" />}
            </div>

            {/* Content */}
            <div className={`flex-1 pb-6 ${isLast ? '' : ''}`}>
              <div className="rounded-lg border border-surface-700 bg-surface-800/50 p-4">
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-xs font-medium text-primary-400">{event.phase}</span>
                  <Badge variant={config.badge}>{statusLabels[event.status]}</Badge>
                </div>
                <h4 className="text-sm font-semibold text-surface-100">{event.title}</h4>
                <p className="mt-1 text-xs text-surface-400">{event.description}</p>
                <div className="mt-2 flex items-center gap-3 text-xs text-surface-500">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    {formatDate(event.start_date)} ~ {formatDate(event.end_date)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
