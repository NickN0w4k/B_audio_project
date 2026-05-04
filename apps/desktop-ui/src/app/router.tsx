import { HashRouter, Route, Routes } from 'react-router-dom'
import { Shell } from '../components/layout/Shell'
import { HomeScreen } from '../features/projects/HomeScreen'
import { AnalysisScreen } from '../features/analysis/AnalysisScreen'
import { RepairScreen } from '../features/repair/RepairScreen'
import { CompareScreen } from '../features/compare/CompareScreen'
import { ExportScreen } from '../features/export/ExportScreen'

export function Router() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<Shell />}>
          <Route index element={<HomeScreen />} />
          <Route path="/analysis/:projectId" element={<AnalysisScreen />} />
          <Route path="/repair/:projectId" element={<RepairScreen />} />
          <Route path="/compare/:projectId/run/:runId" element={<CompareScreen />} />
          <Route path="/export/:projectId/run/:runId" element={<ExportScreen />} />
        </Route>
      </Routes>
    </HashRouter>
  )
}
