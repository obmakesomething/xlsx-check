import { useState } from 'react';
import { Plus } from 'lucide-react';
import Card from '../components/shared/Card';
import ComponentSearch from '../components/components/ComponentSearch';
import ComponentCard from '../components/components/ComponentCard';
import SubstituteTable from '../components/components/SubstituteTable';
import LCSCBrowser from '../components/components/LCSCBrowser';
import Modal from '../components/shared/Modal';
import type { Component, ComponentSearchParams, SubstitutePart } from '../types/component';

const mockComponents: Component[] = [
  { id: '1', name: 'BP2866BJ', category: 'IC - LED Driver', subcategory: 'Non-isolated Buck', manufacturer: 'BPS', part_number: 'BP2866BJ', lcsc_number: 'C94553', package_type: 'SOP-8', description: '비절연 Buck LED 드라이버, 높은 PF, THD < 15%', datasheet_url: '', unit_price: 0.45, moq: 10, stock: 50000, specifications: { 'Max Power': '20W', 'Input Voltage': '85-265VAC' }, tags: ['LED Driver', 'Non-isolated', 'Buck'], usage_count: 15, last_used: '2026-03-25T00:00:00Z', substitutes: [] },
  { id: '2', name: 'NCL30170DR2G', category: 'IC - LED Driver', subcategory: 'PFC Buck', manufacturer: 'ON Semiconductor', part_number: 'NCL30170DR2G', lcsc_number: 'C155387', package_type: 'SOP-8', description: 'PFC 내장 Buck LED 드라이버, TRIAC 디밍 호환', datasheet_url: '', unit_price: 1.20, moq: 1, stock: 15000, specifications: { 'Max Power': '25W', 'PFC': 'Yes' }, tags: ['LED Driver', 'PFC', 'TRIAC'], usage_count: 8, last_used: '2026-03-20T00:00:00Z', substitutes: [] },
  { id: '3', name: 'SM2082EG', category: 'IC - LED Driver', subcategory: 'Linear', manufacturer: 'Bright Power', part_number: 'SM2082EG', lcsc_number: 'C114246', package_type: 'SOP-8', description: '리니어 정전류 LED 드라이버, 저가형', datasheet_url: '', unit_price: 0.18, moq: 10, stock: 80000, specifications: { 'Max Current': '60mA', 'Channels': '1' }, tags: ['LED Driver', 'Linear', 'Low-cost'], usage_count: 22, last_used: '2026-03-22T00:00:00Z', substitutes: [] },
  { id: '4', name: 'ESP32-C3', category: 'IC - MCU', subcategory: 'WiFi+BLE', manufacturer: 'Espressif', part_number: 'ESP32-C3-MINI-1', lcsc_number: 'C2934560', package_type: 'Module', description: 'WiFi + BLE 5.0 SoC, RISC-V 코어', datasheet_url: '', unit_price: 1.50, moq: 1, stock: 25000, specifications: { 'Flash': '4MB', 'Core': 'RISC-V' }, tags: ['MCU', 'WiFi', 'BLE', 'Smart'], usage_count: 5, last_used: '2026-03-18T00:00:00Z', substitutes: [] },
  { id: '5', name: 'HLK-LD2410', category: 'Sensor', subcategory: 'Radar', manufacturer: 'HLK', part_number: 'HLK-LD2410', lcsc_number: '', package_type: 'Module', description: '24GHz mmWave 인체 감지 레이더 센서', datasheet_url: '', unit_price: 2.50, moq: 1, stock: 8000, specifications: { 'Frequency': '24GHz', 'Range': '5m' }, tags: ['Sensor', 'Radar', 'Occupancy'], usage_count: 3, last_used: '2026-03-15T00:00:00Z', substitutes: [] },
  { id: '6', name: 'nRF24L01+', category: 'IC - Communication', subcategory: 'RF', manufacturer: 'Nordic', part_number: 'nRF24L01+', lcsc_number: 'C8020', package_type: 'QFN-20', description: '2.4GHz RF 트랜시버', datasheet_url: '', unit_price: 0.85, moq: 1, stock: 30000, specifications: { 'Frequency': '2.4GHz', 'Data Rate': '2Mbps' }, tags: ['RF', '2.4GHz', 'Communication'], usage_count: 10, last_used: '2026-03-23T00:00:00Z', substitutes: [] },
];

