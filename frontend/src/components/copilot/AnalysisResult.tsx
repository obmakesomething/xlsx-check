import { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Star,
  Zap,
  Shield,
} from 'lucide-react';
import type { CopilotResponse, TopologyOption, NormalizedBomItem, RiskItem, CertCheckItem } from '../../types/copilot';
import { SEVERITY_COLORS } from '../../utils/constants';
import { formatCurrency } from '../../utils/formatters';
import Badge from '../shared/Badge';

interface AnalysisResultProps {
  response: CopilotResponse;
}

function CollapsibleSection({ title, children, defaultOpen = false }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-lg border border-surface-700 bg-surface-800/50">
      <button onClick={() => setOpen(!open)} className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs font-medium text-surface-300 hover:text-surface-100">
        {open ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        {title}
      </button>
      {open && <div className="border-t border-surface-700 px-3 py-2">{children}</div>}
    </div>
  );
}

function TopologyCard({ option }: { option: TopologyOption }) {
  return (
    <div className={`rounded-lg border p-3 ${option.recommended ? 'border-primary-500/50 bg-primary-900/20' : 'border-surface-700 bg-surface-800/50'}`}>
      <div className="mb-2 flex items-center gap-2">
        <Zap className="h-4 w-4 text-primary-400" />
        <span className="text-sm font-medium text-surface-100">{option.name}</span>
        {option.recommended && <Badge variant="success">추천</Badge>}
      </div>
      <p className="mb-2 text-xs text-surface-400">{option.description}</p>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div><span className="text-surface-500">효율:</span> <span className="text-surface-200">{option.efficiency}</span></div>
        <div><span className="text-surface-500">비용:</span> <span className="text-surface-200">{option.cost_level}</span></div>
        <div><span className="text-surface-500">복잡도:</span> <span className="text-surface-200">{option.complexity}</span></div>
      </div>
      <div className="mt-2 flex gap-4 text-xs">
        <div>
          <span className="text-green-400">장점:</span>
          <ul className="mt-0.5 list-inside list-disc text-surface-400">
            {option.pros.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        </div>
        <div>
          <span className="text-red-400">단점:</span>
          <ul className="mt-0.5 list-inside list-disc text-surface-400">
            {option.cons.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </div>
      </div>
      {option.key_components.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {option.key_components.map((c, i) => (
            <span key={i} className="rounded bg-surface-700 px-1.5 py-0.5 text-xs text-surface-300">{c}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function BomNormalizeView({ items }: { items: NormalizedBomItem[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-surface-700 text-left text-surface-400">
            <th className="pb-2 pr-3">지정자</th>
            <th className="pb-2 pr-3">부품명</th>
            <th className="pb-2 pr-3">값</th>
            <th className="pb-2 pr-3">패키지</th>
            <th className="pb-2 pr-3">LCSC</th>
            <th className="pb-2 pr-3">단가</th>
            <th className="pb-2">신뢰도</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, i) => (
            <tr key={i} className="border-b border-surface-700/50">
              <td className="py-1.5 pr-3 text-surface-200">{item.designator}</td>
              <td className="py-1.5 pr-3 text-surface-200">{item.component_name}</td>
              <td className="py-1.5 pr-3 text-surface-300">{item.value}</td>
              <td className="py-1.5 pr-3 text-surface-300">{item.package_type}</td>
              <td className="py-1.5 pr-3 text-primary-400">{item.lcsc_number}</td>
              <td className="py-1.5 pr-3 text-surface-300">{formatCurrency(item.unit_price)}</td>
              <td className="py-1.5">
                <div className="flex items-center gap-1">
                  <div className="h-1.5 w-12 rounded-full bg-surface-700">
                    <div className="h-full rounded-full bg-primary-500" style={{ width: `${item.confidence * 100}%` }} />
                  </div>
                  <span className="text-surface-400">{Math.round(item.confidence * 100)}%</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RiskCard({ risk }: { risk: RiskItem }) {
  const colors = SEVERITY_COLORS[risk.severity] || SEVERITY_COLORS.low;
  const icons: Record<string, React.ReactNode> = {
    low: <Info className="h-4 w-4" />,
    medium: <AlertTriangle className="h-4 w-4" />,
    high: <AlertTriangle className="h-4 w-4" />,
    critical: <XCircle className="h-4 w-4" />,
  };

  return (
    <div className={`rounded-lg border p-3 ${colors}`}>
      <div className="mb-1 flex items-center gap-2">
        {icons[risk.severity]}
        <span className="text-sm font-medium">{risk.title}</span>
        <Badge>{risk.category}</Badge>
      </div>
      <p className="mb-2 text-xs opacity-80">{risk.description}</p>
      <p className="text-xs"><span className="font-medium">권장사항:</span> {risk.recommendation}</p>
    </div>
  );
}

function CertCheckView({ items }: { items: CertCheckItem[] }) {
  const statusIcon = (status: string) => {
    switch (status) {
      case 'pass': return <CheckCircle className="h-4 w-4 text-green-400" />;
      case 'fail': return <XCircle className="h-4 w-4 text-red-400" />;
      case 'needs_review': return <AlertTriangle className="h-4 w-4 text-yellow-400" />;
      default: return <Info className="h-4 w-4 text-surface-400" />;
    }
  };

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div key={item.id} className="flex items-start gap-2 rounded-lg border border-surface-700 p-2.5">
          {statusIcon(item.status)}
          <div className="flex-1 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-medium text-surface-200">{item.standard}</span>
              <Badge variant={item.status === 'pass' ? 'success' : item.status === 'fail' ? 'error' : 'warning'}>
                {item.status === 'pass' ? '통과' : item.status === 'fail' ? '불합격' : '검토 필요'}
              </Badge>
            </div>
            <p className="mt-0.5 text-surface-400">{item.requirement}</p>
            {item.notes && <p className="mt-1 text-surface-500">{item.notes}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AnalysisResult({ response }: AnalysisResultProps) {
  const { data, evidence, inference, warnings, suggestions } = response;

  return (
    <div className="space-y-3">
      {/* Design Draft - Topology Options */}
      {data.topology_options && data.topology_options.length > 0 && (
        <CollapsibleSection title={`토폴로지 옵션 (${data.topology_options.length})`} defaultOpen>
          <div className="space-y-2">
            {data.topology_options.map((opt, i) => <TopologyCard key={i} option={opt} />)}
          </div>
          {data.recommended_topology && (
            <div className="mt-2 flex items-center gap-2 text-xs text-primary-400">
              <Star className="h-3.5 w-3.5" />
              추천 토폴로지: {data.recommended_topology}
            </div>
          )}
        </CollapsibleSection>
      )}

      {/* Circuit Block Suggestions */}
      {data.circuit_blocks && data.circuit_blocks.length > 0 && (
        <CollapsibleSection title={`회로 블록 (${data.circuit_blocks.length})`}>
          <div className="space-y-2">
            {data.circuit_blocks.map((block, i) => (
              <div key={i} className="rounded-lg border border-surface-700 p-2.5">
                <div className="flex items-center gap-2">
                  <Shield className="h-3.5 w-3.5 text-primary-400" />
                  <span className="text-xs font-medium text-surface-200">{block.name}</span>
                  <Badge>{block.type}</Badge>
                </div>
                <p className="mt-1 text-xs text-surface-400">{block.description}</p>
                {block.recommended_components.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {block.recommended_components.map((c, j) => (
                      <span key={j} className="rounded bg-surface-700 px-1.5 py-0.5 text-xs text-surface-300">{c}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* BOM Normalize */}
      {data.normalized_bom && data.normalized_bom.length > 0 && (
        <CollapsibleSection title={`정규화된 BoM (${data.normalized_bom.length}개 항목)`} defaultOpen>
          <BomNormalizeView items={data.normalized_bom} />
          {data.unresolved_items && data.unresolved_items.length > 0 && (
            <div className="mt-2 rounded-lg bg-yellow-900/20 p-2 text-xs text-yellow-300">
              <span className="font-medium">미해결 항목:</span> {data.unresolved_items.join(', ')}
            </div>
          )}
        </CollapsibleSection>
      )}

      {/* Substitutes */}
      {data.substitutes && data.substitutes.length > 0 && (
        <CollapsibleSection title={`대체 부품 (${data.substitutes.length})`} defaultOpen>
          <div className="space-y-2">
            {data.substitutes.map((sub, i) => (
              <div key={i} className="rounded-lg border border-surface-700 p-2.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-surface-200">{sub.original_part} &rarr; {sub.substitute_part}</span>
                  <Badge variant={sub.compatibility >= 0.9 ? 'success' : sub.compatibility >= 0.7 ? 'warning' : 'error'}>
                    호환성 {Math.round(sub.compatibility * 100)}%
                  </Badge>
                </div>
                <p className="mt-1 text-surface-400">{sub.manufacturer} | 가격 차이: {sub.price_diff_percent > 0 ? '+' : ''}{sub.price_diff_percent}%</p>
                <p className="mt-1 text-surface-500">{sub.verification_notes}</p>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* Review Risks */}
      {data.risk_items && data.risk_items.length > 0 && (
        <CollapsibleSection title={`리스크 항목 (${data.risk_items.length})`} defaultOpen>
          {data.overall_score !== undefined && (
            <div className="mb-2 flex items-center gap-2 text-xs text-surface-300">
              전체 점수: <span className="text-lg font-bold text-primary-400">{data.overall_score}</span>/100
            </div>
          )}
          <div className="space-y-2">
            {data.risk_items.map((risk) => <RiskCard key={risk.id} risk={risk} />)}
          </div>
        </CollapsibleSection>
      )}

      {/* Certification Check */}
      {data.checklist && data.checklist.length > 0 && (
        <CollapsibleSection title={`인증 체크리스트 (${data.checklist.length})`} defaultOpen>
          <CertCheckView items={data.checklist} />
          {data.estimated_timeline && (
            <p className="mt-2 text-xs text-surface-400">예상 기간: {data.estimated_timeline}</p>
          )}
        </CollapsibleSection>
      )}

      {/* Cost Estimate */}
      {data.cost_breakdown && (
        <CollapsibleSection title="원가 분석" defaultOpen>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-lg bg-surface-700/50 p-2">
              <span className="text-surface-400">BoM 총계</span>
              <div className="text-lg font-bold text-surface-100">{formatCurrency(data.cost_breakdown.bom_total)}</div>
            </div>
            <div className="rounded-lg bg-surface-700/50 p-2">
              <span className="text-surface-400">PCB</span>
              <div className="text-lg font-bold text-surface-100">{formatCurrency(data.cost_breakdown.pcb_cost)}</div>
            </div>
            <div className="rounded-lg bg-surface-700/50 p-2">
              <span className="text-surface-400">조립</span>
              <div className="text-lg font-bold text-surface-100">{formatCurrency(data.cost_breakdown.assembly_cost)}</div>
            </div>
            <div className="rounded-lg bg-primary-900/30 p-2 border border-primary-700/50">
              <span className="text-primary-300">단가</span>
              <div className="text-lg font-bold text-primary-200">{formatCurrency(data.cost_breakdown.total_per_unit)}</div>
            </div>
          </div>
          {data.optimization_tips && data.optimization_tips.length > 0 && (
            <div className="mt-2 text-xs text-surface-400">
              <span className="font-medium text-surface-300">최적화 팁:</span>
              <ul className="mt-1 list-inside list-disc space-y-0.5">
                {data.optimization_tips.map((tip, i) => <li key={i}>{tip}</li>)}
              </ul>
            </div>
          )}
        </CollapsibleSection>
      )}

      {/* Knowledge Entries */}
      {data.knowledge_entries && data.knowledge_entries.length > 0 && (
        <CollapsibleSection title={`관련 지식 (${data.knowledge_entries.length})`}>
          <div className="space-y-2">
            {data.knowledge_entries.map((entry) => (
              <div key={entry.id} className="rounded-lg border border-surface-700 p-2.5 text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-surface-200">{entry.title}</span>
                  <Badge>{entry.category}</Badge>
                </div>
                <p className="mt-1 text-surface-400">{entry.content.slice(0, 200)}...</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {entry.tags.map((tag, i) => (
                    <span key={i} className="rounded bg-surface-700 px-1.5 py-0.5 text-surface-400">#{tag}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* General text */}
      {data.text && !data.topology_options && !data.normalized_bom && !data.risk_items && (
        <div className="text-sm text-surface-300 whitespace-pre-wrap">{data.text}</div>
      )}

      {/* Evidence */}
      {evidence && evidence.length > 0 && (
        <CollapsibleSection title={`근거 (${evidence.length})`}>
          <div className="space-y-1.5">
            {evidence.map((e, i) => (
              <div key={i} className="text-xs">
                <span className="font-medium text-surface-300">[{e.source}]</span>{' '}
                <span className="text-surface-400">{e.content}</span>
                <span className="ml-1 text-surface-500">(관련도: {Math.round(e.relevance * 100)}%)</span>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* Inference */}
      {inference && inference.length > 0 && (
        <CollapsibleSection title={`추론 과정 (${inference.length})`}>
          <div className="space-y-1.5">
            {inference.map((inf, i) => (
              <div key={i} className="text-xs">
                <span className="font-medium text-surface-300">{inf.step}:</span>{' '}
                <span className="text-surface-400">{inf.reasoning}</span>
                <span className="ml-1 text-surface-500">(신뢰도: {Math.round(inf.confidence * 100)}%)</span>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* Warnings */}
      {warnings && warnings.length > 0 && (
        <div className="space-y-1.5">
          {warnings.map((w, i) => (
            <div key={i} className={`flex items-start gap-2 rounded-lg p-2 text-xs ${
              w.type === 'error' ? 'bg-red-900/20 text-red-300' : w.type === 'warning' ? 'bg-yellow-900/20 text-yellow-300' : 'bg-blue-900/20 text-blue-300'
            }`}>
              {w.type === 'error' ? <XCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" /> : w.type === 'warning' ? <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" /> : <Info className="h-3.5 w-3.5 shrink-0 mt-0.5" />}
              <div>
                <p>{w.message}</p>
                {w.action && <p className="mt-0.5 opacity-80">{w.action}</p>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Suggestions */}
      {suggestions && suggestions.length > 0 && (
        <CollapsibleSection title={`제안 사항 (${suggestions.length})`}>
          <div className="space-y-1.5">
            {suggestions.map((s, i) => (
              <div key={i} className="rounded-lg border border-surface-700 p-2.5 text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-surface-200">{s.title}</span>
                  <Badge variant={s.priority === 'high' ? 'error' : s.priority === 'medium' ? 'warning' : 'info'}>
                    {s.priority === 'high' ? '높음' : s.priority === 'medium' ? '보통' : '낮음'}
                  </Badge>
                </div>
                <p className="mt-0.5 text-surface-400">{s.description}</p>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}
    </div>
  );
}
