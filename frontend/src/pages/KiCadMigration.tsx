import { useState } from 'react';
import MigrationRoadmap from '../components/migration/MigrationRoadmap';
import AssetInventory from '../components/migration/AssetInventory';
import FolderStructure from '../components/migration/FolderStructure';
import MigrationChecklist from '../components/migration/MigrationChecklist';

const TABS = [
  { id: 'roadmap', label: '12주 로드맵' },
  { id: 'inventory', label: '자산 인벤토리' },
  { id: 'checklist', label: '체크리스트' },
  { id: 'structure', label: '폴더 구조' },
] as const;

type TabId = (typeof TABS)[number]['id'];

export default function KiCadMigration() {
  const [activeTab, setActiveTab] = useState<TabId>('roadmap');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-surface-100">KiCad 마이그레이션</h1>
        <p className="mt-1 text-sm text-surface-400">
          기존 EDA 도구에서 KiCad로의 마이그레이션을 체계적으로 관리합니다
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-surface-700">
        <nav className="flex space-x-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-surface-800 text-primary-400 border-b-2 border-primary-400'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'roadmap' && <MigrationRoadmap />}
      {activeTab === 'inventory' && <AssetInventory />}
      {activeTab === 'checklist' && <MigrationChecklist />}
      {activeTab === 'structure' && <FolderStructure />}
    </div>
  );
}
