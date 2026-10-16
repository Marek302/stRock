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

export async function createPost(
  input: Pick<CommunityPost, 'title' | 'description'> & {
    location?: string
    latitude?: number
    longitude?: number
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
    body: JSON.stringify({ ...input, content_type: 'publication' }),
  })

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      throw new Error('Votre session a expiré. Reconnectez-vous pour publier.')
    }
    if (response.status === 422) {
      throw new Error('Vérifiez le titre et la description de la publication.')
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
    throw new Error(`Impossible d’envoyer l’image (HTTP ${response.status}).`)
  }
}
