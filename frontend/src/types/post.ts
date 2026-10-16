export interface PostLocation {
  content_type: "publication" | "event" | "urban_alert" | "safety_alert";
  id: string;
  latitude: number | null;
  longitude: number | null;
}

export interface CommunityPost extends PostLocation {
  user_id: string;
  title: string;
  description: string;
  content_type: "publication" | "event" | "urban_alert" | "safety_alert";
  location: string | null;
  starts_at: string | null;
  ends_at: string | null;
  images: { id: string; image_index: number; post_id: string }[];
}

export interface PostListResponse {
  posts: CommunityPost[];
  count: number;
  skip: number;
  limit: number;
}

export interface PostItem {
  id: string;
  userId: string;
  title: string;
  description: string;
  imageUrl?: string;
  hasLocation: boolean;
  latitude: number | null;
  longitude: number | null;
  images?: string[];
  location?: string;
  startsAt?: string;
  endsAt?: string;
}
