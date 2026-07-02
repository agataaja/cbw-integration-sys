import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  CAlert,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CPagination,
  CPaginationItem,
  CRow,
  CSpinner,
  CTable,
  CTableBody,
  CTableDataCell,
  CFormLabel,
  CFormSelect,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'
import { fetchArenaClients, fetchArenaEvents } from 'src/services/arena'

const PAGE_SIZE = 10

const formatDateTime = (value) => {
  if (!value) {
    return '-'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString()
}

const ArenaEventsList = () => {
  const navigate = useNavigate()

  const [clients, setClients] = useState([])
  const [selectedClientId, setSelectedClientId] = useState('')
  const [events, setEvents] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [reloadKey, setReloadKey] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()

    const loadClients = async () => {
      try {
        const response = await fetchArenaClients({ signal: controller.signal })
        setClients(response)
      } catch {
        setClients([])
      }
    }

    loadClients()

    return () => {
      controller.abort()
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()

    const loadEvents = async () => {
      setIsLoading(true)
      setError('')

      try {
        const response = await fetchArenaEvents({
          page,
          pageSize: PAGE_SIZE,
          arenaClientId: selectedClientId || undefined,
          signal: controller.signal,
        })

        setEvents(response.results)
        setCount(response.count)
      } catch (requestError) {
        if (requestError.name !== 'AbortError') {
          setError(requestError.message || 'Failed to load Arena events.')
          setEvents([])
          setCount(0)
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    loadEvents()

    return () => {
      controller.abort()
    }
  }, [page, reloadKey, selectedClientId])

  const totalPages = useMemo(() => {
    if (count === 0) {
      return 1
    }

    return Math.ceil(count / PAGE_SIZE)
  }, [count])

  const pageItems = useMemo(() => {
    const windowSize = 5
    const start = Math.max(1, page - 2)
    const end = Math.min(totalPages, start + windowSize - 1)
    const pages = []

    for (let currentPage = start; currentPage <= end; currentPage += 1) {
      pages.push(currentPage)
    }

    return pages
  }, [page, totalPages])

  const from = count === 0 ? 0 : (page - 1) * PAGE_SIZE + 1
  const to = Math.min(page * PAGE_SIZE, count)

  return (
    <CRow>
      <CCol xs={12}>
        <CCard className="mb-4">
          <CCardHeader className="d-flex justify-content-between align-items-center">
            <div>
              <strong>Arena Events</strong>
              <span className="text-body-secondary ms-2">Paginated list from Django API</span>
            </div>
            <div className="d-flex gap-2">
              <CButton color="primary" variant="outline" onClick={() => navigate('/arena/sync')}>
                Open Sync
              </CButton>
              <CButton
                color="secondary"
                variant="outline"
                onClick={() => {
                  setPage(1)
                  setReloadKey((value) => value + 1)
                }}
                disabled={isLoading}
              >
                Refresh
              </CButton>
            </div>
          </CCardHeader>
          <CCardBody>
            <CRow className="g-3 mb-3">
              <CCol md={6}>
                <CFormLabel htmlFor="events-client-filter">Arena Client Filter</CFormLabel>
                <CFormSelect
                  id="events-client-filter"
                  value={selectedClientId}
                  onChange={(event) => {
                    setSelectedClientId(event.target.value)
                    setPage(1)
                  }}
                >
                  <option value="">All clients</option>
                  {clients.map((client) => (
                    <option key={client.id} value={String(client.id)}>
                      {client.name} (ID: {client.id})
                    </option>
                  ))}
                </CFormSelect>
              </CCol>
            </CRow>

            {isLoading && (
              <div className="d-flex justify-content-center py-5">
                <CSpinner color="primary" />
              </div>
            )}

            {!isLoading && error && (
              <CAlert
                color="danger"
                className="d-flex justify-content-between align-items-center mb-0"
              >
                <span>{error}</span>
                <CButton
                  color="danger"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setPage(1)
                    setReloadKey((value) => value + 1)
                  }}
                >
                  Retry
                </CButton>
              </CAlert>
            )}

            {!isLoading && !error && events.length === 0 && (
              <CAlert color="info" className="mb-0">
                No Arena events were found.
              </CAlert>
            )}

            {!isLoading && !error && events.length > 0 && (
              <>
                <CTable striped hover responsive>
                  <CTableHead>
                    <CTableRow>
                      <CTableHeaderCell scope="col">ID</CTableHeaderCell>
                      <CTableHeaderCell scope="col">Arena Event ID</CTableHeaderCell>
                      <CTableHeaderCell scope="col">Name</CTableHeaderCell>
                      <CTableHeaderCell scope="col">Arena Client</CTableHeaderCell>
                      <CTableHeaderCell scope="col">Created At</CTableHeaderCell>
                      <CTableHeaderCell scope="col" className="text-end">
                        Actions
                      </CTableHeaderCell>
                    </CTableRow>
                  </CTableHead>
                  <CTableBody>
                    {events.map((event) => (
                      <CTableRow key={event.id}>
                        <CTableDataCell>{event.id}</CTableDataCell>
                        <CTableDataCell>{event.event_id || '-'}</CTableDataCell>
                        <CTableDataCell>{event.name || '-'}</CTableDataCell>
                        <CTableDataCell>{event.arena_client || '-'}</CTableDataCell>
                        <CTableDataCell>{formatDateTime(event.created_at)}</CTableDataCell>
                        <CTableDataCell className="text-end">
                          <CButton
                            size="sm"
                            color="primary"
                            variant="outline"
                            className="me-2"
                            onClick={() =>
                              navigate(
                                `/arena/sync?clientId=${event.arena_client}&eventId=${encodeURIComponent(event.event_id || '')}`,
                              )
                            }
                          >
                            Sync
                          </CButton>
                          <CButton
                            size="sm"
                            color="success"
                            variant="outline"
                            onClick={() =>
                              navigate(
                                `/arena/fights?eventId=${encodeURIComponent(event.event_id || '')}&eventName=${encodeURIComponent(event.name || '')}`,
                              )
                            }
                          >
                            Fights
                          </CButton>
                        </CTableDataCell>
                      </CTableRow>
                    ))}
                  </CTableBody>
                </CTable>

                <div className="d-flex flex-column flex-md-row justify-content-between align-items-center gap-2 mt-3">
                  <span className="text-body-secondary small">
                    Showing {from}-{to} of {count} events
                  </span>

                  <CPagination className="mb-0" aria-label="Arena events pagination">
                    <CPaginationItem
                      aria-label="Previous page"
                      disabled={page <= 1}
                      onClick={() => setPage((current) => Math.max(1, current - 1))}
                    >
                      Previous
                    </CPaginationItem>

                    {pageItems.map((pageNumber) => (
                      <CPaginationItem
                        key={pageNumber}
                        active={pageNumber === page}
                        onClick={() => setPage(pageNumber)}
                      >
                        {pageNumber}
                      </CPaginationItem>
                    ))}

                    <CPaginationItem
                      aria-label="Next page"
                      disabled={page >= totalPages}
                      onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                    >
                      Next
                    </CPaginationItem>
                  </CPagination>
                </div>
              </>
            )}
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>
  )
}

export default ArenaEventsList
