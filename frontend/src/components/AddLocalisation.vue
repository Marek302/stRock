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
      <div class="selected-address-text">
        <span>Lieu sélectionné</span>
        <p>{{ location }}</p>
      </div>
      <button type="button" :disabled="disabled" @click="emit('select')">Changer de lieu</button>
    </div>
    <button v-if="isLoading || !location" type="button" class="add-location-button" :disabled="disabled" @click="emit('select')">
      {{ latitude === null || longitude === null ? 'Ajouter un lieu' : 'Changer de lieu' }}
    </button>
    <span v-if="latitude === null || longitude === null" class="location-required">Lieu obligatoire</span>
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

.add-location-button {
  align-self: center;
}

p { margin: 0; }

.location-required {
  align-self: center;
  font-size: 0.875rem;
  color: #475569;
}

.selected-address {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
}

.selected-address-text {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  overflow-wrap: anywhere;
}

.selected-address-text span { font-size: 0.875rem; color: #475569; }
.selected-address > button {
  flex-shrink: 0;
  font-size: 0.875rem;
  line-height: 1.5;
}
</style>
