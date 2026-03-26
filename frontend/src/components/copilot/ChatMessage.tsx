import { User, Bot, AlertCircle, Paperclip } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '../../types/copilot';
import AgentIndicator from './AgentIndicator';
import AnalysisResult from './AnalysisResult';
import { formatRelativeTime } from '../../utils/formatters';

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex items-center gap-2 px-4 py-2">
        <AlertCircle className="h-4 w-4 shrink-0 text-yellow-400" />
        <span className="text-xs text-surface-400">{message.content}</span>
      </div>
    );
  }

  return (
    <div className={`flex gap-3 px-4 py-3 ${isUser ? '' : 'bg-surface-800/50'}`}>
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${isUser ? 'bg-primary-600' : 'bg-surface-600'}`}>
        {isUser ? <User className="h-4 w-4 text-white" /> : <Bot className="h-4 w-4 text-white" />}
      </div>
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-center gap-2">
          <span className="text-xs font-medium text-surface-300">
            {isUser ? '나' : 'AI 코파일럿'}
          </span>
          {message.agent && <AgentIndicator agent={message.agent} />}
          <span className="text-xs text-surface-500">{formatRelativeTime(message.timestamp)}</span>
        </div>

        {message.files && message.files.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-1.5">
            {message.files.map((f, i) => (
              <span key={i} className="inline-flex items-center gap-1 rounded-md bg-surface-700 px-2 py-1 text-xs text-surface-300">
                <Paperclip className="h-3 w-3" />
                {f.name}
              </span>
            ))}
          </div>
        )}

        <div className="text-sm leading-relaxed text-surface-200 whitespace-pre-wrap">
          {message.content}
        </div>

        {message.analysis && message.analysis.data && (
          <div className="mt-3">
            <AnalysisResult response={message.analysis} />
          </div>
        )}
      </div>
    </div>
  );
}
