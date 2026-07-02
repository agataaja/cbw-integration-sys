import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  CAlert,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CFormInput,
  CFormLabel,
  CRow,
  CSpinner,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'
import { fetchArenaFights } from 'src/services/arena'

const ArenaFightsList = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [eventIdInput, setEventIdInput] = useState(searchParams.get('eventId') || '')
  const [eventName] = useState(searchParams.get('eventName') || '')
  const [fights, setFights] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const loadFights = async (arenaEventId) => {
    if (!arenaEventId) {
      setFights([])
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const response = await fetchArenaFights({ arenaEventId })
      setFights(response)
    } catch (requestError) {
      setError(requestError.message || 'Failed to load Arena fights.')
      setFights([])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (eventIdInput) {
      loadFights(eventIdInput)
    }
  }, [eventIdInput])

  return (
    <CRow>
      <CCol xs={12}>
        <CCard className="mb-4">
          <CCardHeader className="d-flex justify-content-between align-items-center">
            <div>
              <strong>Arena Fights</strong>
              {eventName && <span className="text-body-secondary ms-2">Event: {eventName}</span>}
            </div>
            <CButton color="primary" variant="outline" onClick={() => navigate('/arena/events')}>
              Back To Events
            </CButton>
          </CCardHeader>
          <CCardBody>
            <CRow className="g-3 mb-3">
              <CCol md={8}>
                <CFormLabel htmlFor="arena-event-id-filter">Arena Event ID</CFormLabel>
                <CFormInput
                  id="arena-event-id-filter"
                  value={eventIdInput}
                  onChange={(event) => setEventIdInput(event.target.value)}
                  placeholder="Enter arena event id"
                />
              </CCol>
              <CCol md={4} className="d-flex align-items-end">
                <CButton
                  color="primary"
                  onClick={() => loadFights(eventIdInput)}
                  disabled={!eventIdInput || isLoading}
                >
                  Load Fights
                </CButton>
              </CCol>
            </CRow>

            {error && <CAlert color="danger">{error}</CAlert>}

            {isLoading ? (
              <div className="d-flex justify-content-center py-5">
                <CSpinner color="primary" />
              </div>
            ) : fights.length === 0 ? (
              <CAlert color="info" className="mb-0">
                No fights found for the selected event.
              </CAlert>
            ) : (
              <CTable striped hover responsive>
                <CTableHead>
                  <CTableRow>
                    <CTableHeaderCell>ID</CTableHeaderCell>
                    <CTableHeaderCell>Fight ID</CTableHeaderCell>
                    <CTableHeaderCell>Name</CTableHeaderCell>
                    <CTableHeaderCell>Weight Category</CTableHeaderCell>
                    <CTableHeaderCell className="text-end">Actions</CTableHeaderCell>
                  </CTableRow>
                </CTableHead>
                <CTableBody>
                  {fights.map((fight) => (
                    <CTableRow key={fight.id}>
                      <CTableDataCell>{fight.id}</CTableDataCell>
                      <CTableDataCell>{fight.fight_id || '-'}</CTableDataCell>
                      <CTableDataCell>{fight.name || '-'}</CTableDataCell>
                      <CTableDataCell>
                        {fight.arena_sport_event_weight_category || '-'}
                      </CTableDataCell>
                      <CTableDataCell className="text-end">
                        <CButton
                          size="sm"
                          color="success"
                          variant="outline"
                          onClick={() =>
                            navigate(
                              `/arena/fighters?fightId=${encodeURIComponent(fight.fight_id || '')}&fightName=${encodeURIComponent(fight.name || '')}`,
                            )
                          }
                        >
                          View Fighters
                        </CButton>
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
  )
}

export default ArenaFightsList
