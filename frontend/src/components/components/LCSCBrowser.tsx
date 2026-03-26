import { useState } from 'react';
import { Search, ExternalLink, ShoppingCart, Loader2 } from 'lucide-react';
import type { LCSCComponent } from '../../types/component';
import { formatCurrency } from '../../utils/formatters';

interface LCSCBrowserProps {
  onSelect?: (component: LCSCComponent) => void;
}

export default function LCSCBrowser({ onSelect }: LCSCBrowserProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<LCSCComponent[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const { componentsApi } = await import('../../api/components');
      const res = await componentsApi.searchLCSC(query.trim());
      setResults(res.items);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-surface-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="LCSC 부품 검색 (예: TPS54331, C15850)..."
            className="w-full rounded-lg border border-surface-600 bg-surface-800 py-2 pl-9 pr-3 text-sm text-surface-100 placeholder-surface-500 focus:border-primary-500 focus:outline-none"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={loading}
          className="rounded-lg bg-primary-600 px-6 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'LCSC 검색'}
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary-400" />
        </div>
      ) : results.length > 0 ? (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {results.map((comp) => (
            <div key={comp.lcsc_number} className="rounded-lg border border-surface-700 bg-surface-800/50 p-4">
              <div className="mb-2 flex items-start gap-3">
                {comp.image_url && (
                  <img src={comp.image_url} alt={comp.name} className="h-12 w-12 rounded-lg border border-surface-600 bg-white object-contain p-1" />
                )}
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-surface-100 truncate">{comp.name}</h4>
                  <p className="text-xs text-surface-400">{comp.manufacturer}</p>
                </div>
              </div>
              <p className="mb-2 text-xs text-surface-400 line-clamp-2">{comp.description}</p>
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <span className="text-surface-300">{comp.package}</span>
                  <span className="font-medium text-primary-400">{formatCurrency(comp.price)}</span>
                  <span className={comp.stock > 0 ? 'text-green-400' : 'text-red-400'}>
                    재고: {comp.stock > 0 ? comp.stock.toLocaleString() : '없음'}
                  </span>
                </div>
                <div className="flex gap-1">
                  {comp.datasheet_url && (
                    <a href={comp.datasheet_url} target="_blank" rel="noopener noreferrer" className="rounded p-1 text-surface-400 hover:bg-surface-700 hover:text-surface-200">
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                  {onSelect && (
                    <button
                      onClick={() => onSelect(comp)}
                      className="rounded p-1 text-primary-400 hover:bg-primary-600/20"
                    >
                      <ShoppingCart className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : searched ? (
        <p className="text-center text-sm text-surface-500 py-8">검색 결과가 없습니다.</p>
      ) : null}
    </div>
  );
}
