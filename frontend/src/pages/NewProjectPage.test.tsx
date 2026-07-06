import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { NewProjectPage } from "./NewProjectPage";
import { WorkflowPage } from "./WorkflowPage";

const intakeResponse = {
  extracted_facts: {
    amount: 800,
    currency: "MYR",
    deadline: null,
    missing_fields: ["deadline", "payment_terms"],
    payment_terms: null,
    project_title: "Poster design",
    revision_limit: 2,
    risk_flags: ["informal_platform"],
  },
  project: {
    amount: 800,
    client_name: null,
    created_at: "2026-07-06T10:42:21Z",
    currency: "MYR",
    deadline: null,
    dispute_flag: false,
    id: "3af1e770-20f6-4c9b-a7c7-4f22b9124d8f",
    invoice_due_date: null,
    source_platform: "Instagram",
    status: "DRAFT",
    title: "Poster design",
    updated_at: "2026-07-06T10:42:21Z",
  },
  trace: [
    {
      action: "route_intake",
      actor: "CoordinatorAgent",
      metadata: {},
      status: "SUCCEEDED",
      timestamp: "2026-07-06T10:42:21Z",
    },
    {
      action: "extract_project_facts",
      actor: "IntakeAgent",
      metadata: {},
      status: "SUCCEEDED",
      timestamp: "2026-07-06T10:42:21Z",
    },
  ],
};

const projectDetailResponse = {
  audit_summary: {
    event_count: 1,
    latest_action: "intake_analysed",
    latest_actor: "IntakeAgent",
    latest_event_at: "2026-07-06T10:42:21Z",
  },
  current_agreement: null,
  latest_draft: null,
  latest_policy: null,
  latest_trace: intakeResponse.trace,
  project: intakeResponse.project,
  timeline_summary: null,
};

const auditResponse = {
  events: [
    {
      action: "intake_analysed",
      actor: "IntakeAgent",
      created_at: "2026-07-06T10:42:21Z",
      id: "9c412fd4-2d24-4e7f-a2d9-75b3341f457f",
      metadata: { project_title: "Poster design" },
      project_id: intakeResponse.project.id,
    },
  ],
  project_id: intakeResponse.project.id,
};

const agreementResponse = {
  acceptance_message: 'Please reply: "I agree to Agreement FS-001 Version 1."',
  agreement: {
    acceptance_status: "PENDING",
    accepted_at: null,
    agreement_code: "FS-001",
    amount: 800,
    created_at: "2026-07-06T10:44:03Z",
    currency: "MYR",
    deadline: null,
    deliverables: "One final digital poster file.",
    id: "c6dbf17c-b729-44d6-9488-b3a350f60bf0",
    payment_terms: null,
    project_id: intakeResponse.project.id,
    revision_limit: 2,
    scope: "Design one promotional poster.",
    version_number: 1,
  },
  project_status: "ACCEPTANCE_PENDING",
  trace: [
    {
      action: "route_agreement",
      actor: "CoordinatorAgent",
      metadata: {},
      status: "SUCCEEDED",
      timestamp: "2026-07-06T10:44:03Z",
    },
    {
      action: "create_agreement_version",
      actor: "AgreementAgent",
      metadata: {},
      status: "SUCCEEDED",
      timestamp: "2026-07-06T10:44:03Z",
    },
  ],
};

const projectDetailWithAgreementResponse = {
  ...projectDetailResponse,
  current_agreement: agreementResponse.agreement,
  latest_trace: agreementResponse.trace,
  project: {
    ...intakeResponse.project,
    status: "ACCEPTANCE_PENDING",
  },
};

