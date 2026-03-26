import type { Status } from './common';

export interface ProductSpec {
  product_name: string;
  input_voltage: string;
  output_power: string;
  led_config: string;
  cct_range: string;
  dimming_type: string;
  communication_type: string;
  sensor_type: string;
  certifications: string[];
  additional_notes?: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  status: Status;
  spec: ProductSpec;
  created_at: string;
  updated_at: string;
  bom_count: number;
  analysis_count: number;
  tags: string[];
}

export interface CircuitBlock {
  id: string;
  name: string;
  type: 'input' | 'converter' | 'driver' | 'led' | 'sensor' | 'communication' | 'protection' | 'control';
  x: number;
  y: number;
  width: number;
  height: number;
  connections: string[];
  components: string[];
  description: string;
}

export interface BomItem {
  id: string;
  designator: string;
  component_name: string;
  value: string;
  package_type: string;
  manufacturer: string;
  part_number: string;
  lcsc_number: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  category: string;
  substitutes: string[];
  in_stock: boolean;
  notes: string;
}

export interface CostBreakdown {
  bom_cost: number;
  pcb_cost: number;
  assembly_cost: number;
  enclosure_cost: number;
  testing_cost: number;
  certification_cost: number;
  margin_percent: number;
  total_unit_cost: number;
  selling_price: number;
  quantities: { qty: number; unit_cost: number; total: number }[];
}

export interface CertificationItem {
  id: string;
  name: string;
  category: 'KC' | 'EMC' | 'safety' | 'environmental';
  description: string;
  completed: boolean;
  required: boolean;
  notes: string;
  documents: string[];
}

export interface TimelineEvent {
  id: string;
  phase: string;
  title: string;
  description: string;
  start_date: string;
  end_date: string;
  status: 'pending' | 'in_progress' | 'completed' | 'delayed';
  dependencies: string[];
}
