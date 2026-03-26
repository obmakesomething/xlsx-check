import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, Circle, ArrowRight } from 'lucide-react';
import SpecForm from '../components/project/SpecForm';
import { useProjectStore } from '../store/projectStore';
import { useCopilotStore } from '../store/copilotStore';
import { useUIStore } from '../store/uiStore';
import type { ProductSpec } from '../types/project';

const steps = [
  { id: 1, label: '기본 정보' },
  { id: 2, label: '제품 사양' },
  { id: 3, label: '검토 및 생성' },
];

export default function NewProject() {
  const navigate = useNavigate();
  const { createProject } = useProjectStore();
  const { sendMessage } = useCopilotStore();
  const { setCopilotOpen } = useUIStore();
  const [currentStep, setCurrentStep] = useState(1);
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [projectTags, setProjectTags] = useState('');
  const [spec, setSpec] = useState<ProductSpec | null>(null);
  const [creating, setCreating] = useState(false);

  const inputCls =
    'w-full rounded-lg border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-100 placeholder-surface-500 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500';
  const labelCls = 'block text-xs font-medium text-surface-300 mb-1.5';

  const handleStep1Next = () => {
    if (!projectName.trim()) return;
    setCurrentStep(2);
  };

  const handleSpecSubmit = (submittedSpec: ProductSpec) => {
    setSpec(submittedSpec);
    setCurrentStep(3);
  };

  const handleCreate = async () => {
    if (!spec) return;
    setCreating(true);
    try {
      const project = await createProject({
        name: projectName,
        description: projectDescription,
        spec,
      });
      // Auto-trigger design draft analysis
      sendMessage({
        message: `새 프로젝트 "${projectName}"에 대한 설계 초안을 작성해주세요. 스펙: ${JSON.stringify(spec)}`,
        taskType: 'design_draft',
        projectId: project.id,
      });
      setCopilotOpen(true);
      navigate(`/projects/${project.id}`);
    } catch {
      // If API unavailable, just navigate home
      navigate('/');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-surface-100">새 프로젝트 생성</h1>
        <p className="mt-1 text-sm text-surface-400">LED 제품 개발 프로젝트를 설정합니다</p>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center justify-center gap-2">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center">
            <button
              onClick={() => {
                if (step.id < currentStep) setCurrentStep(step.id);
              }}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                currentStep === step.id
                  ? 'bg-primary-600/20 text-primary-300 border border-primary-500/50'
                  : currentStep > step.id
                  ? 'text-green-400 cursor-pointer hover:bg-surface-800'
                  : 'text-surface-500'
              }`}
            >
              {currentStep > step.id ? (
                <CheckCircle className="h-4 w-4 text-green-400" />
              ) : (
                <Circle className={`h-4 w-4 ${currentStep === step.id ? 'text-primary-400' : 'text-surface-600'}`} />
              )}
              {step.label}
            </button>
            {index < steps.length - 1 && <ArrowRight className="mx-1 h-4 w-4 text-surface-600" />}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <div className="rounded-xl border border-surface-700 bg-surface-800/80 p-6">
        {/* Step 1: Basic Info */}
        {currentStep === 1 && (
          <div className="space-y-5">
            <h2 className="text-lg font-semibold text-surface-100">기본 정보</h2>
            <div>
              <label className={labelCls}>프로젝트 이름 *</label>
              <input
                type="text"
                className={inputCls}
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="예: 40W LED 패널라이트 드라이버"
              />
            </div>
            <div>
              <label className={labelCls}>프로젝트 설명</label>
              <textarea
                className={`${inputCls} min-h-[100px]`}
                value={projectDescription}
                onChange={(e) => setProjectDescription(e.target.value)}
                placeholder="프로젝트에 대한 간략한 설명을 입력하세요..."
                rows={4}
              />
            </div>
            <div>
              <label className={labelCls}>태그 (쉼표로 구분)</label>
              <input
                type="text"
                className={inputCls}
                value={projectTags}
                onChange={(e) => setProjectTags(e.target.value)}
                placeholder="예: 실내, DALI, 40W"
              />
            </div>
            <div className="flex justify-end pt-2">
              <button
                onClick={handleStep1Next}
                disabled={!projectName.trim()}
                className="rounded-lg bg-primary-600 px-6 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50 transition-colors"
              >
                다음
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Spec Form */}
        {currentStep === 2 && (
          <div className="space-y-5">
            <h2 className="text-lg font-semibold text-surface-100">제품 사양 입력</h2>
            <SpecForm
              initialValues={spec || undefined}
              onSubmit={handleSpecSubmit}
              onBack={() => setCurrentStep(1)}
            />
          </div>
        )}

        {/* Step 3: Review & Create */}
        {currentStep === 3 && (
          <div className="space-y-5">
            <h2 className="text-lg font-semibold text-surface-100">검토 및 생성</h2>

            {/* Basic Info Review */}
            <div className="rounded-lg border border-surface-700 bg-surface-900/50 p-4">
              <h3 className="mb-3 text-sm font-medium text-surface-300">기본 정보</h3>
              <div className="space-y-2 text-sm">
                <div className="flex">
                  <span className="w-32 shrink-0 text-surface-500">프로젝트명</span>
                  <span className="text-surface-200">{projectName}</span>
                </div>
                {projectDescription && (
                  <div className="flex">
                    <span className="w-32 shrink-0 text-surface-500">설명</span>
                    <span className="text-surface-200">{projectDescription}</span>
                  </div>
                )}
                {projectTags && (
                  <div className="flex">
                    <span className="w-32 shrink-0 text-surface-500">태그</span>
                    <div className="flex flex-wrap gap-1">
                      {projectTags.split(',').map((tag) => (
                        <span
                          key={tag.trim()}
                          className="rounded bg-surface-700 px-2 py-0.5 text-xs text-surface-300"
                        >
                          {tag.trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Spec Review */}
            {spec && (
              <div className="rounded-lg border border-surface-700 bg-surface-900/50 p-4">
                <h3 className="mb-3 text-sm font-medium text-surface-300">제품 사양</h3>
                <div className="grid grid-cols-1 gap-2 text-sm md:grid-cols-2">
                  <div className="flex">
                    <span className="w-28 shrink-0 text-surface-500">제품명</span>
                    <span className="text-surface-200">{spec.product_name}</span>
                  </div>
                  <div className="flex">
                    <span className="w-28 shrink-0 text-surface-500">입력 전압</span>
                    <span className="text-surface-200">{spec.input_voltage}</span>
                  </div>
                  <div className="flex">
                    <span className="w-28 shrink-0 text-surface-500">출력 전력</span>
                    <span className="text-surface-200">{spec.output_power}</span>
                  </div>
                  <div className="flex">
                    <span className="w-28 shrink-0 text-surface-500">LED 구성</span>
                    <span className="text-surface-200">{spec.led_config}</span>
                  </div>
                  {spec.cct_range && (
                    <div className="flex">
                      <span className="w-28 shrink-0 text-surface-500">CCT 범위</span>
                      <span className="text-surface-200">{spec.cct_range}</span>
                    </div>
                  )}
                  <div className="flex">
                    <span className="w-28 shrink-0 text-surface-500">디밍 방식</span>
                    <span className="text-surface-200">{spec.dimming_type}</span>
                  </div>
                  <div className="flex">
                    <span className="w-28 shrink-0 text-surface-500">통신 방식</span>
                    <span className="text-surface-200">{spec.communication_type}</span>
                  </div>
                  <div className="flex">
                    <span className="w-28 shrink-0 text-surface-500">센서</span>
                    <span className="text-surface-200">{spec.sensor_type}</span>
                  </div>
                </div>
                {spec.certifications.length > 0 && (
                  <div className="mt-3 flex items-start gap-2 text-sm">
                    <span className="w-28 shrink-0 text-surface-500">인증</span>
                    <div className="flex flex-wrap gap-1">
                      {spec.certifications.map((cert) => (
                        <span
                          key={cert}
                          className="rounded bg-primary-600/20 px-2 py-0.5 text-xs text-primary-300"
                        >
                          {cert.toUpperCase()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-between pt-2">
              <button
                onClick={() => setCurrentStep(2)}
                className="rounded-lg border border-surface-600 bg-surface-800 px-6 py-2 text-sm font-medium text-surface-300 hover:bg-surface-700 transition-colors"
              >
                이전
              </button>
              <button
                onClick={handleCreate}
                disabled={creating}
                className="rounded-lg bg-primary-600 px-8 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50 transition-colors"
              >
                {creating ? '생성 중...' : '프로젝트 생성'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
