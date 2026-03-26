import { useState, useRef } from 'react';
import { Upload, X, FileText, Loader2 } from 'lucide-react';
import { formatFileSize } from '../../utils/formatters';

interface FileUploaderProps {
  accept?: string;
  multiple?: boolean;
  onUpload: (files: File[]) => Promise<void>;
  label?: string;
  description?: string;
}

export default function FileUploader({
  accept = '.xlsx,.xls,.csv,.json,.pdf,.txt,.kicad_sch,.kicad_pcb',
  multiple = false,
  onUpload,
  label = '파일 업로드',
  description = '파일을 드래그하거나 클릭하여 선택하세요',
}: FileUploaderProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (newFiles: FileList) => {
    const arr = Array.from(newFiles);
    setFiles(multiple ? (prev) => [...prev, ...arr] : arr);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    try {
      await onUpload(files);
      setFiles([]);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-3">
      <div
        className={`flex min-h-[140px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 transition-colors ${
          dragOver
            ? 'border-primary-500 bg-primary-600/10'
            : 'border-surface-600 bg-surface-800/30 hover:border-surface-500'
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <Upload className="mb-3 h-8 w-8 text-surface-400" />
        <p className="text-sm font-medium text-surface-300">{label}</p>
        <p className="mt-1 text-xs text-surface-500">{description}</p>
        <p className="mt-1 text-xs text-surface-600">지원 형식: {accept}</p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={(e) => e.target.files && handleFiles(e.target.files)}
        className="hidden"
      />

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file, i) => (
            <div key={i} className="flex items-center gap-3 rounded-lg border border-surface-700 bg-surface-800/50 p-3">
              <FileText className="h-5 w-5 shrink-0 text-primary-400" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-surface-200 truncate">{file.name}</p>
                <p className="text-xs text-surface-500">{formatFileSize(file.size)}</p>
              </div>
              <button onClick={() => removeFile(i)} className="rounded p-1 text-surface-400 hover:bg-surface-700 hover:text-surface-200">
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full rounded-lg bg-primary-600 py-2.5 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
          >
            {uploading ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                업로드 중...
              </span>
            ) : (
              `${files.length}개 파일 업로드`
            )}
          </button>
        </div>
      )}
    </div>
  );
}
