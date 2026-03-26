import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { useProjectStore } from '../store/projectStore';
import StatsOverview from '../components/dashboard/StatsOverview';
import ProjectCard from '../components/dashboard/ProjectCard';
import RecentActivity from '../components/dashboard/RecentActivity';
import EmptyState from '../components/shared/EmptyState';
import type { Stats, Activity } from '../types/common';
import type { Project } from '../types/project';

const mockStats: Stats = {
  total_projects: 12,
  total_components: 847,
  boms_generated: 34,
  analyses_run: 56,
};

const mockProjects: Project[] = [
  {
    id: 'proj-001',
    name: '40W LED 패널라이트 드라이버',
    description: 'DALI 디밍 지원 40W 실내용 패널라이트 LED 드라이버 설계',
    status: 'in_progress',
    spec: {
      product_name: '40W LED 패널라이트 드라이버',
      input_voltage: 'AC 220V',
      output_power: '40W',
      led_config: '2835 x 120ea',
      cct_range: '4000K',
      dimming_type: 'dali',
      communication_type: 'uart',
      sensor_type: 'none',
      certifications: ['kc', 'kc_ems'],
    },
    created_at: '2026-03-20T09:00:00Z',
    updated_at: '2026-03-25T14:30:00Z',
    bom_count: 3,
    analysis_count: 5,
    tags: ['실내', 'DALI', '40W'],
  },
  {
    id: 'proj-002',
    name: '100W LED 가로등 드라이버',
    description: '방수 IP65 100W 가로등용 LED 드라이버, 서지 보호 포함',
    status: 'review',
    spec: {
      product_name: '100W LED 가로등 드라이버',
      input_voltage: 'AC 220V',
      output_power: '100W',
      led_config: '3030 x 60ea',
      cct_range: '5000K',
      dimming_type: '0-10v',
      communication_type: 'none',
      sensor_type: 'ambient_light',
      certifications: ['kc', 'ce', 'ip_rating'],
    },
    created_at: '2026-03-10T09:00:00Z',
    updated_at: '2026-03-24T11:00:00Z',
    bom_count: 2,
    analysis_count: 8,
    tags: ['가로등', 'IP65', '100W'],
  },
  {
    id: 'proj-003',
    name: '20W 조광기 내장 다운라이트',
    description: 'TRIAC 디밍 호환 20W 매입형 다운라이트 드라이버',
    status: 'completed',
    spec: {
      product_name: '20W 조광기 내장 다운라이트',
      input_voltage: 'AC 220V',
      output_power: '20W',
      led_config: '2835 x 60ea',
      cct_range: '3000K~6500K',
      dimming_type: 'triac',
      communication_type: 'none',
      sensor_type: 'none',
      certifications: ['kc'],
    },
    created_at: '2026-02-15T09:00:00Z',
    updated_at: '2026-03-18T16:00:00Z',
    bom_count: 4,
    analysis_count: 12,
    tags: ['다운라이트', 'TRIAC', 'Tunable White'],
  },
  {
    id: 'proj-004',
    name: 'BLE 스마트 조명 모듈',
    description: 'Bluetooth 5.0 기반 스마트 조명 제어 모듈, iOS/Android 앱 연동',
    status: 'draft',
    spec: {
      product_name: 'BLE 스마트 조명 모듈',
      input_voltage: 'DC 24V',
      output_power: '15W',
      led_config: '5050 RGB x 30ea',
      cct_range: '2700K~6500K',
      dimming_type: 'bluetooth',
      communication_type: 'bluetooth',
      sensor_type: 'none',
      certifications: ['kc', 'fcc', 'ce'],
    },
    created_at: '2026-03-24T09:00:00Z',
    updated_at: '2026-03-25T10:00:00Z',
    bom_count: 0,
    analysis_count: 1,
    tags: ['스마트', 'BLE', 'RGB'],
  },
  {
    id: 'proj-005',
    name: '200W 산업용 고천장등 드라이버',
    description: '산업용 200W LED 하이베이 드라이버, 넓은 입력 전압 범위',
    status: 'in_progress',
    spec: {
      product_name: '200W 산업용 고천장등 드라이버',
      input_voltage: 'AC 100-277V',
      output_power: '200W',
      led_config: '3030 x 120ea',
      cct_range: '5000K',
      dimming_type: '0-10v',
      communication_type: 'none',
      sensor_type: 'pir',
      certifications: ['kc', 'ul', 'ce'],
    },
    created_at: '2026-03-05T09:00:00Z',
    updated_at: '2026-03-25T08:00:00Z',
    bom_count: 1,
    analysis_count: 3,
    tags: ['하이베이', '산업용', '200W'],
  },
  {
    id: 'proj-006',
    name: 'Zigbee 리니어 조명 제어기',
    description: 'Zigbee 3.0 프로토콜 지원 리니어 조명용 제어 모듈',
    status: 'draft',
    spec: {
      product_name: 'Zigbee 리니어 조명 제어기',
      input_voltage: 'DC 48V',
      output_power: '50W',
      led_config: '2835 x 200ea',
      cct_range: '3000K~4000K',
      dimming_type: 'zigbee',
      communication_type: 'zigbee',
      sensor_type: 'occupancy',
      certifications: ['kc', 'ce'],
    },
    created_at: '2026-03-22T09:00:00Z',
    updated_at: '2026-03-23T17:00:00Z',
    bom_count: 0,
    analysis_count: 0,
    tags: ['Zigbee', '리니어', '스마트'],
  },
];

