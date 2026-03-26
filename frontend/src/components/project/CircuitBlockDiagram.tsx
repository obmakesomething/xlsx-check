import type { CircuitBlock } from '../../types/project';

interface CircuitBlockDiagramProps {
  blocks: CircuitBlock[];
}

const blockColors: Record<string, { fill: string; stroke: string; text: string }> = {
  input: { fill: '#1e3a5f', stroke: '#3b82f6', text: '#93c5fd' },
  converter: { fill: '#1e3a3a', stroke: '#14b8a6', text: '#5eead4' },
  driver: { fill: '#3b1e5f', stroke: '#8b5cf6', text: '#c4b5fd' },
  led: { fill: '#5f3b1e', stroke: '#f59e0b', text: '#fcd34d' },
  sensor: { fill: '#1e5f3b', stroke: '#22c55e', text: '#86efac' },
  communication: { fill: '#5f1e3b', stroke: '#ec4899', text: '#f9a8d4' },
  protection: { fill: '#5f1e1e', stroke: '#ef4444', text: '#fca5a5' },
  control: { fill: '#1e1e5f', stroke: '#6366f1', text: '#a5b4fc' },
};

export default function CircuitBlockDiagram({ blocks }: CircuitBlockDiagramProps) {
  if (blocks.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-surface-600 text-sm text-surface-500">
        회로 블록 다이어그램이 아직 생성되지 않았습니다.
        <br />
        AI 코파일럿에서 설계 초안을 요청하세요.
      </div>
    );
  }

  const svgWidth = 900;
  const svgHeight = 500;

  return (
    <div className="overflow-auto rounded-xl border border-surface-700 bg-surface-900 p-4">
      <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full" style={{ minWidth: '600px' }}>
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />
          </marker>
        </defs>

        {/* Draw connections */}
        {blocks.map((block) =>
          block.connections.map((targetId) => {
            const target = blocks.find((b) => b.id === targetId);
            if (!target) return null;
            const x1 = block.x + block.width;
            const y1 = block.y + block.height / 2;
            const x2 = target.x;
            const y2 = target.y + target.height / 2;
            const midX = (x1 + x2) / 2;
            return (
              <path
                key={`${block.id}-${targetId}`}
                d={`M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`}
                fill="none"
                stroke="#475569"
                strokeWidth="2"
                markerEnd="url(#arrowhead)"
              />
            );
          })
        )}

        {/* Draw blocks */}
        {blocks.map((block) => {
          const colors = blockColors[block.type] || blockColors.control;
          return (
            <g key={block.id}>
              <rect
                x={block.x}
                y={block.y}
                width={block.width}
                height={block.height}
                rx="8"
                fill={colors.fill}
                stroke={colors.stroke}
                strokeWidth="2"
              />
              <text
                x={block.x + block.width / 2}
                y={block.y + block.height / 2 - 8}
                textAnchor="middle"
                fill={colors.text}
                fontSize="13"
                fontWeight="600"
              >
                {block.name}
              </text>
              <text
                x={block.x + block.width / 2}
                y={block.y + block.height / 2 + 10}
                textAnchor="middle"
                fill="#94a3b8"
                fontSize="10"
              >
                {block.type.toUpperCase()}
              </text>
              {block.components.length > 0 && (
                <text
                  x={block.x + block.width / 2}
                  y={block.y + block.height - 10}
                  textAnchor="middle"
                  fill="#64748b"
                  fontSize="9"
                >
                  {block.components.slice(0, 3).join(', ')}
                  {block.components.length > 3 && ` +${block.components.length - 3}`}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
