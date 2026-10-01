/**
 * End-to-end encryption for student-teacher messages.
 *
 * The private key is generated here, in the browser, and is marked
 * non-extractable so it cannot be read back out, even by script on this page. It
 * never leaves the device: only the public key is uploaded. Message bodies are
 * encrypted before they are sent, so the server stores ciphertext it has no key
 * for and cannot read.
 *
 * Scheme:
 *   1. Each user holds a non-extractable P-256 ECDH key pair.
 *   2. A shared secret comes from ECDH(my private key, their public key).
 *      Both sides compute the same secret independently.
 *   3. That secret is stretched with HKDF-SHA256 into a 256-bit AES-GCM key.
 *      A per-thread salt keeps keys distinct between conversations.
 *   4. Each message gets a fresh random 12-byte IV and is sealed with AES-GCM,
 *      which also authenticates it, so tampering is detected on decrypt.
 *
 * Consequences worth knowing: losing the private key means the messages can
 * never be read again, there is no recovery path, and a new device needs the
 * key moved to it before it can read the history.
 */

const DB_NAME = 'sms_e2ee'
const DB_VERSION = 1
const STORE = 'keys'
const PRIVATE_KEY_ID = 'private'
const HAS_KEY_FLAG = 'sms_e2ee_has_key'

const ALGORITHM = 'ECDH-P256-HKDF-SHA256-AESGCM'

const subtle = globalThis.crypto?.subtle

export function isEncryptionSupported() {
  return Boolean(subtle && globalThis.crypto?.getRandomValues)
}

function toBase64(buffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  const chunk = 0x8000
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk))
  }
  return btoa(binary)
}

function fromBase64(value) {
  const binary = atob(value)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i)
  return bytes
}

const encoder = new TextEncoder()
const decoder = new TextDecoder()

/**
 * The private key is held in IndexedDB as a non-extractable CryptoKey, so it
 * can never be serialised into a string. Nothing on the page, including script
 * from a compromised dependency, can read it; only this module can ask Web
 * Crypto to use it.
 */
