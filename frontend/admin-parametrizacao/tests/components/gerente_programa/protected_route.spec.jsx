import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ProtectedRoute from "../../../src/pages/ProtectedRoute";
import { ROUTES } from "../../../src/utils/routes";
import { registerCase } from "../../support/caseLog";

const { getTokenMock } = vi.hoisted(() => ({
  getTokenMock: vi.fn(),
}));

vi.mock("../../../src/utils/authStorage", () => ({
  default: {
    getToken: getTokenMock,
  },
}));

vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual,
    Navigate: ({ to }) => <div data-testid="redirect-target">{to}</div>,
    Outlet: () => <div data-testid="protected-outlet">Área protegida</div>,
  };
});

describe("Gerente de Programa - ProtectedRoute", () => {
  beforeEach(() => {
    getTokenMock.mockReset();
  });

  it("redireciona para login quando não há token", () => {
    getTokenMock.mockReturnValue(null);
    const caseLog = registerCase({
      input: {
        token: null,
      },
      expected: {
        redirectTo: ROUTES.LOGIN,
      },
    });

    render(<ProtectedRoute />);

    expect(screen.getByTestId("redirect-target")).toHaveTextContent(
      ROUTES.LOGIN,
    );

    caseLog.output = {
      redirectTarget: screen.getByTestId("redirect-target").textContent,
    };
  });

  it("renderiza o conteúdo interno quando o token existe", () => {
    getTokenMock.mockReturnValue("admin-token");
    const caseLog = registerCase({
      input: {
        token: "admin-token",
      },
      expected: {
        outletVisible: true,
      },
    });

    render(<ProtectedRoute />);

    expect(screen.getByTestId("protected-outlet")).toHaveTextContent(
      "Área protegida",
    );

    caseLog.output = {
      outletText: screen.getByTestId("protected-outlet").textContent,
    };
  });
});
