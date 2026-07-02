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
import { fetchArenaFighters } from 'src/services/arena'

const ArenaFightersList = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [fightIdInput, setFightIdInput] = useState(searchParams.get('fightId') || '')
  const [fightName] = useState(searchParams.get('fightName') || '')
  const [fighters, setFighters] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const loadFighters = async (fightId) => {
    if (!fightId) {
      setFighters([])
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const response = await fetchArenaFighters({ fightId })
      setFighters(response)
    } catch (requestError) {
      setError(requestError.message || 'Failed to load Arena fighters.')
      setFighters([])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (fightIdInput) {
      loadFighters(fightIdInput)
    }
  }, [fightIdInput])

  return (
    <CRow>
      <CCol xs={12}>
        <CCard className="mb-4">
          <CCardHeader className="d-flex justify-content-between align-items-center">
            <div>
              <strong>Arena Fighters</strong>
              {fightName && <span className="text-body-secondary ms-2">Fight: {fightName}</span>}
            </div>
            <CButton color="primary" variant="outline" onClick={() => navigate('/arena/fights')}>
              Back To Fights
            </CButton>
          </CCardHeader>
          <CCardBody>
            <CRow className="g-3 mb-3">
              <CCol md={8}>
                <CFormLabel htmlFor="arena-fight-id-filter">Fight ID</CFormLabel>
                <CFormInput
                  id="arena-fight-id-filter"
                  value={fightIdInput}
                  onChange={(event) => setFightIdInput(event.target.value)}
                  placeholder="Enter fight id"
                />
              </CCol>
              <CCol md={4} className="d-flex align-items-end">
                <CButton
                  color="primary"
                  onClick={() => loadFighters(fightIdInput)}
                  disabled={!fightIdInput || isLoading}
                >
                  Load Fighters
                </CButton>
              </CCol>
            </CRow>

            {error && <CAlert color="danger">{error}</CAlert>}

            {isLoading ? (
              <div className="d-flex justify-content-center py-5">
                <CSpinner color="primary" />
              </div>
            ) : fighters.length === 0 ? (
              <CAlert color="info" className="mb-0">
                No fighters found for the selected fight.
              </CAlert>
            ) : (
              <CTable striped hover responsive>
                <CTableHead>
                  <CTableRow>
                    <CTableHeaderCell>ID</CTableHeaderCell>
                    <CTableHeaderCell>Fighter ID</CTableHeaderCell>
                    <CTableHeaderCell>Name</CTableHeaderCell>
                    <CTableHeaderCell>Fight</CTableHeaderCell>
                  </CTableRow>
                </CTableHead>
                <CTableBody>
                  {fighters.map((fighter) => (
                    <CTableRow key={fighter.id}>
                      <CTableDataCell>{fighter.id}</CTableDataCell>
                      <CTableDataCell>{fighter.fighter_id || '-'}</CTableDataCell>
                      <CTableDataCell>{fighter.name || '-'}</CTableDataCell>
                      <CTableDataCell>{fighter.fight || '-'}</CTableDataCell>
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

export default ArenaFightersList
