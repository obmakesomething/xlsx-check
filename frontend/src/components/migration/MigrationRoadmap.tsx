import { CheckCircle, Circle, Clock } from 'lucide-react';
import Card from '../shared/Card';
import Badge from '../shared/Badge';

interface RoadmapWeek {
  week: number;
  title: string;
  tasks: string[];
  status: 'completed' | 'in_progress' | 'pending';
  phase: string;
}

const roadmap: RoadmapWeek[] = [
  { week: 1, title: 'KiCad 설치 및 환경 설정', tasks: ['KiCad 8.x 설치', '기본 라이브러리 설정', '한글 환경 구성', '기존 도구 호환성 확인'], status: 'completed', phase: '기초 학습' },
  { week: 2, title: '기본 조작 학습', tasks: ['스키매틱 에디터 기본 조작', '심볼 배치 및 와이어링', '단축키 커스터마이즈', 'ERC 실행 및 해석'], status: 'completed', phase: '기초 학습' },
  { week: 3, title: 'PCB 에디터 학습', tasks: ['PCB 에디터 기본 조작', '부품 배치 및 라우팅', 'DRC 설정', '디자인 룰 구성'], status: 'in_progress', phase: '기초 학습' },
  { week: 4, title: '라이브러리 관리', tasks: ['커스텀 심볼 생성', '커스텀 풋프린트 생성', '3D 모델 연결', '라이브러리 구조 설계'], status: 'pending', phase: '라이브러리' },
  { week: 5, title: '기존 부품 라이브러리 이전', tasks: ['자주 사용하는 LED 드라이버 IC', '패시브 부품 라이브러리', 'LCSC 호환 풋프린트', '라이브러리 검증'], status: 'pending', phase: '라이브러리' },
  { week: 6, title: '템플릿 프로젝트 생성', tasks: ['LED 드라이버 기본 템플릿', '디자인 룰 템플릿 (JLCPCB)', '제조 출력 설정 프리셋', 'BOM 출력 형식 설정'], status: 'pending', phase: '템플릿' },
  { week: 7, title: '첫 프로젝트 (간단한 설계)', tasks: ['단순 벅 LED 드라이버 설계', '스키매틱 완성', 'PCB 레이아웃', '거버 출력 및 검증'], status: 'pending', phase: '실전' },
  { week: 8, title: '첫 프로젝트 완성', tasks: ['BOM 생성 및 LCSC 매핑', '3D 뷰어 확인', '제조 파일 출력', '기존 도구 결과와 비교'], status: 'pending', phase: '실전' },
  { week: 9, title: '고급 기능 학습', tasks: ['계층적 스키매틱', '버스 와이어링', '다채널 설계', '시뮬레이션 (SPICE)'], status: 'pending', phase: '고급' },
  { week: 10, title: '자동화 도구 구축', tasks: ['Python 스크립팅 기초', 'BOM 자동 생성 스크립트', '넷리스트 비교 도구', 'CI/CD 파이프라인'], status: 'pending', phase: '자동화' },
  { week: 11, title: '팀 워크플로우 구축', tasks: ['Git 기반 버전 관리', '프로젝트 구조 표준화', '코드 리뷰 프로세스', '라이브러리 공유 시스템'], status: 'pending', phase: '워크플로우' },
  { week: 12, title: '완전 전환 및 최적화', tasks: ['남은 프로젝트 이전', '문서화 완성', '성능 비교 보고서', '지속적 개선 계획'], status: 'pending', phase: '완성' },
];

const statusConfig = {
  completed: { icon: CheckCircle, color: 'text-green-400', bgColor: 'bg-green-900/20 border-green-700/30' },
  in_progress: { icon: Clock, color: 'text-blue-400', bgColor: 'bg-blue-900/20 border-blue-700/30' },
  pending: { icon: Circle, color: 'text-surface-500', bgColor: 'bg-surface-800/50 border-surface-700' },
};

export default function MigrationRoadmap() {
  const completedWeeks = roadmap.filter((w) => w.status === 'completed').length;
  const progress = (completedWeeks / roadmap.length) * 100;

  return (
    <div className="space-y-6">
      {/* Progress Bar */}
      <Card>
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-surface-200">전체 진행률</span>
          <span className="text-sm text-surface-400">{completedWeeks}/{roadmap.length}주 완료</span>
        </div>
        <div className="h-3 rounded-full bg-surface-700">
          <div className="h-full rounded-full bg-gradient-to-r from-primary-600 to-primary-400 transition-all" style={{ width: `${progress}%` }} />
        </div>
      </Card>

      {/* Timeline */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {roadmap.map((week) => {
          const config = statusConfig[week.status];
          const Icon = config.icon;
          return (
            <div key={week.week} className={`rounded-lg border p-4 ${config.bgColor}`}>
              <div className="mb-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon className={`h-4 w-4 ${config.color}`} />
                  <span className="text-xs font-bold text-surface-300">Week {week.week}</span>
                </div>
                <Badge variant={week.status === 'completed' ? 'success' : week.status === 'in_progress' ? 'info' : 'default' as never}>
                  {week.phase}
                </Badge>
              </div>
              <h4 className="mb-2 text-sm font-medium text-surface-100">{week.title}</h4>
              <ul className="space-y-1">
                {week.tasks.map((task, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-surface-400">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-surface-500" />
                    {task}
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}
