<script setup lang="ts">
import { ref, watch, onUnmounted, nextTick } from 'vue';
import {
  Search,
  Send,
  Trash2,
  User,
  ArrowLeft,
  X,
  MessageSquare,
} from 'lucide-vue-next';
import { useRoute } from 'vue-router';
import { mergeMessage } from '../api/messageEvents';
import { auth } from '../profile-auth/firebase';
import {
  MessagingApi,
  type ConversationDTO,
  type MessageDTO,
  type OtherUserProfile,
} from '../api/messagingApi';

const route = useRoute();
const conversations = ref<ConversationDTO[]>([]);
const selectedConvo = ref<ConversationDTO | null>(null);
const messages = ref<MessageDTO[]>([]);
const otherProfiles = ref<Record<string, OtherUserProfile>>({});
const activeProfile = ref<OtherUserProfile | null>(null);

const searchQuery = ref('');
const messageInput = ref('');
const isLoading = ref(false);
const isSending = ref(false);
const sendError = ref('');
const showProfileModal = ref(false);
const convoToDelete = ref<ConversationDTO | null>(null);
const messagesContainer = ref<HTMLDivElement | null>(null);

let activeWs: WebSocket | null = null;
const currentUid = ref(auth.currentUser?.uid || '');

watch(
  () => route.name === 'messages' ? [route.query.conversation, route.query.user] : null,
  async (target) => {
    if (!target) return;
    await auth.authStateReady();
    currentUid.value = auth.currentUser?.uid || '';
    await loadConversations();
  },
  { immediate: true },
);

onUnmounted(() => {
  if (activeWs) activeWs.close();
});

async function loadConversations() {
  isLoading.value = true;
  try {
    conversations.value = await MessagingApi.getConversations();
    // Load profiles for each other participant
    for (const c of conversations.value) {
      if (c.other_participant_firebase_uid) {
        try {
          otherProfiles.value[c.other_participant_firebase_uid] =
            await MessagingApi.getOtherUserProfile(c.other_participant_firebase_uid);
        } catch (error) {
          console.error('Erreur chargement du profil du contact:', error);
        }
      }
    }
    if (route.name !== 'messages') return;
    const requestedId = route.query.conversation;
    const requestedUser = route.query.user;
    const target = typeof requestedId === 'string'
      ? conversations.value.find(c => c.id === requestedId
          && (typeof requestedUser !== 'string' || c.participants.includes(requestedUser)))
      : conversations.value.find(c => c.id === selectedConvo.value?.id) || conversations.value[0];
    if (target) await selectConversation(target);
    else {
      selectedConvo.value = null;
      activeProfile.value = null;
      messages.value = [];
      activeWs?.close();
    }
  } catch (err) {
    console.error('Erreur chargement conversations:', err);
  } finally {
    isLoading.value = false;
  }
}

async function selectConversation(convo: ConversationDTO) {
  selectedConvo.value = convo;
  messages.value = [];
  messageInput.value = "";
  activeProfile.value = null;
  activeWs?.close();

  // Set active profile for the modal
  if (convo.other_participant_firebase_uid) {
    activeProfile.value = otherProfiles.value[convo.other_participant_firebase_uid] || {
      uid: convo.other_participant_firebase_uid,
      displayName: 'Utilisateur',
      email: '',
      photoURL: '',
    };
  }

  // Load messages from GET /messaging/conversations/{id}/messages
  try {
    const loadedMessages = await MessagingApi.getMessages(convo.id);
    if (selectedConvo.value?.id !== convo.id) return;
    messages.value = loadedMessages;
    scrollToBottom();
    MessagingApi.markRead(convo.id);
  } catch (err) {
    console.error('Erreur chargement messages:', err);
  }

  if (selectedConvo.value?.id !== convo.id) return;

  // Connect WebSocket for live real-time updates
  if (activeWs) activeWs.close();
  activeWs = await MessagingApi.connectWebSocket(convo.id, (newMsg) => {
    if (selectedConvo.value?.id !== convo.id) return;
    messages.value = mergeMessage(messages.value, newMsg);
    convo.last_message = {
      content: newMsg.content,
      sender_uid: newMsg.sender_uid,
      timestamp: newMsg.timestamp,
    };
    scrollToBottom();
  });
}

