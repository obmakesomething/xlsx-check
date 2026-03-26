import { CheckCircle, AlertTriangle, FileText } from 'lucide-react';
import type { FileUploadResult } from '../../types/common';
import Card from '../shared/Card';

interface ParseResultProps {
  result: FileUploadResult;
}

export default function ParseResult({ result }: ParseResultProps) {
  return (
    <Card>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-400/10 text-green-400">
            <CheckCircle className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-surface-100">파싱 완료</h3>
            <div className="flex items-center gap-2 text-xs text-surface-400">
              <FileText className="h-3 w-3" />
              {result.filename}
              <span className="text-surface-500">({result.file_type})</span>
            </div>
          </div>
        </div>

        {/* Warnings */}
        {result.warnings.length > 0 && (
          <div className="rounded-lg bg-yellow-900/20 p-3">
            <div className="mb-1 flex items-center gap-1.5 text-xs font-medium text-yellow-300">
              <AlertTriangle className="h-3.5 w-3.5" />
              주의사항 ({result.warnings.length})
            </div>
            <ul className="space-y-0.5 text-xs text-yellow-400">
              {result.warnings.map((w, i) => (
                <li key={i}>- {w}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Parsed Data */}
        <div className="rounded-lg border border-surface-700 bg-surface-900 p-3">
          <p className="mb-2 text-xs font-medium text-surface-300">파싱된 데이터</p>
          <pre className="max-h-80 overflow-auto text-xs text-surface-400">
            {JSON.stringify(result.parsed_data, null, 2)}
          </pre>
        </div>
      </div>
    </Card>
  );
}
