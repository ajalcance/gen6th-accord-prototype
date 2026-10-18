/** Read state stays in memory, clears old values and ignores late/cancelled responses. */
import { ApiError } from "./api-client";
import { PersonaDisconnectedError } from "./persona-gateway";
import { ContractError } from "./persona-validation";

export type QueryState<Result> =
  | { phase: "idle" }
  | { phase: "loading" }
  | { phase: "ready"; value: Result }
  | {
      phase:
        | "cancelled"
        | "denied"
        | "invalid"
        | "unavailable"
        | "disconnected"
        | "expired";
      message: string;
    };

function queryFailure<Result>(error: unknown): QueryState<Result> {
  if (error instanceof ApiError && error.status === 410)
    return {
      phase: "expired",
      message: "This query expired or was cleared. Prepare a new image query.",
    };
  if (error instanceof PersonaDisconnectedError)
    return {
      phase: "disconnected",
      message: "Saved records are not connected.",
    };
  if (error instanceof Error && error.name === "AbortError")
    return {
      phase: "cancelled",
      message: "Loading stopped. You can try again.",
    };
  if (error instanceof ContractError)
    return {
      phase: "invalid",
      message:
        "The response could not be validated. No records were displayed.",
    };
  if (
    error instanceof ApiError &&
    (error.status === 401 || error.status === 403)
  )
    return {
      phase: "denied",
      message:
        "Your session or workspace access is no longer available. Saved records were cleared.",
    };
  return {
    phase: "unavailable",
    message:
      "Saved records are temporarily unavailable. Try again when the connection is restored.",
  };
}

export class PersonaQuery<Result> {
  private state: QueryState<Result> = { phase: "idle" };
  private listeners = new Set<() => void>();
  private controller: AbortController | null = null;
  private generation = 0;
  private execute: ((signal: AbortSignal) => Promise<Result>) | null = null;
  readonly snapshot = (): QueryState<Result> => this.state;
  readonly subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };
  private publish(state: QueryState<Result>): void {
    this.state = state;
    this.listeners.forEach((listener) => listener());
  }
  async run(execute: (signal: AbortSignal) => Promise<Result>): Promise<void> {
    this.stop();
    this.execute = execute;
    const generation = this.generation;
    const controller = new AbortController();
    this.controller = controller;
    this.publish({ phase: "loading" });
    try {
      const value = await execute(controller.signal);
      if (generation !== this.generation || controller.signal.aborted) return;
      this.publish({ phase: "ready", value });
    } catch (error) {
      if (generation === this.generation && !controller.signal.aborted)
        this.publish(queryFailure(error));
    } finally {
      if (generation === this.generation) this.controller = null;
    }
  }
  retry(): Promise<void> {
    if (
      !this.execute ||
      this.state.phase === "loading" ||
      this.state.phase === "denied" ||
      this.state.phase === "expired" ||
      this.state.phase === "invalid"
    )
      throw new Error("This query needs a fresh request or restored access.");
    return this.run(this.execute);
  }
  cancel(): void {
    this.stop();
    this.publish({
      phase: "cancelled",
      message: "Loading stopped. You can try again.",
    });
  }
  clear(): void {
    this.stop();
    this.execute = null;
    this.publish({ phase: "idle" });
  }
  stop(): void {
    this.generation++;
    this.controller?.abort();
    this.controller = null;
  }
}