const acceptanceResponse = {
  acceptance_evidence: {
    content_hash: "36ae756a72ea4677b451f45f6b9d2855c2c0c1ac4be6deab2dc7b7a66ee11cc52",
    created_at: "2026-07-06T10:46:03Z",
    event_type: "ACCEPTANCE",
    id: "0a844b1c-9394-431e-a9f4-05136c44db8b",
    project_id: intakeResponse.project.id,
    summary: "I agree to Agreement FS-001 Version 1.",
  },
  agreement: {
    ...agreementResponse.agreement,
    acceptance_status: "ACCEPTED",
    accepted_at: "2026-07-06T10:46:03Z",
  },
  project_status: "ACCEPTED",
  trace: [
    {
      action: "record_acceptance",
      actor: "CoordinatorAgent",
      metadata: {},
      status: "SUCCEEDED",
      timestamp: "2026-07-06T10:46:03Z",
    },
  ],
};

const projectDetailAcceptedResponse = {
  ...projectDetailWithAgreementResponse,
  current_agreement: acceptanceResponse.agreement,
  latest_trace: acceptanceResponse.trace,
  project: {
    ...intakeResponse.project,
    status: "ACCEPTED",
  },
  timeline_summary: {
    event_count: 1,
    hash_previews: ["36ae75"],
    latest_event_at: "2026-07-06T10:46:03Z",
    latest_event_type: "ACCEPTANCE",
  },
};

const timelineResponse = {
  events: [
    {
      content_hash: acceptanceResponse.acceptance_evidence.content_hash,
      event_type: "ACCEPTANCE",
      reference_id: acceptanceResponse.acceptance_evidence.id,
      summary: acceptanceResponse.acceptance_evidence.summary,
      timestamp: acceptanceResponse.acceptance_evidence.created_at,
    },
  ],
  project_id: intakeResponse.project.id,
};

const deliveryEvidenceResponse = {
  evidence: {
    content_hash: "64be0102e09a41c1b61d68c4b3cb7df14598b52baf93c2a50d50b65ea75b5002",
    created_at: "2026-07-06T10:49:03Z",
    event_type: "DELIVERY",
    id: "d0d86299-2583-4ce0-aee1-c33f58449c88",
    project_id: intakeResponse.project.id,
    summary: "Synthetic poster delivery recorded.",
  },
  project_status: "DELIVERED",
  trace: [
    {
      action: "record_evidence",
      actor: "CoordinatorAgent",
      metadata: {},
      status: "SUCCEEDED",
      timestamp: "2026-07-06T10:49:03Z",
    },
  ],
};

const invoiceEvidenceResponse = {
  evidence: {
    content_hash: "895e58f190a84da0a817b94bde466cf22045fb5db102ca54d2321d98ac7420d4",
    created_at: "2026-07-06T10:50:03Z",
    event_type: "INVOICE",
    id: "907b74ef-2591-455e-a7ac-d4b82bf7ff53",
    project_id: intakeResponse.project.id,
    summary: "Synthetic invoice INV-DEMO-001 recorded.",
  },
  project_status: "INVOICED",
  trace: [
    {
      action: "record_evidence",
      actor: "CoordinatorAgent",
      metadata: {},
      status: "SUCCEEDED",
      timestamp: "2026-07-06T10:50:03Z",
    },
  ],
};

const projectDetailInvoicedResponse = {
  ...projectDetailAcceptedResponse,
  latest_trace: invoiceEvidenceResponse.trace,
  project: {
    ...intakeResponse.project,
    invoice_due_date: "2026-07-13",
    status: "INVOICED",
  },
  timeline_summary: {
    event_count: 3,
    hash_previews: ["36ae75", "64be01", "895e58"],
    latest_event_at: "2026-07-06T10:50:03Z",
    latest_event_type: "INVOICE",
  },
};

