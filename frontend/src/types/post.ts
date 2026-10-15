export interface PostLocation {
  id: string
  latitude: number | null
  longitude: number | null
}

export interface PostSummary {
  id: string
  user_id: string
  title: string
  description: string
  first_image: { id: string } | null
}

export interface PostListResponse {
  posts: PostSummary[]
  count: number
  skip: number
  limit: number
}

export interface PostItem {
  id: string
  userId: string
  title: string
  description: string
  imageUrl?: string
}
