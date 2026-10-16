import { apiFetch } from './client'
import type { CommunityPost, PostLocation, PostListResponse } from '../types/post'

export async function getPostLocations(signal?: AbortSignal): Promise<PostLocation[]> {
  const response = await apiFetch('/posts/locations', { signal })

  if (!response.ok) {
    throw new Error(`Impossible de charger les positions des publications (HTTP ${response.status}).`)
  }

  return response.json()
}

export async function reverseGeocode(latitude: number, longitude: number): Promise<string> {
  const query = new URLSearchParams({ latitude: String(latitude), longitude: String(longitude) })
  const response = await apiFetch(`/posts/reverse-geocode?${query}`)
  if (!response.ok) throw new Error('Impossible de trouver l’adresse. Choisissez un autre point ou réessayez.')
  const result: { address: string } = await response.json()
  return result.address
}

export async function getPosts(skip = 0, limit = 20, signal?: AbortSignal): Promise<PostListResponse> {
  const response = await apiFetch(`/posts?skip=${skip}&limit=${limit}`, { signal })
  if (!response.ok) {
    throw new Error(`Impossible de charger les publications (HTTP ${response.status}).`)
  }
  return response.json()
}

export async function getPost(id: string, signal?: AbortSignal): Promise<CommunityPost> {
  const response = await apiFetch(`/posts/${encodeURIComponent(id)}`, { signal })
  if (!response.ok) {
    throw new Error(`Impossible de charger la publication (HTTP ${response.status}).`)
  }
  return response.json()
}

export async function getNearestPostAddress(
  id: string, signal?: AbortSignal,
): Promise<{ address: string; source: 'saved' | 'openstreetmap' }> {
  const response = await apiFetch(`/posts/${encodeURIComponent(id)}/nearest-address`, { signal })
  if (!response.ok) throw new Error(`Impossible de trouver l’adresse de la publication (HTTP ${response.status}).`)
  return response.json()
}

export async function createPost(
  input: Pick<CommunityPost, 'title' | 'description'> & {
    location: string
    latitude: number
    longitude: number
    content_type: 'publication' | 'event' | 'safety_alert'
    starts_at?: string
    ends_at?: string
    expiration_hours?: number
    images?: { image_index: number }[]
  },
  token: string,
): Promise<CommunityPost> {
  const response = await apiFetch('/posts', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  })

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      throw new Error('Votre session a expiré. Reconnectez-vous pour publier.')
    }
    if (response.status === 422) {
      const body: unknown = await response.json().catch(() => null)
      if (body && typeof body === 'object' && 'detail' in body) {
        const detail = body.detail
        if (Array.isArray(detail) && detail.some((issue) =>
          issue && typeof issue === 'object' && issue.type === 'extra_forbidden'
          && Array.isArray(issue.loc) && issue.loc.includes('expiration_hours')
        )) {
          throw new Error('Le serveur de publication ne prend pas encore en charge la durée. Mettez à jour l’API pour publier.')
        }
        if (typeof detail === 'string' && detail.trim()) throw new Error(detail)
      }
      throw new Error('Vérifiez le titre, la description, le lieu et la durée de la publication.')
    }
    throw new Error(`Impossible de publier la publication (HTTP ${response.status}).`)
  }

  const result: { post: CommunityPost } = await response.json()
  return result.post
}

export async function uploadPostImage(imageId: string, file: File, token: string): Promise<void> {
  const body = new FormData()
  body.append('image', file)
  const response = await apiFetch(`/images/${encodeURIComponent(imageId)}`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}` },
    body,
  })
  if (!response.ok) {
    if (response.status === 413) throw new Error('L’image est trop volumineuse (10 Mo maximum).')
    const details = await response.json().catch(() => null)
    if (typeof details?.detail === 'string') throw new Error(`Impossible d’envoyer l’image : ${details.detail}`)
    throw new Error(`Impossible d’envoyer l’image (HTTP ${response.status}).`)
  }
}
