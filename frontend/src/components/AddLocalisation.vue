<script setup lang="ts">
defineProps<{
  disabled?: boolean
  location: string
  latitude: number | null
  longitude: number | null
  isLoading?: boolean
}>()

const emit = defineEmits<{ select: [] }>()
</script>

<template>
  <div class="add-localisation">
    <p v-if="isLoading" role="status">Recherche de l’adresse…</p>
    <div v-else-if="location" class="selected-address">
      <span>Lieu sélectionné</span>
      <p>{{ location }}</p>
    </div>
    <button type="button" :disabled="disabled" @click="emit('select')">
      {{ latitude === null || longitude === null ? 'Choisir un lieu' : 'Changer de lieu' }}
    </button>
  </div>
</template>

<style scoped>
.add-localisation {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

button {
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}

p { margin: 0; }

.selected-address span { font-size: 0.875rem; color: #475569; }
</style>
