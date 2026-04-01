"""Tests for enhanced PairManager — file tracking and conflict detection."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from orchestrator.pair.manager import PairManager
from orchestrator.pair.session import PairSession


@pytest.fixture
def manager():
    db = AsyncMock()
    wt = AsyncMock()
    mgr = PairManager(db=db, wt=wt)

    session = PairSession(
        chat_id=1, task_name="test", branch="feat/test", worktree_path="/tmp/repo"
    )
    session.add_member(100, "alice")
    session.add_member(200, "bob")

    mock_proc = MagicMock()
    mock_proc.send_message = AsyncMock(return_value="Done!")
    mock_proc.total_cost_usd = 0.01
    mock_proc.last_tool_events = [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "name": "Edit", "input": {"file_path": "/tmp/repo/app/api.py", "old_string": "x", "new_string": "y"}},
                ]
            },
        }
    ]

    mgr._sessions[1] = session
    mgr._processes[1] = mock_proc
    return mgr


@pytest.mark.asyncio
async def test_send_message_tracks_file_ownership(manager):
    response, diff = await manager.send_message_with_tracking(1, 100, "alice", "build the API")
    session = manager.get_session(1)
    assert session.file_ownership.get("app/api.py") == 100


@pytest.mark.asyncio
async def test_send_message_returns_diff_summary(manager):
    response, diff = await manager.send_message_with_tracking(1, 100, "alice", "build the API")
    assert "app/api.py" in diff
    assert "@alice" in diff


@pytest.mark.asyncio
async def test_send_message_warns_on_conflict(manager):
    session = manager.get_session(1)
    session.set_file_owner("app/api.py", 100)  # alice owns it

    # Bob's process will touch the same file
    response, diff = await manager.send_message_with_tracking(1, 200, "bob", "edit the API")
    # Should still work but diff should mention the conflict
    assert response == "Done!"
