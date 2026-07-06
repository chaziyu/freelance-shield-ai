import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { NewProjectPage } from "./NewProjectPage";

describe("NewProjectPage", () => {
  it("shows the safe inactive intake scaffold", () => {
    render(<NewProjectPage />);

    expect(
      screen.getByRole("heading", { name: "FreelanceShield AI" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Draft only — review and send manually\./),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Analyse Deal" })).toBeDisabled();
    expect(screen.getByText(/No trace yet\./)).toBeInTheDocument();
  });
});