const mockSubstitutes: SubstitutePart[] = [
  { id: 's1', part_number: 'BP2863J', manufacturer: 'BPS', lcsc_number: 'C3003468', compatibility: 92, price_diff: -0.05, unit_price: 0.40, stock: 45000, notes: '유사 성능, 약간 낮은 효율' },
  { id: 's2', part_number: 'SM2082D', manufacturer: 'Bright Power', lcsc_number: 'C114245', compatibility: 78, price_diff: -0.27, unit_price: 0.18, stock: 60000, notes: '리니어 방식, 효율 차이 있음' },
  { id: 's3', part_number: 'OB2532', manufacturer: 'On-Bright', lcsc_number: 'C127640', compatibility: 88, price_diff: 0.10, unit_price: 0.55, stock: 20000, notes: 'PFC 내장, 고효율' },
];

type ViewTab = 'components' | 'lcsc';

export default function ComponentDB() {
  const [components, setComponents] = useState<Component[]>(mockComponents);
  const [selectedComponent, setSelectedComponent] = useState<Component | null>(null);
  const [showSubstitutes, setShowSubstitutes] = useState(false);
  const [activeView, setActiveView] = useState<ViewTab>('components');

  const handleSearch = (params: ComponentSearchParams) => {
    let filtered = mockComponents;
    if (params.query) {
      const q = params.query.toLowerCase();
      filtered = filtered.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.part_number.toLowerCase().includes(q) ||
          c.description.toLowerCase().includes(q) ||
          c.manufacturer.toLowerCase().includes(q)
      );
    }
    if (params.category) filtered = filtered.filter((c) => c.category === params.category);
    if (params.manufacturer) filtered = filtered.filter((c) => c.manufacturer.toLowerCase().includes(params.manufacturer!.toLowerCase()));
    if (params.package_type) filtered = filtered.filter((c) => c.package_type === params.package_type);
    if (params.in_stock) filtered = filtered.filter((c) => c.stock > 0);
    setComponents(filtered);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-100">부품 데이터베이스</h1>
          <p className="mt-1 text-sm text-surface-400">LED 제품 개발에 사용되는 부품을 관리합니다</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border border-surface-700 bg-surface-800">
            <button
              onClick={() => setActiveView('components')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${activeView === 'components' ? 'bg-primary-600 text-white rounded-lg' : 'text-surface-400 hover:text-surface-200'}`}
            >
              내부 DB
            </button>
            <button
              onClick={() => setActiveView('lcsc')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${activeView === 'lcsc' ? 'bg-primary-600 text-white rounded-lg' : 'text-surface-400 hover:text-surface-200'}`}
            >
              LCSC 검색
            </button>
          </div>
          <button className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700">
            <Plus className="h-4 w-4" />
            부품 추가
          </button>
        </div>
      </div>

      {activeView === 'components' ? (
        <>
          <ComponentSearch onSearch={handleSearch} />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {components.map((comp) => (
              <ComponentCard
                key={comp.id}
                component={comp}
                onClick={() => {
                  setSelectedComponent(comp);
                  setShowSubstitutes(true);
                }}
              />
            ))}
          </div>
          {components.length === 0 && (
            <div className="text-center py-12 text-surface-500">검색 결과가 없습니다</div>
          )}
        </>
      ) : (
        <Card title="LCSC 부품 검색" subtitle="LCSC에서 부품을 검색하여 데이터베이스에 추가할 수 있습니다">
          <LCSCBrowser
            onSelect={(comp) => {
              console.log('Selected LCSC component:', comp);
            }}
          />
        </Card>
      )}

      <Modal
        open={showSubstitutes && !!selectedComponent}
        onClose={() => { setShowSubstitutes(false); setSelectedComponent(null); }}
        title={`대체 부품 - ${selectedComponent?.name || ''}`}
        size="xl"
      >
        {selectedComponent && (
          <div className="space-y-4">
            <div className="rounded-lg bg-surface-700/50 p-3 text-sm">
              <p className="text-surface-200">{selectedComponent.description}</p>
              <p className="mt-1 text-xs text-surface-400">
                {selectedComponent.manufacturer} | {selectedComponent.package_type} | {selectedComponent.lcsc_number}
              </p>
            </div>
            <SubstituteTable substitutes={mockSubstitutes} originalPartNumber={selectedComponent.part_number} />
          </div>
        )}
      </Modal>
    </div>
  );
}
