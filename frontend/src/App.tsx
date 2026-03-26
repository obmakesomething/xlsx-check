import { Routes, Route } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import Dashboard from './pages/Dashboard';
import NewProject from './pages/NewProject';
import ProjectDetail from './pages/ProjectDetail';
import ComponentDB from './pages/ComponentDB';
import KnowledgeBase from './pages/KnowledgeBase';
import KiCadMigration from './pages/KiCadMigration';

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/projects/new" element={<NewProject />} />
        <Route path="/projects/:id" element={<ProjectDetail />} />
        <Route path="/components" element={<ComponentDB />} />
        <Route path="/knowledge" element={<KnowledgeBase />} />
        <Route path="/migration" element={<KiCadMigration />} />
      </Route>
    </Routes>
  );
}