const followUpResponse = {
  draft: {
    audit_status: "APPROVED_TO_SHOW",
    body: "Thanks for raising your concern. Please identify the incomplete items so we can compare them with the agreed scope and discuss next steps.\n\nDraft only — review and send manually.",
    created_at: "2026-07-06T10:52:03Z",
    draft_type: "DISPUTE_CLARIFICATION",
    id: "724a9f6e-f6de-41fa-8f64-f8bb7a8da235",
    project_id: intakeResponse.project.id,
  },
  policy: {
    allowed_draft_type: "DISPUTE_CLARIFICATION",
    blocked_draft_types: ["PAYMENT_REMINDER"],
    reason_codes: ["PROJECT_DISPUTED"],
  },
  safety: {
    blocked: false,
    blocked_reasons: [],
    safe_to_show: true,
    warnings: ["Draft only — review and send manually."],
  },
  trace: [
    {
      action: "evaluate_follow_up_policy",
      actor: "FollowUpAgent",
      metadata: {},
      status: "SUCCEEDED",
      timestamp: "2026-07-06T10:52:03Z",
    },
    {
      action: "review_draft",
      actor: "SafetyAuditAgent",
      metadata: {},
      status: "SUCCEEDED",
      timestamp: "2026-07-06T10:52:03Z",
    },
  ],
};

const projectDetailAfterFollowUpResponse = {
  ...projectDetailInvoicedResponse,
  latest_draft: followUpResponse.draft,
  latest_policy: followUpResponse.policy,
  latest_trace: followUpResponse.trace,
  project: {
    ...projectDetailInvoicedResponse.project,
    dispute_flag: true,
    status: "DISPUTED",
    updated_at: "2026-07-06T10:52:03Z",
  },
};

const auditAfterFollowUpResponse = {
  events: [
    ...auditResponse.events,
    {
      action: "policy_evaluated",
      actor: "FollowUpAgent",
      created_at: "2026-07-06T10:52:03Z",
      id: "493d472c-77d7-4562-af4e-54d2bcaab049",
      metadata: {
        allowed_draft_type: "DISPUTE_CLARIFICATION",
        blocked_draft_types: ["PAYMENT_REMINDER"],
      },
      project_id: intakeResponse.project.id,
    },
    {
      action: "draft_approved_to_show",
      actor: "SafetyAuditAgent",
      created_at: "2026-07-06T10:52:03Z",
      id: "91b13719-1c64-4806-b2bb-2f2e6c6ef7d1",
      metadata: { draft_type: "DISPUTE_CLARIFICATION" },
      project_id: intakeResponse.project.id,
    },
  ],
  project_id: intakeResponse.project.id,
};

function renderWithQueryClient(children: React.ReactNode) {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({
          defaultOptions: { queries: { retry: false } },
        })
      }
    >
      {children}
    </QueryClientProvider>,
  );
}

