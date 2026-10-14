/**
 * Counter-based random numbers.
 *
 * Every random number the sampler uses is a pure function of
 *   (seed, person index, stream, k)
 * where `stream` identifies the model node (a hash of its id) and `k` numbers the draws
 * a node makes for one person. Nothing is stateful, so:
 *   - person #i is identical whether you draw 1 person or 150;
 *   - re-estimating one node never reshuffles another node's random numbers.
 *
 * The mixer is Chris Wellons' "lowbias32" integer hash, applied in a fixed chain.
 * It only uses 32-bit multiply/xor/shift, so it is trivial to reproduce exactly in any
 * language (pipeline/popsim/rng.py is the Python twin; both are checked against the
 * same test vectors). This is a simulation RNG, not a cryptographic one.
 */

const TWO_32 = 4294967296;
const TWO_53 = 9007199254740992;

export function lowbias32(x: number): number {
  x >>>= 0;
  x ^= x >>> 16;
  x = Math.imul(x, 0x7feb352d);
  x ^= x >>> 15;
  x = Math.imul(x, 0x846ca68b);
  x ^= x >>> 16;
  return x >>> 0;
}

/** FNV-1a 32-bit hash of a string (UTF-16 code units) — turns node ids into stream numbers. */
export function streamId(name: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < name.length; i++) {
    h ^= name.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

function chain(seedHi: number, seedLo: number, person: number, stream: number, k: number, salt: number): number {
  let h = lowbias32(salt ^ 0x9e3779b9);
  h = lowbias32(h ^ seedLo);
  h = lowbias32(h ^ seedHi);
  h = lowbias32(h ^ (person >>> 0));
  h = lowbias32(h ^ stream);
  h = lowbias32(h ^ (k >>> 0));
  return h;
}

/** Splits a non-negative integer seed (< 2^53) into two 32-bit words. */
export function splitSeed(seed: number): [number, number] {
  if (!Number.isSafeInteger(seed) || seed < 0) {
    throw new Error(`seed must be a non-negative safe integer, got ${seed}`);
  }
  return [Math.floor(seed / TWO_32) >>> 0, seed >>> 0];
}

/** Uniform double in [0, 1) with 53 random bits. */
export function uniform(seed: number, person: number, stream: number, k = 0): number {
  const [hi, lo] = splitSeed(seed);
  const a = chain(hi, lo, person, stream, k, 1) >>> 5; // 27 bits
  const b = chain(hi, lo, person, stream, k, 2) >>> 6; // 26 bits
  return (a * 67108864 + b) / TWO_53;
}

/**
 * Picks an index from non-negative integer weights by inverse CDF.
 * Integer weights (sums < 2^53) make the cumulative sums exact, so every
 * implementation picks the same index for the same u.
 */
export function pickIndex(cumulative: ArrayLike<number>, u: number): number {
  const total = cumulative[cumulative.length - 1];
  const target = Math.floor(u * total); // 0 <= target < total
  let lo = 0;
  let hi = cumulative.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (cumulative[mid] > target) hi = mid;
    else lo = mid + 1;
  }
  return lo;
}

export function cumulate(weights: ArrayLike<number>): Float64Array {
  const out = new Float64Array(weights.length);
  let s = 0;
  for (let i = 0; i < weights.length; i++) {
    const w = weights[i];
    if (!(w >= 0) || !Number.isInteger(w)) throw new Error(`weights must be non-negative integers, got ${w}`);
    s += w;
    out[i] = s;
  }
  if (s <= 0) throw new Error("all weights are zero");
  if (s > TWO_53) throw new Error("weights sum exceeds 2^53");
  return out;
}
