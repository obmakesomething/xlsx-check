import { useState } from 'react';
import { Edit3, Check, X, Search, ExternalLink } from 'lucide-react';
import type { BomItem } from '../../types/project';
import { formatCurrency } from '../../utils/formatters';
import Badge from '../shared/Badge';

interface BomTableProps {
  items: BomItem[];
  onUpdate?: (itemId: string, updates: Partial<BomItem>) => void;
  onSearchLCSC?: (query: string) => void;
}

export default function BomTable({ items, onUpdate, onSearchLCSC }: BomTableProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Partial<BomItem>>({});
  const [filter, setFilter] = useState('');

  const startEdit = (item: BomItem) => {
    setEditingId(item.id);
    setEditValues({ quantity: item.quantity, unit_price: item.unit_price, notes: item.notes });
  };

  const saveEdit = () => {
    if (editingId && onUpdate) {
      onUpdate(editingId, editValues);
    }
    setEditingId(null);
    setEditValues({});
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValues({});
  };

  const filtered = items.filter(
    (item) =>
      !filter ||
      item.component_name.toLowerCase().includes(filter.toLowerCase()) ||
      item.designator.toLowerCase().includes(filter.toLowerCase()) ||
      item.part_number.toLowerCase().includes(filter.toLowerCase()) ||
      item.lcsc_number.toLowerCase().includes(filter.toLowerCase())
  );

  const totalCost = items.reduce((sum, item) => sum + item.total_price, 0);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-surface-500" />
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="부품 검색..."
            className="rounded-lg border border-surface-600 bg-surface-800 py-2 pl-9 pr-3 text-sm text-surface-100 placeholder-surface-500 focus:border-primary-500 focus:outline-none"
          />
        </div>
        <div className="text-sm text-surface-300">
          총 원가: <span className="font-bold text-primary-400">{formatCurrency(totalCost)}</span>
          <span className="ml-2 text-surface-500">({items.length}개 항목)</span>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-surface-700">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-700 bg-surface-800/80 text-left text-xs text-surface-400">
              <th className="px-3 py-2.5">지정자</th>
              <th className="px-3 py-2.5">부품명</th>
              <th className="px-3 py-2.5">값</th>
              <th className="px-3 py-2.5">패키지</th>
              <th className="px-3 py-2.5">제조사</th>
              <th className="px-3 py-2.5">LCSC</th>
              <th className="px-3 py-2.5 text-right">수량</th>
              <th className="px-3 py-2.5 text-right">단가</th>
              <th className="px-3 py-2.5 text-right">소계</th>
              <th className="px-3 py-2.5">재고</th>
              <th className="px-3 py-2.5"></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => (
              <tr key={item.id} className="border-b border-surface-700/50 hover:bg-surface-800/50">
                <td className="px-3 py-2 text-surface-200 font-mono text-xs">{item.designator}</td>
                <td className="px-3 py-2 text-surface-200">{item.component_name}</td>
                <td className="px-3 py-2 text-surface-300">{item.value}</td>
                <td className="px-3 py-2 text-surface-400">{item.package_type}</td>
                <td className="px-3 py-2 text-surface-400">{item.manufacturer}</td>
                <td className="px-3 py-2">
                  {item.lcsc_number ? (
                    <button
                      onClick={() => onSearchLCSC?.(item.lcsc_number)}
                      className="flex items-center gap-1 text-primary-400 hover:text-primary-300"
                    >
                      {item.lcsc_number}
                      <ExternalLink className="h-3 w-3" />
                    </button>
                  ) : (
                    <span className="text-surface-500">-</span>
                  )}
                </td>
                <td className="px-3 py-2 text-right text-surface-200">
                  {editingId === item.id ? (
                    <input
                      type="number"
                      value={editValues.quantity ?? item.quantity}
                      onChange={(e) => setEditValues({ ...editValues, quantity: parseInt(e.target.value) })}
                      className="w-16 rounded border border-surface-600 bg-surface-700 px-2 py-0.5 text-right text-xs text-surface-100"
                    />
                  ) : (
                    item.quantity
                  )}
                </td>
                <td className="px-3 py-2 text-right text-surface-300">
                  {editingId === item.id ? (
                    <input
                      type="number"
                      step="0.001"
                      value={editValues.unit_price ?? item.unit_price}
                      onChange={(e) => setEditValues({ ...editValues, unit_price: parseFloat(e.target.value) })}
                      className="w-20 rounded border border-surface-600 bg-surface-700 px-2 py-0.5 text-right text-xs text-surface-100"
                    />
                  ) : (
                    formatCurrency(item.unit_price)
                  )}
                </td>
                <td className="px-3 py-2 text-right font-medium text-surface-200">{formatCurrency(item.total_price)}</td>
                <td className="px-3 py-2">
                  <Badge variant={item.in_stock ? 'success' : 'error'}>
                    {item.in_stock ? '있음' : '없음'}
                  </Badge>
                </td>
                <td className="px-3 py-2">
                  {editingId === item.id ? (
                    <div className="flex gap-1">
                      <button onClick={saveEdit} className="rounded p-1 text-green-400 hover:bg-surface-700">
                        <Check className="h-3.5 w-3.5" />
                      </button>
                      <button onClick={cancelEdit} className="rounded p-1 text-red-400 hover:bg-surface-700">
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ) : onUpdate ? (
                    <button onClick={() => startEdit(item)} className="rounded p-1 text-surface-400 hover:bg-surface-700 hover:text-surface-200">
                      <Edit3 className="h-3.5 w-3.5" />
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-surface-600 bg-surface-800/80">
              <td colSpan={8} className="px-3 py-2.5 text-right text-xs font-medium text-surface-300">합계</td>
              <td className="px-3 py-2.5 text-right font-bold text-primary-400">{formatCurrency(totalCost)}</td>
              <td colSpan={2}></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
