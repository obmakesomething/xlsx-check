import { useState } from 'react';
import { Search, BookOpen, Lightbulb, Bug, ShieldCheck } from 'lucide-react';
import KnowledgeCard from '../components/knowledge/KnowledgeCard';
import InterviewUpload from '../components/knowledge/InterviewUpload';
import DesignPrinciples from '../components/knowledge/DesignPrinciples';
import Modal from '../components/shared/Modal';
import type { KnowledgeEntry } from '../types/copilot';

const mockEntries: KnowledgeEntry[] = [
  {
    id: 'k1', title: 'TRIAC 디밍 설계 시 Bleeder 회로 필요성', category: 'design',
    content: 'TRIAC 디머 사용 시 유지전류(holding current)를 확보하기 위해 Bleeder 회로가 필수적입니다. 일반적으로 2~5mA 정도의 Bleeder 전류가 필요하며, 저항값은 47K~100K 범위로 설정합니다. Bleeder 없이는 LED가 깜빡이거나 완전히 꺼지지 않는 현상이 발생합니다. 아버지가 20년간 경험한 바에 따르면, TRIAC 호환성 시험 시 최소 5종의 디머로 테스트하는 것이 좋습니다.',
    source: '아버지 인터뷰 (2024-01)', tags: ['TRIAC', '디밍', 'Bleeder', '호환성'], created_at: '2026-01-15T00:00:00Z',
  },
  {
    id: 'k2', title: 'EMC 전도 방출 대책 - 입력 필터 설계', category: 'debugging',
    content: 'CISPR 15 기준 전도 방출 시험 불합격 시 대책: 1) X-cap 용량 증가 (100nF -> 220nF), 2) Y-cap 추가 (2.2nF, 안전 규격 확인), 3) Common Mode Choke 인덕턴스 증가, 4) 스너버 회로 추가. 특히 150kHz ~ 500kHz 대역에서 문제가 많으며, 스위칭 주파수와 그 고조파가 주원인입니다.',
    source: '디버깅 노트', tags: ['EMC', '전도방출', '필터', 'CISPR15'], created_at: '2026-02-10T00:00:00Z',
  },
  {
    id: 'k3', title: 'KC 인증 필수 시험 항목 체크리스트', category: 'certification',
    content: 'KC 안전 인증 필수 시험: 1) 절연 내압 시험 (3kVac/1min 또는 4.2kVdc/1min), 2) 절연 저항 (500Vdc, >2MΩ), 3) 누설 전류 (<0.75mA), 4) 이상 동작 시험, 5) 온도 상승 시험 (절연재 부위), 6) 내전압 시험. EMC 등록: 전도 방출, 복사 방출, 서지 내성, EFT 내성, 정전기 내성.',
    source: '인증 가이드', tags: ['KC', '인증', '안전', '시험항목'], created_at: '2026-02-20T00:00:00Z',
  },
  {
    id: 'k4', title: '전해 콘덴서 수명 계산 및 선정 가이드', category: 'component',
    content: '전해 콘덴서 수명 = L0 x 2^((T0-Ta)/10). 여기서 L0은 정격 수명, T0은 정격 온도, Ta는 실사용 온도입니다. 105C/2000h 제품을 85C에서 사용하면 약 8000시간. LED 드라이버에서는 최소 30,000시간 수명이 필요하므로, 105C/5000h 이상의 제품을 선택하거나 동작 온도를 낮춰야 합니다.',
    source: '아버지 인터뷰 (2024-02)', tags: ['콘덴서', '수명', '열관리', '신뢰성'], created_at: '2026-01-25T00:00:00Z',
  },
  {
    id: 'k5', title: 'PCB 레이아웃 - 전류 루프 최소화', category: 'design',
    content: 'Buck LED 드라이버의 핵심 전류 루프: MOSFET -> 인덕터 -> 출력 캡 -> GND -> MOSFET. 이 루프의 면적을 최소화해야 EMI를 줄일 수 있습니다. 특히 스위칭 노드(SW)의 구리 면적은 방열을 고려하되 불필요하게 크게 만들지 말아야 합니다. 바이패스 캡은 IC VCC 핀에 최대한 가까이 배치하세요.',
    source: '설계 원칙', tags: ['PCB', '레이아웃', 'EMI', '전류루프'], created_at: '2026-03-05T00:00:00Z',
  },
  {
    id: 'k6', title: '서지 보호 설계 - MOV 및 TVS 선정', category: 'design',
    content: '가로등 등 옥외용 LED 드라이버는 IEC 61000-4-5 기준 6kV/3kA 서지 내성이 요구됩니다. 1차 보호: MOV (14D471K, ~300V 클램핑), 2차 보호: TVS 다이오드 (P6KE400A). MOV는 에너지 흡수량이 크지만 열화되므로, TVS와 병렬 사용이 권장됩니다. GDT(가스 방전관)를 1차에 추가하면 더 강력한 보호가 가능합니다.',
    source: '아버지 인터뷰 (2024-03)', tags: ['서지', 'MOV', 'TVS', '보호회로', '옥외'], created_at: '2026-03-10T00:00:00Z',
  },
];

