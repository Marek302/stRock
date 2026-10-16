import type { MessageDTO } from './messagingApi'

export function parseMessageEvent(raw: string): MessageDTO | null {
  try {
    const event = JSON.parse(raw)
    if (event?.type !== 'message.created') return null
    const message = event.data
    if (!message || typeof message.id !== 'string'
      || typeof message.conversation_id !== 'string'
      || typeof message.sender_uid !== 'string'
      || typeof message.content !== 'string'
      || typeof message.timestamp !== 'string'
      || !Array.isArray(message.read_by)) return null
    return message as MessageDTO
  } catch {
    return null
  }
}

export function mergeMessage(messages: MessageDTO[], message: MessageDTO): MessageDTO[] {
  const index = messages.findIndex(item => item.id === message.id)
  if (index === -1) return [...messages, message]
  return messages.map((item, i) => i === index ? message : item)
}
