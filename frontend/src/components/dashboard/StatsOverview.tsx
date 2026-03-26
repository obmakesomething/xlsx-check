import { FolderOpen, Cpu, FileSpreadsheet, BarChart3 } from 'lucide-react';
import type { Stats } from '../../types/common';
import { formatNumber } from '../../utils/formatters';

interface StatsOverviewProps {
  stats: Stats;
}

const statItems = [
  { key: 'total_projects' as const, label: '전체 프로젝트', icon: FolderOpen, color: 'text-blue-400 bg-blue-400/10' },
  { key: 'total_components' as const, label: '사용 부품', icon: Cpu, color: 'text-emerald-400 bg-emerald-400/10' },
  { key: 'boms_generated' as const, label: '생성된 BoM', icon: FileSpreadsheet, color: 'text-orange-400 bg-orange-400/10' },
  { key: 'analyses_run' as const, label: '분석 실행', icon: BarChart3, color: 'text-purple-400 bg-purple-400/10' },
];

export default function StatsOverview({ stats }: StatsOverviewProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {statItems.map((item) => (
        <div key={item.key} className="rounded-xl border border-surface-700 bg-surface-800/80 p-5">
          <div className="flex items-center gap-3">
            <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${item.color}`}>
              <item.icon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs text-surface-400">{item.label}</p>
              <p className="text-2xl font-bold text-surface-100">{formatNumber(stats[item.key])}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
