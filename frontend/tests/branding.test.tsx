import { readFileSync } from "node:fs";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ConnectedWorkspace from "../app/passport/connected-workspace";
import SignedOutWelcome from "../app/passport/signed-out-welcome";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("signed-out welcome", () => {
  it("names the product, shows the mark and offers sign-in", () => {
    const signIn = vi.fn();
    render(<SignedOutWelcome signIn={signIn} />);
    expect(
      screen.getByRole("region", { name: "Saved records connection" }),
    ).toBeDefined();
    expect(screen.getByRole("img", { name: "Gen6th Accord" })).toBeDefined();
    expect(screen.getByRole("heading", { level: 2 }).textContent).toContain(
      "registry",
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Sign in to your workspace" }),
    );
    expect(signIn).toHaveBeenCalledTimes(1);
  });
  it("does not offer a sign-in action it cannot run", () => {
    render(<SignedOutWelcome />);
    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.getByText(/not available right now/)).toBeDefined();
  });
});

describe("connected workspace first screen", () => {
  it("puts a sign-in action in the main area when sign-in is configured", async () => {
    const assign = vi.fn();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("{}", { status: 401 })),
    );
    vi.stubGlobal("location", {
      href: "https://accord.test/",
      origin: "https://accord.test",
      assign,
    });
    render(<ConnectedWorkspace enabled />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Sign in to your workspace" }),
    );
    expect(assign).toHaveBeenCalledWith("https://accord.test/api/auth/login");
  });
  it("shows the real mark beside the product name in the sidebar", () => {
    render(<ConnectedWorkspace enabled={false} />);
    const home = screen.getByRole("link", { name: "Accord home" });
    expect(home.textContent).toBe("Accord");
    expect(home.querySelector("img")?.getAttribute("src")).toContain(
      "gen6th-icon.svg",
    );
  });
});

describe("branding stylesheet", () => {
  const css = readFileSync("app/passport/branding.css", "utf8");
  it("fetches nothing outside our own origin and loads no font", () => {
    expect(css).not.toMatch(/https?:/);
    expect(css).not.toMatch(/@font-face|@import/);
    const urls = [...css.matchAll(/url\(["']?([^"')]+)/g)].map((m) => m[1]);
    expect(urls.length).toBeGreaterThan(0);
    for (const url of urls) expect(url).toMatch(/^\/brand\/[a-z0-9-]+\.svg$/);
  });
  it("turns the decorative backdrop off for high contrast and print", () => {
    expect(css).toMatch(/prefers-contrast: more[^{]*\{\s*\.welcome::before/);
    expect(css).toMatch(/prefers-contrast: more\), print/);
  });
});
