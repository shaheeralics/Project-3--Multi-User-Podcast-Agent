export const API_BASE = import.meta.env.VITE_API_BASE || ''

async function jsonPost(path: string, body: any, responseType: 'json' | 'blob' = 'json'){
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body)
  })
  if(!res.ok){
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  if(responseType === 'blob') return await res.blob()
  return await res.json()
}

export async function fetchVoices(elevenlabs_api_key: string){
  return jsonPost('/api/voices', { elevenlabs_api_key })
}

export async function previewVoice(elevenlabs_api_key: string, voice_id: string, text?: string){
  const blob = await jsonPost('/api/voice-preview', { elevenlabs_api_key, voice_id, text }, 'blob')
  return URL.createObjectURL(blob)
}

export async function generateScript(payload: {
  url: string
  openai_api_key: string
  host_name: string
  guest_name: string
  aussie?: boolean
  model?: string
}){
  return jsonPost('/api/generate-script', payload)
}

export async function generateAudio(payload: {
  script: any[]
  elevenlabs_api_key: string
  host_voice_id: string
  guest_voice_id: string
  pause_ms: number
}){
  const blob = await jsonPost('/api/generate-audio', payload, 'blob')
  return blob
}
