import { Folder, FolderOpen, FileText, FileCode, FileSpreadsheet } from 'lucide-react';
import { useState } from 'react';
import Card from '../shared/Card';

interface TreeNode {
  name: string;
  type: 'folder' | 'file';
  icon?: React.ElementType;
  children?: TreeNode[];
  description?: string;
}

const recommendedStructure: TreeNode[] = [
  {
    name: 'kicad-projects/',
    type: 'folder',
    children: [
      {
        name: 'libraries/',
        type: 'folder',
        description: '공유 라이브러리',
        children: [
          { name: 'symbols/', type: 'folder', children: [
            { name: 'LED_Drivers.kicad_sym', type: 'file', icon: FileCode, description: 'LED 드라이버 IC 심볼' },
            { name: 'Power_ICs.kicad_sym', type: 'file', icon: FileCode, description: '전원 IC 심볼' },
            { name: 'Connectors.kicad_sym', type: 'file', icon: FileCode, description: '커넥터 심볼' },
          ]},
          { name: 'footprints/', type: 'folder', children: [
            { name: 'LED_Drivers.pretty/', type: 'folder', description: 'LED 드라이버 풋프린트' },
            { name: 'Passives.pretty/', type: 'folder', description: '패시브 부품 풋프린트' },
            { name: 'LCSC_Custom.pretty/', type: 'folder', description: 'LCSC 커스텀 풋프린트' },
          ]},
          { name: '3d_models/', type: 'folder', description: '3D 모델 파일' },
        ],
      },
      {
        name: 'templates/',
        type: 'folder',
        description: '프로젝트 템플릿',
        children: [
          { name: 'led_driver_ac/', type: 'folder', description: 'AC LED 드라이버 템플릿' },
          { name: 'led_driver_dc/', type: 'folder', description: 'DC LED 드라이버 템플릿' },
          { name: 'sensor_module/', type: 'folder', description: '센서 모듈 템플릿' },
        ],
      },
      {
        name: 'projects/',
        type: 'folder',
        description: '실제 프로젝트',
        children: [
          {
            name: 'PRJ-2024-001_40W_Panel/',
            type: 'folder',
            children: [
              { name: '40W_Panel.kicad_pro', type: 'file', icon: FileCode, description: '프로젝트 파일' },
              { name: '40W_Panel.kicad_sch', type: 'file', icon: FileCode, description: '스키매틱' },
              { name: '40W_Panel.kicad_pcb', type: 'file', icon: FileCode, description: 'PCB 레이아웃' },
              { name: 'bom/', type: 'folder', children: [
                { name: 'bom.csv', type: 'file', icon: FileSpreadsheet },
              ]},
              { name: 'gerber/', type: 'folder', description: '제조 파일' },
              { name: 'docs/', type: 'folder', children: [
                { name: 'design_notes.md', type: 'file', icon: FileText },
              ]},
            ],
          },
        ],
      },
      {
        name: 'scripts/',
        type: 'folder',
        description: '자동화 스크립트',
        children: [
          { name: 'generate_bom.py', type: 'file', icon: FileCode, description: 'BoM 자동 생성' },
          { name: 'lcsc_mapper.py', type: 'file', icon: FileCode, description: 'LCSC 번호 매핑' },
          { name: 'drc_check.py', type: 'file', icon: FileCode, description: 'DRC 자동 검사' },
        ],
      },
    ],
  },
];

function TreeItem({ node, depth = 0 }: { node: TreeNode; depth?: number }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const isFolder = node.type === 'folder';
  const hasChildren = node.children && node.children.length > 0;
  const Icon = node.icon || (isFolder ? (expanded ? FolderOpen : Folder) : FileText);

  return (
    <div>
      <button
        onClick={() => isFolder && setExpanded(!expanded)}
        className={`flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-sm hover:bg-surface-700/50 ${
          isFolder ? 'cursor-pointer' : 'cursor-default'
        }`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        <Icon className={`h-4 w-4 shrink-0 ${isFolder ? 'text-primary-400' : 'text-surface-400'}`} />
        <span className={`${isFolder ? 'font-medium text-surface-200' : 'text-surface-300'}`}>{node.name}</span>
        {node.description && <span className="ml-2 text-xs text-surface-500">- {node.description}</span>}
      </button>
      {expanded && hasChildren && (
        <div>
          {node.children!.map((child, i) => (
            <TreeItem key={i} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function FolderStructure() {
  return (
    <Card title="추천 폴더 구조" subtitle="KiCad 프로젝트 관리를 위한 표준 폴더 구조">
      <div className="rounded-lg border border-surface-700 bg-surface-900 p-2">
        {recommendedStructure.map((node, i) => (
          <TreeItem key={i} node={node} />
        ))}
      </div>
      <div className="mt-4 rounded-lg bg-blue-900/20 p-3 text-xs text-blue-300">
        <p className="font-medium mb-1">팁:</p>
        <ul className="space-y-0.5 list-disc list-inside text-blue-400">
          <li>라이브러리는 프로젝트와 별도로 Git으로 관리하세요</li>
          <li>프로젝트 폴더명에 프로젝트 번호와 간략한 설명을 포함하세요</li>
          <li>제조 파일(거버)은 항상 별도 폴더에 저장하세요</li>
        </ul>
      </div>
    </Card>
  );
}
