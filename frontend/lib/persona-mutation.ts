/** Explicit retry/CAS state for session-gated record forms. */
import { ApiError } from "./api-client";
import { PersonaDisconnectedError } from "./persona-gateway";
import { ContractError } from "./persona-validation";

export type MutationFailure = {
  phase:
    | "retryable"
    | "conflict"
    | "denied"
    | "invalid"
    | "cancelled"
    | "failed"
    | "disconnected";
  message: string;
};
export type MutationCheckpoint<Command> = {
  intent: Command;
  state: MutationFailure;
  uncertain: boolean;
};
export type MutationState<Result> =
  | { phase: "idle" | "pending" }
  | { phase: "succeeded"; receipt: Result }
  | MutationFailure;

const cancelled = (): MutationFailure => ({
  phase: "cancelled",
  message:
    "Stopped waiting. The server may have committed this request; retry the same intent to resolve its outcome.",
});

function failure<Result>(error: unknown): MutationState<Result> {
  if (error instanceof PersonaDisconnectedError)
    return { phase: "disconnected", message: error.message };
  if (
    (error instanceof Error || error instanceof DOMException) &&
    error.name === "AbortError"
  )
    return cancelled();
  if (error instanceof ContractError)
    return {
      phase: "invalid",
      message:
        "The response could not be validated and the outcome is uncertain. Keep your draft; retry the same intent to resolve its outcome.",
    };
  if (error instanceof ApiError) {
    if (error.status === 409)
      return {
        phase: "conflict",
        message:
          "The server record changed. Keep your draft, load the latest version and review differences before saving a new intent.",
      };
    if (error.status === 401 || error.status === 403)
      return {
        phase: "denied",
        message:
          "Your session or permission no longer allows this action. Keep your draft and restore access.",
      };
    if (error.isRetryable)
      return {
        phase: "retryable",
        message:
          "The outcome is uncertain. Retry uses the same request ID and content to avoid a duplicate decision.",
      };
  }
  return {
    phase: "failed",
    message:
      "The request failed. Keep your draft and check the inputs before trying again.",
  };
}

export class PersonaMutation<Command extends { request_id: string }, Result> {
  private state: MutationState<Result> = { phase: "idle" };
  private controller: AbortController | null = null;
  private encoded: string | null = null;
  private generation = 0;
  private uncertain = false;
  constructor(
    private readonly send: (
      command: Command,
      signal: AbortSignal,
    ) => Promise<Result>,
    checkpoint?: MutationCheckpoint<Command>,
    private readonly validate?: (command: Command) => Command,
  ) {
    if (checkpoint) {
      this.encoded = JSON.stringify(checkpoint.intent);
      this.uncertain = checkpoint.uncertain;
      this.state =
        checkpoint.uncertain &&
        ["denied", "failed"].includes(checkpoint.state.phase)
          ? cancelled()
          : { ...checkpoint.state };
    }
  }

  get snapshot(): MutationState<Result> {
    return this.state;
  }
  get intent(): Command | null {
    return this.encoded === null ? null : (JSON.parse(this.encoded) as Command);
  }
  get requiresResolution(): boolean {
    return this.uncertain;
  }
  get canRetry(): boolean {
    return (
      this.uncertain &&
      this.state.phase !== "pending" &&
      this.state.phase !== "denied"
    );
  }
  get checkpoint(): MutationCheckpoint<Command> | null {
    const intent = this.intent;
    return intent && "message" in this.state
      ? { intent, state: { ...this.state }, uncertain: this.uncertain }
      : null;
  }

  async submit(command: Command): Promise<MutationState<Result>> {
    if (this.state.phase === "pending")
      throw new Error("A request is already pending.");
    if (this.uncertain)
      throw new Error("Resolve the existing intent before preparing another.");
    try {
      command = this.validate?.(command) ?? command;
    } catch {
      this.encoded = JSON.stringify(command);
      this.state = {
        phase: "invalid",
        message:
          "The write intent is invalid. Keep your draft and check the fields before submitting a new intent.",
      };
      return this.state;
    }
    this.encoded = JSON.stringify(command);
    return this.execute();
  }
  async retry(): Promise<MutationState<Result>> {
    if (!this.canRetry)
      throw new Error("This request needs review before retrying.");
    return this.execute();
  }
  cancel(): void {
    if (this.state.phase !== "pending") return;
    this.generation += 1;
    this.controller?.abort();
    this.controller = null;
    this.uncertain = true;
    this.state = cancelled();
  }
  reset(): void {
    if (this.uncertain || this.state.phase === "pending")
      throw new Error("Resolve the existing intent before preparing another.");
    this.encoded = null;
    this.state = { phase: "idle" };
  }

  private async execute(): Promise<MutationState<Result>> {
    const command = this.intent;
    if (command === null) throw new Error("No request to send.");
    this.state = { phase: "pending" };
    const controller = new AbortController();
    const generation = ++this.generation;
    this.controller = controller;
    try {
      const receipt = await this.send(command, controller.signal);
      if (generation !== this.generation) return cancelled();
      if (controller.signal.aborted)
        throw new DOMException("Cancelled", "AbortError");
      this.state = { phase: "succeeded", receipt };
      this.uncertain = false;
    } catch (error) {
      if (generation !== this.generation) return cancelled();
      this.uncertain = uncertainOutcome(error, this.uncertain);
      this.state = failure<Result>(error);
    } finally {
      if (generation === this.generation) this.controller = null;
    }
    return this.state;
  }
}

function uncertainOutcome(error: unknown, prior: boolean): boolean {
  if (error instanceof ApiError)
    return error.status === 409 ? false : prior || error.isRetryable;
  if (error instanceof PersonaDisconnectedError) return prior;
  return true;
}
