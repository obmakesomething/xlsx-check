import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { MessageSquare, Settings, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../store/projectStore';
import { useUIStore } from '../store/uiStore';
import Card from '../components/shared/Card';
import Badge from '../components/shared/Badge';
import BomTable from '../components/project/BomTable';
import CircuitBlockDiagram from '../components/project/CircuitBlockDiagram';
import CostCalculator from '../components/project/CostCalculator';
import CertificationChecklist from '../components/project/CertificationChecklist';
import ProjectTimeline from '../components/project/ProjectTimeline';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import { STATUS_LABELS, STATUS_COLORS } from '../utils/constants';
import { formatDate } from '../utils/formatters';
import type { Project, BomItem, CostBreakdown, CertificationItem, TimelineEvent, CircuitBlock } from '../types/project';

const TABS = [
  { id: 'overview', label: '개요' },
  { id: 'circuit', label: '회로' },
  { id: 'bom', label: 'BoM' },
  { id: 'cost', label: '원가' },
  { id: 'cert', label: '인증' },
  { id: 'timeline', label: '타임라인' },
] as const;

type TabId = (typeof TABS)[number]['id'];

// Mock data for demo
const mockBom: BomItem[] = [
  { id: 'b1', designator: 'U1', component_name: 'BP2866BJ', value: '-', package_type: 'SOP-8', manufacturer: 'BPS', part_number: 'BP2866BJ', lcsc_number: 'C94553', quantity: 1, unit_price: 0.45, total_price: 0.45, category: 'IC - LED Driver', substitutes: [], in_stock: true, notes: '' },
  { id: 'b2', designator: 'L1', component_name: 'Inductor 470uH', value: '470uH', package_type: '1210', manufacturer: 'Sunlord', part_number: 'SWPA4030S471MT', lcsc_number: 'C408352', quantity: 1, unit_price: 0.12, total_price: 0.12, category: 'Inductor', substitutes: [], in_stock: true, notes: '' },
  { id: 'b3', designator: 'C1', component_name: 'Cap 4.7uF/400V', value: '4.7uF/400V', package_type: '10x12mm', manufacturer: 'Rubycon', part_number: 'ZLH400M4R7', lcsc_number: 'C311290', quantity: 1, unit_price: 0.35, total_price: 0.35, category: 'Capacitor', substitutes: [], in_stock: true, notes: '전해 콘덴서' },
  { id: 'b4', designator: 'C2', component_name: 'Cap 100nF', value: '100nF', package_type: '0603', manufacturer: 'Samsung', part_number: 'CL10B104KB8NNNC', lcsc_number: 'C14663', quantity: 3, unit_price: 0.003, total_price: 0.009, category: 'Capacitor', substitutes: [], in_stock: true, notes: '' },
  { id: 'b5', designator: 'R1', component_name: 'Resistor 10R', value: '10R', package_type: '0805', manufacturer: 'Yageo', part_number: 'RC0805FR-0710RL', lcsc_number: 'C17407', quantity: 1, unit_price: 0.005, total_price: 0.005, category: 'Resistor', substitutes: [], in_stock: true, notes: '전류 감지' },
  { id: 'b6', designator: 'R2-R3', component_name: 'Resistor 100K', value: '100K', package_type: '0603', manufacturer: 'Yageo', part_number: 'RC0603FR-07100KL', lcsc_number: 'C14675', quantity: 2, unit_price: 0.003, total_price: 0.006, category: 'Resistor', substitutes: [], in_stock: true, notes: '' },
  { id: 'b7', designator: 'D1', component_name: 'Bridge Rectifier', value: 'MB10F', package_type: 'MBF', manufacturer: 'Rectron', part_number: 'MB10F', lcsc_number: 'C109155', quantity: 1, unit_price: 0.08, total_price: 0.08, category: 'Diode', substitutes: [], in_stock: true, notes: '' },
  { id: 'b8', designator: 'D2', component_name: 'Schottky Diode', value: 'SS34', package_type: 'SMA', manufacturer: 'MDD', part_number: 'SS34', lcsc_number: 'C8678', quantity: 1, unit_price: 0.04, total_price: 0.04, category: 'Diode', substitutes: [], in_stock: true, notes: '' },
  { id: 'b9', designator: 'F1', component_name: 'Fuse 2A', value: '2A/250V', package_type: '5x20mm', manufacturer: 'Littelfuse', part_number: '0215002', lcsc_number: 'C182970', quantity: 1, unit_price: 0.05, total_price: 0.05, category: 'Protection', substitutes: [], in_stock: true, notes: '' },
  { id: 'b10', designator: 'NTC1', component_name: 'NTC 5D-9', value: '5D-9', package_type: '9mm', manufacturer: 'TKS', part_number: '5D-9', lcsc_number: 'C124388', quantity: 1, unit_price: 0.03, total_price: 0.03, category: 'Protection', substitutes: [], in_stock: true, notes: '돌입전류 제한' },
];

const mockCost: CostBreakdown = {
  bom_cost: 1.17,
  pcb_cost: 0.35,
  assembly_cost: 0.80,
  enclosure_cost: 0.50,
  testing_cost: 0.20,
  certification_cost: 0.15,
  margin_percent: 30,
  total_unit_cost: 3.17,
  selling_price: 4.12,
  quantities: [
    { qty: 100, unit_cost: 4.50, total: 450 },
    { qty: 500, unit_cost: 3.80, total: 1900 },
    { qty: 1000, unit_cost: 3.17, total: 3170 },
    { qty: 5000, unit_cost: 2.85, total: 14250 },
    { qty: 10000, unit_cost: 2.60, total: 26000 },
  ],
};

const mockCerts: CertificationItem[] = [
  { id: 'c1', name: 'KC 안전 인증', category: 'KC', description: '전기용품 안전 인증 (KC 마크)', completed: true, required: true, notes: '', documents: ['KC_cert_report.pdf'] },
  { id: 'c2', name: 'KC EMC 적합성', category: 'EMC', description: '전자파 적합성 등록', completed: false, required: true, notes: 'RE, CE 시험 필요', documents: [] },
  { id: 'c3', name: '전도 방출 (CE)', category: 'EMC', description: 'CISPR 15 기준 전도 방출 시험', completed: false, required: true, notes: '150kHz~30MHz', documents: [] },
  { id: 'c4', name: '복사 방출 (RE)', category: 'EMC', description: 'CISPR 15 기준 복사 방출 시험', completed: false, required: true, notes: '30MHz~1GHz', documents: [] },
  { id: 'c5', name: '서지 내성', category: 'safety', description: 'IEC 61000-4-5 서지 시험', completed: true, required: true, notes: '1kV L-N, 2kV L-PE', documents: ['surge_test.pdf'] },
  { id: 'c6', name: 'EFT 내성', category: 'safety', description: 'IEC 61000-4-4 EFT 시험', completed: false, required: true, notes: '2kV', documents: [] },
  { id: 'c7', name: 'RoHS 적합', category: 'environmental', description: '유해물질 사용제한 지침 준수', completed: true, required: true, notes: '모든 부품 RoHS 인증', documents: ['rohs_declaration.pdf'] },
  { id: 'c8', name: '절연 내압 시험', category: 'safety', description: '입출력간 절연 내압 시험 (3kVac)', completed: false, required: true, notes: '강화 절연 기준', documents: [] },
];

const mockTimeline: TimelineEvent[] = [
  { id: 't1', phase: '설계', title: '회로 설계 및 시뮬레이션', description: '스키매틱 설계, SPICE 시뮬레이션', start_date: '2026-03-01', end_date: '2026-03-15', status: 'completed', dependencies: [] },
  { id: 't2', phase: '설계', title: 'PCB 레이아웃', description: '2레이어 PCB 설계, DRC 검증', start_date: '2026-03-10', end_date: '2026-03-20', status: 'completed', dependencies: ['t1'] },
  { id: 't3', phase: '시작품', title: 'PCB 제조 및 부품 조달', description: 'JLCPCB 발주, LCSC 부품 주문', start_date: '2026-03-20', end_date: '2026-03-28', status: 'in_progress', dependencies: ['t2'] },
  { id: 't4', phase: '시작품', title: 'SMT 조립', description: '시작품 10pcs 조립', start_date: '2026-03-28', end_date: '2026-04-02', status: 'pending', dependencies: ['t3'] },
  { id: 't5', phase: '검증', title: '기능 시험', description: '전기적 특성, 효율, 디밍 시험', start_date: '2026-04-02', end_date: '2026-04-10', status: 'pending', dependencies: ['t4'] },
  { id: 't6', phase: '검증', title: 'EMC 시험', description: '전도/복사 방출, 내성 시험', start_date: '2026-04-10', end_date: '2026-04-20', status: 'pending', dependencies: ['t5'] },
  { id: 't7', phase: '인증', title: 'KC 인증 접수', description: '시험 성적서 기반 인증 신청', start_date: '2026-04-20', end_date: '2026-05-15', status: 'pending', dependencies: ['t6'] },
  { id: 't8', phase: '양산', title: '양산 준비', description: '양산 BoM 확정, 치구 제작', start_date: '2026-05-15', end_date: '2026-05-30', status: 'pending', dependencies: ['t7'] },
];

const mockBlocks: CircuitBlock[] = [
  { id: 'blk1', name: 'AC 입력', type: 'input', x: 20, y: 200, width: 120, height: 80, connections: ['blk2'], components: ['F1', 'NTC1', 'MOV1'], description: 'AC 입력 보호 회로' },
  { id: 'blk2', name: '정류 회로', type: 'converter', x: 180, y: 200, width: 120, height: 80, connections: ['blk3'], components: ['D1', 'C1'], description: '브릿지 정류 및 필터' },
  { id: 'blk3', name: 'LED 드라이버', type: 'driver', x: 340, y: 200, width: 140, height: 80, connections: ['blk4', 'blk5'], components: ['U1', 'L1', 'D2'], description: 'Buck LED 드라이버 IC' },
  { id: 'blk4', name: 'LED 출력', type: 'led', x: 530, y: 150, width: 120, height: 80, connections: [], components: ['LED1-LED10'], description: 'LED 모듈 연결' },
  { id: 'blk5', name: '피드백', type: 'control', x: 530, y: 270, width: 120, height: 80, connections: ['blk3'], components: ['R1', 'R2', 'R3'], description: '전류 감지 및 피드백' },
];

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const { currentProject, circuitBlocks, bomItems, costBreakdown, certifications, timeline, loading, fetchProject, fetchCircuitBlocks, fetchBom, fetchCostBreakdown, fetchCertifications, fetchTimeline, updateBomItem, updateCertification } = useProjectStore();
  const { setCopilotOpen } = useUIStore();

  useEffect(() => {
    if (id) {
      fetchProject(id).catch(() => {});
      fetchCircuitBlocks(id).catch(() => {});
      fetchBom(id).catch(() => {});
      fetchCostBreakdown(id).catch(() => {});
      fetchCertifications(id).catch(() => {});
      fetchTimeline(id).catch(() => {});
    }
  }, [id, fetchProject, fetchCircuitBlocks, fetchBom, fetchCostBreakdown, fetchCertifications, fetchTimeline]);

  // Use mock data when API unavailable
  const project: Project | null = currentProject || (id ? {
    id, name: '40W LED 패널라이트 드라이버', description: 'DALI 디밍 지원 40W 실내용 패널라이트 LED 드라이버 설계', status: 'in_progress',
    spec: { product_name: '40W LED 패널라이트 드라이버', input_voltage: 'AC 220V', output_power: '40W', led_config: '2835 x 120ea', cct_range: '4000K', dimming_type: 'dali', communication_type: 'uart', sensor_type: 'none', certifications: ['kc', 'kc_ems'] },
    created_at: '2026-03-20T09:00:00Z', updated_at: '2026-03-25T14:30:00Z', bom_count: 3, analysis_count: 5, tags: ['실내', 'DALI', '40W'],
  } : null);

  const displayBlocks = circuitBlocks.length > 0 ? circuitBlocks : mockBlocks;
  const displayBom = bomItems.length > 0 ? bomItems : mockBom;
  const displayCost = costBreakdown || mockCost;
  const displayCerts = certifications.length > 0 ? certifications : mockCerts;
  const displayTimeline = timeline.length > 0 ? timeline : mockTimeline;

  if (loading && !project) {
    return <LoadingSpinner size="lg" text="프로젝트를 불러오는 중..." className="min-h-[60vh]" />;
  }

  if (!project) {
    return <div className="text-center text-surface-400 py-20">프로젝트를 찾을 수 없습니다.</div>;
  }

  const specItems = [
    { label: '제품명', value: project.spec.product_name },
    { label: '입력 전압', value: project.spec.input_voltage },
    { label: '출력 전력', value: project.spec.output_power },
    { label: 'LED 구성', value: project.spec.led_config },
    { label: 'CCT 범위', value: project.spec.cct_range },
    { label: '디밍 방식', value: project.spec.dimming_type },
    { label: '통신 방식', value: project.spec.communication_type },
    { label: '센서', value: project.spec.sensor_type },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/')} className="rounded-lg p-2 text-surface-400 hover:bg-surface-800 hover:text-surface-200">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-surface-100">{project.name}</h1>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[project.status] || STATUS_COLORS.draft}`}>
                {STATUS_LABELS[project.status] || project.status}
              </span>
            </div>
            <p className="mt-1 text-sm text-surface-400">{project.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setCopilotOpen(true)} className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700">
            <MessageSquare className="h-4 w-4" />
            AI 분석
          </button>
          <button className="rounded-lg border border-surface-600 p-2 text-surface-400 hover:bg-surface-800 hover:text-surface-200">
            <Settings className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-surface-700">
        <nav className="flex space-x-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-surface-800 text-primary-400 border-b-2 border-primary-400'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card title="제품 사양">
            <dl className="space-y-2.5">
              {specItems.map((item) => (
                <div key={item.label} className="flex justify-between text-sm">
                  <dt className="text-surface-400">{item.label}</dt>
                  <dd className="font-medium text-surface-200">{item.value || '-'}</dd>
                </div>
              ))}
            </dl>
            {project.spec.certifications.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1 pt-3 border-t border-surface-700">
                {project.spec.certifications.map((cert) => (
                  <Badge key={cert} variant="info">{cert.toUpperCase()}</Badge>
                ))}
              </div>
            )}
          </Card>
          <Card title="프로젝트 정보">
            <dl className="space-y-2.5">
              <div className="flex justify-between text-sm">
                <dt className="text-surface-400">생성일</dt>
                <dd className="text-surface-200">{formatDate(project.created_at)}</dd>
              </div>
              <div className="flex justify-between text-sm">
                <dt className="text-surface-400">최종 수정</dt>
                <dd className="text-surface-200">{formatDate(project.updated_at)}</dd>
              </div>
              <div className="flex justify-between text-sm">
                <dt className="text-surface-400">BoM 수</dt>
                <dd className="text-surface-200">{project.bom_count}</dd>
              </div>
              <div className="flex justify-between text-sm">
                <dt className="text-surface-400">분석 횟수</dt>
                <dd className="text-surface-200">{project.analysis_count}</dd>
              </div>
              <div className="flex justify-between text-sm">
                <dt className="text-surface-400">태그</dt>
                <dd className="flex flex-wrap gap-1">
                  {project.tags.map((tag) => <Badge key={tag}>{tag}</Badge>)}
                </dd>
              </div>
            </dl>
          </Card>
        </div>
      )}

      {activeTab === 'circuit' && <CircuitBlockDiagram blocks={displayBlocks} />}
      {activeTab === 'bom' && (
        <BomTable
          items={displayBom}
          onUpdate={(itemId, updates) => id && updateBomItem(id, itemId, updates)}
        />
      )}
      {activeTab === 'cost' && <CostCalculator cost={displayCost} />}
      {activeTab === 'cert' && (
        <CertificationChecklist
          items={displayCerts}
          onToggle={(itemId, completed) => id && updateCertification(id, itemId, { completed })}
        />
      )}
      {activeTab === 'timeline' && <ProjectTimeline events={displayTimeline} />}
    </div>
  );
}
