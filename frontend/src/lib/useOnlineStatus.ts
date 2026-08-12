// Connectivity status (Experience Cycle 1, Phase E).
//
// A minimal, truthful read of the browser's own online/offline signal. It adds NO
// persistence layer and makes no claim about offline capability — it only lets
// Today tell the difference between "cached data is still on screen but stale" and
// "there is nothing to show and we are offline". `navigator.onLine` is a hint, so
// this is used for presentation only, never to gate authorization or data writes.

import { useSyncExternalStore } from 'react'

function subscribe(callback: () => void): () => void {
  window.addEventListener('online', callback)
  window.addEventListener('offline', callback)
  return () => {
    window.removeEventListener('online', callback)
    window.removeEventListener('offline', callback)
  }
}

function getSnapshot(): boolean {
  return navigator.onLine
}

export function useOnlineStatus(): boolean {
  // Server snapshot is `true` so SSR/first paint never flashes an offline state.
  return useSyncExternalStore(subscribe, getSnapshot, () => true)
}
