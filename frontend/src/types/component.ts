export interface Component {
  id: string;
  name: string;
  category: string;
  subcategory: string;
  manufacturer: string;
  part_number: string;
  lcsc_number: string;
  package_type: string;
  description: string;
  datasheet_url: string;
  unit_price: number;
  moq: number;
  stock: number;
  specifications: Record<string, string>;
  tags: string[];
  usage_count: number;
  last_used: string;
  substitutes: SubstitutePart[];
}

export interface SubstitutePart {
  id: string;
  part_number: string;
  manufacturer: string;
  lcsc_number: string;
  compatibility: number;
  price_diff: number;
  unit_price: number;
  stock: number;
  notes: string;
}

export interface ComponentSearchParams {
  query?: string;
  category?: string;
  manufacturer?: string;
  package_type?: string;
  in_stock?: boolean;
  page?: number;
  page_size?: number;
}

export interface LCSCComponent {
  lcsc_number: string;
  name: string;
  manufacturer: string;
  package: string;
  price: number;
  stock: number;
  description: string;
  datasheet_url: string;
  image_url: string;
}

export const COMPONENT_CATEGORIES = [
  'IC - LED Driver',
  'IC - SMPS Controller',
  'IC - MCU',
  'IC - Communication',
  'MOSFET',
  'Diode',
  'Capacitor',
  'Resistor',
  'Inductor',
  'Transformer',
  'Connector',
  'LED Module',
  'Sensor',
  'Protection',
  'Crystal/Oscillator',
  'Other',
] as const;

export const PACKAGE_TYPES = [
  'SOT-23', 'SOT-223', 'SOP-8', 'SOP-16', 'TSSOP-16', 'TSSOP-20',
  'QFN-16', 'QFN-32', 'QFP-48', 'QFP-64',
  'TO-252', 'TO-263', 'TO-220',
  '0402', '0603', '0805', '1206', '1210', '2512',
  'SMD', 'THT', 'Other',
] as const;