async function handleSendMessage() {
  if (isSending.value || !messageInput.value.trim() || !selectedConvo.value) return;
  const text = messageInput.value.trim();
  const convo = selectedConvo.value;
  isSending.value = true;
  sendError.value = '';
  try {
    const sent = await MessagingApi.sendMessage(convo.id, text);
    convo.last_message = {
      content: sent.content, sender_uid: sent.sender_uid, timestamp: sent.timestamp,
    };
    if (selectedConvo.value?.id === convo.id) {
      messages.value = mergeMessage(messages.value, sent);
      if (messageInput.value.trim() === text) messageInput.value = '';
      scrollToBottom();
    }
  } catch {
    sendError.value = 'Impossible d’envoyer le message. Réessayez.';
  } finally {
    isSending.value = false;
  }
}

function confirmDelete(convo: ConversationDTO, e?: Event) {
  if (e) e.stopPropagation();
  convoToDelete.value = convo;
}

async function executeDelete() {
  if (!convoToDelete.value) return;
  const idToDelete = convoToDelete.value.id;
  try {
    // Calls DELETE /messaging/conversations with { conversation_ids: [id] }
    await MessagingApi.deleteConversation(idToDelete);
    conversations.value = conversations.value.filter((c) => c.id !== idToDelete);
    if (selectedConvo.value?.id === idToDelete) {
      selectedConvo.value = conversations.value[0] || null;
      if (selectedConvo.value) {
        await selectConversation(selectedConvo.value);
      } else {
        messages.value = [];
      }
    }
  } catch (err) {
    console.error('Erreur suppression conversation:', err);
  } finally {
    convoToDelete.value = null;
    showProfileModal.value = false;
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
}

function formatTime(isoString?: string) {
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}
</script>

<template>
  <div class="h-screen w-full bg-slate-50 flex flex-col overflow-hidden text-slate-900">
    <!-- En-tête -->
    <header class="bg-white border-b border-slate-200 px-4 h-12 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-3">
        <button
          type="button"
          class="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200/80 rounded-lg transition-colors cursor-pointer"
        >
          <ArrowLeft class="w-3.5 h-3.5" />
          <span>Accueil</span>
        </button>
        <div class="h-4 w-px bg-slate-200" />
        <span class="font-bold text-sm tracking-tight text-slate-900">roch-on messagerie</span>
      </div>
      <span class="text-xs text-slate-400">
        {{ conversations.length }} {{ conversations.length <= 1 ? 'conversation' : 'conversations' }}
      </span>
    </header>

    <div class="flex-1 flex overflow-hidden relative">
      <!-- Liste des conversations -->
      <aside :class="['w-full md:w-80 lg:w-96 bg-white border-r border-slate-200 flex flex-col shrink-0', selectedConvo ? 'hidden md:flex' : 'flex']">
        <div class="p-3 border-b border-slate-100">
          <div class="relative">
            <Search class="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Rechercher une conversation..."
              class="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-slate-900 focus:bg-white"
            />
          </div>
        </div>

        <div class="flex-1 overflow-y-auto divide-y divide-slate-100">
          <div v-if="conversations.length === 0" class="p-8 text-center text-xs text-slate-400">
            Aucune conversation pour le moment.
          </div>

          <div
            v-for="convo in conversations"
            :key="convo.id"
            @click="selectConversation(convo)"
            :class="['group flex items-center gap-3 p-3.5 cursor-pointer transition-colors relative', selectedConvo?.id === convo.id ? 'bg-slate-100/80' : 'hover:bg-slate-50']"
          >
            <div class="w-11 h-11 rounded-full bg-slate-100 border border-slate-200 overflow-hidden shrink-0 flex items-center justify-center font-bold text-slate-500">
              <img
                v-if="convo.other_participant_firebase_uid && otherProfiles[convo.other_participant_firebase_uid]?.photoURL"
                :src="otherProfiles[convo.other_participant_firebase_uid].photoURL"
                class="w-full h-full object-cover"
              />
              <span v-else>
                {{ convo.other_participant_firebase_uid ? (otherProfiles[convo.other_participant_firebase_uid]?.displayName?.charAt(0) || 'U') : 'U' }}
              </span>
            </div>

            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-0.5">
                <span class="font-semibold text-xs text-slate-900 truncate">
                  {{ convo.other_participant_firebase_uid ? (otherProfiles[convo.other_participant_firebase_uid]?.displayName || 'Utilisateur') : 'Utilisateur' }}
                </span>
                <span class="text-[10px] text-slate-400 shrink-0">
                  {{ formatTime(convo.last_message?.timestamp || convo.created_at) }}
                </span>
              </div>
              <p class="text-xs text-slate-500 truncate">
                {{ convo.last_message?.content || 'Nouvelle conversation' }}
              </p>
            </div>

            <button
              type="button"
              @click="confirmDelete(convo, $event)"
              title="Supprimer la conversation"
              class="opacity-0 group-hover:opacity-100 p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-all"
            >
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </aside>

      <!-- Salle de chat active -->
      <section v-if="selectedConvo" :class="['flex-1 flex flex-col bg-slate-50/50', selectedConvo ? 'flex' : 'hidden md:flex']">
        <div class="bg-white border-b border-slate-200 px-4 py-2.5 flex items-center justify-between shrink-0 shadow-2xs">
          <div class="flex items-center gap-3 min-w-0">
            <button type="button" @click="selectedConvo = null" class="md:hidden p-1.5 text-slate-500 hover:text-slate-900 rounded-lg">
              <ArrowLeft class="w-4 h-4" />
            </button>

            <!-- Déclencheur du profil contact (Avatar + Nom) -->
            <button type="button" @click="showProfileModal = true" class="flex items-center gap-2.5 text-left group">
              <div class="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 overflow-hidden flex items-center justify-center font-bold text-xs text-slate-500">
                <img v-if="activeProfile?.photoURL" :src="activeProfile.photoURL" class="w-full h-full object-cover" />
                <span v-else>{{ activeProfile?.displayName?.charAt(0) || 'U' }}</span>
              </div>
              <div class="min-w-0">
                <span class="block font-bold text-xs text-slate-900 group-hover:text-slate-700 leading-tight">
                  {{ activeProfile?.displayName || 'Utilisateur' }}
                </span>
                <span class="block text-[11px] text-slate-400">Voir le profil</span>
              </div>
            </button>
          </div>

          <div class="flex items-center gap-1">
            <button type="button" @click="showProfileModal = true" class="p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg text-xs font-medium flex items-center gap-1">
              <User class="w-4 h-4" />
              <span class="hidden sm:inline">Profil</span>
            </button>
            <button type="button" @click="confirmDelete(selectedConvo)" class="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg">
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Messages -->
        <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-3">
          <div
            v-for="msg in messages"
            :key="msg.id"
            :class="['flex flex-col max-w-[80%] sm:max-w-[70%]', msg.sender_uid === currentUid ? 'ml-auto items-end' : 'mr-auto items-start']"
          >
            <div :class="['whitespace-pre-wrap break-words px-3.5 py-2 rounded-2xl text-xs sm:text-sm leading-relaxed shadow-2xs', msg.sender_uid === currentUid ? 'bg-slate-900 text-white rounded-br-xs' : 'bg-white text-slate-800 border border-slate-200/80 rounded-bl-xs']">
              {{ msg.content }}
            </div>
            <span class="text-[10px] text-slate-400 px-1 mt-0.5">
              {{ formatTime(msg.timestamp) }}
            </span>
          </div>
        </div>

        <!-- Saisie message -->
        <div class="p-3 bg-white border-t border-slate-200 shrink-0">
          <p v-if="sendError" role="alert" class="mb-2 text-sm text-red-700">{{ sendError }}</p>
          <form @submit.prevent="handleSendMessage" class="flex items-center gap-2">
            <input
              v-model="messageInput"
              type="text"
              placeholder="Écrire un message..."
              class="flex-1 px-4 py-2 text-xs sm:text-sm bg-slate-50 rounded-xl border border-slate-300 focus:outline-none focus:ring-1 focus:ring-slate-900 focus:bg-white"
            />
            <button type="submit" :disabled="isSending || !messageInput.trim()" class="p-2.5 bg-slate-900 text-white rounded-xl hover:bg-slate-800 disabled:opacity-40 shadow-2xs">
              <Send class="w-4 h-4" />
            </button>
          </form>
        </div>
      </section>

      <section v-else class="hidden md:flex flex-1 items-center justify-center p-8 text-center text-slate-400 text-xs">
        <div>
          <MessageSquare class="w-8 h-8 mx-auto mb-2 opacity-30" />
          <p>Sélectionnez une conversation pour commencer à discuter</p>
        </div>
      </section>
    </div>

    <!-- Modale Profil du Contact -->
    <div v-if="showProfileModal && activeProfile" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/40 backdrop-blur-xs">
      <div class="bg-white rounded-2xl max-w-sm w-full p-6 shadow-xl border border-slate-200">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
          <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Profil du contact</span>
          <button type="button" @click="showProfileModal = false" class="p-1 text-slate-400 hover:text-slate-700 rounded-lg">
            <X class="w-4 h-4" />
          </button>
        </div>

        <div class="flex flex-col items-center text-center space-y-3">
          <div class="w-20 h-20 rounded-full bg-slate-100 border-2 border-slate-200 overflow-hidden shadow-xs flex items-center justify-center font-bold text-xl text-slate-500">
            <img v-if="activeProfile.photoURL" :src="activeProfile.photoURL" class="w-full h-full object-cover" />
            <span v-else>{{ activeProfile.displayName?.charAt(0) || 'U' }}</span>
          </div>

          <div>
            <h3 class="font-bold text-base text-slate-900">{{ activeProfile.displayName }}</h3>
            <p v-if="activeProfile.email" class="text-xs text-slate-500 font-mono mt-1">{{ activeProfile.email }}</p>
          </div>
        </div>

        <div class="mt-6 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
          <button
            type="button"
            v-if="selectedConvo"
            @click="confirmDelete(selectedConvo)"
            class="py-2 px-3 text-xs font-medium text-rose-600 hover:bg-rose-50 rounded-xl flex items-center gap-1.5"
          >
            <Trash2 class="w-3.5 h-3.5" />
            <span>Supprimer le chat</span>
          </button>
          <button type="button" @click="showProfileModal = false" class="py-2 px-4 bg-slate-900 text-white text-xs font-semibold rounded-xl">
            Fermer
          </button>
        </div>
      </div>
    </div>

    <!-- Modale Confirmation Suppression -->
    <div v-if="convoToDelete" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/40 backdrop-blur-xs">
      <div class="bg-white rounded-2xl max-w-xs w-full p-5 shadow-xl border border-slate-200 text-center space-y-4">
        <div class="w-10 h-10 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
          <Trash2 class="w-5 h-5" />
        </div>
        <div>
          <h3 class="font-bold text-sm text-slate-900">Supprimer la conversation ?</h3>
          <p class="text-xs text-slate-500 mt-1">
            Cette action supprimera définitivement l'historique de discussion.
          </p>
        </div>
        <div class="flex items-center gap-2 pt-2">
          <button type="button" @click="convoToDelete = null" class="flex-1 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl">
            Annuler
          </button>
          <button type="button" @click="executeDelete" class="flex-1 py-2 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-xl shadow-2xs">
            Supprimer
          </button>
        </div>
      </div>
    </div>
  </div>
</template>