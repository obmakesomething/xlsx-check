import { Bot, Cpu, FileSpreadsheet, Search, ShieldCheck, DollarSign, BookOpen, Layers } from 'lucide-react';
import { AGENT_LABELS } from '../../utils/constants';
import type { AgentType } from '../../types/copilot';

interface AgentIndicatorProps {
  agent: AgentType;
  active?: boolean;
}

const agentIcons: Record<string, React.ElementType> = {
  orchestrator: Layers,
  spec_agent: Bot,
  bom_agent: FileSpreadsheet,
  component_agent: Search,
  review_agent: Cpu,
  certification_agent: ShieldCheck,
  cost_agent: DollarSign,
  knowledge_agent: BookOpen,
};

const agentColors: Record<string, string> = {
  orchestrator: 'bg-purple-600/20 text-purple-400 border-purple-600/40',
  spec_agent: 'bg-blue-600/20 text-blue-400 border-blue-600/40',
  bom_agent: 'bg-emerald-600/20 text-emerald-400 border-emerald-600/40',
  component_agent: 'bg-orange-600/20 text-orange-400 border-orange-600/40',
  review_agent: 'bg-cyan-600/20 text-cyan-400 border-cyan-600/40',
  certification_agent: 'bg-yellow-600/20 text-yellow-400 border-yellow-600/40',
  cost_agent: 'bg-pink-600/20 text-pink-400 border-pink-600/40',
  knowledge_agent: 'bg-indigo-600/20 text-indigo-400 border-indigo-600/40',
};

export default function AgentIndicator({ agent, active }: AgentIndicatorProps) {
  const Icon = agentIcons[agent] || Bot;
  const color = agentColors[agent] || agentColors.orchestrator;

  return (
    <div className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${color}`}>
      <Icon className="h-3.5 w-3.5" />
      <span>{AGENT_LABELS[agent] || agent}</span>
      {active && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}
    </div>
  );
}
