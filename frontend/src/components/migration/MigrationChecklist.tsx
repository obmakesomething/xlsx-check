import { useState } from 'react';
import { CheckCircle, Circle, AlertTriangle } from 'lucide-react';
import Card from '../shared/Card';

interface CheckItem {
  id: string;
  category: string;
  text: string;
  required: boolean;
  completed: boolean;
  notes?: string;
}

const initialChecklist: CheckItem[] = [
  { id: '1', category: '환경 설정', text: 'KiCad 8.x 최신 버전 설치', required: true, completed: true },
  { id: '2', category: '환경 설정', text: 'JLCPCB/LCSC 플러그인 설치', required: true, completed: true },
  { id: '3', category: '환경 설정', text: 'Git 버전 관리 설정', required: true, completed: false },
  { id: '4', category: '환경 설정', text: '사용자 단축키 설정', required: false, completed: false },
  { id: '5', category: '라이브러리', text: 'LED 드라이버 IC 심볼 생성 (상위 20종)', required: true, completed: false },
  { id: '6', category: '라이브러리', text: 'MOSFET/다이오드 심볼 생성', required: true, completed: false },
  { id: '7', category: '라이브러리', text: 'LCSC 호환 풋프린트 확인', required: true, completed: false },
  { id: '8', category: '라이브러리', text: '3D 모델 연결', required: false, completed: false },
  { id: '9', category: '템플릿', text: 'AC-DC LED 드라이버 템플릿 생성', required: true, completed: false },
  { id: '10', category: '템플릿', text: 'DC-DC LED 드라이버 템플릿 생성', required: true, completed: false },
  { id: '11', category: '템플릿', text: '디자인 룰 프리셋 (2Layer, 4Layer)', required: true, completed: false },
  { id: '12', category: '템플릿', text: '제조 출력 설정 (JLCPCB 규격)', required: true, completed: false },
  { id: '13', category: '검증', text: '기존 설계 1건 KiCad로 재설계', required: true, completed: false },
  { id: '14', category: '검증', text: '거버 파일 비교 검증', required: true, completed: false },
  { id: '15', category: '검증', text: 'BoM 출력 비교', required: true, completed: false },
  { id: '16', category: '자동화', text: 'BoM 자동 생성 스크립트', required: false, completed: false },
  { id: '17', category: '자동화', text: 'LCSC 가격 자동 조회', required: false, completed: false },
  { id: '18', category: '문서화', text: '마이그레이션 가이드 작성', required: false, completed: false },
  { id: '19', category: '문서화', text: 'KiCad 사용 팁 정리', required: false, completed: false },
];

export default function MigrationChecklist() {
  const [items, setItems] = useState(initialChecklist);

  const toggle = (id: string) => {
    setItems((prev) => prev.map((item) => (item.id === id ? { ...item, completed: !item.completed } : item)));
  };

  const categories = [...new Set(items.map((i) => i.category))];
  const totalRequired = items.filter((i) => i.required).length;
  const completedRequired = items.filter((i) => i.required && i.completed).length;
  const totalCompleted = items.filter((i) => i.completed).length;

  return (
    <Card
      title="마이그레이션 체크리스트"
      subtitle={`전체 ${totalCompleted}/${items.length} 완료 | 필수 ${completedRequired}/${totalRequired} 완료`}
    >
      {/* Progress */}
      <div className="mb-5 h-2 rounded-full bg-surface-700">
        <div
          className="h-full rounded-full bg-primary-500 transition-all"
          style={{ width: `${(totalCompleted / items.length) * 100}%` }}
        />
      </div>

      <div className="space-y-5">
        {categories.map((category) => {
          const categoryItems = items.filter((i) => i.category === category);
          const catCompleted = categoryItems.filter((i) => i.completed).length;
          return (
            <div key={category}>
              <h4 className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-surface-400">
                {category}
                <span className="text-surface-500">({catCompleted}/{categoryItems.length})</span>
              </h4>
              <div className="space-y-1">
                {categoryItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => toggle(item.id)}
                    className="flex w-full items-start gap-3 rounded-lg p-2.5 text-left hover:bg-surface-700/50"
                  >
                    {item.completed ? (
                      <CheckCircle className="h-5 w-5 shrink-0 text-green-400 mt-0.5" />
                    ) : (
                      <Circle className="h-5 w-5 shrink-0 text-surface-500 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <span className={`text-sm ${item.completed ? 'text-surface-400 line-through' : 'text-surface-200'}`}>
                        {item.text}
                      </span>
                      {item.required && !item.completed && (
                        <span className="ml-2 inline-flex items-center gap-0.5 text-xs text-yellow-400">
                          <AlertTriangle className="h-3 w-3" />
                          필수
                        </span>
                      )}
                      {item.notes && <p className="mt-0.5 text-xs text-surface-500">{item.notes}</p>}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
