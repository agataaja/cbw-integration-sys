import React, { useEffect, useMemo, useState } from 'react'
import {
  CAlert,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CForm,
  CFormFeedback,
  CFormInput,
  CFormLabel,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
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
  createArenaClient,
  deleteArenaClient,
  extractFieldErrors,
  fetchArenaClients,
  updateArenaClient,
} from 'src/services/arena'

const EMPTY_FORM = {
  name: '',
  username: '',
  host: '',
  api_key: '',
  client_id: '',
  client_secret: '',
  grant_type: 'client_credentials',
}

const ArenaClients = () => {
  const [clients, setClients] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const [visible, setVisible] = useState(false)
  const [editingClientId, setEditingClientId] = useState(null)
  const [formData, setFormData] = useState(EMPTY_FORM)
  const [formErrors, setFormErrors] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeletingId, setIsDeletingId] = useState(null)

  const selectedClient = useMemo(
    () => clients.find((client) => client.id === editingClientId) || null,
    [clients, editingClientId],
  )

  const loadClients = async () => {
    setIsLoading(true)
    setError('')

    try {
      const response = await fetchArenaClients()
      setClients(response)
    } catch (requestError) {
      setError(requestError.message || 'Failed to load Arena clients.')
      setClients([])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadClients()
  }, [])

  const resetForm = () => {
    setEditingClientId(null)
    setFormData(EMPTY_FORM)
    setFormErrors({})
  }

  const openCreateModal = () => {
    resetForm()
    setVisible(true)
  }

  const openEditModal = (client) => {
    setEditingClientId(client.id)
    setFormData({
      name: client.name || '',
      username: client.username || '',
      host: client.host || '',
      api_key: client.api_key || '',
      client_id: client.client_id || '',
      client_secret: client.client_secret || '',
      grant_type: client.grant_type || 'client_credentials',
    })
    setFormErrors({})
    setVisible(true)
  }

  const handleInputChange = (event) => {
    const { name, value } = event.target
    setFormData((current) => ({
      ...current,
      [name]: value,
    }))
    setFormErrors((current) => ({
      ...current,
      [name]: undefined,
    }))
  }

  const getFieldError = (fieldName) => {
    const fieldError = formErrors[fieldName]
    if (Array.isArray(fieldError) && fieldError.length > 0) {
      return String(fieldError[0])
    }
    if (typeof fieldError === 'string') {
      return fieldError
    }
    return ''
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsSubmitting(true)
    setFormErrors({})

    const payload = {
      ...formData,
      host: formData.host || null,
    }

    try {
      if (editingClientId) {
        const updated = await updateArenaClient(editingClientId, payload)
        setClients((current) =>
          current.map((client) => (client.id === editingClientId ? updated : client)),
        )
      } else {
        const created = await createArenaClient(payload)
        setClients((current) => [...current, created])
      }

      setVisible(false)
      resetForm()
    } catch (requestError) {
      setFormErrors(extractFieldErrors(requestError))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (clientId) => {
    const confirmation = window.confirm('Delete this Arena client? This action cannot be undone.')
    if (!confirmation) {
      return
    }

    setIsDeletingId(clientId)
    setError('')

    try {
      await deleteArenaClient(clientId)
      setClients((current) => current.filter((client) => client.id !== clientId))
    } catch (requestError) {
      setError(requestError.message || 'Failed to delete Arena client.')
    } finally {
      setIsDeletingId(null)
    }
  }

  return (
    <CRow>
      <CCol xs={12}>
        <CCard className="mb-4">
          <CCardHeader className="d-flex justify-content-between align-items-center">
            <div>
              <strong>Arena Clients</strong>
              <span className="text-body-secondary ms-2">Manage environment connections</span>
            </div>
            <CButton color="primary" onClick={openCreateModal}>
              New Client
            </CButton>
          </CCardHeader>
          <CCardBody>
            {error && <CAlert color="danger">{error}</CAlert>}

            {isLoading ? (
              <div className="d-flex justify-content-center py-5">
                <CSpinner color="primary" />
              </div>
            ) : clients.length === 0 ? (
              <CAlert color="info" className="mb-0">
                No Arena clients configured yet.
              </CAlert>
            ) : (
              <CTable hover responsive>
                <CTableHead>
                  <CTableRow>
                    <CTableHeaderCell>ID</CTableHeaderCell>
                    <CTableHeaderCell>Name</CTableHeaderCell>
                    <CTableHeaderCell>Username</CTableHeaderCell>
                    <CTableHeaderCell>Host</CTableHeaderCell>
                    <CTableHeaderCell>Grant Type</CTableHeaderCell>
                    <CTableHeaderCell className="text-end">Actions</CTableHeaderCell>
                  </CTableRow>
                </CTableHead>
                <CTableBody>
                  {clients.map((client) => (
                    <CTableRow key={client.id}>
                      <CTableDataCell>{client.id}</CTableDataCell>
                      <CTableDataCell>{client.name}</CTableDataCell>
                      <CTableDataCell>{client.username}</CTableDataCell>
                      <CTableDataCell>{client.host || '-'}</CTableDataCell>
                      <CTableDataCell>{client.grant_type}</CTableDataCell>
                      <CTableDataCell className="text-end">
                        <CButton
                          size="sm"
                          color="secondary"
                          variant="outline"
                          className="me-2"
                          onClick={() => openEditModal(client)}
                        >
                          Edit
                        </CButton>
                        <CButton
                          size="sm"
                          color="danger"
                          variant="outline"
                          disabled={isDeletingId === client.id}
                          onClick={() => handleDelete(client.id)}
                        >
                          {isDeletingId === client.id ? 'Deleting...' : 'Delete'}
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

      <CModal alignment="center" visible={visible} onClose={() => setVisible(false)} size="lg">
        <CModalHeader>
          <CModalTitle>{selectedClient ? 'Edit Arena Client' : 'New Arena Client'}</CModalTitle>
        </CModalHeader>
        <CModalBody>
          <CForm onSubmit={handleSubmit}>
            <CRow className="g-3">
              <CCol md={6}>
                <CFormLabel htmlFor="name">Name</CFormLabel>
                <CFormInput
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  invalid={Boolean(getFieldError('name'))}
                  required
                />
                <CFormFeedback invalid>{getFieldError('name')}</CFormFeedback>
              </CCol>

              <CCol md={6}>
                <CFormLabel htmlFor="username">Username</CFormLabel>
                <CFormInput
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  invalid={Boolean(getFieldError('username'))}
                  required
                />
                <CFormFeedback invalid>{getFieldError('username')}</CFormFeedback>
              </CCol>

              <CCol md={6}>
                <CFormLabel htmlFor="host">Host</CFormLabel>
                <CFormInput
                  id="host"
                  name="host"
                  value={formData.host}
                  onChange={handleInputChange}
                  invalid={Boolean(getFieldError('host'))}
                />
                <CFormFeedback invalid>{getFieldError('host')}</CFormFeedback>
              </CCol>

              <CCol md={6}>
                <CFormLabel htmlFor="grant_type">Grant Type</CFormLabel>
                <CFormInput
                  id="grant_type"
                  name="grant_type"
                  value={formData.grant_type}
                  onChange={handleInputChange}
                  invalid={Boolean(getFieldError('grant_type'))}
                  required
                />
                <CFormFeedback invalid>{getFieldError('grant_type')}</CFormFeedback>
              </CCol>

              <CCol md={6}>
                <CFormLabel htmlFor="api_key">API Key</CFormLabel>
                <CFormInput
                  id="api_key"
                  name="api_key"
                  value={formData.api_key}
                  onChange={handleInputChange}
                  invalid={Boolean(getFieldError('api_key'))}
                  required
                />
                <CFormFeedback invalid>{getFieldError('api_key')}</CFormFeedback>
              </CCol>

              <CCol md={6}>
                <CFormLabel htmlFor="client_id">Client ID</CFormLabel>
                <CFormInput
                  id="client_id"
                  name="client_id"
                  value={formData.client_id}
                  onChange={handleInputChange}
                  invalid={Boolean(getFieldError('client_id'))}
                  required
                />
                <CFormFeedback invalid>{getFieldError('client_id')}</CFormFeedback>
              </CCol>

              <CCol xs={12}>
                <CFormLabel htmlFor="client_secret">Client Secret</CFormLabel>
                <CFormInput
                  id="client_secret"
                  name="client_secret"
                  value={formData.client_secret}
                  onChange={handleInputChange}
                  invalid={Boolean(getFieldError('client_secret'))}
                  required
                />
                <CFormFeedback invalid>{getFieldError('client_secret')}</CFormFeedback>
              </CCol>

              {getFieldError('non_field_errors') && (
                <CCol xs={12}>
                  <CAlert color="danger" className="mb-0">
                    {getFieldError('non_field_errors')}
                  </CAlert>
                </CCol>
              )}
            </CRow>
          </CForm>
        </CModalBody>
        <CModalFooter>
          <CButton color="secondary" variant="outline" onClick={() => setVisible(false)}>
            Cancel
          </CButton>
          <CButton color="primary" onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : 'Save'}
          </CButton>
        </CModalFooter>
      </CModal>
    </CRow>
  )
}

export default ArenaClients
