import { useNavigate } from 'react-router-dom';
import { FileSpreadsheet, BarChart3, Clock } from 'lucide-react';
import type { Project } from '../../types/project';
import { STATUS_LABELS, STATUS_COLORS } from '../../utils/constants';
import { formatRelativeTime } from '../../utils/formatters';
import Badge from '../shared/Badge';

interface ProjectCardProps {
  project: Project;
}

export default function ProjectCard({ project }: ProjectCardProps) {
  const navigate = useNavigate();

  return (
    <div
      onClick={() => navigate(`/projects/${project.id}`)}
      className="cursor-pointer rounded-xl border border-surface-700 bg-surface-800/80 p-5 transition-all hover:border-primary-500/50 hover:shadow-lg hover:shadow-primary-500/5"
    >
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h3 className="text-sm font-semibold text-surface-100">{project.name}</h3>
          <p className="mt-0.5 text-xs text-surface-400 line-clamp-2">{project.description}</p>
        </div>
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[project.status] || STATUS_COLORS.draft}`}>
          {STATUS_LABELS[project.status] || project.status}
        </span>
      </div>

      <div className="mb-3 flex flex-wrap gap-1.5">
        {project.tags.map((tag) => (
          <Badge key={tag}>{tag}</Badge>
        ))}
      </div>

      <div className="flex items-center gap-4 text-xs text-surface-400">
        <span className="flex items-center gap-1">
          <FileSpreadsheet className="h-3.5 w-3.5" />
          BoM {project.bom_count}
        </span>
        <span className="flex items-center gap-1">
          <BarChart3 className="h-3.5 w-3.5" />
          분석 {project.analysis_count}
        </span>
        <span className="ml-auto flex items-center gap-1">
          <Clock className="h-3.5 w-3.5" />
          {formatRelativeTime(project.updated_at)}
        </span>
      </div>
    </div>
  );
}
