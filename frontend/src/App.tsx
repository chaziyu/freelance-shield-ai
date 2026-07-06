import { Navigate, Route, Routes } from "react-router-dom";

import { WorkflowPage } from "./pages/WorkflowPage";

export function App() {
  return (
    <Routes>
      <Route element={<Navigate replace to="/intake" />} path="/" />
      <Route element={<WorkflowPage activeStep="intake" />} path="/intake" />
      <Route
        element={<WorkflowPage activeStep="intake" />}
        path="/new-project"
      />
      <Route
        element={<WorkflowPage activeStep="agreement" />}
        path="/agreement/:projectId?"
      />
      <Route
        element={<WorkflowPage activeStep="acceptance" />}
        path="/acceptance/:projectId?"
      />
      <Route
        element={<WorkflowPage activeStep="evidence" />}
        path="/timeline/:projectId?"
      />
      <Route
        element={<WorkflowPage activeStep="evidence" />}
        path="/evidence/:projectId?"
      />
      <Route
        element={<WorkflowPage activeStep="follow-up" />}
        path="/follow-up/:projectId?"
      />
      <Route
        element={<WorkflowPage activeStep="audit" />}
        path="/audit/:projectId?"
      />
    </Routes>
  );
}
