import React, { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  CAlert,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CFormInput,
  CFormLabel,
  CFormSelect,
  CRow,
  CSpinner,
} from '@coreui/react'
import {
  fetchArenaClients,
  fetchArenaEvents,
  syncArenaEventStructure,
  syncArenaSportEvents,
} from 'src/services/arena'

const ArenaSync = () => {
  const [searchParams] = useSearchParams()
  const prefilledClientId = searchParams.get('clientId') || ''
  const prefilledEventId = searchParams.get('eventId') || ''

  const [clients, setClients] = useState([])
  const [events, setEvents] = useState([])

  const [selectedClientId, setSelectedClientId] = useState('')
  const [selectedEventId, setSelectedEventId] = useState('')

  const [isLoadingClients, setIsLoadingClients] = useState(true)
  const [isLoadingEvents, setIsLoadingEvents] = useState(false)

  const [isSyncingEvents, setIsSyncingEvents] = useState(false)
  const [isSyncingStructure, setIsSyncingStructure] = useState(false)

  const [error, setError] = useState('')
  const [eventSyncResult, setEventSyncResult] = useState(null)
  const [structureSyncResult, setStructureSyncResult] = useState(null)

  useEffect(() => {
    const loadClients = async () => {
      setIsLoadingClients(true)
      setError('')

      try {
        const response = await fetchArenaClients()
        setClients(response)
        if (prefilledClientId) {
          setSelectedClientId(prefilledClientId)
        } else if (response.length > 0) {
          setSelectedClientId(String(response[0].id))
        }
      } catch (requestError) {
        setError(requestError.message || 'Failed to load Arena clients.')
        setClients([])
      } finally {
        setIsLoadingClients(false)
      }
    }

    loadClients()
  }, [prefilledClientId])

  useEffect(() => {
    if (!selectedClientId) {
      setEvents([])
      setSelectedEventId('')
      return
    }

    const controller = new AbortController()

    const loadEvents = async () => {
      setIsLoadingEvents(true)
      setError('')

      try {
        const response = await fetchArenaEvents({
          page: 1,
          pageSize: 100,
          arenaClientId: selectedClientId,
          signal: controller.signal,
        })
        setEvents(response.results)
        if (prefilledEventId) {
          const matched = response.results.find((event) => event.event_id === prefilledEventId)
          if (matched) {
            setSelectedEventId(prefilledEventId)
          }
        }
      } catch (requestError) {
        if (requestError.name !== 'AbortError') {
          setError(requestError.message || 'Failed to load Arena events for selected client.')
          setEvents([])
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoadingEvents(false)
        }
      }
    }

    loadEvents()

    return () => {
      controller.abort()
    }
  }, [selectedClientId, prefilledEventId])

  const runSportEventSync = async () => {
    if (!selectedClientId) {
      setError('Select an Arena client before running sync.')
      return
    }

    setIsSyncingEvents(true)
    setError('')

    try {
      const result = await syncArenaSportEvents({
        arenaClientId: Number(selectedClientId),
      })
      setEventSyncResult(result)
      setStructureSyncResult(null)
      const refreshedEvents = await fetchArenaEvents({
        page: 1,
        pageSize: 100,
        arenaClientId: selectedClientId,
      })
      setEvents(refreshedEvents.results)
    } catch (requestError) {
      setError(requestError.message || 'Failed to sync sport events.')
    } finally {
      setIsSyncingEvents(false)
    }
  }

  const runEventStructureSync = async () => {
    if (!selectedClientId || !selectedEventId) {
      setError('Select an Arena client and event before syncing event structure.')
      return
    }

    setIsSyncingStructure(true)
    setError('')

    try {
      const result = await syncArenaEventStructure({
        arenaClientId: Number(selectedClientId),
        arenaEventId: selectedEventId,
      })
      setStructureSyncResult(result)
      setEventSyncResult(null)
    } catch (requestError) {
      setError(requestError.message || 'Failed to sync event structure.')
    } finally {
      setIsSyncingStructure(false)
    }
  }

  return (
    <CRow>
      <CCol xs={12}>
        <CCard className="mb-4">
          <CCardHeader>
            <strong>Arena Sync Control</strong>
            <span className="text-body-secondary ms-2">
              Trigger backend integration sync actions
            </span>
          </CCardHeader>
          <CCardBody>
            {error && <CAlert color="danger">{error}</CAlert>}

            {isLoadingClients ? (
              <div className="d-flex justify-content-center py-5">
                <CSpinner color="primary" />
              </div>
            ) : (
              <>
                <CRow className="g-3">
                  <CCol md={6}>
                    <CFormLabel htmlFor="arena-client-id">Arena Client</CFormLabel>
                    <CFormSelect
                      id="arena-client-id"
                      value={selectedClientId}
                      onChange={(event) => {
                        setSelectedClientId(event.target.value)
                        setSelectedEventId('')
                      }}
                    >
                      <option value="">Select a client</option>
                      {clients.map((client) => (
                        <option key={client.id} value={client.id}>
                          {client.name} (ID: {client.id})
                        </option>
                      ))}
                    </CFormSelect>
                  </CCol>

                  <CCol md={6}>
                    <CFormLabel htmlFor="arena-event-id">Arena Event</CFormLabel>
                    <CFormSelect
                      id="arena-event-id"
                      value={selectedEventId}
                      onChange={(event) => setSelectedEventId(event.target.value)}
                      disabled={!selectedClientId || isLoadingEvents}
                    >
                      <option value="">Select an event</option>
                      {events.map((event) => (
                        <option key={event.id} value={event.event_id}>
                          {event.name}
                        </option>
                      ))}
                    </CFormSelect>
                  </CCol>

                  <CCol xs={12}>
                    <CFormLabel htmlFor="selected-event-readonly">Selected Event ID</CFormLabel>
                    <CFormInput id="selected-event-readonly" value={selectedEventId} readOnly />
                  </CCol>
                </CRow>

                <div className="d-flex flex-column flex-md-row gap-2 mt-4">
                  <CButton
                    color="primary"
                    disabled={isSyncingEvents || !selectedClientId}
                    onClick={runSportEventSync}
                  >
                    {isSyncingEvents ? 'Syncing Events...' : 'Sync Sport Events'}
                  </CButton>
                  <CButton
                    color="success"
                    disabled={isSyncingStructure || !selectedClientId || !selectedEventId}
                    onClick={runEventStructureSync}
                  >
                    {isSyncingStructure ? 'Syncing Structure...' : 'Sync Event Structure'}
                  </CButton>
                </div>

                {eventSyncResult && (
                  <CAlert color="success" className="mt-4 mb-0">
                    <strong>Sport Events Sync Completed</strong>
                    <div>Client ID: {eventSyncResult.arena_client_id}</div>
                    <div>Events Synced: {eventSyncResult.events_synced}</div>
                  </CAlert>
                )}

                {structureSyncResult && (
                  <CAlert color="success" className="mt-4 mb-0">
                    <strong>Event Structure Sync Completed</strong>
                    <div>Client ID: {structureSyncResult.arena_client_id}</div>
                    <div>Event ID: {structureSyncResult.arena_event_id}</div>
                    <div>Categories Synced: {structureSyncResult.categories_synced}</div>
                    <div>Fights Synced: {structureSyncResult.fights_synced}</div>
                    <div>Fighters Synced: {structureSyncResult.fighters_synced}</div>
                  </CAlert>
                )}
              </>
            )}
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>
  )
}

export default ArenaSync
