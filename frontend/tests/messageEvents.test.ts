import { test } from 'node:test'
import assert from 'node:assert/strict'
import { parseMessageEvent, mergeMessage } from '../src/api/messageEvents.ts'

const message = {
  id: 'msg-1', conversation_id: 'conversation-1', sender_uid: 'alice',
  content: 'Salut Léa 👋\nÇa marche !', timestamp: '2026-10-16T15:00:00Z', read_by: ['alice'],
}

test('reads message content from the actual WebSocket envelope', () => {
  const received = parseMessageEvent(JSON.stringify({ type: 'message.created', data: message }))
  assert.deepEqual(received, message)
  assert.equal(received?.content, 'Salut Léa 👋\nÇa marche !')
})

test('ignores unrelated events and malformed messages instead of creating empty bubbles', () => {
  for (const value of ['bad json', '{}', 'null', JSON.stringify({ type: 'read' }),
    JSON.stringify({ type: 'message.created', data: { id: 'empty' } })]) {
    assert.equal(parseMessageEvent(value), null)
  }
})

test('HTTP response and WebSocket echo produce just one message regardless of order', () => {
  const received = parseMessageEvent(JSON.stringify({ type: 'message.created', data: message }))!
  assert.deepEqual(mergeMessage(mergeMessage([], received), message), [message])
  assert.deepEqual(mergeMessage(mergeMessage([], message), received), [message])
})
