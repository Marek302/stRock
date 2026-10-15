import { GridLayer, latLng, latLngBounds, type Coords, type DoneCallback } from 'leaflet'
import boundary from '../data/saint-roch.json'
import { type Coordinate, type Ring } from './geometry'

// Ville de Québec, jeu de données « Quartiers » (voir README pour la source).
export const saintRochRings: Ring[] = boundary.geometry.coordinates.map((ring) =>
  ring.map((coordinate): Coordinate => [coordinate[0]!, coordinate[1]!]),
)
export const saintRochBounds = latLngBounds(
  saintRochRings[0]!.map(([longitude, latitude]) => latLng(latitude, longitude)),
)

/** One tile image: muted outside Saint-Roch, original colors inside its contour. */
export class SaintRochLayer extends GridLayer {
  private projectedRings = new Map<number, Ring[]>()

  protected override createTile(coords: Coords, done: DoneCallback): HTMLElement {
    const tile = document.createElement('div')
    const canvas = document.createElement('canvas')
    const size = this.getTileSize()
    canvas.width = size.x
    canvas.height = size.y
    canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;'
    canvas.setAttribute('aria-hidden', 'true')
    const left = coords.x * size.x
    const top = coords.y * size.y
    let rings = this.projectedRings.get(coords.z)
    if (!rings) {
      rings = saintRochRings.map((ring) => ring.map(([lng, lat]): Coordinate => {
        const p = this._map.project([lat, lng], coords.z)
        return [p.x, p.y]
      }))
      this.projectedRings.set(coords.z, rings)
    }
    const context = canvas.getContext('2d')
    if (!context) {
      queueMicrotask(() => done(new Error('Canvas indisponible'), tile))
      return tile
    }
    context.beginPath()
    for (const ring of rings) {
      ring.forEach(([x, y], i) => {
        if (i === 0) context.moveTo(x - left, y - top)
        else context.lineTo(x - left, y - top)
      })
      context.closePath()
    }
    context.clip('evenodd')
    const image = new Image()
    image.alt = ''
    image.draggable = false
    image.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;filter:grayscale(1) brightness(0.65);'
    tile.append(image, canvas)
    image.onload = () => {
      context.drawImage(image, 0, 0, size.x, size.y)
      done(undefined, tile)
    }
    image.onerror = () => done(new Error('Chargement du fond de carte impossible'), tile)
    image.src = `https://tile.openstreetmap.org/${coords.z}/${coords.x}/${coords.y}.png`
    return tile
  }
}
