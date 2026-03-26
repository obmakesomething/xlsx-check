import { Lightbulb, Shield, Zap, ThermometerSun, CircuitBoard, TestTube } from 'lucide-react';
import Card from '../shared/Card';

interface Principle {
  icon: React.ElementType;
  title: string;
  description: string;
  details: string[];
  color: string;
}

const principles: Principle[] = [
  {
    icon: Shield,
    title: '안전 설계 우선',
    description: '모든 LED 드라이버 설계에서 안전은 최우선 고려사항',
    details: [
      'KC 인증 기준 충족을 위한 절연 설계',
      '과전압/과전류 보호 회로 필수 적용',
      '열 퓨즈 및 NTC 적용',
      '입출력 분리 기준 준수 (강화 절연 > 3kV)',
    ],
    color: 'border-l-red-500',
  },
  {
    icon: ThermometerSun,
    title: '열 관리',
    description: '장수명 LED 제품을 위한 열 설계 원칙',
    details: [
      'LED 드라이버 IC의 Tjunction 여유 20% 이상 확보',
      '전해 콘덴서 주변 온도 관리 (105C 기준)',
      'MOSFET 방열 설계 시 Rth(j-a) 계산 필수',
      'PCB 구리 면적을 활용한 방열 설계',
    ],
    color: 'border-l-orange-500',
  },
  {
    icon: Zap,
    title: 'EMC 설계',
    description: '전자파 적합성을 위한 설계 가이드',
    details: [
      '입력 필터 (X-cap, Y-cap, CM choke) 적용',
      '스위칭 노드 면적 최소화',
      'GND 리턴 경로 최적화',
      '스너버 회로 적용으로 ringing 억제',
    ],
    color: 'border-l-purple-500',
  },
  {
    icon: CircuitBoard,
    title: 'PCB 레이아웃',
    description: '성능과 신뢰성을 위한 PCB 설계 원칙',
    details: [
      '전류 루프 면적 최소화',
      '고전압/저전압 영역 분리',
      'Kelvin 연결 적용 (전류 감지 저항)',
      '바이패스 콘덴서는 IC 핀 가까이 배치',
    ],
    color: 'border-l-green-500',
  },
  {
    icon: Lightbulb,
    title: '디밍 설계',
    description: 'LED 디밍 시 주의사항',
    details: [
      'TRIAC 디밍: Bleeder 회로 적용 (유지전류 확보)',
      '0-10V: 입력 임피던스 및 노이즈 필터링',
      'PWM 디밍: 주파수는 가시적 깜박임 이상 (>1kHz)',
      'Flicker Free 설계 (IEEE 1789 기준)',
    ],
    color: 'border-l-yellow-500',
  },
  {
    icon: TestTube,
    title: '시험 및 검증',
    description: '제품 출시 전 필수 검증 항목',
    details: [
      '서지 시험: IEC 61000-4-5 (1kV L-N, 2kV L-PE)',
      'EFT 시험: IEC 61000-4-4 (2kV)',
      '온도 사이클 시험: -40C ~ +85C',
      '수명 시험: 6000시간 (Ta=65C)',
    ],
    color: 'border-l-cyan-500',
  },
];

export default function DesignPrinciples() {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {principles.map((principle) => (
        <Card key={principle.title}>
          <div className={`-ml-5 -mt-5 -mb-5 border-l-4 ${principle.color} pl-5 py-5 pr-0`}>
            <div className="mb-3 flex items-center gap-2">
              <principle.icon className="h-5 w-5 text-primary-400" />
              <h3 className="text-sm font-semibold text-surface-100">{principle.title}</h3>
            </div>
            <p className="mb-3 text-xs text-surface-400">{principle.description}</p>
            <ul className="space-y-1.5">
              {principle.details.map((detail, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-surface-300">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary-400" />
                  {detail}
                </li>
              ))}
            </ul>
          </div>
        </Card>
      ))}
    </div>
  );
}
