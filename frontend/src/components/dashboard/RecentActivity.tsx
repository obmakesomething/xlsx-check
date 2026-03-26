import { FolderPlus, FileSpreadsheet, BarChart3, Cpu, Upload } from 'lucide-react';
import type { Activity } from '../../types/common';
import { formatRelativeTime } from '../../utils/formatters';
import Card from '../shared/Card';

interface RecentActivityProps {
  activities: Activity[];
}

const activityIcons: Record<string, React.ElementType> = {
  project_created: FolderPlus,
  bom_generated: FileSpreadsheet,
  analysis_completed: BarChart3,
  component_added: Cpu,
  file_uploaded: Upload,
};

const activityColors: Record<string, string> = {
  project_created: 'text-blue-400 bg-blue-400/10',
  bom_generated: 'text-emerald-400 bg-emerald-400/10',
  analysis_completed: 'text-purple-400 bg-purple-400/10',
  component_added: 'text-orange-400 bg-orange-400/10',
  file_uploaded: 'text-cyan-400 bg-cyan-400/10',
};

export default function RecentActivity({ activities }: RecentActivityProps) {
  return (
    <Card title="최근 활동">
      {activities.length === 0 ? (
        <p className="text-sm text-surface-500">아직 활동 기록이 없습니다.</p>
      ) : (
        <div className="space-y-3">
          {activities.map((activity) => {
            const Icon = activityIcons[activity.type] || FolderPlus;
            const color = activityColors[activity.type] || activityColors.project_created;
            return (
              <div key={activity.id} className="flex items-start gap-3">
                <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${color}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-surface-200">{activity.description}</p>
                  {activity.project_name && (
                    <p className="text-xs text-surface-500">{activity.project_name}</p>
                  )}
                </div>
                <span className="shrink-0 text-xs text-surface-500">{formatRelativeTime(activity.timestamp)}</span>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
