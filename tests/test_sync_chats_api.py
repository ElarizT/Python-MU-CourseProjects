import pytest
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
     app.config['TESTING'] = True
     client = app.test_client()
     # Set a dummy user_id in session
     with client.session_transaction() as sess:
         sess['user_id'] = 'user1'
     return client
def test_sync_chats_no_data(client):
     # No chats in payload
     response = client.post('/api/sync-chats', json={})
     assert response.status_code == 200
     data = response.get_json()
     assert data['success'] is False
     assert 'error' in data

@patch('firebase_chat_utils.get_user_chats')
@patch('firebase_chat_utils.save_chat_session')
def test_sync_chats_new_and_updated(mock_save, mock_get, client):
     # Prepare server chats: one existing
     mock_get.return_value = [
         {'id': 'chat1', 'timestamp': '2021-01-01T00:00:00'}
     ]
     # Prepare client chats: updated existing and new
     client_chats = [
         {'id': 'chat1', 'timestamp': '2021-01-02T00:00:00'},
         {'id': 'chat2', 'timestamp': '2021-01-01T12:00:00'}
     ]
     mock_save.return_value = True

     response = client.post('/api/sync-chats', json={'chats': client_chats})
     assert response.status_code == 200
     data = response.get_json()
     assert data['success'] is True
     # Both chats should be synced
     assert data['syncedCount'] == 2
     assert data['totalCount'] == 2
     # Ensure save_chat_session called for each chat
     assert mock_save.call_count == 2

@patch('firebase_chat_utils.get_user_chats')
@patch('firebase_chat_utils.save_chat_session')
def test_sync_chats_skips_old(mock_save, mock_get, client):
     # Server has newer chat timestamp
     mock_get.return_value = [
         {'id': 'chat1', 'timestamp': '2021-02-01T00:00:00'}
     ]
     client_chats = [
         {'id': 'chat1', 'timestamp': '2021-01-01T00:00:00'}
     ]
     # Should not call save since client is older
     response = client.post('/api/sync-chats', json={'chats': client_chats})
     data = response.get_json()
     assert data['success'] is True
     assert data['syncedCount'] == 0
     assert data['totalCount'] == 1
     assert mock_save.call_count == 0
