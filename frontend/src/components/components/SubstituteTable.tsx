import { ArrowRight, ExternalLink } from 'lucide-react';
import type { SubstitutePart } from '../../types/component';
import { formatCurrency } from '../../utils/formatters';
import Badge from '../shared/Badge';

interface SubstituteTableProps {
  substitutes: SubstitutePart[];
  originalPartNumber?: string;
}

export default function SubstituteTable({ substitutes, originalPartNumber }: SubstituteTableProps) {
  if (substitutes.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-surface-600 p-6 text-center text-sm text-surface-500">
        대체 부품이 없습니다.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-surface-700">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-surface-700 bg-surface-800/80 text-left text-xs text-surface-400">
            <th className="px-3 py-2.5">부품번호</th>
            <th className="px-3 py-2.5">제조사</th>
            <th className="px-3 py-2.5">LCSC</th>
            <th className="px-3 py-2.5 text-center">호환성</th>
            <th className="px-3 py-2.5 text-right">단가</th>
            <th className="px-3 py-2.5 text-right">가격차이</th>
            <th className="px-3 py-2.5 text-right">재고</th>
            <th className="px-3 py-2.5">비고</th>
          </tr>
        </thead>
        <tbody>
          {originalPartNumber && (
            <tr className="border-b border-surface-700/50 bg-primary-900/10">
              <td className="px-3 py-2 font-medium text-primary-300">{originalPartNumber}</td>
              <td colSpan={7} className="px-3 py-2 text-xs text-primary-400">
                <ArrowRight className="inline h-3 w-3 mr-1" />
                원본 부품
              </td>
            </tr>
          )}
          {substitutes.map((sub) => (
            <tr key={sub.id} className="border-b border-surface-700/50 hover:bg-surface-800/50">
              <td className="px-3 py-2 font-medium text-surface-200">{sub.part_number}</td>
              <td className="px-3 py-2 text-surface-300">{sub.manufacturer}</td>
              <td className="px-3 py-2">
                {sub.lcsc_number ? (
                  <a
                    href={`https://www.lcsc.com/product-detail/${sub.lcsc_number}.html`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-primary-400 hover:text-primary-300"
                  >
                    {sub.lcsc_number}
                    <ExternalLink className="h-3 w-3" />
                  </a>
                ) : '-'}
              </td>
              <td className="px-3 py-2 text-center">
                <Badge variant={sub.compatibility >= 90 ? 'success' : sub.compatibility >= 70 ? 'warning' : 'error'}>
                  {sub.compatibility}%
                </Badge>
              </td>
              <td className="px-3 py-2 text-right text-surface-300">{formatCurrency(sub.unit_price)}</td>
              <td className="px-3 py-2 text-right">
                <span className={sub.price_diff < 0 ? 'text-green-400' : sub.price_diff > 0 ? 'text-red-400' : 'text-surface-400'}>
                  {sub.price_diff > 0 ? '+' : ''}{formatCurrency(sub.price_diff)}
                </span>
              </td>
              <td className="px-3 py-2 text-right">
                <span className={sub.stock > 0 ? 'text-green-400' : 'text-red-400'}>
                  {sub.stock > 0 ? sub.stock.toLocaleString() : '품절'}
                </span>
              </td>
              <td className="px-3 py-2 text-xs text-surface-400 max-w-[200px] truncate">{sub.notes}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
