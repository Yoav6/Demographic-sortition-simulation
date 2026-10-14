/**
 * Seat positions for a hemicycle (parliament-style half circle).
 *
 * Rows sit on concentric half circles; each row gets seats in proportion to its length,
 * and seats are spaced evenly along it. Returned seats are ordered by angle from the
 * left end to the right end, so assigning people in a sorted order produces contiguous
 * coloured wedges, as in parliament diagrams.
 */

export interface Seat {
  x: number;
  y: number;
  row: number;
  angle: number; // radians, PI (left) .. 0 (right)
}

export function hemicycle(n: number, rows = 0, inner = 0.38): { seats: Seat[]; radius: number } {
  const R = rows || Math.max(3, Math.round(Math.sqrt(n / 3.2)));
  const radii = Array.from({ length: R }, (_, i) => inner + ((1 - inner) * (i + 0.5)) / R);
  const total = radii.reduce((a, r) => a + r, 0);
  // largest-remainder allocation of seats to rows
  const exact = radii.map((r) => (n * r) / total);
  const counts = exact.map(Math.floor);
  let left = n - counts.reduce((a, c) => a + c, 0);
  const order = exact.map((e, i) => [e - Math.floor(e), i] as const).sort((a, b) => b[0] - a[0]);
  for (let k = 0; left > 0; k++, left--) counts[order[k % R][1]]++;
  const seatRadius = (Math.PI * radii[R - 1]) / Math.max(counts[R - 1], 1) / 2.4;
  const seats: Seat[] = [];
  radii.forEach((r, row) => {
    const c = counts[row];
    for (let j = 0; j < c; j++) {
      const angle = c === 1 ? Math.PI / 2 : Math.PI - (Math.PI * j) / (c - 1);
      seats.push({ x: r * Math.cos(angle), y: r * Math.sin(angle), row, angle });
    }
  });
  seats.sort((a, b) => b.angle - a.angle || a.row - b.row);
  return { seats, radius: Math.min(seatRadius, ((1 - inner) / R) * 0.42) };
}
