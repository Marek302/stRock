import { computed, ref, type Ref } from 'vue'

export function useBubble(container: Readonly<Ref<HTMLElement | null>>, sectionCount: number, initialIndex = 0) {
  const activeIndex = ref(initialIndex)
  const attraction = ref(0)

  const bubbleStyle = computed(() => ({
    width: `${100 / sectionCount}%`,
    transform: `translateX(calc(${activeIndex.value * 100}% + ${attraction.value * 16}px)) scaleX(${1 + Math.abs(attraction.value) * 0.14})`,
    transformOrigin: attraction.value < 0 ? 'right center' : 'left center',
    '--bubble-resting-transform': `translateX(${activeIndex.value * 100}%)`,
  }))

  function attractBubble(event: PointerEvent) {
    if (event.pointerType !== 'mouse' || !container.value) return
    const bounds = container.value.getBoundingClientRect()
    const sectionWidth = container.value.clientWidth / sectionCount
    const selectedCenter = bounds.left + container.value.clientLeft + (activeIndex.value + 0.5) * sectionWidth
    attraction.value = Math.max(-1, Math.min(1, (event.clientX - selectedCenter) / sectionWidth))
  }

  function resetBubble() {
    attraction.value = 0
  }

  function selectBubble(index: number) {
    activeIndex.value = index
    resetBubble()
  }

  return { activeIndex, bubbleStyle, attractBubble, resetBubble, selectBubble }
}
