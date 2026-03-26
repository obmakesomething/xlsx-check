import { CheckCircle, Circle, AlertTriangle, MinusCircle, FileText } from 'lucide-react';
import type { CertificationItem } from '../../types/project';
import Badge from '../shared/Badge';

interface CertificationChecklistProps {
  items: CertificationItem[];
  onToggle?: (itemId: string, completed: boolean) => void;
}

const categoryLabels: Record<string, string> = {
  KC: 'KC 인증',
  EMC: '전자파 적합성',
  safety: '안전 인증',
  environmental: '환경 인증',
};

const categoryColors: Record<string, string> = {
  KC: 'border-l-blue-500',
  EMC: 'border-l-purple-500',
  safety: 'border-l-red-500',
  environmental: 'border-l-green-500',
};

export default function CertificationChecklist({ items, onToggle }: CertificationChecklistProps) {
  if (items.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-surface-600 text-sm text-surface-500">
        인증 체크리스트가 아직 생성되지 않았습니다.
      </div>
    );
  }

  const grouped = items.reduce<Record<string, CertificationItem[]>>((acc, item) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {});

  const completedCount = items.filter((i) => i.completed).length;
  const requiredCount = items.filter((i) => i.required).length;
  const completedRequired = items.filter((i) => i.required && i.completed).length;

  return (
    <div className="space-y-6">
      {/* Progress */}
      <div className="rounded-xl border border-surface-700 bg-surface-800/80 p-5">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm font-medium text-surface-200">인증 진행률</span>
          <span className="text-sm text-surface-400">{completedCount}/{items.length} 완료</span>
        </div>
        <div className="h-3 rounded-full bg-surface-700">
          <div
            className="h-full rounded-full bg-primary-500 transition-all"
            style={{ width: `${items.length > 0 ? (completedCount / items.length) * 100 : 0}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-surface-400">
          필수 항목: {completedRequired}/{requiredCount} 완료
        </p>
      </div>

      {/* Grouped Checklist */}
      {Object.entries(grouped).map(([category, categoryItems]) => (
        <div key={category}>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-surface-200">
            {categoryLabels[category] || category}
            <Badge>{categoryItems.filter((i) => i.completed).length}/{categoryItems.length}</Badge>
          </h3>
          <div className="space-y-2">
            {categoryItems.map((item) => (
              <div
                key={item.id}
                className={`rounded-lg border-l-4 border border-surface-700 bg-surface-800/50 p-4 ${categoryColors[category] || 'border-l-surface-500'}`}
              >
                <div className="flex items-start gap-3">
                  <button
                    onClick={() => onToggle?.(item.id, !item.completed)}
                    className="mt-0.5 shrink-0"
                    disabled={!onToggle}
                  >
                    {item.completed ? (
                      <CheckCircle className="h-5 w-5 text-green-400" />
                    ) : item.required ? (
                      <Circle className="h-5 w-5 text-yellow-400" />
                    ) : (
                      <MinusCircle className="h-5 w-5 text-surface-500" />
                    )}
                  </button>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-medium ${item.completed ? 'text-surface-400 line-through' : 'text-surface-200'}`}>
                        {item.name}
                      </span>
                      {item.required && <Badge variant="warning">필수</Badge>}
                    </div>
                    <p className="mt-1 text-xs text-surface-400">{item.description}</p>
                    {item.notes && <p className="mt-1 text-xs text-surface-500">{item.notes}</p>}
                    {item.documents.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {item.documents.map((doc, i) => (
                          <span key={i} className="inline-flex items-center gap-1 rounded bg-surface-700 px-2 py-0.5 text-xs text-surface-400">
                            <FileText className="h-3 w-3" />
                            {doc}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
