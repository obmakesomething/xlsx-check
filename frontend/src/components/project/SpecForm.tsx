import { useState } from 'react';
import type { ProductSpec } from '../../types/project';
import {
  DIMMING_TYPES,
  COMMUNICATION_TYPES,
  SENSOR_TYPES,
  CERTIFICATIONS_OPTIONS,
} from '../../utils/constants';

interface SpecFormProps {
  initialValues?: Partial<ProductSpec>;
  onSubmit: (spec: ProductSpec) => void;
  onBack?: () => void;
  loading?: boolean;
}

const defaultSpec: ProductSpec = {
  product_name: '',
  input_voltage: '',
  output_power: '',
  led_config: '',
  cct_range: '',
  dimming_type: 'none',
  communication_type: 'none',
  sensor_type: 'none',
  certifications: [],
  additional_notes: '',
};

export default function SpecForm({ initialValues, onSubmit, onBack, loading }: SpecFormProps) {
  const [spec, setSpec] = useState<ProductSpec>({ ...defaultSpec, ...initialValues });

  const update = <K extends keyof ProductSpec>(key: K, value: ProductSpec[K]) => {
    setSpec((prev) => ({ ...prev, [key]: value }));
  };

  const toggleCert = (value: string) => {
    setSpec((prev) => ({
      ...prev,
      certifications: prev.certifications.includes(value)
        ? prev.certifications.filter((c) => c !== value)
        : [...prev.certifications, value],
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(spec);
  };

  const inputCls = 'w-full rounded-lg border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-100 placeholder-surface-500 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500';
  const labelCls = 'block text-xs font-medium text-surface-300 mb-1.5';

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <div>
          <label className={labelCls}>제품명 *</label>
          <input type="text" className={inputCls} value={spec.product_name} onChange={(e) => update('product_name', e.target.value)} placeholder="예: 40W LED 패널라이트 드라이버" required />
        </div>
        <div>
          <label className={labelCls}>입력 전압 *</label>
          <input type="text" className={inputCls} value={spec.input_voltage} onChange={(e) => update('input_voltage', e.target.value)} placeholder="예: AC 220V, DC 24V" required />
        </div>
        <div>
          <label className={labelCls}>출력 전력 *</label>
          <input type="text" className={inputCls} value={spec.output_power} onChange={(e) => update('output_power', e.target.value)} placeholder="예: 40W" required />
        </div>
        <div>
          <label className={labelCls}>LED 구성 *</label>
          <input type="text" className={inputCls} value={spec.led_config} onChange={(e) => update('led_config', e.target.value)} placeholder="예: 2835 x 120ea, 직렬 12 x 병렬 10" required />
        </div>
        <div>
          <label className={labelCls}>CCT 범위</label>
          <input type="text" className={inputCls} value={spec.cct_range} onChange={(e) => update('cct_range', e.target.value)} placeholder="예: 3000K ~ 6500K (Tunable White)" />
        </div>

        <div>
          <label className={labelCls}>디밍 방식</label>
          <select className={inputCls} value={spec.dimming_type} onChange={(e) => update('dimming_type', e.target.value)}>
            {DIMMING_TYPES.map((dt) => (
              <option key={dt.value} value={dt.value}>{dt.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelCls}>통신 방식</label>
          <select className={inputCls} value={spec.communication_type} onChange={(e) => update('communication_type', e.target.value)}>
            {COMMUNICATION_TYPES.map((ct) => (
              <option key={ct.value} value={ct.value}>{ct.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelCls}>센서 종류</label>
          <select className={inputCls} value={spec.sensor_type} onChange={(e) => update('sensor_type', e.target.value)}>
            {SENSOR_TYPES.map((st) => (
              <option key={st.value} value={st.value}>{st.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className={labelCls}>필요 인증</label>
        <div className="flex flex-wrap gap-2">
          {CERTIFICATIONS_OPTIONS.map((cert) => (
            <button
              key={cert.value}
              type="button"
              onClick={() => toggleCert(cert.value)}
              className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                spec.certifications.includes(cert.value)
                  ? 'border-primary-500 bg-primary-600/20 text-primary-300'
                  : 'border-surface-600 bg-surface-800 text-surface-400 hover:border-surface-500'
              }`}
            >
              {cert.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className={labelCls}>추가 요구사항</label>
        <textarea
          className={`${inputCls} min-h-[80px]`}
          value={spec.additional_notes || ''}
          onChange={(e) => update('additional_notes', e.target.value)}
          placeholder="기타 요구사항, 참조 제품, 특별 조건 등을 입력하세요..."
          rows={3}
        />
      </div>

      <div className="flex justify-between pt-2">
        {onBack && (
          <button type="button" onClick={onBack} className="rounded-lg border border-surface-600 bg-surface-800 px-6 py-2 text-sm font-medium text-surface-300 hover:bg-surface-700">
            이전
          </button>
        )}
        <button type="submit" disabled={loading} className="ml-auto rounded-lg bg-primary-600 px-6 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50">
          {loading ? '처리 중...' : '다음'}
        </button>
      </div>
    </form>
  );
}