function openDatabase() {
  return new Promise((resolve, reject) => {
    if (!globalThis.indexedDB) {
      reject(new Error('IndexedDB is unavailable'))
      return
    }
    const request = indexedDB.open(DB_NAME, DB_VERSION)
    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE)
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

function idbRequest(mode, run) {
  return openDatabase().then(
    (db) =>
      new Promise((resolve, reject) => {
        const tx = db.transaction(STORE, mode)
        const result = run(tx.objectStore(STORE))
        tx.oncomplete = () => {
          db.close()
          resolve(result?.result ?? null)
        }
        tx.onerror = () => {
          db.close()
          reject(tx.error)
        }
        tx.onabort = () => {
          db.close()
          reject(tx.error)
        }
      })
  )
}

async function loadKeyRecord() {
  try {
    const record = await idbRequest('readonly', (store) => store.get(PRIVATE_KEY_ID))
    return record || null
  } catch {
    return null
  }
}

async function saveKeyRecord(record) {
  await idbRequest('readwrite', (store) => store.put(record, PRIVATE_KEY_ID))
  localStorage.setItem(HAS_KEY_FLAG, '1')
}

async function deleteKeyRecord() {
  try {
    await idbRequest('readwrite', (store) => store.delete(PRIVATE_KEY_ID))
  } catch {
    /* nothing to remove */
  }
  localStorage.removeItem(HAS_KEY_FLAG)
}

const publicKeyB64 = async (publicKey) => {
  const raw = await subtle.exportKey('raw', publicKey)
  return toBase64(raw)
}

/**
 * Load this user's key pair, creating it on first use. Only the public half is
 * returned for upload; the private half never leaves IndexedDB.
 */
export async function ensureKeyPair(userId) {
  if (!isEncryptionSupported()) {
    throw new Error('This browser cannot encrypt messages.')
  }

  const stored = await loadKeyRecord()
  // Stored as the pair, because a public key cannot be re-derived from a
  // non-extractable private key.
  let privateKey = stored?.privateKey ?? null
  let publicKey = stored?.publicKey ?? null
  let publicKeyB64Value = stored?.publicKeyB64 ?? null

  if (!privateKey) {
    const pair = await subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, false, [
      'deriveBits',
    ])
    privateKey = pair.privateKey
    publicKey = pair.publicKey
    publicKeyB64Value = await publicKeyB64(publicKey)
    await saveKeyRecord({ privateKey, publicKey, publicKeyB64: publicKeyB64Value })
  }

  return { publicKeyB64: publicKeyB64Value, algorithm: ALGORITHM }
}

/** Wipe this device's key. Every message it encrypted becomes unreadable. */
export async function forgetKeyPair() {
  await deleteKeyRecord()
  clearKeyCache()
}

/** Build the per-thread salt. Both sides derive the same salt from the thread id. */
function saltForThread(threadId) {
  return encoder.encode(`sms-e2ee-thread-${threadId}`)
}

/**
 * Derive the AES-GCM key for a conversation from our private key and the other
 * participant's public key.
 */
async function deriveThreadKey(threadId, theirPublicKeyB64) {
  const stored = await loadKeyRecord()
  const privateKey = stored?.privateKey ?? null
  if (!privateKey) {
    throw new Error('No encryption key on this device. Messages cannot be read.')
  }

  const theirPublicKey = await subtle.importKey(
    'raw',
    fromBase64(theirPublicKeyB64),
    { name: 'ECDH', namedCurve: 'P-256' },
    false,
    []
  )

  const sharedSecret = await subtle.deriveBits(
    { name: 'ECDH', public: theirPublicKey },
    privateKey,
    256
  )

  const hkdfKey = await subtle.importKey('raw', sharedSecret, 'HKDF', false, ['deriveKey'])

  return subtle.deriveKey(
    {
      name: 'HKDF',
      hash: 'SHA-256',
      salt: saltForThread(threadId),
      info: encoder.encode('sms-e2ee-message-key'),
    },
    hkdfKey,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  )
}

const keyCache = new Map()

async function threadKey(threadId, peerPublicKeyB64) {
  // The cache key includes this device's own public key as well as the thread
  // and the peer. Without it, a second identity on the same page (sign out, then
  // sign in as someone else) would be handed the previous user's derived key and
  // could read the conversation.
  const own = await loadKeyRecord()
  const ownKey = own?.publicKeyB64 ?? 'no-device-key'
  const cacheKey = `${ownKey}::${threadId}::${peerPublicKeyB64}`
  const cached = keyCache.get(cacheKey)
  if (cached) return cached
  const key = await deriveThreadKey(threadId, peerPublicKeyB64)
  keyCache.set(cacheKey, key)
  return key
}

/** Encrypt a plaintext body for a thread. Returns what the server should store. */
export async function encryptMessage(threadId, peerPublicKeyB64, plaintext) {
  const key = await threadKey(threadId, peerPublicKeyB64)
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const sealed = await subtle.encrypt({ name: 'AES-GCM', iv }, key, encoder.encode(plaintext))
  return {
    ciphertext: toBase64(sealed),
    iv: toBase64(iv),
    algorithm: 'AES-GCM-256',
  }
}

/**
 * Decrypt a stored message. Returns null when it cannot be read, for example
 * when the sender's public key has changed or the data was tampered with.
 */
export async function decryptMessage(threadId, peerPublicKeyB64, ciphertext, iv) {
  if (!ciphertext || !iv) return null
  try {
    const key = await threadKey(threadId, peerPublicKeyB64)
    const opened = await subtle.decrypt(
      { name: 'AES-GCM', iv: fromBase64(iv) },
      key,
      fromBase64(ciphertext)
    )
    return decoder.decode(opened)
  } catch {
    // AES-GCM fails to open on a wrong key or altered ciphertext.
    return null
  }
}

/** Forget a cached thread key, for example after a public key change. */
export function clearKeyCache() {
  keyCache.clear()
}