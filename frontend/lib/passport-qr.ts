/** Fixed QR Model 2 version 8 / L / mask 0, for ASCII share URLs up to 192 bytes.
 * Pattern and field arithmetic informed by Project Nayuki's MIT reference.
 * Attribution and licence: docs/hackathon/qr-notice.md. No network encoder or dependencies.
 */
const SIZE = 49;
function multiply(a: number, b: number): number {
  let value = 0;
  while (b) {
    if (b & 1) value ^= a;
    a <<= 1;
    if (a & 256) a ^= 0x11d;
    b >>>= 1;
  }
  return value;
}
function correction(data: number[]): number[] {
  let polynomial = [1],
    root = 1;
  for (let degree = 0; degree < 24; degree++) {
    const next = new Array(polynomial.length + 1).fill(0);
    polynomial.forEach((coefficient, index) => {
      next[index] ^= coefficient;
      next[index + 1] ^= multiply(coefficient, root);
    });
    polynomial = next;
    root = multiply(root, 2);
  }
  const dividend = [...data, ...new Array(24).fill(0)];
  for (let index = 0; index < data.length; index++) {
    const leading = dividend[index];
    polynomial.forEach((coefficient, offset) => {
      dividend[index + offset] ^= multiply(coefficient, leading);
    });
  }
  return dividend.slice(-24);
}
function codewords(value: string): number[] {
  if (!/^[\x20-\x7e]{1,192}$/.test(value))
    throw new Error("Share URL exceeds QR capacity");
  const bits: number[] = [];
  function append(number: number, count: number) {
    for (let bit = count - 1; bit >= 0; bit--) bits.push((number >>> bit) & 1);
  }
  append(4, 4);
  append(value.length, 8);
  for (const char of value) append(char.charCodeAt(0), 8);
  append(0, Math.min(4, 1552 - bits.length));
  while (bits.length % 8) bits.push(0);
  const bytes: number[] = [];
  for (let offset = 0; offset < bits.length; offset += 8)
    bytes.push(
      bits.slice(offset, offset + 8).reduce((sum, bit) => sum * 2 + bit, 0),
    );
  for (let pad = 0; bytes.length < 194; pad++)
    bytes.push(pad % 2 ? 0x11 : 0xec);
  const left = bytes.slice(0, 97),
    right = bytes.slice(97),
    eccLeft = correction(left),
    eccRight = correction(right);
  const result: number[] = [];
  left.forEach((byte, index) => result.push(byte, right[index]));
  eccLeft.forEach((byte, index) => result.push(byte, eccRight[index]));
  return result;
}
function functionPatterns(matrix: boolean[][], reserved: boolean[][]) {
  function set(x: number, y: number, dark: boolean) {
    if (x >= 0 && y >= 0 && x < SIZE && y < SIZE) {
      matrix[y][x] = dark;
      reserved[y][x] = true;
    }
  }
  for (let i = 0; i < SIZE; i++) {
    set(6, i, i % 2 === 0);
    set(i, 6, i % 2 === 0);
  }
  for (const [x, y] of [
    [3, 3],
    [45, 3],
    [3, 45],
  ])
    for (let dy = -4; dy <= 4; dy++)
      for (let dx = -4; dx <= 4; dx++) {
        const distance = Math.max(Math.abs(dx), Math.abs(dy));
        set(x + dx, y + dy, distance !== 2 && distance !== 4);
      }
  for (const x of [6, 24, 42])
    for (const y of [6, 24, 42]) {
      if ((x === 6 && [6, 42].includes(y)) || (x === 42 && y === 6)) continue;
      for (let dy = -2; dy <= 2; dy++)
        for (let dx = -2; dx <= 2; dx++)
          set(x + dx, y + dy, Math.max(Math.abs(dx), Math.abs(dy)) !== 1);
    }
  let remainder = 8;
  for (let i = 0; i < 10; i++)
    remainder = (remainder << 1) ^ ((remainder >>> 9) * 0x537);
  const format = ((8 << 10) | remainder) ^ 0x5412;
  const bit = (number: number, index: number) => ((number >>> index) & 1) !== 0;
  for (let i = 0; i < 6; i++) set(8, i, bit(format, i));
  set(8, 7, bit(format, 6));
  set(8, 8, bit(format, 7));
  set(7, 8, bit(format, 8));
  for (let i = 9; i < 15; i++) set(14 - i, 8, bit(format, i));
  for (let i = 0; i < 8; i++) set(SIZE - 1 - i, 8, bit(format, i));
  for (let i = 8; i < 15; i++) set(8, SIZE - 15 + i, bit(format, i));
  set(8, SIZE - 8, true);
  remainder = 8;
  for (let i = 0; i < 12; i++)
    remainder = (remainder << 1) ^ ((remainder >>> 11) * 0x1f25);
  const version = (8 << 12) | remainder;
  for (let i = 0; i < 18; i++) {
    const x = SIZE - 11 + (i % 3),
      y = Math.floor(i / 3);
    set(x, y, bit(version, i));
    set(y, x, bit(version, i));
  }
}
export function passportQr(value: string): boolean[][] {
  const bytes = codewords(value);
  const matrix = Array.from({ length: SIZE }, () =>
    new Array<boolean>(SIZE).fill(false),
  );
  const reserved = Array.from({ length: SIZE }, () =>
    new Array<boolean>(SIZE).fill(false),
  );
  functionPatterns(matrix, reserved);
  let index = 0;
  for (let right = SIZE - 1; right >= 1; right -= 2) {
    if (right === 6) right = 5;
    const upward = ((right + 1) & 2) === 0;
    for (let offset = 0; offset < SIZE; offset++) {
      const y = upward ? SIZE - 1 - offset : offset;
      for (let column = 0; column < 2; column++) {
        const x = right - column;
        if (!reserved[y][x]) {
          const dark =
            index < bytes.length * 8 &&
            ((bytes[index >>> 3] >>> (7 - (index & 7))) & 1) !== 0;
          matrix[y][x] = dark !== ((x + y) % 2 === 0);
          index++;
        }
      }
    }
  }
  if (index !== 1936) throw new Error("QR layout failed");
  return matrix;
}
