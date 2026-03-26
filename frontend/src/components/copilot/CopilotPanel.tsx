import { useRef, useEffect } from 'react';
import { X, Trash2, Sparkles } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';
import { useCopilotStore } from '../../store/copilotStore';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import AgentIndicator from './AgentIndicator';
import LoadingSpinner from '../shared/LoadingSpinner';

export default function CopilotPanel() {
  const { copilotOpen, setCopilotOpen } = useUIStore();
  const { messages, isLoading, currentAgent, sendMessage, clearMessages } = useCopilotStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <>
      {/* Backdrop */}
      {copilotOpen && (
        <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm lg:hidden" onClick={() => setCopilotOpen(false)} />
      )}

      {/* Panel */}
      <div
        className={`fixed right-0 top-0 z-50 flex h-screen w-full max-w-md flex-col border-l border-surface-700 bg-surface-900 shadow-2xl transition-transform duration-300 ${
          copilotOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-surface-700 px-4 py-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary-400" />
            <h2 className="text-sm font-semibold text-surface-100">AI 코파일럿</h2>
            {currentAgent && <AgentIndicator agent={currentAgent as never} active={isLoading} />}
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={clearMessages}
              className="rounded-lg p-1.5 text-surface-400 hover:bg-surface-800 hover:text-surface-200"
              title="대화 초기화"
            >
              <Trash2 className="h-4 w-4" />
            </button>
            <button
              onClick={() => setCopilotOpen(false)}
              className="rounded-lg p-1.5 text-surface-400 hover:bg-surface-800 hover:text-surface-200"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full px-6 text-center">
              <Sparkles className="h-10 w-10 text-primary-500/50 mb-4" />
              <h3 className="text-sm font-medium text-surface-300 mb-2">LED 제품 개발 AI 코파일럿</h3>
              <p className="text-xs text-surface-500 leading-relaxed">
                설계 초안, BoM 분석, 부품 검색, 인증 검토 등<br />
                LED 제품 개발에 관한 모든 질문을 해보세요.
              </p>
              <div className="mt-6 grid grid-cols-2 gap-2 w-full max-w-xs">
                {[
                  '설계 초안 작성',
                  'BoM 최적화',
                  '대체 부품 검색',
                  'KC 인증 검토',
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => sendMessage({ message: suggestion })}
                    className="rounded-lg border border-surface-700 bg-surface-800 px-3 py-2 text-xs text-surface-300 hover:border-primary-500/50 hover:text-surface-200 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div>
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}
              {isLoading && (
                <div className="px-4 py-6">
                  <LoadingSpinner size="sm" text="분석 중..." />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input */}
        <ChatInput
          onSend={(message, taskType, files) => sendMessage({ message, taskType, files })}
          loading={isLoading}
        />
      </div>
    </>
  );
}
