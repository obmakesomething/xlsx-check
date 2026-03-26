import { ExternalLink, Package, Clock } from 'lucide-react';
import type { Component } from '../../types/component';
import { formatCurrency, formatRelativeTime } from '../../utils/formatters';
import Badge from '../shared/Badge';

interface ComponentCardProps {
  component: Component;
  onClick?: () => void;
}

export default function ComponentCard({ component, onClick }: ComponentCardProps) {
  return (
    <div
      onClick={onClick}
      className="cursor-pointer rounded-xl border border-surface-700 bg-surface-800/80 p-4 transition-all hover:border-primary-500/50 hover:shadow-lg hover:shadow-primary-500/5"
    >
      <div className="mb-2 flex items-start justify-between">
        <div>
          <h3 className="text-sm font-semibold text-surface-100">{component.name}</h3>
          <p className="text-xs text-surface-400">{component.manufacturer} - {component.part_number}</p>
        </div>
        <Badge>{component.category}</Badge>
      </div>

      <p className="mb-3 text-xs text-surface-400 line-clamp-2">{component.description}</p>

      <div className="mb-3 grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg bg-surface-700/50 px-2.5 py-1.5">
          <span className="text-surface-500">단가</span>
          <div className="font-medium text-surface-200">{formatCurrency(component.unit_price)}</div>
        </div>
        <div className="rounded-lg bg-surface-700/50 px-2.5 py-1.5">
          <span className="text-surface-500">재고</span>
          <div className={`font-medium ${component.stock > 0 ? 'text-green-400' : 'text-red-400'}`}>
            {component.stock > 0 ? component.stock.toLocaleString() : '품절'}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-3 text-surface-400">
          <span className="flex items-center gap-1">
            <Package className="h-3.5 w-3.5" />
            {component.package_type}
          </span>
          {component.lcsc_number && (
            <a
              href={`https://www.lcsc.com/product-detail/${component.lcsc_number}.html`}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="flex items-center gap-1 text-primary-400 hover:text-primary-300"
            >
              {component.lcsc_number}
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
        <span className="flex items-center gap-1 text-surface-500">
          <Clock className="h-3 w-3" />
          사용 {component.usage_count}회
        </span>
      </div>

      {component.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {component.tags.slice(0, 4).map((tag) => (
            <span key={tag} className="rounded bg-surface-700 px-1.5 py-0.5 text-xs text-surface-400">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
