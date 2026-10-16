<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ disabled?: boolean; initialFile?: File | null }>()
const emit = defineEmits<{ selected: [file: File | null] }>()

const input = ref<HTMLInputElement | null>(null)
const fileName = ref(props.initialFile?.name ?? '')
const error = ref('')
const acceptedTypes = ['image/jpeg', 'image/png', 'image/webp']
const maxSize = 10 * 1024 * 1024

function selectFile(file?: File) {
  if (!file) return
  if (!acceptedTypes.includes(file.type) || file.size > maxSize) {
    fileName.value = ''
    error.value = 'Choisissez une image JPEG, PNG ou WebP de 10 Mo maximum.'
    emit('selected', null)
    return
  }
  fileName.value = file.name
  error.value = ''
  emit('selected', file)
}

function onDrop(event: DragEvent) {
  if (event.dataTransfer?.files.length) selectFile(event.dataTransfer.files[0])
}

function onInput(event: Event) {
  const target = event.target as HTMLInputElement
  selectFile(target.files?.[0])
  target.value = ''
}
</script>

<template>
  <div class="load-image">
    <div class="drop-zone" @dragover.prevent @drop.prevent="!disabled && onDrop($event)">
      <p>Déposez une image ici</p>
      <button type="button" :disabled="disabled" @click="input?.click()">
        {{ fileName ? 'Changer l’image' : 'Importer une image' }}
      </button>
      <input ref="input" type="file" accept="image/jpeg,image/png,image/webp" hidden :disabled="disabled" @change="onInput" />
      <p v-if="fileName">{{ fileName }}</p>
    </div>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
  </div>
</template>

<style scoped>
.drop-zone {
  padding: 16px;
  border: 2px dashed #cbd5e1;
  border-radius: 6px;
  text-align: center;
}

.drop-zone p {
  margin: 0 0 8px;
}

.drop-zone button {
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}

.error {
  color: #b91c1c;
}
</style>
