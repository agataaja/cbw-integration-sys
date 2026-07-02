import React, { useEffect, useMemo, useState } from 'react'
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
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'
import {
  createClientBridge,
  createEventBridge,
  extractFieldErrors,
  fetchAgeGroupMappings,
  fetchArenaClients,
  fetchArenaEvents,
  fetchClientBridges,
  fetchEventBridges,
  fetchSgeEvents,
  syncEventBridgeFights,
  syncEventBridgeRankings,
} from 'src/services/arena'

const INITIAL_EVENT_BRIDGE_FORM = {
  nome: '',
  arena_event: '',
  sge_event: '',
  age_group: '',
  sge_age_category: '',
  age_group_mapping_ids: [],
}

const INITIAL_CLIENT_BRIDGE_FORM = {
  arena_client: '',
  eventos_match_ids: [],
}

const ArenaBridgeSync = () => {
  const [arenaEvents, setArenaEvents] = useState([])
  const [arenaClients, setArenaClients] = useState([])
  const [sgeEvents, setSgeEvents] = useState([])
  const [ageGroups, setAgeGroups] = useState([])
  const [eventBridges, setEventBridges] = useState([])
  const [clientBridges, setClientBridges] = useState([])

  const [eventBridgeForm, setEventBridgeForm] = useState(INITIAL_EVENT_BRIDGE_FORM)
  const [clientBridgeForm, setClientBridgeForm] = useState(INITIAL_CLIENT_BRIDGE_FORM)

  const [credentialClientId, setCredentialClientId] = useState('')

  const [eventBridgeErrors, setEventBridgeErrors] = useState({})
  const [clientBridgeErrors, setClientBridgeErrors] = useState({})

  const [isLoading, setIsLoading] = useState(true)
  const [isSavingEventBridge, setIsSavingEventBridge] = useState(false)
  const [isSavingClientBridge, setIsSavingClientBridge] = useState(false)
  const [syncingBridgeId, setSyncingBridgeId] = useState(null)

  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  const eventsById = useMemo(() => {
    const map = new Map()
    arenaEvents.forEach((event) => {
      map.set(event.id, event)
    })
    return map
  }, [arenaEvents])

  const loadReferenceData = async () => {
    setIsLoading(true)
    setError('')

    try {
      const [clients, sge, groups, bridges, clientBridgeList, allEvents] = await Promise.all([
        fetchArenaClients(),
        fetchSgeEvents(),
        fetchAgeGroupMappings(),
        fetchEventBridges(),
        fetchClientBridges(),
        fetchArenaEvents({ page: 1, pageSize: 100 }),
      ])

      setArenaClients(clients)
      setSgeEvents(sge)
      setAgeGroups(groups)
      setEventBridges(bridges)
      setClientBridges(clientBridgeList)
      setArenaEvents(allEvents.results)

      if (clients.length > 0) {
        setCredentialClientId(String(clients[0].id))
        setClientBridgeForm((current) => ({
          ...current,
          arena_client: String(clients[0].id),
        }))
      }
    } catch (requestError) {
      setError(requestError.message || 'Failed to load bridge synchronization data.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadReferenceData()
  }, [])

  const toIdArray = (selectedOptions) =>
    Array.from(selectedOptions)
      .map((option) => Number(option.value))
      .filter(Boolean)

  const handleEventBridgeCreate = async () => {
    setIsSavingEventBridge(true)
    setEventBridgeErrors({})
    setError('')
    setSuccessMessage('')

    try {
      await createEventBridge({
        ...eventBridgeForm,
        arena_event: Number(eventBridgeForm.arena_event),
        sge_event: Number(eventBridgeForm.sge_event),
      })

      const refreshed = await fetchEventBridges()
      setEventBridges(refreshed)
      setEventBridgeForm(INITIAL_EVENT_BRIDGE_FORM)
      setSuccessMessage('Event bridge created successfully.')
    } catch (requestError) {
      setEventBridgeErrors(extractFieldErrors(requestError))
      setError(requestError.message || 'Failed to create event bridge.')
    } finally {
      setIsSavingEventBridge(false)
    }
  }

  const handleClientBridgeCreate = async () => {
    setIsSavingClientBridge(true)
    setClientBridgeErrors({})
    setError('')
    setSuccessMessage('')

    try {
      await createClientBridge({
        arena_client: Number(clientBridgeForm.arena_client),
        eventos_match_ids: clientBridgeForm.eventos_match_ids,
      })

      const refreshed = await fetchClientBridges()
      setClientBridges(refreshed)
      setClientBridgeForm((current) => ({
        ...current,
        eventos_match_ids: [],
      }))
      setSuccessMessage('Client bridge created successfully.')
    } catch (requestError) {
      setClientBridgeErrors(extractFieldErrors(requestError))
      setError(requestError.message || 'Failed to create client bridge.')
    } finally {
      setIsSavingClientBridge(false)
    }
  }

  const runBridgeSync = async (bridgeId, mode) => {
    if (!credentialClientId) {
      setError('Select a credential client before running sync actions.')
      return
    }

    setSyncingBridgeId(bridgeId)
    setError('')
    setSuccessMessage('')

    try {
      if (mode === 'rankings') {
        await syncEventBridgeRankings(bridgeId, {
          credentialId: Number(credentialClientId),
        })
        setSuccessMessage(`Rankings sync completed for bridge ${bridgeId}.`)
      } else {
        await syncEventBridgeFights(bridgeId, {
          credentialId: Number(credentialClientId),
        })
        setSuccessMessage(`Fights sync completed for bridge ${bridgeId}.`)
      }
    } catch (requestError) {
      setError(requestError.message || 'Bridge sync failed.')
    } finally {
      setSyncingBridgeId(null)
    }
  }

  return (
    <CRow>
      <CCol xs={12}>
        <CCard className="mb-4">
          <CCardHeader>
            <strong>Bridge Sync</strong>
            <span className="text-body-secondary ms-2">
              Arena event to SGE event mapping, client bridges, and sync actions
            </span>
          </CCardHeader>
          <CCardBody>
            {error && <CAlert color="danger">{error}</CAlert>}
            {successMessage && <CAlert color="success">{successMessage}</CAlert>}

            {isLoading ? (
              <div className="d-flex justify-content-center py-5">
                <CSpinner color="primary" />
              </div>
            ) : (
              <>
                <CRow className="g-4">
                  <CCol lg={6}>
                    <CCard className="h-100">
                      <CCardHeader>
                        <strong>Create Event Bridge</strong>
                      </CCardHeader>
                      <CCardBody>
                        <CRow className="g-3">
                          <CCol xs={12}>
                            <CFormLabel htmlFor="bridge-name">Bridge Name</CFormLabel>
                            <CFormInput
                              id="bridge-name"
                              value={eventBridgeForm.nome}
                              onChange={(event) =>
                                setEventBridgeForm((current) => ({
                                  ...current,
                                  nome: event.target.value,
                                }))
                              }
                            />
                          </CCol>

                          <CCol md={6}>
                            <CFormLabel htmlFor="bridge-arena-event">Arena Event</CFormLabel>
                            <CFormSelect
                              id="bridge-arena-event"
                              value={eventBridgeForm.arena_event}
                              onChange={(event) =>
                                setEventBridgeForm((current) => ({
                                  ...current,
                                  arena_event: event.target.value,
                                }))
                              }
                            >
                              <option value="">Select arena event</option>
                              {arenaEvents.map((event) => (
                                <option key={event.id} value={event.id}>
                                  {event.name}
                                </option>
                              ))}
                            </CFormSelect>
                          </CCol>

                          <CCol md={6}>
                            <CFormLabel htmlFor="bridge-sge-event">SGE Event</CFormLabel>
                            <CFormSelect
                              id="bridge-sge-event"
                              value={eventBridgeForm.sge_event}
                              onChange={(event) =>
                                setEventBridgeForm((current) => ({
                                  ...current,
                                  sge_event: event.target.value,
                                }))
                              }
                            >
                              <option value="">Select SGE event</option>
                              {sgeEvents.map((event) => (
                                <option key={event.id} value={event.id}>
                                  {event.descricao}
                                </option>
                              ))}
                            </CFormSelect>
                          </CCol>

                          <CCol md={6}>
                            <CFormLabel htmlFor="bridge-age-group">
                              Legacy Arena Age Group
                            </CFormLabel>
                            <CFormInput
                              id="bridge-age-group"
                              value={eventBridgeForm.age_group}
                              onChange={(event) =>
                                setEventBridgeForm((current) => ({
                                  ...current,
                                  age_group: event.target.value,
                                }))
                              }
                            />
                          </CCol>

                          <CCol md={6}>
                            <CFormLabel htmlFor="bridge-sge-age">
                              Legacy SGE Age Category
                            </CFormLabel>
                            <CFormInput
                              id="bridge-sge-age"
                              value={eventBridgeForm.sge_age_category}
                              onChange={(event) =>
                                setEventBridgeForm((current) => ({
                                  ...current,
                                  sge_age_category: event.target.value,
                                }))
                              }
                            />
                          </CCol>

                          <CCol xs={12}>
                            <CFormLabel htmlFor="bridge-age-mappings">
                              Age Group Mappings (Normalized)
                            </CFormLabel>
                            <CFormSelect
                              id="bridge-age-mappings"
                              multiple
                              value={eventBridgeForm.age_group_mapping_ids.map(String)}
                              onChange={(event) =>
                                setEventBridgeForm((current) => ({
                                  ...current,
                                  age_group_mapping_ids: toIdArray(event.target.selectedOptions),
                                }))
                              }
                              style={{ minHeight: '8rem' }}
                            >
                              {ageGroups.map((mapping) => (
                                <option key={mapping.id} value={mapping.id}>
                                  {mapping.canonical_name}
                                </option>
                              ))}
                            </CFormSelect>
                          </CCol>

                          {(eventBridgeErrors?.detail || eventBridgeErrors?.non_field_errors) && (
                            <CCol xs={12}>
                              <CAlert color="danger" className="mb-0">
                                {eventBridgeErrors?.detail ||
                                  eventBridgeErrors?.non_field_errors?.[0] ||
                                  'Validation error while creating event bridge.'}
                              </CAlert>
                            </CCol>
                          )}

                          <CCol xs={12}>
                            <CButton
                              color="primary"
                              disabled={isSavingEventBridge}
                              onClick={handleEventBridgeCreate}
                            >
                              {isSavingEventBridge ? 'Creating...' : 'Create Event Bridge'}
                            </CButton>
                          </CCol>
                        </CRow>
                      </CCardBody>
                    </CCard>
                  </CCol>

                  <CCol lg={6}>
                    <CCard className="h-100">
                      <CCardHeader>
                        <strong>Create Client Bridge</strong>
                      </CCardHeader>
                      <CCardBody>
                        <CRow className="g-3">
                          <CCol xs={12}>
                            <CFormLabel htmlFor="client-bridge-client">Arena Client</CFormLabel>
                            <CFormSelect
                              id="client-bridge-client"
                              value={clientBridgeForm.arena_client}
                              onChange={(event) =>
                                setClientBridgeForm((current) => ({
                                  ...current,
                                  arena_client: event.target.value,
                                }))
                              }
                            >
                              <option value="">Select arena client</option>
                              {arenaClients.map((client) => (
                                <option key={client.id} value={client.id}>
                                  {client.name}
                                </option>
                              ))}
                            </CFormSelect>
                          </CCol>

                          <CCol xs={12}>
                            <CFormLabel htmlFor="client-bridge-events">Event Bridges</CFormLabel>
                            <CFormSelect
                              id="client-bridge-events"
                              multiple
                              value={clientBridgeForm.eventos_match_ids.map(String)}
                              onChange={(event) =>
                                setClientBridgeForm((current) => ({
                                  ...current,
                                  eventos_match_ids: toIdArray(event.target.selectedOptions),
                                }))
                              }
                              style={{ minHeight: '8rem' }}
                            >
                              {eventBridges.map((bridge) => (
                                <option key={bridge.id} value={bridge.id}>
                                  {bridge.nome}
                                </option>
                              ))}
                            </CFormSelect>
                          </CCol>

                          {(clientBridgeErrors?.detail || clientBridgeErrors?.non_field_errors) && (
                            <CCol xs={12}>
                              <CAlert color="danger" className="mb-0">
                                {clientBridgeErrors?.detail ||
                                  clientBridgeErrors?.non_field_errors?.[0] ||
                                  'Validation error while creating client bridge.'}
                              </CAlert>
                            </CCol>
                          )}

                          <CCol xs={12}>
                            <CButton
                              color="primary"
                              disabled={isSavingClientBridge}
                              onClick={handleClientBridgeCreate}
                            >
                              {isSavingClientBridge ? 'Creating...' : 'Create Client Bridge'}
                            </CButton>
                          </CCol>
                        </CRow>
                      </CCardBody>
                    </CCard>
                  </CCol>
                </CRow>

                <CRow className="g-4 mt-1">
                  <CCol xs={12}>
                    <CCard>
                      <CCardHeader className="d-flex justify-content-between align-items-center">
                        <strong>Event Bridge Sync Actions</strong>
                        <div className="d-flex align-items-center gap-2">
                          <CFormLabel htmlFor="bridge-credential" className="mb-0">
                            Credential Client
                          </CFormLabel>
                          <CFormSelect
                            id="bridge-credential"
                            value={credentialClientId}
                            onChange={(event) => setCredentialClientId(event.target.value)}
                          >
                            <option value="">Select credential client</option>
                            {arenaClients.map((client) => (
                              <option key={client.id} value={client.id}>
                                {client.name}
                              </option>
                            ))}
                          </CFormSelect>
                        </div>
                      </CCardHeader>
                      <CCardBody>
                        {eventBridges.length === 0 ? (
                          <CAlert color="info" className="mb-0">
                            No event bridges found.
                          </CAlert>
                        ) : (
                          <CTable striped hover responsive>
                            <CTableHead>
                              <CTableRow>
                                <CTableHeaderCell>ID</CTableHeaderCell>
                                <CTableHeaderCell>Name</CTableHeaderCell>
                                <CTableHeaderCell>Arena Event</CTableHeaderCell>
                                <CTableHeaderCell>SGE Event</CTableHeaderCell>
                                <CTableHeaderCell>Age Mapping</CTableHeaderCell>
                                <CTableHeaderCell className="text-end">Sync</CTableHeaderCell>
                              </CTableRow>
                            </CTableHead>
                            <CTableBody>
                              {eventBridges.map((bridge) => {
                                const arenaEvent = eventsById.get(bridge.arena_event)
                                return (
                                  <CTableRow key={bridge.id}>
                                    <CTableDataCell>{bridge.id}</CTableDataCell>
                                    <CTableDataCell>{bridge.nome}</CTableDataCell>
                                    <CTableDataCell>
                                      {arenaEvent?.name || bridge.arena_event}
                                    </CTableDataCell>
                                    <CTableDataCell>
                                      {bridge.sge_event?.descricao || '-'}
                                    </CTableDataCell>
                                    <CTableDataCell>
                                      {bridge.age_group_mappings?.length
                                        ? bridge.age_group_mappings
                                            .map((mapping) => mapping.canonical_name)
                                            .join(', ')
                                        : bridge.age_group || '-'}
                                    </CTableDataCell>
                                    <CTableDataCell className="text-end">
                                      <CButton
                                        size="sm"
                                        color="primary"
                                        variant="outline"
                                        className="me-2"
                                        disabled={
                                          syncingBridgeId === bridge.id || !credentialClientId
                                        }
                                        onClick={() => runBridgeSync(bridge.id, 'rankings')}
                                      >
                                        Sync Rankings
                                      </CButton>
                                      <CButton
                                        size="sm"
                                        color="success"
                                        variant="outline"
                                        disabled={
                                          syncingBridgeId === bridge.id || !credentialClientId
                                        }
                                        onClick={() => runBridgeSync(bridge.id, 'fights')}
                                      >
                                        Sync Fights
                                      </CButton>
                                    </CTableDataCell>
                                  </CTableRow>
                                )
                              })}
                            </CTableBody>
                          </CTable>
                        )}
                      </CCardBody>
                    </CCard>
                  </CCol>

                  <CCol xs={12}>
                    <CCard>
                      <CCardHeader>
                        <strong>Client Bridge List</strong>
                      </CCardHeader>
                      <CCardBody>
                        {clientBridges.length === 0 ? (
                          <CAlert color="info" className="mb-0">
                            No client bridges found.
                          </CAlert>
                        ) : (
                          <CTable striped responsive>
                            <CTableHead>
                              <CTableRow>
                                <CTableHeaderCell>ID</CTableHeaderCell>
                                <CTableHeaderCell>Arena Client</CTableHeaderCell>
                                <CTableHeaderCell>Event Bridges</CTableHeaderCell>
                              </CTableRow>
                            </CTableHead>
                            <CTableBody>
                              {clientBridges.map((bridge) => (
                                <CTableRow key={bridge.id}>
                                  <CTableDataCell>{bridge.id}</CTableDataCell>
                                  <CTableDataCell>{bridge.arena_client}</CTableDataCell>
                                  <CTableDataCell>
                                    {bridge.eventos_match?.length
                                      ? bridge.eventos_match
                                          .map((eventBridge) => eventBridge.nome)
                                          .join(', ')
                                      : '-'}
                                  </CTableDataCell>
                                </CTableRow>
                              ))}
                            </CTableBody>
                          </CTable>
                        )}
                      </CCardBody>
                    </CCard>
                  </CCol>
                </CRow>
              </>
            )}
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>
  )
}

export default ArenaBridgeSync
