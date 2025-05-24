import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

import firebase_chat_utils

class DummyTimestamp:
    """
    Dummy timestamp class with seconds and nanos attributes to simulate Firestore Timestamp.
    """
    def __init__(self, seconds, nanos):
        self.seconds = seconds
        self.nanos = nanos


def test_get_user_chats_no_user():
    # Should return empty list if no user_id
    assert firebase_chat_utils.get_user_chats('', limit=5) == []

@patch('firebase_chat_utils.firestore.client')
def test_get_user_chats_with_data(mock_client):
    # Setup mock Firestore client and data
    mock_db = MagicMock()
    mock_client.return_value = mock_db

    # Mock chain of collection/document/collection/order_by/limit
    mock_chats_ref = MagicMock()
    (mock_db.collection.return_value
            .document.return_value
            .collection.return_value
            .order_by.return_value
            .limit.return_value) = mock_chats_ref

    # Create dummy document with timestamp
    ts = DummyTimestamp(seconds=1609459200, nanos=123000000)  # 2021-01-01T00:00:00.123
    doc = MagicMock()
    doc.to_dict.return_value = {'message': 'hello', 'timestamp': ts}
    doc.id = 'doc123'
    mock_chats_ref.stream.return_value = [doc]

    # Call function
    result = firebase_chat_utils.get_user_chats('user1', limit=1)

    # Validate
    assert isinstance(result, list)
    assert len(result) == 1
    item = result[0]
    assert item['id'] == 'doc123'
    assert item['message'] == 'hello'
    # ISO format includes milliseconds
    expected = datetime.fromtimestamp(1609459200 + 0.123).isoformat()
    assert item['timestamp'].startswith(expected[:19])


def test_save_chat_session_no_user():
    assert not firebase_chat_utils.save_chat_session('', {'id': 'chat1'})

@patch('firebase_chat_utils.firestore.client')
def test_save_chat_session_success(mock_client):
    mock_db = MagicMock()
    mock_client.return_value = mock_db

    # Setup reference chain
    mock_ref = MagicMock()
    (mock_db.collection.return_value
            .document.return_value
            .collection.return_value
            .document.return_value) = mock_ref

    # Call function
    chat = {'id': 'chat1', 'messages': []}
    assert firebase_chat_utils.save_chat_session('user1', chat)

    # Ensure set was called with merge=True and timestamp key present
    args, kwargs = mock_ref.set.call_args
    saved_data = args[0]
    assert 'timestamp' in saved_data
    assert kwargs.get('merge', False) is True


def test_delete_chat_session_no_params():
    assert not firebase_chat_utils.delete_chat_session('', '')

@patch('firebase_chat_utils.firestore.client')
def test_delete_chat_session_success(mock_client):
    mock_db = MagicMock()
    mock_client.return_value = mock_db

    mock_ref = MagicMock()
    (mock_db.collection.return_value
            .document.return_value
            .collection.return_value
            .document.return_value) = mock_ref

    # Should return True when deletion succeeds
    assert firebase_chat_utils.delete_chat_session('user1', 'chat1')
    mock_ref.delete.assert_called_once()
