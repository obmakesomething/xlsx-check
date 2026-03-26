import { useState } from 'react';
import { FileSpreadsheet, CircuitBoard, Package, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import Badge from '../shared/Badge';
import Card from '../shared/Card';

interface Asset {
  id: string;
  name: string;
  type: 'schematic' | 'pcb' | 'library' | 'bom' | 'gerber' | 'document';
  source_tool: string;
  migration_status: 'migrated' | 'in_progress' | 'pending' | 'not_needed';
  priority: 'high' | 'medium' | 'low';
  notes: string;
}

const sampleAssets: Asset[] = [
  { id: '1', name: '40W LED 드라이버 스키매틱', type: 'schematic', source_tool: 'OrCAD', migration_status: 'migrated', priority: 'high', notes: 'KiCad 변환 완료' },
  { id: '2', name: '40W LED 드라이버 PCB', type: 'pcb', source_tool: 'OrCAD', migration_status: 'in_progress', priority: 'high', notes: '레이아웃 검증 중' },
  { id: '3', name: 'LED 드라이버 IC 라이브러리', type: 'library', source_tool: 'OrCAD', migration_status: 'migrated', priority: 'high', notes: '자주 사용하는 IC 50종' },
  { id: '4', name: '패시브 부품 라이브러리', type: 'library', source_tool: 'OrCAD', migration_status: 'pending', priority: 'medium', notes: '0402~1206 기본 부품' },
  { id: '5', name: '100W 드라이버 BoM', type: 'bom', source_tool: 'Excel', migration_status: 'pending', priority: 'medium', notes: 'LCSC 매핑 필요' },
  { id: '6', name: '센서 모듈 스키매틱', type: 'schematic', source_tool: 'Altium', migration_status: 'pending', priority: 'low', notes: '' },
  { id: '7', name: '인증 관련 문서', type: 'document', source_tool: 'Various', migration_status: 'not_needed', priority: 'low', notes: 'PDF로 유지' },
];

const typeIcons: Record<string, React.ElementType> = {
  schematic: CircuitBoard,
  pcb: CircuitBoard,
  library: Package,
  bom: FileSpreadsheet,
  gerber: FileSpreadsheet,
  document: FileSpreadsheet,
};

const statusConfig: Record<string, { label: string; variant: 'success' | 'info' | 'warning' | 'default'; icon: React.ElementType }> = {
  migrated: { label: '이전 완료', variant: 'success', icon: CheckCircle },
  in_progress: { label: '이전 중', variant: 'info', icon: Clock },
  pending: { label: '대기', variant: 'warning', icon: AlertTriangle },
  not_needed: { label: '해당없음', variant: 'default' as never, icon: CheckCircle },
};

export default function AssetInventory() {
  const [assets] = useState<Asset[]>(sampleAssets);
  const [filterStatus, setFilterStatus] = useState<string>('');

  const filtered = assets.filter((a) => !filterStatus || a.migration_status === filterStatus);
  const counts = {
    total: assets.length,
    migrated: assets.filter((a) => a.migration_status === 'migrated').length,
    in_progress: assets.filter((a) => a.migration_status === 'in_progress').length,
    pending: assets.filter((a) => a.migration_status === 'pending').length,
  };

  return (
    <Card title="자산 인벤토리" subtitle={`총 ${counts.total}개 자산 | 이전 완료 ${counts.migrated} | 진행 중 ${counts.in_progress} | 대기 ${counts.pending}`}>
      <div className="mb-4 flex gap-2">
        {[
          { key: '', label: '전체' },
          { key: 'migrated', label: '이전 완료' },
          { key: 'in_progress', label: '이전 중' },
          { key: 'pending', label: '대기' },
        ].map((f) => (
          <button
            key={f.key}
            onClick={() => setFilterStatus(f.key)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              filterStatus === f.key ? 'bg-primary-600 text-white' : 'bg-surface-700 text-surface-300 hover:bg-surface-600'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto rounded-lg border border-surface-700">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-700 bg-surface-800/80 text-left text-xs text-surface-400">
              <th className="px-3 py-2.5">이름</th>
              <th className="px-3 py-2.5">유형</th>
              <th className="px-3 py-2.5">원본 도구</th>
              <th className="px-3 py-2.5">상태</th>
              <th className="px-3 py-2.5">우선순위</th>
              <th className="px-3 py-2.5">비고</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((asset) => {
              const Icon = typeIcons[asset.type] || FileSpreadsheet;
              const status = statusConfig[asset.migration_status];
              return (
                <tr key={asset.id} className="border-b border-surface-700/50 hover:bg-surface-800/50">
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4 text-surface-400" />
                      <span className="text-surface-200">{asset.name}</span>
                    </div>
                  </td>
                  <td className="px-3 py-2 text-surface-400">{asset.type}</td>
                  <td className="px-3 py-2 text-surface-400">{asset.source_tool}</td>
                  <td className="px-3 py-2">
                    <Badge variant={status.variant}>{status.label}</Badge>
                  </td>
                  <td className="px-3 py-2">
                    <Badge variant={asset.priority === 'high' ? 'error' : asset.priority === 'medium' ? 'warning' : 'info'}>
                      {asset.priority === 'high' ? '높음' : asset.priority === 'medium' ? '보통' : '낮음'}
                    </Badge>
                  </td>
                  <td className="px-3 py-2 text-xs text-surface-400">{asset.notes}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
