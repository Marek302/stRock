<script setup lang="ts">
import { computed, ref } from 'vue'
import { VueScrollPicker, type VueScrollPickerValue } from 'vue-scroll-picker'
import 'vue-scroll-picker/style.css'

const props = defineProps<{
  modelValue: number | null
  disabled?: boolean
}>()

const emit = defineEmits<{ 'update:modelValue': [hours: number] }>()
const isOpen = ref(false)
const days = ref(0)
const hours = ref(1)
const movingDays = ref<number | null>(null)
const movingHours = ref<number | null>(null)
const dayOptions = Array.from({ length: 11 }, (_, value) => ({ name: String(value), value }))
const hourOptions = computed(() => Array.from({ length: 24 }, (_, value) => ({
  name: String(value),
  value,
  disabled: (days.value === 0 && value === 0) || (days.value === 10 && value > 0),
})))
const totalHours = computed(() => days.value * 24 + hours.value)
const isValid = computed(() => totalHours.value >= 1 && totalHours.value <= 240)
const previewDays = computed(() => movingDays.value ?? days.value)
const previewHours = computed(() => movingHours.value ?? hours.value)
const previewTotalHours = computed(() => previewDays.value * 24 + previewHours.value)
const isPreviewValid = computed(() => previewTotalHours.value >= 1 && previewTotalHours.value <= 240)
const selectedLabel = computed(() => props.modelValue === null ? '' : formatDuration(props.modelValue))

function formatDuration(duration: number) {
  const selectedDays = Math.floor(duration / 24)
  const selectedHours = duration % 24
  const parts: string[] = []
  if (selectedDays) parts.push(`${selectedDays} ${selectedDays === 1 ? 'jour' : 'jours'}`)
  if (selectedHours) parts.push(`${selectedHours} ${selectedHours === 1 ? 'heure' : 'heures'}`)
  return parts.join(' et ')
}

function setDays(value: VueScrollPickerValue | undefined) {
  if (typeof value !== 'number') return
  days.value = value
  if (value === 0 && hours.value === 0) hours.value = 1
  if (value === 10 && hours.value > 0) hours.value = 0
}

function setHours(value: VueScrollPickerValue | undefined) {
  if (typeof value !== 'number') return
  if ((days.value === 0 && value === 0) || (days.value === 10 && value > 0)) return
  hours.value = value
}

function previewMove(kind: 'days' | 'hours', value: VueScrollPickerValue | undefined) {
  if (typeof value !== 'number') return
  if (kind === 'days') movingDays.value = value
  else movingHours.value = value
}

function finishMove(kind: 'days' | 'hours') {
  if (kind === 'days') movingDays.value = null
  else movingHours.value = null
}

function onWheelKey(kind: 'days' | 'hours', event: KeyboardEvent) {
  const current = kind === 'days' ? days.value : hours.value
  const max = kind === 'days' ? 10 : days.value === 10 ? 0 : 23
  const min = kind === 'hours' && days.value === 0 ? 1 : 0
  let next = current
  if (event.key === 'ArrowDown' || event.key === 'ArrowRight') next = Math.min(max, current + 1)
  else if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') next = Math.max(min, current - 1)
  else if (event.key === 'Home') next = min
  else if (event.key === 'End') next = max
  else return
  event.preventDefault()
  if (kind === 'days') setDays(next)
  else setHours(next)
}

function toggleMenu() {
  if (props.disabled) return
  isOpen.value = !isOpen.value
  if (!isOpen.value) return
  movingDays.value = null
  movingHours.value = null
  const duration = props.modelValue ?? 1
  days.value = Math.floor(duration / 24)
  hours.value = duration % 24
}

function selectDuration() {
  if (!isValid.value) return
  emit('update:modelValue', totalHours.value)
  isOpen.value = false
}
</script>

