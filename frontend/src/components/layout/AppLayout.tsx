import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import CopilotPanel from '../copilot/CopilotPanel';
import { useUIStore } from '../../store/uiStore';

export default function AppLayout() {
  const { sidebarCollapsed } = useUIStore();

  return (
    <div className="min-h-screen bg-surface-950">
      <Sidebar />
      <div className={`transition-all duration-300 ${sidebarCollapsed ? 'ml-16' : 'ml-60'}`}>
        <Header />
        <main className="p-6">
          <Outlet />
        </main>
      </div>
      <CopilotPanel />
    </div>
  );
}