const categories = [
  { key: 'all', label: '전체', icon: BookOpen },
  { key: 'design', label: '설계 원칙', icon: Lightbulb },
  { key: 'debugging', label: '디버깅 노트', icon: Bug },
  { key: 'certification', label: '인증 가이드', icon: ShieldCheck },
  { key: 'component', label: '부품 정보', icon: BookOpen },
];

type ViewTab = 'browse' | 'principles' | 'upload';

export default function KnowledgeBase() {
  const [activeView, setActiveView] = useState<ViewTab>('browse');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEntry, setSelectedEntry] = useState<KnowledgeEntry | null>(null);

  const filtered = mockEntries.filter((e) => {
    const matchCat = selectedCategory === 'all' || e.category === selectedCategory;
    const matchSearch = !searchQuery ||
      e.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchCat && matchSearch;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-100">지식 베이스</h1>
          <p className="mt-1 text-sm text-surface-400">LED 제품 개발 경험과 노하우를 체계적으로 관리합니다</p>
        </div>
        <div className="flex rounded-lg border border-surface-700 bg-surface-800">
          {([
            { key: 'browse' as ViewTab, label: '지식 탐색' },
            { key: 'principles' as ViewTab, label: '설계 원칙' },
            { key: 'upload' as ViewTab, label: '인터뷰 업로드' },
          ]).map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveView(tab.key)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${activeView === tab.key ? 'bg-primary-600 text-white rounded-lg' : 'text-surface-400 hover:text-surface-200'}`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {activeView === 'browse' && (
        <>
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-surface-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="지식 베이스 검색..."
                className="w-full rounded-lg border border-surface-600 bg-surface-800 py-2 pl-9 pr-3 text-sm text-surface-100 placeholder-surface-500 focus:border-primary-500 focus:outline-none"
              />
            </div>
            <div className="flex gap-1">
              {categories.map((cat) => (
                <button
                  key={cat.key}
                  onClick={() => setSelectedCategory(cat.key)}
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
                    selectedCategory === cat.key ? 'bg-primary-600/20 text-primary-300 border border-primary-500/50' : 'border border-surface-700 bg-surface-800 text-surface-400 hover:text-surface-200'
                  }`}
                >
                  <cat.icon className="h-3.5 w-3.5" />
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filtered.map((entry) => (
              <KnowledgeCard key={entry.id} entry={entry} onClick={() => setSelectedEntry(entry)} />
            ))}
          </div>
          {filtered.length === 0 && (
            <div className="text-center py-12 text-surface-500">검색 결과가 없습니다</div>
          )}
        </>
      )}

      {activeView === 'principles' && <DesignPrinciples />}
      {activeView === 'upload' && <InterviewUpload />}

      <Modal
        open={!!selectedEntry}
        onClose={() => setSelectedEntry(null)}
        title={selectedEntry?.title || ''}
        size="lg"
      >
        {selectedEntry && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-primary-600/20 px-2.5 py-0.5 text-xs font-medium text-primary-300">{selectedEntry.category}</span>
              <span className="text-xs text-surface-500">출처: {selectedEntry.source}</span>
            </div>
            <p className="text-sm text-surface-200 leading-relaxed whitespace-pre-wrap">{selectedEntry.content}</p>
            <div className="flex flex-wrap gap-1 pt-2 border-t border-surface-700">
              {selectedEntry.tags.map((tag) => (
                <span key={tag} className="rounded bg-surface-700 px-2 py-0.5 text-xs text-surface-400">#{tag}</span>
              ))}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
