import { useState, useRef, type KeyboardEvent } from 'react';
import { Send, Paperclip, X } from 'lucide-react';
import type { TaskType } from '../../types/copilot';
import TaskTypeSelector from './TaskTypeSelector';

interface ChatInputProps {
  onSend: (message: string, taskType?: TaskType, files?: File[]) => void;
  loading?: boolean;
}

export default function ChatInput({ onSend, loading }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [taskType, setTaskType] = useState<TaskType | undefined>(undefined);
  const [showTaskTypes, setShowTaskTypes] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed && files.length === 0) return;
    onSend(trimmed, taskType, files.length > 0 ? files : undefined);
    setMessage('');
    setFiles([]);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="border-t border-surface-700 bg-surface-900 p-3">
      {showTaskTypes && (
        <div className="mb-2 rounded-lg bg-surface-800 p-2">
          <TaskTypeSelector value={taskType} onChange={(t) => { setTaskType(t); setShowTaskTypes(false); }} />
        </div>
      )}

      {files.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-1.5">
          {files.map((f, i) => (
            <span key={i} className="inline-flex items-center gap-1.5 rounded-lg bg-surface-700 px-2.5 py-1.5 text-xs text-surface-300">
              <Paperclip className="h-3 w-3" />
              {f.name}
              <button onClick={() => removeFile(i)} className="text-surface-400 hover:text-surface-200">
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2">
        <div className="flex gap-1">
          <button
            onClick={() => setShowTaskTypes(!showTaskTypes)}
            className={`rounded-lg p-2 text-sm transition-colors ${
              taskType ? 'bg-primary-600/20 text-primary-400' : 'text-surface-400 hover:bg-surface-800 hover:text-surface-200'
            }`}
            title="작업 유형 선택"
          >
            <span className="text-xs font-medium">{taskType ? 'T' : 'A'}</span>
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="rounded-lg p-2 text-surface-400 hover:bg-surface-800 hover:text-surface-200"
            title="파일 첨부"
          >
            <Paperclip className="h-4 w-4" />
          </button>
        </div>

        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="메시지를 입력하세요..."
          rows={1}
          className="flex-1 resize-none rounded-lg border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-100 placeholder-surface-500 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          style={{ maxHeight: '120px' }}
          onInput={(e) => {
            const el = e.currentTarget;
            el.style.height = 'auto';
            el.style.height = Math.min(el.scrollHeight, 120) + 'px';
          }}
        />

        <button
          onClick={handleSend}
          disabled={loading || (!message.trim() && files.length === 0)}
          className="rounded-lg bg-primary-600 p-2 text-white transition-colors hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileSelect}
        className="hidden"
        accept=".xlsx,.xls,.csv,.json,.kicad_sch,.kicad_pcb,.pdf,.txt,.md"
      />
    </div>
  );
}
