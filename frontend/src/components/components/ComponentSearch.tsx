import { useState } from 'react';
import { Search, Filter, X } from 'lucide-react';
import { COMPONENT_CATEGORIES, PACKAGE_TYPES } from '../../types/component';
import type { ComponentSearchParams } from '../../types/component';

interface ComponentSearchProps {
  onSearch: (params: ComponentSearchParams) => void;
  loading?: boolean;
}

export default function ComponentSearch({ onSearch, loading }: ComponentSearchProps) {
  const [query, setQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [category, setCategory] = useState('');
  const [manufacturer, setManufacturer] = useState('');
  const [packageType, setPackageType] = useState('');
  const [inStock, setInStock] = useState(false);

  const handleSearch = () => {
    onSearch({
      query: query || undefined,
      category: category || undefined,
      manufacturer: manufacturer || undefined,
      package_type: packageType || undefined,
      in_stock: inStock || undefined,
    });
  };

  const clearFilters = () => {
    setCategory('');
    setManufacturer('');
    setPackageType('');
    setInStock(false);
  };

  const selectCls = 'rounded-lg border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-100 focus:border-primary-500 focus:outline-none';

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-surface-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="부품명, 부품번호, LCSC 번호로 검색..."
            className="w-full rounded-lg border border-surface-600 bg-surface-800 py-2 pl-9 pr-3 text-sm text-surface-100 placeholder-surface-500 focus:border-primary-500 focus:outline-none"
          />
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
            showFilters ? 'border-primary-500 bg-primary-600/20 text-primary-300' : 'border-surface-600 bg-surface-800 text-surface-300 hover:border-surface-500'
          }`}
        >
          <Filter className="h-4 w-4" />
          필터
        </button>
        <button
          onClick={handleSearch}
          disabled={loading}
          className="rounded-lg bg-primary-600 px-6 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
        >
          검색
        </button>
      </div>

      {showFilters && (
        <div className="rounded-lg border border-surface-700 bg-surface-800/50 p-4">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-xs font-medium text-surface-300">필터 옵션</span>
            <button onClick={clearFilters} className="flex items-center gap-1 text-xs text-surface-400 hover:text-surface-200">
              <X className="h-3 w-3" />
              초기화
            </button>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="mb-1 block text-xs text-surface-400">카테고리</label>
              <select className={selectCls} value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="">전체</option>
                {COMPONENT_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-surface-400">제조사</label>
              <input
                type="text"
                value={manufacturer}
                onChange={(e) => setManufacturer(e.target.value)}
                placeholder="제조사명"
                className={selectCls}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-surface-400">패키지</label>
              <select className={selectCls} value={packageType} onChange={(e) => setPackageType(e.target.value)}>
                <option value="">전체</option>
                {PACKAGE_TYPES.map((pkg) => (
                  <option key={pkg} value={pkg}>{pkg}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 text-sm text-surface-300">
                <input
                  type="checkbox"
                  checked={inStock}
                  onChange={(e) => setInStock(e.target.checked)}
                  className="h-4 w-4 rounded border-surface-600 bg-surface-700 text-primary-500 focus:ring-primary-500"
                />
                재고 있는 부품만
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
