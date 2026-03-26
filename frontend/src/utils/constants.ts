import type { TaskType } from '../types/copilot';

export const APP_NAME = 'LED Copilot';

export const TASK_TYPE_LABELS: Record<TaskType, string> = {
  design_draft: '설계 초안',
  bom_normalize: 'BoM 정규화',
  component_substitute: '대체 부품 검색',
  review: '설계 리뷰',
  certification_check: '인증 검토',
  cost_estimate: '원가 분석',
  knowledge_query: '지식 베이스 조회',
  general: '일반 질문',
};

export const AGENT_LABELS: Record<string, string> = {
  spec_agent: '설계 에이전트',
  bom_agent: 'BoM 에이전트',
  component_agent: '부품 에이전트',
  review_agent: '리뷰 에이전트',
  certification_agent: '인증 에이전트',
  cost_agent: '원가 에이전트',
  knowledge_agent: '지식 에이전트',
  orchestrator: '오케스트레이터',
};

export const STATUS_LABELS: Record<string, string> = {
  draft: '초안',
  in_progress: '진행 중',
  review: '검토 중',
  completed: '완료',
  archived: '보관됨',
};

export const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-600 text-gray-200',
  in_progress: 'bg-blue-600 text-blue-100',
  review: 'bg-yellow-600 text-yellow-100',
  completed: 'bg-green-600 text-green-100',
  archived: 'bg-gray-700 text-gray-300',
};

export const SEVERITY_COLORS: Record<string, string> = {
  low: 'bg-blue-900/50 text-blue-300 border-blue-700',
  medium: 'bg-yellow-900/50 text-yellow-300 border-yellow-700',
  high: 'bg-orange-900/50 text-orange-300 border-orange-700',
  critical: 'bg-red-900/50 text-red-300 border-red-700',
};

export const CERTIFICATION_TYPES = ['KC', 'EMC', 'Safety', 'Environmental'] as const;

export const DIMMING_TYPES = [
  { value: 'none', label: '없음' },
  { value: 'triac', label: 'TRIAC' },
  { value: '0-10v', label: '0-10V' },
  { value: 'dali', label: 'DALI' },
  { value: 'pwm', label: 'PWM' },
  { value: 'bluetooth', label: 'Bluetooth' },
  { value: 'zigbee', label: 'Zigbee' },
];

export const COMMUNICATION_TYPES = [
  { value: 'none', label: '없음' },
  { value: 'uart', label: 'UART' },
  { value: 'i2c', label: 'I2C' },
  { value: 'spi', label: 'SPI' },
  { value: 'bluetooth', label: 'Bluetooth' },
  { value: 'wifi', label: 'Wi-Fi' },
  { value: 'zigbee', label: 'Zigbee' },
  { value: 'dali', label: 'DALI' },
];

export const SENSOR_TYPES = [
  { value: 'none', label: '없음' },
  { value: 'pir', label: 'PIR 모션 센서' },
  { value: 'ambient_light', label: '조도 센서' },
  { value: 'temperature', label: '온도 센서' },
  { value: 'radar', label: '레이더 센서' },
  { value: 'occupancy', label: '재실 센서' },
];

export const CERTIFICATIONS_OPTIONS = [
  { value: 'kc', label: 'KC 인증' },
  { value: 'kc_ems', label: 'KC EMC (전자파적합성)' },
  { value: 'cb', label: 'CB 인증' },
  { value: 'ce', label: 'CE 마킹' },
  { value: 'ul', label: 'UL 인증' },
  { value: 'fcc', label: 'FCC' },
  { value: 'rohs', label: 'RoHS' },
  { value: 'ip_rating', label: 'IP 등급' },
];
