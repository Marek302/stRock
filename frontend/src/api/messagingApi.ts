import { auth, db } from '../profile-auth/firebase';
import { doc, getDoc } from 'firebase/firestore';

// In production / docker, this defaults to your reverse proxy root or env var
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || '';

export interface LastMessageDTO {
  content: string;
  sender_uid: string;
  timestamp: string;
}

export interface ConversationDTO {
  id: string;
  participants: string[];
  listing_id: string;
  created_at: string;
  last_message?: LastMessageDTO | null;
  other_participant_firebase_uid?: string | null;
}

export interface MessageDTO {
  id: string;
  conversation_id: string;
  sender_uid: string;
  content: string;
  timestamp: string;
  read_by: string[];
}

export interface OtherUserProfile {
  uid: string;
  displayName: string;
  email: string;
  photoURL: string;
}

async function getAuthHeaders(): Promise<HeadersInit> {
  const token = await auth.currentUser?.getIdToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export const MessagingApi = {
  // 1. GET /messaging/conversations
  async getConversations(): Promise<ConversationDTO[]> {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/messaging/conversations`, { headers });
    if (!res.ok) throw new Error('Failed to fetch conversations');
    return res.json();
  },
 // Inside your MessagingApi object:
    async createConversation(listingId: string): Promise<ConversationDTO> {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/messaging/conversations`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ listing_id: listingId }),
    });
    if (!res.ok) throw new Error('Impossible de créer la discussion.');
    return res.json();
    },
  // 2. GET /messaging/conversations/{id}/messages
  async getMessages(conversationId: string): Promise<MessageDTO[]> {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/messaging/conversations/${conversationId}/messages`, { headers });
    if (!res.ok) throw new Error('Failed to fetch messages');
    return res.json();
  },

  // 3. POST /messaging/conversations/{id}/messages
  async sendMessage(conversationId: string, content: string): Promise<MessageDTO> {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/messaging/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ content, image_ids: [] }),
    });
    if (!res.ok) throw new Error('Failed to send message');
    return res.json();
  },

  // 4. DELETE /messaging/conversations (with { conversation_ids: [id] })
  async deleteConversation(conversationId: string): Promise<void> {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/messaging/conversations`, {
      method: 'DELETE',
      headers,
      body: JSON.stringify({ conversation_ids: [conversationId] }),
    });
    if (!res.ok && res.status !== 204) throw new Error('Failed to delete conversation');
  },

  // 5. POST /messaging/conversations/{id}/read
  async markRead(conversationId: string): Promise<void> {
    const headers = await getAuthHeaders();
    await fetch(`${API_BASE_URL}/messaging/conversations/${conversationId}/read`, {
      method: 'POST',
      headers,
    });
  },

  // 6. Connect WebSocket for live incoming messages
  async connectWebSocket(
    conversationId: string,
    onMessage: (msg: MessageDTO) => void
  ): Promise<WebSocket | null> {
    const token = await auth.currentUser?.getIdToken();
    if (!token) return null;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = API_BASE_URL ? API_BASE_URL.replace(/^https?:\/\//, '') : window.location.host;
    const wsUrl = `${protocol}//${host}/messaging/ws/conversations/${conversationId}?token=${token}`;

    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error('Failed to parse WS message', e);
      }
    };
    return ws;
  },

  // 7. Get the other person's profile from Firestore using their other_participant_firebase_uid
  async getOtherUserProfile(uid: string): Promise<OtherUserProfile> {
    try {
      const snap = await getDoc(doc(db, 'users', uid));
      if (snap.exists()) {
        const data = snap.data();
        return {
          uid,
          displayName: data.displayName || 'Utilisateur',
          email: data.email || '',
          photoURL: data.photoURL || '',
        };
      }
    } catch (e) {
      console.warn('Firestore profile lookup note:', e);
    }
    return {
      uid,
      displayName: 'Utilisateur',
      email: '',
      photoURL: '',
    };
  },
};