describe("NewProjectPage", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("shows the intake workflow with safety context", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      json: async () => intakeResponse,
      ok: true,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithQueryClient(
      <MemoryRouter>
        <NewProjectPage />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { name: "New project intake" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("This app never sends messages or takes action on your behalf."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Analyse chat" })).toBeEnabled();
    expect(screen.getByText("No intake analysis yet.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Analyse chat" }));

    await waitFor(() =>
      expect(screen.getByText("Intake analysis completed")).toBeInTheDocument(),
    );

    expect(fetchMock).toHaveBeenCalledWith("/api/intake/analyse", {
      body: JSON.stringify({
        chat_text: "Need a poster by Friday. RM800. Two revisions.",
        source_platform: "Instagram",
      }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    expect(screen.getByText("Missing: deadline, payment terms")).toBeInTheDocument();
    expect(screen.getByText("Informal platform (Instagram)")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Create FS-001 V1" })).toHaveAttribute(
      "href",
      "/agreement/3af1e770-20f6-4c9b-a7c7-4f22b9124d8f",
    );
  });

  it("loads project data and creates Agreement FS-001 Version 1", async () => {
    const projectId = intakeResponse.project.id;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = input.toString();
      if (url === `/api/projects/${projectId}/audit`) {
        return { json: async () => auditResponse, ok: true };
      }
      if (url === `/api/projects/${projectId}`) {
        return { json: async () => projectDetailResponse, ok: true };
      }
      if (url === `/api/projects/${projectId}/agreements`) {
        return { json: async () => agreementResponse, ok: true };
      }
      return { json: async () => ({}), ok: false };
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithQueryClient(
      <MemoryRouter initialEntries={[`/agreement/${projectId}`]}>
        <Routes>
          <Route
            element={<WorkflowPage activeStep="agreement" />}
            path="/agreement/:projectId"
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() =>
      expect(screen.getByText("Agreement assistant")).toBeInTheDocument(),
    );
    expect(screen.getAllByText("Poster design").length).toBeGreaterThan(0);
    expect(screen.getByDisplayValue("800")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Create FS-001 V1" }));

    await waitFor(() =>
      expect(
        screen.getByText('Please reply: "I agree to Agreement FS-001 Version 1."'),
      ).toBeInTheDocument(),
    );
    expect(fetchMock).toHaveBeenCalledWith(`/api/projects/${projectId}/agreements`, {
      body: JSON.stringify({
        amount: 800,
        change_reason: null,
        currency: "MYR",
        deadline: null,
        deliverables: "One final digital poster file.",
        payment_terms: null,
        revision_limit: 2,
        scope: "Design one promotional poster.",
      }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    expect(
      screen.getByRole("link", { name: "Continue to acceptance" }),
    ).toHaveAttribute("href", `/acceptance/${projectId}`);
  });

  it("records exact agreement acceptance from backend agreement data", async () => {
    const projectId = intakeResponse.project.id;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = input.toString();
      if (url === `/api/projects/${projectId}/audit`) {
        return { json: async () => auditResponse, ok: true };
      }
      if (url === `/api/projects/${projectId}`) {
        return { json: async () => projectDetailWithAgreementResponse, ok: true };
      }
      if (url === `/api/projects/${projectId}/acceptance`) {
        return { json: async () => acceptanceResponse, ok: true };
      }
      return { json: async () => ({}), ok: false };
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithQueryClient(
      <MemoryRouter initialEntries={[`/acceptance/${projectId}`]}>
        <Routes>
          <Route
            element={<WorkflowPage activeStep="acceptance" />}
            path="/acceptance/:projectId"
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() =>
      expect(screen.getByText("Acceptance message")).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByRole("button", { name: "Record acceptance" }));

    await waitFor(() =>
      expect(
        screen.getByText("Acceptance recorded. Agreement code and version matched."),
      ).toBeInTheDocument(),
    );
    expect(fetchMock).toHaveBeenCalledWith(`/api/projects/${projectId}/acceptance`, {
      body: JSON.stringify({
        acceptance_text: "I agree to Agreement FS-001 Version 1.",
        agreement_code: "FS-001",
        version_number: 1,
      }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    expect(screen.getByText("Acceptance hash: 36ae756a")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Open evidence timeline" }),
    ).toHaveAttribute("href", `/evidence/${projectId}`);
  });

  it("records delivery and invoice evidence from accepted project data", async () => {
    const projectId = intakeResponse.project.id;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = input.toString();
      if (url === `/api/projects/${projectId}/audit`) {
        return { json: async () => auditResponse, ok: true };
      }
      if (url === `/api/projects/${projectId}/timeline`) {
        return { json: async () => timelineResponse, ok: true };
      }
      if (url === `/api/projects/${projectId}`) {
        return { json: async () => projectDetailAcceptedResponse, ok: true };
      }
      if (url === `/api/projects/${projectId}/evidence`) {
        const body = JSON.parse(init?.body as string);
        return {
          json: async () =>
            body.event_type === "DELIVERY"
              ? deliveryEvidenceResponse
              : invoiceEvidenceResponse,
          ok: true,
        };
      }
      return { json: async () => ({}), ok: false };
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithQueryClient(
      <MemoryRouter initialEntries={[`/evidence/${projectId}`]}>
        <Routes>
          <Route
            element={<WorkflowPage activeStep="evidence" />}
            path="/evidence/:projectId"
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() =>
      expect(screen.getByText("Chronological case file")).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByRole("button", { name: "Record delivery" }));
    await waitFor(() =>
      expect(
        screen.getByText("Synthetic poster delivery recorded."),
      ).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByRole("button", { name: "Create invoice" }));
    await waitFor(() =>
      expect(
        screen.getByText("Synthetic invoice INV-DEMO-001 recorded."),
      ).toBeInTheDocument(),
    );

    expect(fetchMock).toHaveBeenCalledWith(`/api/projects/${projectId}/evidence`, {
      body: JSON.stringify({
        event_type: "DELIVERY",
        invoice_due_date: null,
        summary: "Synthetic poster delivery recorded.",
      }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    expect(fetchMock).toHaveBeenCalledWith(`/api/projects/${projectId}/evidence`, {
      body: JSON.stringify({
        event_type: "INVOICE",
        invoice_due_date: "2026-07-13",
        summary: "Synthetic invoice INV-DEMO-001 recorded.",
      }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    expect(await screen.findByText(/sha:64be01/)).toBeInTheDocument();
    expect(await screen.findByText(/sha:895e58/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Run follow-up policy" })).toHaveAttribute(
      "href",
      `/follow-up/${projectId}`,
    );
  });

  it("requests dispute follow-up policy and renders the backend draft", async () => {
    const projectId = intakeResponse.project.id;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = input.toString();
      if (url === `/api/projects/${projectId}/audit`) {
        return { json: async () => auditResponse, ok: true };
      }
      if (url === `/api/projects/${projectId}`) {
        return { json: async () => projectDetailInvoicedResponse, ok: true };
      }
      if (url === `/api/projects/${projectId}/follow-up`) {
        return { json: async () => followUpResponse, ok: true };
      }
      return { json: async () => ({}), ok: false };
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithQueryClient(
      <MemoryRouter initialEntries={[`/follow-up/${projectId}`]}>
        <Routes>
          <Route
            element={<WorkflowPage activeStep="follow-up" />}
            path="/follow-up/:projectId"
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() =>
      expect(screen.getByText("Client dispute simulation")).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByRole("button", { name: "Simulate client dispute" }));

    await waitFor(() =>
      expect(screen.getByText("Payment reminder blocked")).toBeInTheDocument(),
    );

    expect(fetchMock).toHaveBeenCalledWith(`/api/projects/${projectId}/follow-up`, {
      body: JSON.stringify({
        dispute: {
          declared: true,
          message: "The poster is incomplete. I will not pay.",
        },
      }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    expect(screen.getByText("DISPUTE_CLARIFICATION allowed")).toBeInTheDocument();
    expect(screen.getByText("PAYMENT_REMINDER blocked")).toBeInTheDocument();
    expect(screen.getByText("Draft approved to show")).toBeInTheDocument();
    expect(screen.getByText(/Thanks for raising your concern/)).toBeInTheDocument();
    expect(screen.getAllByText("Draft only — review and send manually.").length).toBeGreaterThan(
      0,
    );
  });

  it("renders backend trace and append-only audit events", async () => {
    const projectId = intakeResponse.project.id;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = input.toString();
      if (url === `/api/projects/${projectId}/audit`) {
        return { json: async () => auditAfterFollowUpResponse, ok: true };
      }
      if (url === `/api/projects/${projectId}`) {
        return { json: async () => projectDetailAfterFollowUpResponse, ok: true };
      }
      return { json: async () => ({}), ok: false };
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithQueryClient(
      <MemoryRouter initialEntries={[`/audit/${projectId}`]}>
        <Routes>
          <Route
            element={<WorkflowPage activeStep="audit" />}
            path="/audit/:projectId"
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() =>
      expect(screen.getByText("Append-only audit trail")).toBeInTheDocument(),
    );

    expect(screen.getAllByText("FollowUpAgent").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Evaluate Follow Up Policy").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("SafetyAuditAgent Draft Approved To Show").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("Dispute blocks payment-demand wording")).toBeInTheDocument();
    expect(screen.getAllByText("VERIFIED").length).toBeGreaterThanOrEqual(2);
  });
});