<template>
  <div class="date-selection">
    <div class="selection-summary">
      <span v-if="modelValue !== null" class="selected-duration">Suppression après {{ selectedLabel }}</span>
      <button type="button" class="selection-button" :disabled="disabled" :aria-expanded="isOpen" :aria-label="modelValue === null ? undefined : 'Changer la durée de publication'" @click="toggleMenu">
        {{ modelValue === null ? 'Définir la durée de publication' : 'Changer' }}
      </button>
    </div>

    <div v-if="isOpen" class="selection-menu" role="group" aria-label="Durée avant suppression" @keydown.esc.stop.prevent="isOpen = false">
      <div class="wheels">
        <div class="wheel-column">
          <span>Jours</span>
          <div
            class="picker-wheel"
            :class="{ 'is-moving': movingDays !== null }"
            role="spinbutton"
            tabindex="0"
            aria-label="Jours"
            aria-valuemin="0"
            aria-valuemax="10"
            :aria-valuenow="days"
            :aria-valuetext="`${days} ${days === 1 ? 'jour' : 'jours'}`"
            @keydown="onWheelKey('days', $event)"
          >
            <VueScrollPicker
              :model-value="days"
              :options="dayOptions"
              :drag-sensitivity="2.4"
              :touch-sensitivity="2.4"
              @move="previewMove('days', $event)"
              @end="finishMove('days')"
              @cancel="finishMove('days')"
              @update:model-value="setDays"
            >
              <template #default="{ option }">
                <span :class="{ 'is-preview': option.value === previewDays }">{{ option.name }}</span>
              </template>
            </VueScrollPicker>
          </div>
        </div>
        <div class="wheel-column">
          <span>Heures</span>
          <div
            class="picker-wheel"
            :class="{ 'is-moving': movingHours !== null }"
            role="spinbutton"
            tabindex="0"
            aria-label="Heures"
            :aria-valuemin="days === 0 ? 1 : 0"
            :aria-valuemax="days === 10 ? 0 : 23"
            :aria-valuenow="hours"
            :aria-valuetext="`${hours} ${hours === 1 ? 'heure' : 'heures'}`"
            @keydown="onWheelKey('hours', $event)"
          >
            <VueScrollPicker
              :model-value="hours"
              :options="hourOptions"
              :drag-sensitivity="2.4"
              :touch-sensitivity="2.4"
              @move="previewMove('hours', $event)"
              @end="finishMove('hours')"
              @cancel="finishMove('hours')"
              @update:model-value="setHours"
            >
              <template #default="{ option }">
                <span :class="{ 'is-preview': option.value === previewHours }">{{ option.name }}</span>
              </template>
            </VueScrollPicker>
          </div>
        </div>
      </div>

      <p class="duration-preview">{{ isPreviewValid ? formatDuration(previewTotalHours) : 'Entre 1 heure et 10 jours' }}</p>
      <button type="button" class="confirm-button" :disabled="!isValid" @click="selectDuration">Confirmer</button>
    </div>

    <span v-if="modelValue === null" class="required-hint">Durée obligatoire</span>
  </div>
</template>

<style scoped>
.date-selection {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.selection-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
}

.selected-duration {
  min-width: 0;
  color: #b91c1c;
  font-size: 0.875rem;
  font-weight: 600;
}

.selection-button { flex-shrink: 0; }

button {
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: white;
  cursor: pointer;
}

.selection-menu {
  width: min(100%, 340px);
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: #f8fafc;
  box-shadow: 0 12px 28px rgb(15 23 42 / 10%);
}

.wheels {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.wheel-column > span {
  display: block;
  margin-bottom: 4px;
  color: #475569;
  font-size: 0.875rem;
  font-weight: 600;
  text-align: center;
}

.picker-wheel { border-radius: 10px; }
.picker-wheel:focus-visible { outline: 2px solid #2563eb; outline-offset: 2px; }
.picker-wheel :deep(.vue-scroll-picker) { height: 180px; cursor: grab; touch-action: none; }
.picker-wheel :deep(.vue-scroll-picker:active) { cursor: grabbing; }
.picker-wheel :deep(.vue-scroll-picker-layer) { cursor: grab; }
.picker-wheel :deep(.vue-scroll-picker:active .vue-scroll-picker-layer) { cursor: grabbing; }
.picker-wheel :deep(.vue-scroll-picker-item) { color: #94a3b8; font-size: 1.125rem; line-height: 1.5em; }
.picker-wheel :deep(.vue-scroll-picker-item[aria-selected="true"]) { color: #0f172a; font-weight: 600; }
.picker-wheel.is-moving :deep(.vue-scroll-picker-item[aria-selected="true"]) { color: #94a3b8; font-weight: 400; }
.picker-wheel.is-moving :deep(.is-preview) { color: #0f172a; font-weight: 600; }
.picker-wheel :deep(.vue-scroll-picker-layer-top) { border-color: #dbe3ee; background: linear-gradient(#f8fafc 10%, rgb(248 250 252 / 68%)); }
.picker-wheel :deep(.vue-scroll-picker-layer-bottom) { border-color: #dbe3ee; background: linear-gradient(0deg, #f8fafc 10%, rgb(248 250 252 / 68%)); }

.duration-preview {
  min-height: 24px;
  margin: 10px 0;
  color: #334155;
  font-size: 0.875rem;
  text-align: center;
}

.confirm-button {
  width: 100%;
  border-color: #2563eb;
  background: #2563eb;
  color: white;
  font-weight: 600;
}

.confirm-button:disabled { opacity: 0.5; cursor: not-allowed; }
.required-hint { color: #475569; font-size: 0.875rem; }
</style>
