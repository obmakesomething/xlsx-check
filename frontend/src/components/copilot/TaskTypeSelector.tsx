import type { TaskType } from '../../types/copilot';
import { TASK_TYPE_LABELS } from '../../utils/constants';

interface TaskTypeSelectorProps {
  value: TaskType | undefined;
  onChange: (type: TaskType | undefined) => void;
}

export default function TaskTypeSelector({ value, onChange }: TaskTypeSelectorProps) {
  const taskTypes = Object.entries(TASK_TYPE_LABELS) as [TaskType, string][];

  return (
    <div className="flex flex-wrap gap-1.5">
      <button
        onClick={() => onChange(undefined)}
        className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
          !value ? 'bg-primary-600 text-white' : 'bg-surface-700 text-surface-300 hover:bg-surface-600'
        }`}
      >
        자동 감지
      </button>
      {taskTypes.map(([type, label]) => (
        <button
          key={type}
          onClick={() => onChange(type)}
          className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
            value === type ? 'bg-primary-600 text-white' : 'bg-surface-700 text-surface-300 hover:bg-surface-600'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
