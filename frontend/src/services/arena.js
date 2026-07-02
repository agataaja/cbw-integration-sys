const DEFAULT_API_BASE_URL = 'http://localhost:8001'

const API_BASE_URL = (import.meta.env.VITE_API_URL || DEFAULT_API_BASE_URL).replace(/\/$/, '')

class ArenaApiError extends Error {
  constructor(message, { status, details } = {}) {
    super(message)
    this.name = 'ArenaApiError'
    this.status = status
    this.details = details
  }
}

const toQueryString = (params) => {
  const query = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value))
    }
  })

  return query.toString()
}

const firstValidationMessage = (payload) => {
  if (!payload || typeof payload !== 'object') {
    return null
  }

  if (typeof payload.detail === 'string') {
    return payload.detail
  }

  const [firstKey] = Object.keys(payload)
  const firstValue = payload[firstKey]

  if (Array.isArray(firstValue) && firstValue.length > 0) {
    return String(firstValue[0])
  }

  if (typeof firstValue === 'string') {
    return firstValue
  }

  return null
}

const parseErrorBody = async (response) => {
  const contentType = response.headers.get('content-type') || ''

  if (contentType.includes('application/json')) {
    try {
      return await response.json()
    } catch {
      return null
    }
  }

  try {
    const text = await response.text()
    return text || null
  } catch {
    return null
  }
}

const requestArenaApi = async (path, { method = 'GET', body, signal } = {}) => {
  const headers = {
    Accept: 'application/json',
  }

  const requestConfig = {
    method,
    headers,
    signal,
  }

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    requestConfig.body = JSON.stringify(body)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, requestConfig)

  if (!response.ok) {
    const details = await parseErrorBody(response)
    const message =
      firstValidationMessage(details) || `Request failed with status ${response.status}`
    throw new ArenaApiError(message, {
      status: response.status,
      details,
    })
  }

  if (response.status === 204) {
    return null
  }

  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    return null
  }

  return response.json()
}

export const extractFieldErrors = (error) => {
  if (error instanceof ArenaApiError && error.details && typeof error.details === 'object') {
    return error.details
  }

  return {}
}

export const fetchArenaEvents = async ({ page = 1, pageSize = 10, arenaClientId, signal } = {}) => {
  const query = toQueryString({
    page,
    page_size: pageSize,
    arena_client_id: arenaClientId,
  })

  const payload = await requestArenaApi(`/api/arena/sport-events/?${query}`, { signal })

  if (Array.isArray(payload)) {
    return {
      count: payload.length,
      next: null,
      previous: null,
      results: payload,
    }
  }

  return {
    count: payload?.count ?? 0,
    next: payload?.next ?? null,
    previous: payload?.previous ?? null,
    results: Array.isArray(payload?.results) ? payload.results : [],
  }
}

export const fetchArenaClients = async ({ signal } = {}) => {
  const payload = await requestArenaApi('/api/arena/clients/', { signal })
  return Array.isArray(payload) ? payload : []
}

export const createArenaClient = async (clientData, { signal } = {}) => {
  return requestArenaApi('/api/arena/clients/', {
    method: 'POST',
    body: clientData,
    signal,
  })
}

export const updateArenaClient = async (clientId, clientData, { signal } = {}) => {
  return requestArenaApi(`/api/arena/clients/${clientId}/`, {
    method: 'PATCH',
    body: clientData,
    signal,
  })
}

export const deleteArenaClient = async (clientId, { signal } = {}) => {
  return requestArenaApi(`/api/arena/clients/${clientId}/`, {
    method: 'DELETE',
    signal,
  })
}

export const syncArenaSportEvents = async ({ arenaClientId }, { signal } = {}) => {
  return requestArenaApi('/api/arena/sync/sport-events/', {
    method: 'POST',
    body: {
      arena_client_id: arenaClientId,
    },
    signal,
  })
}

export const syncArenaEventStructure = async ({ arenaClientId, arenaEventId }, { signal } = {}) => {
  return requestArenaApi('/api/arena/sync/event-structure/', {
    method: 'POST',
    body: {
      arena_client_id: arenaClientId,
      arena_event_id: arenaEventId,
    },
    signal,
  })
}

export const fetchArenaFights = async ({ arenaEventId, signal } = {}) => {
  const query = toQueryString({ arena_event_id: arenaEventId })
  const payload = await requestArenaApi(`/api/arena/fights/?${query}`, { signal })
  return Array.isArray(payload) ? payload : []
}

export const fetchArenaFighters = async ({ fightId, signal } = {}) => {
  const query = toQueryString({ fight_id: fightId })
  const payload = await requestArenaApi(`/api/arena/fighters/?${query}`, { signal })
  return Array.isArray(payload) ? payload : []
}

export const sendArenaWebhookTest = async (payload, { signal } = {}) => {
  return requestArenaApi('/api/arena/arena-webhook/', {
    method: 'POST',
    body: payload,
    signal,
  })
}

export const fetchSgeEvents = async ({ signal } = {}) => {
  const payload = await requestArenaApi('/api/integration/eventos-sge/', { signal })
  return Array.isArray(payload) ? payload : []
}

export const fetchAgeGroupMappings = async ({ signal } = {}) => {
  const payload = await requestArenaApi('/api/normalization/age-groups/', { signal })
  return Array.isArray(payload) ? payload : []
}

export const fetchEventBridges = async ({ signal } = {}) => {
  const payload = await requestArenaApi('/api/integration/bridge/eventos/', { signal })
  return Array.isArray(payload) ? payload : []
}

export const createEventBridge = async (bridgeData, { signal } = {}) => {
  return requestArenaApi('/api/integration/bridge/eventos/', {
    method: 'POST',
    body: bridgeData,
    signal,
  })
}

export const syncEventBridgeRankings = async (bridgeId, { credentialId }, { signal } = {}) => {
  return requestArenaApi(`/api/integration/bridge/eventos/${bridgeId}/sync-rankings/`, {
    method: 'POST',
    body: {
      credential_id: credentialId,
    },
    signal,
  })
}

export const syncEventBridgeFights = async (bridgeId, { credentialId }, { signal } = {}) => {
  return requestArenaApi(`/api/integration/bridge/eventos/${bridgeId}/sync-fights/`, {
    method: 'POST',
    body: {
      credential_id: credentialId,
    },
    signal,
  })
}

export const fetchClientBridges = async ({ signal } = {}) => {
  const payload = await requestArenaApi('/api/integration/bridge/clients/', { signal })
  return Array.isArray(payload) ? payload : []
}

export const createClientBridge = async (bridgeData, { signal } = {}) => {
  return requestArenaApi('/api/integration/bridge/clients/', {
    method: 'POST',
    body: bridgeData,
    signal,
  })
}
