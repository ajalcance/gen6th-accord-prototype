/** Runtime checks supplement TypeScript; invalid responses never become success state. */
export class ContractError extends Error {
  constructor() {
    super("The persona service returned an invalid response.");
    this.name = "ContractError";
  }
}
export function requireContract(condition: unknown): asserts condition {
  if (!condition) throw new ContractError();
}
export function object(
  value: unknown,
  keys: string[],
): Record<string, unknown> {
  requireContract(
    value !== null && typeof value === "object" && !Array.isArray(value),
  );
  const record = value as Record<string, unknown>;
  requireContract(
    Object.keys(record).length === keys.length &&
      keys.every((key) => Object.hasOwn(record, key)),
  );
  return record;
}
export function text(value: unknown, max: number): string {
  requireContract(typeof value === "string");
  const normalized = value.trim();
  requireContract(normalized.length > 0 && [...normalized].length <= max);
  return normalized;
}
export function uuid(value: unknown): string {
  requireContract(
    typeof value === "string" &&
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
        value,
      ),
  );
  return value.toLowerCase();
}
export function integer(value: unknown, minimum = 1): number {
  requireContract(
    typeof value === "number" &&
      Number.isSafeInteger(value) &&
      value >= minimum,
  );
  return value;
}
export function timestamp(value: unknown): string {
  requireContract(
    typeof value === "string" &&
      /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/.test(
        value,
      ),
  );
  requireContract(Number.isFinite(Date.parse(value)));
  const [year, month, day, hour, minute, second] = value
    .slice(0, 19)
    .split(/[-T:]/)
    .map(Number);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  requireContract(
    year >= 1 &&
      month >= 1 &&
      month <= 12 &&
      day >= 1 &&
      day <= days[month - 1] &&
      hour <= 23 &&
      minute <= 59 &&
      second <= 59,
  );
  return value;
}
export function choice<const T extends readonly string[]>(
  value: unknown,
  values: T,
): T[number] {
  requireContract(typeof value === "string" && values.includes(value));
  return value;
}
export function hex(value: unknown, length: number): string {
  requireContract(
    typeof value === "string" &&
      value.length === length &&
      /^[0-9a-f]+$/.test(value),
  );
  return value;
}
export function list<T>(
  value: unknown,
  parse: (item: unknown) => T,
  max: number,
  min = 0,
): T[] {
  requireContract(
    Array.isArray(value) && value.length >= min && value.length <= max,
  );
  return value.map(parse);
}