const mockActivities: Activity[] = [
  { id: 'act-001', type: 'bom_generated', description: 'BoM Rev.3 생성 완료 (34개 부품)', project_id: 'proj-001', project_name: '40W LED 패널라이트 드라이버', timestamp: '2026-03-25T14:30:00Z' },
  { id: 'act-002', type: 'analysis_completed', description: '원가 분석 완료 - 단가 $12.50', project_id: 'proj-001', project_name: '40W LED 패널라이트 드라이버', timestamp: '2026-03-25T13:00:00Z' },
  { id: 'act-003', type: 'component_added', description: 'BP2309 LED 드라이버 IC 추가', project_id: 'proj-002', project_name: '100W LED 가로등 드라이버', timestamp: '2026-03-25T11:00:00Z' },
  { id: 'act-004', type: 'project_created', description: '새 프로젝트 생성', project_id: 'proj-004', project_name: 'BLE 스마트 조명 모듈', timestamp: '2026-03-24T09:00:00Z' },
  { id: 'act-005', type: 'file_uploaded', description: 'KiCad 회로도 파일 업로드', project_id: 'proj-003', project_name: '20W 조광기 내장 다운라이트', timestamp: '2026-03-23T16:00:00Z' },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const { projects, stats, recentActivity, loading, fetchProjects, setStats, setRecentActivity } = useProjectStore();

  useEffect(() => {
    fetchProjects().catch(() => {
      // If API is unavailable, the store will stay with empty projects
    });
    // Set mock data for demo
    setStats(mockStats);
    setRecentActivity(mockActivities);
  }, [fetchProjects, setStats, setRecentActivity]);

  const displayProjects = projects.length > 0 ? projects : mockProjects;
  const displayStats = stats.total_projects > 0 ? stats : mockStats;
  const displayActivity = recentActivity.length > 0 ? recentActivity : mockActivities;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-100">대시보드</h1>
          <p className="mt-1 text-sm text-surface-400">LED 제품 개발 프로젝트 현황</p>
        </div>
        <button
          onClick={() => navigate('/projects/new')}
          className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-primary-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          새 프로젝트
        </button>
      </div>

      <StatsOverview stats={displayStats} />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-surface-100">프로젝트</h2>
            <span className="text-sm text-surface-400">{displayProjects.length}개 프로젝트</span>
          </div>
          {displayProjects.length === 0 ? (
            <EmptyState
              title="프로젝트가 없습니다"
              description="새 프로젝트를 생성하여 LED 제품 개발을 시작하세요."
              action={
                <button onClick={() => navigate('/projects/new')} className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700">
                  프로젝트 생성
                </button>
              }
            />
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {displayProjects.map((project) => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          )}
        </div>
        <div>
          <RecentActivity activities={displayActivity} />
        </div>
      </div>
    </div>
  );
}
