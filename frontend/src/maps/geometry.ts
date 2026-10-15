export type Coordinate = readonly [number, number]
export type Ring = readonly Coordinate[]

function onSegment(point: Coordinate, a: Coordinate, b: Coordinate): boolean {
  const cross = (point[0] - a[0]) * (b[1] - a[1]) - (point[1] - a[1]) * (b[0] - a[0])
  return Math.abs(cross) < 1e-12 &&
    point[0] >= Math.min(a[0], b[0]) && point[0] <= Math.max(a[0], b[0]) &&
    point[1] >= Math.min(a[1], b[1]) && point[1] <= Math.max(a[1], b[1])
}

export function containsPoint(point: Coordinate, rings: readonly Ring[]): boolean {
  let inside = false
  for (const ring of rings) {
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const a = ring[i]!
      const b = ring[j]!
      if (onSegment(point, a, b)) return true
      if ((a[1] > point[1]) !== (b[1] > point[1]) &&
        point[0] < (b[0] - a[0]) * (point[1] - a[1]) / (b[1] - a[1]) + a[0]) {
        inside = !inside
      }
    }
  }
  return inside
}

/** Stop at the first polygon edge along a movement, including concave edges. */
export function limitMovement(from: Coordinate, to: Coordinate, rings: readonly Ring[], margin = 0): Coordinate {
  const dx = to[0] - from[0]
  const dy = to[1] - from[1]
  if (dx === 0 && dy === 0) return from
  const crossings = [0, 1]
  for (const ring of rings) {
    for (let i = 0; i < ring.length; i++) {
      const a = ring[i]!
      const b = ring[(i + 1) % ring.length]!
      const ex = b[0] - a[0]
      const ey = b[1] - a[1]
      const denominator = dx * ey - dy * ex
      if (Math.abs(denominator) < 1e-15) continue
      const ax = a[0] - from[0]
      const ay = a[1] - from[1]
      const t = (ax * ey - ay * ex) / denominator
      const u = (ax * dy - ay * dx) / denominator
      if (t >= 0 && t <= 1 && u >= 0 && u <= 1) crossings.push(t)
    }
  }
  crossings.sort((a, b) => a - b)
  for (let i = 0; i < crossings.length - 1; i++) {
    const start = crossings[i]!
    const end = crossings[i + 1]!
    if (end - start < 1e-12) continue
    const middle = (start + end) / 2
    if (!containsPoint([from[0] + dx * middle, from[1] + dy * middle], rings)) {
      const stop = Math.max(0, start - Math.max(1e-7, margin / Math.hypot(dx, dy)))
      return [from[0] + dx * stop, from[1] + dy * stop]
    }
  }
  return to
}

export function intersectsRectangle(rings: readonly Ring[], box: readonly [number, number, number, number]): boolean {
  const [left, top, right, bottom] = box
  const corners: Coordinate[] = [[left, top], [right, top], [right, bottom], [left, bottom]]
  if (corners.some((p) => containsPoint(p, rings))) return true
  return rings.some((ring) => ring.some((a, i) => {
    const b = ring[(i + 1) % ring.length]!
    let start = 0
    let end = 1
    for (const axis of [0, 1] as const) {
      const delta = b[axis] - a[axis]
      if (delta === 0) {
        if (a[axis] < box[axis] || a[axis] > box[axis + 2]!) return false
      } else {
        const t1 = (box[axis] - a[axis]) / delta
        const t2 = (box[axis + 2]! - a[axis]) / delta
        start = Math.max(start, Math.min(t1, t2))
        end = Math.min(end, Math.max(t1, t2))
        if (start > end) return false
      }
    }
    return true
  }))
}
