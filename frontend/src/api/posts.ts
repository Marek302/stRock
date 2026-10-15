import { apiFetch } from './client'
import type { CommunityPost, PostLocation, PostListResponse } from '../types/post'

export async function getPostLocations(signal?: AbortSignal): Promise<PostLocation[]> {
  const response = await apiFetch('/posts/locations', { signal })

  if (!response.ok) {
    throw new Error(`Impossible de charger les positions des publications (HTTP ${response.status}).`)
  }

  return response.json()
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
