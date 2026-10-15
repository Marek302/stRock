import { point, type Draggable, type Map, type Point } from 'leaflet'
import { limitMovement, type Ring } from './geometry'
import { saintRochRings } from './saintRoch'

// Leaflet 1.9 exposes predrag, but its pending pane position is an internal field.
// Keep this adapter isolated so the position is limited BEFORE the pane moves.
type PendingDrag = Draggable & { _newPos: Point; _startPos: Point }

export function constrainMovement(map: Map): () => void {
  const draggable = (map.dragging as typeof map.dragging & { _draggable: PendingDrag })._draggable
  const projectRings = (): Ring[] => saintRochRings.map((ring) => ring.map(([lng, lat]) => {
    const p = map.project([lat, lng])
    return [p.x, p.y] as const
  }))
  let dragRings: Ring[] = []
  let origin = point(0, 0)
  let previous = origin
  const startDrag = () => {
    dragRings = projectRings()
    origin = map.project(map.getCenter())
    previous = origin
  }
  const limitDrag = () => {
    const candidate = origin.subtract(draggable._newPos.subtract(draggable._startPos))
    const allowed = limitMovement([previous.x, previous.y], [candidate.x, candidate.y], dragRings, 0.5)
    previous = point(allowed[0], allowed[1])
    draggable._newPos = draggable._startPos.add(origin.subtract(previous))
  }
  map.on('dragstart', startDrag)
  draggable.on('predrag', limitDrag)

  // Keyboard arrows and panTo also go through panBy: clamp them before movement.
  const originalPanBy = map.panBy
  map.panBy = function (offset, options) {
    const current = map.project(map.getCenter())
    const candidate = current.add(point(offset))
    const allowed = limitMovement([current.x, current.y], [candidate.x, candidate.y], projectRings(), 1)
    const limited = point(allowed[0], allowed[1]).subtract(current)
    // Leaflet rounds offsets to pixels, so back off one pixel at a hard edge.
    if (limited.distanceTo(point(offset)) > 0.01) {
      limited.x = Math.trunc(limited.x)
      limited.y = Math.trunc(limited.y)
    }
    return originalPanBy.call(this, limited, options)
  }
  return () => {
    map.off('dragstart', startDrag)
    draggable.off('predrag', limitDrag)
    map.panBy = originalPanBy
  }
}
