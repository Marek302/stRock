import { computed, reactive, ref } from 'vue'
import { createPost, reverseGeocode, uploadPostImage } from '../api/posts'
import { auth } from '../profile-auth/firebase'
import type { CommunityPost } from '../types/post'

export const postCreationDraft = reactive({
  contentType: 'publication' as 'publication' | 'safety_alert',
  title: '',
  description: '',
  image: null as File | null,
  location: '',
  latitude: null as number | null,
  longitude: null as number | null,
  expirationHours: null as number | null,
  isResolvingLocation: false,
})

let locationRequest = 0

function coordinateLabel(latitude: number, longitude: number) {
  return `lat: ${latitude.toFixed(6)}, lon: ${longitude.toFixed(6)}`
}

export async function selectPostLocation(latitude: number, longitude: number) {
  const request = ++locationRequest
  postCreationDraft.latitude = latitude
  postCreationDraft.longitude = longitude
  postCreationDraft.location = coordinateLabel(latitude, longitude)
  postCreationDraft.isResolvingLocation = true

  try {
    const address = await reverseGeocode(latitude, longitude)
    if (request === locationRequest && address.trim()) postCreationDraft.location = address.trim()
  } catch {
    // The selected coordinates remain available when no address is found.
  } finally {
    if (request === locationRequest) postCreationDraft.isResolvingLocation = false
  }
}

export function clearPostCreationDraft() {
  locationRequest++
  postCreationDraft.contentType = 'publication'
  postCreationDraft.title = ''
  postCreationDraft.description = ''
  postCreationDraft.image = null
  postCreationDraft.location = ''
  postCreationDraft.latitude = null
  postCreationDraft.longitude = null
  postCreationDraft.expirationHours = null
  postCreationDraft.isResolvingLocation = false
}

export function usePostCreation() {
  const draft = postCreationDraft
  const error = ref<string | null>(null)
  const needsLogin = ref(false)
  const isSubmitting = ref(false)
  const pendingPost = ref<CommunityPost | null>(null)

  const canEdit = computed(() => !isSubmitting.value && !pendingPost.value)
  const canSubmit = computed(() => !isSubmitting.value && !draft.isResolvingLocation
    && draft.latitude !== null && draft.longitude !== null && !!draft.location.trim()
    && (draft.contentType === 'safety_alert' || (draft.expirationHours !== null && Number.isInteger(draft.expirationHours)
    && draft.expirationHours >= 1 && draft.expirationHours <= 240)))

  function validate() {
    const title = draft.title.trim()
    const description = draft.description.trim()
    if (title.length < 3 || title.length > 128 || !description || description.length > 5000) {
      error.value = 'Saisissez un titre de 3 à 128 caractères et une description de 1 à 5000 caractères.'
      return null
    }
    if (draft.isResolvingLocation) {
      error.value = 'Attendez que le lieu sélectionné soit disponible.'
      return null
    }
    if (draft.latitude === null || draft.longitude === null || !draft.location.trim()) {
      error.value = 'Ajoutez un lieu avant de publier.'
      return null
    }
    if (draft.contentType === 'publication' && (draft.expirationHours === null || !Number.isInteger(draft.expirationHours)
      || draft.expirationHours < 1 || draft.expirationHours > 240)) {
      error.value = 'Choisissez une durée de publication entre 1 heure et 10 jours.'
      return null
    }
    return { title, description, location: draft.location.trim(), latitude: draft.latitude,
      longitude: draft.longitude, content_type: draft.contentType,
      ...(draft.contentType === 'publication' ? { expiration_hours: draft.expirationHours! } : {}) }
  }

  async function publish(): Promise<CommunityPost | null> {
    if (isSubmitting.value) return null
    const fields = validate()
    if (!fields) return null

    isSubmitting.value = true
    error.value = null
    needsLogin.value = false
    try {
      await auth.authStateReady()
      const user = auth.currentUser
      if (!user) {
        needsLogin.value = true
        throw new Error('Connectez-vous pour publier une publication.')
      }
      const token = await user.getIdToken()
      let post = pendingPost.value
      if (!post) {
        post = await createPost({
          ...fields,
          images: draft.image ? [{ image_index: 0 }] : [],
        }, token)
        pendingPost.value = post
      }
      if (draft.image) {
        const imageId = post.images[0]?.id
        if (!imageId) throw new Error('Impossible de préparer l’image du post.')
        await uploadPostImage(imageId, draft.image, token)
      }
      return post
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : 'Impossible de publier la publication.'
      if (pendingPost.value) error.value += ' Le post est créé ; réessayez pour envoyer l’image.'
      return null
    } finally {
      isSubmitting.value = false
    }
  }

  return { draft, error, needsLogin, isSubmitting, canEdit, canSubmit, publish }
}
