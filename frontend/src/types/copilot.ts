export type TaskType =
  | 'design_draft'
  | 'bom_normalize'
  | 'component_substitute'
  | 'review'
  | 'certification_check'
  | 'cost_estimate'
  | 'knowledge_query'
  | 'general';

export type AgentType =
  | 'spec_agent'
  | 'bom_agent'
  | 'component_agent'
  | 'review_agent'
  | 'certification_agent'
  | 'cost_agent'
  | 'knowledge_agent'
  | 'orchestrator';

export interface CopilotRequest {
  message: string;
  task_type?: TaskType;
  project_id?: string;
  context?: Record<string, unknown>;
  files?: File[];
}

export interface CopilotResponse {
  id: string;
  task_type: TaskType;
  agent: AgentType;
  status: 'success' | 'partial' | 'error';
  message: string;
  data: CopilotResponseData;
  evidence: Evidence[];
  inference: Inference[];
  warnings: Warning[];
  suggestions: Suggestion[];
  timestamp: string;
  processing_time_ms: number;
}

export interface CopilotResponseData {
  // design_draft
  topology_options?: TopologyOption[];
  recommended_topology?: string;
  circuit_blocks?: CircuitBlockSuggestion[];

  // bom_normalize
  normalized_bom?: NormalizedBomItem[];
  unresolved_items?: string[];

  // component_substitute
  substitutes?: SubstituteSuggestion[];
  compatibility_score?: number;

  // review
  risk_items?: RiskItem[];
  overall_score?: number;
  category_scores?: Record<string, number>;

  // certification_check
  checklist?: CertCheckItem[];
  missing_items?: string[];
  estimated_timeline?: string;

  // cost_estimate
  cost_breakdown?: CostEstimate;
  optimization_tips?: string[];

  // knowledge_query
  knowledge_entries?: KnowledgeEntry[];
  related_projects?: string[];

  // general
  text?: string;
}

export interface TopologyOption {
  name: string;
  description: string;
  pros: string[];
  cons: string[];
  efficiency: string;
  cost_level: 'low' | 'medium' | 'high';
  complexity: 'low' | 'medium' | 'high';
  recommended: boolean;
  key_components: string[];
}

export interface CircuitBlockSuggestion {
  name: string;
  type: string;
  description: string;
  recommended_components: string[];
}

export interface NormalizedBomItem {
  original: string;
  designator: string;
  component_name: string;
  value: string;
  package_type: string;
  lcsc_number: string;
  unit_price: number;
  confidence: number;
}

export interface SubstituteSuggestion {
  original_part: string;
  substitute_part: string;
  manufacturer: string;
  compatibility: number;
  price_diff_percent: number;
  advantages: string[];
  disadvantages: string[];
  verification_notes: string;
}

export interface RiskItem {
  id: string;
  category: 'thermal' | 'emc' | 'reliability' | 'cost' | 'supply_chain' | 'design';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  recommendation: string;
  affected_components: string[];
}

export interface CertCheckItem {
  id: string;
  standard: string;
  requirement: string;
  status: 'pass' | 'fail' | 'needs_review' | 'not_applicable';
  notes: string;
  action_items: string[];
}

export interface CostEstimate {
  bom_total: number;
  pcb_cost: number;
  assembly_cost: number;
  total_per_unit: number;
  quantity_breaks: { qty: number; price: number }[];
  currency: string;
}

export interface Evidence {
  source: string;
  content: string;
  relevance: number;
}

export interface Inference {
  step: string;
  reasoning: string;
  confidence: number;
}

export interface Warning {
  type: 'info' | 'warning' | 'error';
  message: string;
  action?: string;
}

export interface Suggestion {
  title: string;
  description: string;
  action_type: string;
  priority: 'low' | 'medium' | 'high';
}

export interface KnowledgeEntry {
  id: string;
  title: string;
  category: string;
  content: string;
  source: string;
  tags: string[];
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  task_type?: TaskType;
  agent?: AgentType;
  analysis?: CopilotResponse;
  files?: { name: string; type: string }[];
  timestamp: string;
}
