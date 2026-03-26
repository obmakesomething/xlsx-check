import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderPlus,
  Cpu,
  BookOpen,
  ArrowRightLeft,
  ChevronLeft,
  ChevronRight,
  Lightbulb,
} from 'lucide-react';
import { useUIStore } from '../../store/uiStore';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '대시보드' },
  { to: '/projects/new', icon: FolderPlus, label: '새 프로젝트' },
  { to: '/components', icon: Cpu, label: '부품 데이터베이스' },
  { to: '/knowledge', icon: BookOpen, label: '지식 베이스' },
  { to: '/migration', icon: ArrowRightLeft, label: 'KiCad 마이그레이션' },
];

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  return (
    <aside
      className={`fixed left-0 top-0 z-30 flex h-screen flex-col border-r border-surface-700 bg-surface-900 transition-all duration-300 ${
        sidebarCollapsed ? 'w-16' : 'w-60'
      }`}
    >
      <div className="flex h-16 items-center gap-3 border-b border-surface-700 px-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary-600">
          <Lightbulb className="h-5 w-5 text-white" />
        </div>
        {!sidebarCollapsed && (
          <span className="text-lg font-bold text-surface-100">LED Copilot</span>
        )}
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-600/20 text-primary-300'
                  : 'text-surface-400 hover:bg-surface-800 hover:text-surface-200'
              }`
            }
          >
            <item.icon className="h-5 w-5 shrink-0" />
            {!sidebarCollapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <button
        onClick={toggleSidebar}
        className="flex h-12 items-center justify-center border-t border-surface-700 text-surface-400 hover:bg-surface-800 hover:text-surface-200"
      >
        {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
      </button>
    </aside>
  );
}
