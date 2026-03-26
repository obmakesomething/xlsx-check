import { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { parsersApi } from '../../api/parsers';
import type { FileUploadResult } from '../../types/common';
import Card from '../shared/Card';

export default function InterviewUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<FileUploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFileSelect = (f: File) => {
    setFile(f);
    setResult(null);
    setError(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFileSelect(f);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const res = await parsersApi.uploadInterview(file);
      setResult(res);
    } catch (err) {
      setError((err as Error).message || '업로드에 실패했습니다.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card title="인터뷰 녹취록 업로드" subtitle="아버지의 경험과 노하우를 AI가 분석합니다">
      <div
        className={`mb-4 flex min-h-[120px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 transition-colors ${
          dragOver
            ? 'border-primary-500 bg-primary-600/10'
            : 'border-surface-600 bg-surface-800/50 hover:border-surface-500'
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => {
          const input = document.createElement('input');
          input.type = 'file';
          input.accept = '.txt,.md,.pdf,.docx';
          input.onchange = (e) => {
            const f = (e.target as HTMLInputElement).files?.[0];
            if (f) handleFileSelect(f);
          };
          input.click();
        }}
      >
        <Upload className="mb-2 h-8 w-8 text-surface-400" />
        <p className="text-sm text-surface-300">파일을 드래그하거나 클릭하여 선택하세요</p>
        <p className="mt-1 text-xs text-surface-500">지원 형식: TXT, MD, PDF, DOCX</p>
      </div>

      {file && (
        <div className="mb-4 flex items-center gap-3 rounded-lg border border-surface-700 bg-surface-800/50 p-3">
          <FileText className="h-5 w-5 text-primary-400" />
          <div className="flex-1">
            <p className="text-sm text-surface-200">{file.name}</p>
            <p className="text-xs text-surface-500">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="rounded-lg bg-primary-600 px-4 py-1.5 text-xs font-medium text-white hover:bg-primary-700 disabled:opacity-50"
          >
            {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : '분석 시작'}
          </button>
        </div>
      )}

      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-900/20 p-3 text-sm text-red-300">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-green-400">
            <CheckCircle className="h-4 w-4" />
            분석 완료
          </div>
          {result.warnings.length > 0 && (
            <div className="rounded-lg bg-yellow-900/20 p-3">
              <p className="mb-1 text-xs font-medium text-yellow-300">주의사항:</p>
              <ul className="space-y-0.5 text-xs text-yellow-400">
                {result.warnings.map((w, i) => <li key={i}>- {w}</li>)}
              </ul>
            </div>
          )}
          <div className="rounded-lg border border-surface-700 bg-surface-800/50 p-3">
            <p className="mb-2 text-xs font-medium text-surface-300">추출된 데이터:</p>
            <pre className="text-xs text-surface-400 overflow-auto max-h-64">
              {JSON.stringify(result.parsed_data, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </Card>
  );
}
