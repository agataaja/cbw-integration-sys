"""
Service layer for SGE app CRUD operations.
Handles business logic for interacting with SGE external API endpoints.
"""
import os
import logging
from typing import Dict, List, Any, Optional

import requests
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)

# SGE API configuration - ensure no trailing slash in base URL
_SGE_BASE_URL = os.getenv("SGE_ARENA_API_URL", "https://restcbw.bigmidia.com/cbw/api").rstrip('/')
SGE_RANKING_ENDPOINT = f"{_SGE_BASE_URL}/resultado-rank-arena"
SGE_FIGHT_ENDPOINT = f"{_SGE_BASE_URL}/evento-luta"
REQUEST_TIMEOUT = 30


class SGEServiceError(Exception):
    """Base exception for SGE service errors."""
    pass


class SGEResultadoService:
    """
    Service for handling resultado-rank-arena operations.
    Manages ranking data CRUD operations with SGE external API.
    """

    @staticmethod
    def get_by_event_id(event_id: int, fetch_all_pages: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch all ranking records for a specific event from SGE API.
        Handles pagination automatically if fetch_all_pages is True.
        
        Args:
            event_id: SGE event ID to filter records
            fetch_all_pages: If True, fetches all pages; if False, only first page
            
        Returns:
            List of ranking records from SGE API
            
        Raises:
            SGEServiceError: If API request fails
        """
        all_items = []
        current_page = 1
        
        try:
            while True:
                response = requests.get(
                    SGE_RANKING_ENDPOINT,
                    params={'id_evento': event_id, 'page': current_page},
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extract items from paginated response
                items = data.get('items', [])
                all_items.extend(items)
                
                # Check pagination metadata
                meta = data.get('_meta', {})
                total_pages = meta.get('pageCount', 1)
                
                logger.info(
                    f"[SGEResultadoService] Fetched page {current_page}/{total_pages} "
                    f"({len(items)} records) for event {event_id}"
                )
                
                # Stop if we don't want all pages or if we're on the last page
                if not fetch_all_pages or current_page >= total_pages:
                    break
                
                current_page += 1
            
            logger.info(f"[SGEResultadoService] Total fetched: {len(all_items)} ranking records for event {event_id}")
            return all_items
            
        except Timeout:
            logger.error(f"[SGEResultadoService] Timeout fetching rankings for event {event_id}")
            raise SGEServiceError(f"Request timeout for event {event_id}")
        except RequestException as e:
            logger.error(f"[SGEResultadoService] Error fetching rankings for event {event_id}: {e}")
            raise SGEServiceError(f"Failed to fetch rankings: {str(e)}")

    @staticmethod
    def delete_by_id(record_id: int) -> Dict[str, Any]:
        """
        Delete a single ranking record by its ID.
        
        Args:
            record_id: Individual ranking record ID
            
        Returns:
            Dictionary with status and response details
        """
        try:
            url = f"{SGE_RANKING_ENDPOINT}/{record_id}"
            response = requests.delete(url, timeout=REQUEST_TIMEOUT)
            
            return {
                'id': record_id,
                'status_code': response.status_code,
                'success': response.status_code in [200, 204],
                'response_text': response.text[:200]  # Truncate for logging
            }
            
        except RequestException as e:
            logger.error(f"[SGEResultadoService] Error deleting ranking {record_id}: {e}")
            return {
                'id': record_id,
                'status_code': None,
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def bulk_delete_by_event_id(event_id: int) -> Dict[str, Any]:
        """
        Delete all ranking records for a specific event.
        Fetches records by event_id, then deletes each individually.
        
        Args:
            event_id: SGE event ID
            
        Returns:
            Summary of bulk delete operation
        """
        # Fetch all records for this event
        records = SGEResultadoService.get_by_event_id(event_id)
        
        if not records:
            return {
                'success_count': 0,
                'failure_count': 0,
                'total_records': 0,
                'successful_ids': [],
                'failed_operations': [],
                'message': f'No ranking records found for event {event_id}'
            }
        
        # Delete each record individually
        successful_ids = []
        failed_operations = []
        
        for record in records:
            record_id = record.get('id')
            if not record_id:
                failed_operations.append({
                    'record': record,
                    'reason': 'Missing ID field'
                })
                continue
            
            result = SGEResultadoService.delete_by_id(record_id)
            
            if result['success']:
                successful_ids.append(str(record_id))
                logger.info(f"[SGEResultadoService] Deleted ranking {record_id}")
            else:
                failed_operations.append(result)
                logger.error(f"[SGEResultadoService] Failed to delete ranking {record_id}")
        
        return {
            'success_count': len(successful_ids),
            'failure_count': len(failed_operations),
            'total_records': len(records),
            'successful_ids': successful_ids,
            'failed_operations': failed_operations,
            'message': f'Deleted {len(successful_ids)}/{len(records)} ranking records for event {event_id}'
        }

    @staticmethod
    def update_by_id(record_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a single ranking record by its ID.
        
        Args:
            record_id: Individual ranking record ID
            data: Updated data payload
            
        Returns:
            Dictionary with status and response details
        """
        try:
            url = f"{SGE_RANKING_ENDPOINT}/{record_id}"
            response = requests.put(
                url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=REQUEST_TIMEOUT
            )
            
            return {
                'id': record_id,
                'status_code': response.status_code,
                'success': response.status_code in [200, 204],
                'response_text': response.text[:200]
            }
            
        except RequestException as e:
            logger.error(f"[SGEResultadoService] Error updating ranking {record_id}: {e}")
            return {
                'id': record_id,
                'status_code': None,
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def bulk_update_by_event_id(event_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update all ranking records for a specific event with provided data.
        Fetches records by event_id, then updates each individually.
        
        Args:
            event_id: SGE event ID
            updates: Dictionary of fields to update on each record
            
        Returns:
            Summary of bulk update operation
        """
        # Fetch all records for this event
        records = SGEResultadoService.get_by_event_id(event_id)
        
        if not records:
            return {
                'success_count': 0,
                'failure_count': 0,
                'total_records': 0,
                'successful_ids': [],
                'failed_operations': [],
                'message': f'No ranking records found for event {event_id}'
            }
        
        # Update each record individually
        successful_ids = []
        failed_operations = []
        
        for record in records:
            record_id = record.get('id')
            if not record_id:
                failed_operations.append({
                    'record': record,
                    'reason': 'Missing ID field'
                })
                continue
            
            # Merge existing record data with updates
            updated_data = {**record, **updates}
            result = SGEResultadoService.update_by_id(record_id, updated_data)
            
            if result['success']:
                successful_ids.append(str(record_id))
                logger.info(f"[SGEResultadoService] Updated ranking {record_id}")
            else:
                failed_operations.append(result)
                logger.error(f"[SGEResultadoService] Failed to update ranking {record_id}")
        
        return {
            'success_count': len(successful_ids),
            'failure_count': len(failed_operations),
            'total_records': len(records),
            'successful_ids': successful_ids,
            'failed_operations': failed_operations,
            'message': f'Updated {len(successful_ids)}/{len(records)} ranking records for event {event_id}'
        }


class SGELutaService:
    """
    Service for handling evento-luta operations.
    Manages fight/bout data CRUD operations with SGE external API.
    """

    @staticmethod
    def get_by_event_id(event_id: int, fetch_all_pages: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch all fight records for a specific event from SGE API.
        Handles pagination automatically if fetch_all_pages is True.
        
        Args:
            event_id: SGE event ID to filter records
            fetch_all_pages: If True, fetches all pages; if False, only first page
            
        Returns:
            List of fight records from SGE API
            
        Raises:
            SGEServiceError: If API request fails
        """
        all_items = []
        current_page = 1
        
        try:
            while True:
                response = requests.get(
                    SGE_FIGHT_ENDPOINT,
                    params={'id_evento': event_id, 'page': current_page},
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extract items from paginated response
                items = data.get('items', [])
                all_items.extend(items)
                
                # Check pagination metadata
                meta = data.get('_meta', {})
                total_pages = meta.get('pageCount', 1)
                
                logger.info(
                    f"[SGELutaService] Fetched page {current_page}/{total_pages} "
                    f"({len(items)} records) for event {event_id}"
                )
                
                # Stop if we don't want all pages or if we're on the last page
                if not fetch_all_pages or current_page >= total_pages:
                    break
                
                current_page += 1
            
            logger.info(f"[SGELutaService] Total fetched: {len(all_items)} fight records for event {event_id}")
            return all_items
            
        except Timeout:
            logger.error(f"[SGELutaService] Timeout fetching fights for event {event_id}")
            raise SGEServiceError(f"Request timeout for event {event_id}")
        except RequestException as e:
            logger.error(f"[SGELutaService] Error fetching fights for event {event_id}: {e}")
            raise SGEServiceError(f"Failed to fetch fights: {str(e)}")

    @staticmethod
    def delete_by_id(record_id: str) -> Dict[str, Any]:
        """
        Delete a single fight record by its ID.
        
        Args:
            record_id: Individual fight record ID (UUID format)
            
        Returns:
            Dictionary with status and response details
        """
        try:
            url = f"{SGE_FIGHT_ENDPOINT}/{record_id}"
            response = requests.delete(url, timeout=REQUEST_TIMEOUT)
            
            return {
                'id': record_id,
                'status_code': response.status_code,
                'success': response.status_code in [200, 204],
                'response_text': response.text[:200]
            }
            
        except RequestException as e:
            logger.error(f"[SGELutaService] Error deleting fight {record_id}: {e}")
            return {
                'id': record_id,
                'status_code': None,
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def bulk_delete_by_event_id(event_id: int) -> Dict[str, Any]:
        """
        Delete all fight records for a specific event.
        Fetches records by event_id, then deletes each individually.
        
        Args:
            event_id: SGE event ID
            
        Returns:
            Summary of bulk delete operation
        """
        # Fetch all records for this event
        records = SGELutaService.get_by_event_id(event_id)
        
        if not records:
            return {
                'success_count': 0,
                'failure_count': 0,
                'total_records': 0,
                'successful_ids': [],
                'failed_operations': [],
                'message': f'No fight records found for event {event_id}'
            }
        
        # Delete each record individually
        successful_ids = []
        failed_operations = []
        
        for record in records:
            record_id = record.get('id')
            if not record_id:
                failed_operations.append({
                    'record': record,
                    'reason': 'Missing ID field'
                })
                continue
            
            result = SGELutaService.delete_by_id(record_id)
            
            if result['success']:
                successful_ids.append(record_id)
                logger.info(f"[SGELutaService] Deleted fight {record_id}")
            else:
                failed_operations.append(result)
                logger.error(f"[SGELutaService] Failed to delete fight {record_id}")
        
        return {
            'success_count': len(successful_ids),
            'failure_count': len(failed_operations),
            'total_records': len(records),
            'successful_ids': successful_ids,
            'failed_operations': failed_operations,
            'message': f'Deleted {len(successful_ids)}/{len(records)} fight records for event {event_id}'
        }

    @staticmethod
    def update_by_id(record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a single fight record by its ID.
        
        Args:
            record_id: Individual fight record ID (UUID format)
            data: Updated data payload
            
        Returns:
            Dictionary with status and response details
        """
        try:
            url = f"{SGE_FIGHT_ENDPOINT}/{record_id}"
            response = requests.put(
                url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=REQUEST_TIMEOUT
            )
            
            return {
                'id': record_id,
                'status_code': response.status_code,
                'success': response.status_code in [200, 204],
                'response_text': response.text[:200]
            }
            
        except RequestException as e:
            logger.error(f"[SGELutaService] Error updating fight {record_id}: {e}")
            return {
                'id': record_id,
                'status_code': None,
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def bulk_update_by_event_id(event_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update all fight records for a specific event with provided data.
        Fetches records by event_id, then updates each individually.
        
        Args:
            event_id: SGE event ID
            updates: Dictionary of fields to update on each record
            
        Returns:
            Summary of bulk update operation
        """
        # Fetch all records for this event
        records = SGELutaService.get_by_event_id(event_id)
        
        if not records:
            return {
                'success_count': 0,
                'failure_count': 0,
                'total_records': 0,
                'successful_ids': [],
                'failed_operations': [],
                'message': f'No fight records found for event {event_id}'
            }
        
        # Update each record individually
        successful_ids = []
        failed_operations = []
        
        for record in records:
            record_id = record.get('id')
            if not record_id:
                failed_operations.append({
                    'record': record,
                    'reason': 'Missing ID field'
                })
                continue
            
            # Merge existing record data with updates
            updated_data = {**record, **updates}
            result = SGELutaService.update_by_id(record_id, updated_data)
            
            if result['success']:
                successful_ids.append(record_id)
                logger.info(f"[SGELutaService] Updated fight {record_id}")
            else:
                failed_operations.append(result)
                logger.error(f"[SGELutaService] Failed to update fight {record_id}")
        
        return {
            'success_count': len(successful_ids),
            'failure_count': len(failed_operations),
            'total_records': len(records),
            'successful_ids': successful_ids,
            'failed_operations': failed_operations,
            'message': f'Updated {len(successful_ids)}/{len(records)} fight records for event {event_id}'
        }
