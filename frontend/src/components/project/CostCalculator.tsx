import { DollarSign, TrendingDown, Package } from 'lucide-react';
import type { CostBreakdown } from '../../types/project';
import { formatCurrency } from '../../utils/formatters';
import Card from '../shared/Card';

interface CostCalculatorProps {
  cost: CostBreakdown | null;
}

export default function CostCalculator({ cost }: CostCalculatorProps) {
  if (!cost) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-surface-600 text-sm text-surface-500">
        원가 분석 데이터가 아직 없습니다.
      </div>
    );
  }

  const costItems = [
    { label: 'BoM 원가', value: cost.bom_cost, color: 'text-blue-400' },
    { label: 'PCB 비용', value: cost.pcb_cost, color: 'text-emerald-400' },
    { label: '조립 비용', value: cost.assembly_cost, color: 'text-orange-400' },
    { label: '외함 비용', value: cost.enclosure_cost, color: 'text-purple-400' },
    { label: '시험 비용', value: cost.testing_cost, color: 'text-cyan-400' },
    { label: '인증 비용', value: cost.certification_cost, color: 'text-pink-400' },
  ];

  const maxCostValue = Math.max(...costItems.map((c) => c.value));

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-400/10 text-blue-400">
              <DollarSign className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs text-surface-400">총 단가</p>
              <p className="text-xl font-bold text-surface-100">{formatCurrency(cost.total_unit_cost)}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-400/10 text-green-400">
              <TrendingDown className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs text-surface-400">판매가 (마진 {cost.margin_percent}%)</p>
              <p className="text-xl font-bold text-surface-100">{formatCurrency(cost.selling_price)}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-400/10 text-purple-400">
              <Package className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs text-surface-400">BoM 원가 비중</p>
              <p className="text-xl font-bold text-surface-100">{cost.total_unit_cost > 0 ? Math.round((cost.bom_cost / cost.total_unit_cost) * 100) : 0}%</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Cost Breakdown */}
      <Card title="비용 항목별 분석">
        <div className="space-y-3">
          {costItems.map((item) => (
            <div key={item.label} className="flex items-center gap-3">
              <span className="w-24 shrink-0 text-sm text-surface-400">{item.label}</span>
              <div className="flex-1">
                <div className="h-6 rounded-lg bg-surface-700">
                  <div
                    className="flex h-full items-center rounded-lg bg-primary-600/30 pl-2 text-xs font-medium text-surface-200"
                    style={{ width: maxCostValue > 0 ? `${Math.max((item.value / maxCostValue) * 100, 8)}%` : '8%' }}
                  >
                    {formatCurrency(item.value)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Quantity Breaks */}
      {cost.quantities.length > 0 && (
        <Card title="수량별 단가">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-700 text-left text-xs text-surface-400">
                  <th className="pb-2 pr-4">수량</th>
                  <th className="pb-2 pr-4 text-right">단가</th>
                  <th className="pb-2 text-right">총액</th>
                </tr>
              </thead>
              <tbody>
                {cost.quantities.map((q) => (
                  <tr key={q.qty} className="border-b border-surface-700/50">
                    <td className="py-2 pr-4 text-surface-200">{q.qty.toLocaleString()}개</td>
                    <td className="py-2 pr-4 text-right text-surface-300">{formatCurrency(q.unit_cost)}</td>
                    <td className="py-2 text-right font-medium text-surface-200">{formatCurrency(q.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
