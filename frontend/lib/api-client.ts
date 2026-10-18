/**
 * Typed HTTP client for the backend API.
 *
 * The backend enforces a consistent error contract; this is the browser half of it. Using
 * `fetch` directly at each call site is how a codebase ends up with a dozen slightly different
 * error-handling behaviours and no timeouts.
 *
 * Contract:
 *  - Non-2xx  -> throws `ApiError` (status + parsed body when JSON).
 *  - Timeout / network failure -> throws `ApiError` with status 0.
 *  - Retries **only idempotent methods** (GET/HEAD) and only on timeout, network failure, 429
 *    or 5xx. Retrying a POST is how you get duplicate writes, so it never happens implicitly —
 *    if a mutation is safe to retry, make it idempotent and call `request` again yourself.
 */

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(message: string, status: number, body: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }

  /** True when retrying the same request could plausibly succeed. */
  get isRetryable(): boolean {
    return this.status === 0 || this.status === 429 || this.status >= 500;
  }
}

export interface RequestOptions extends Omit<RequestInit, "body"> {
  /** JSON-serialisable request body. Sets Content-Type automatically. */
  json?: unknown;
  /** Abort after this many ms (default 10000). */
  timeoutMs?: number;
  /** Extra attempts for idempotent requests only (default 2, so 3 attempts total). */
  retries?: number;
}

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
const IDEMPOTENT = new Set(["GET", "HEAD"]);

function backoffMs(attempt: number): number {
  // 200ms, 400ms, 800ms... with jitter, so retries don't align across clients.
  return 2 ** attempt * 200 + Math.random() * 100;
}

async function responseBody<T>(response: Response): Promise<T> {
  const isJson =
    response.headers.get("content-type")?.includes("application/json") ?? false;
  const body: unknown = isJson ? await response.json() : await response.text();
  if (!response.ok)
    throw new ApiError(
      `${response.status} ${response.statusText}`,
      response.status,
      body,
    );
  return body as T;
}

function requestHeaders(
  headers: HeadersInit | undefined,
  hasJson: boolean,
): Headers {
  const result = new Headers(headers);
  if (!result.has("Accept")) result.set("Accept", "application/json");
  if (hasJson && !result.has("Content-Type"))
    result.set("Content-Type", "application/json");
  return result;
}

async function once<T>(path: string, options: RequestOptions): Promise<T> {
  // `retries` is consumed by request() below; strip it here so it never reaches fetch(),
  // without binding an unused name (which eslint flags, and the gate now fails on warnings).
  const { json, timeoutMs = 10_000, headers, signal, ...rest } = options;
  const init: Omit<typeof rest, "retries"> = rest;
  delete (init as { retries?: number }).retries;
  const controller = new AbortController();
  const cancel = () => controller.abort();
  if (signal?.aborted) throw new DOMException("Cancelled", "AbortError");
  signal?.addEventListener("abort", cancel, { once: true });
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: requestHeaders(headers, json !== undefined),
      ...(json !== undefined ? { body: JSON.stringify(json) } : {}),
    });

    return await responseBody<T>(response);
  } catch (error) {
    if (signal?.aborted) throw new DOMException("Cancelled", "AbortError");
    if (error instanceof ApiError) throw error;
    const reason = controller.signal.aborted ? "timeout" : "network";
    throw new ApiError(`Request failed (${reason}): ${path}`, 0);
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", cancel);
  }
}

export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const attempts = IDEMPOTENT.has(method) ? (options.retries ?? 2) + 1 : 1;

  let lastError: ApiError | undefined;
  for (let attempt = 0; attempt < attempts; attempt++) {
    if (options.signal?.aborted)
      throw new DOMException("Cancelled", "AbortError");
    try {
      return await once<T>(path, options);
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      lastError = error;
      if (!lastError.isRetryable || attempt === attempts - 1) throw lastError;
      await new Promise((resolve) => setTimeout(resolve, backoffMs(attempt)));
    }
  }
  throw lastError as ApiError;
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, json?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", json }),
  put: <T>(path: string, json?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PUT", json }),
  patch: <T>(path: string, json?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PATCH", json }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
};
