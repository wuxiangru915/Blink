"""
工作流 API 端点测试
测试工作流启动、状态查询、线程管理等接口
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.db import get_async_session
from app.main import app


@pytest.fixture(autouse=True)
async def override_db(db_session):
    """覆盖数据库依赖，使用内存 SQLite"""

    async def get_session_override():
        yield db_session

    app.dependency_overrides[get_async_session] = get_session_override
    yield
    app.dependency_overrides.clear()


class TestWorkflowStart:
    """测试启动工作流接口 POST /api/v1/workflow/start"""

    async def test_start_workflow_unauthorized(self, client):
        """无 token 返回 401"""
        resp = await client.post(
            "/api/v1/workflow/start",
            json={"topic_direction": "AI技术", "generate_images": True},
        )
        assert resp.status_code == 401


class TestWorkflowState:
    """测试获取工作流状态接口 GET /api/v1/workflow/state/{thread_id}"""

    async def test_get_workflow_state_not_found(self, client, auth_headers):
        """不存在的 thread_id 返回 404"""
        # 获取当前用户 ID 以构造合法的 thread_id 前缀
        me_resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = me_resp.json()["id"]
        thread_id = f"{user_id}_nonexistent"

        # mock get_graph 返回空状态快照
        mock_graph = AsyncMock()
        mock_snapshot = MagicMock()
        mock_snapshot.values = None
        mock_graph.aget_state.return_value = mock_snapshot

        with patch("app.api.v1.workflow.get_graph", new_callable=AsyncMock, return_value=mock_graph):
            resp = await client.get(
                f"/api/v1/workflow/state/{thread_id}",
                headers=auth_headers,
            )
            assert resp.status_code == 404


class TestWorkflowThreads:
    """测试线程管理接口"""

    async def test_get_threads_empty(self, client, auth_headers):
        """新用户线程列表为空"""
        # mock 连接池返回空结果
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.__aenter__.return_value = mock_conn
        mock_conn.__aexit__.return_value = None
        mock_cursor_cm = AsyncMock()
        mock_cur = AsyncMock()
        mock_cur.fetchall.return_value = []
        mock_cursor_cm.__aenter__.return_value = mock_cur
        mock_cursor_cm.__aexit__.return_value = None
        mock_conn.cursor = MagicMock(return_value=mock_cursor_cm)
        mock_pool.connection.return_value = mock_conn

        mock_graph = AsyncMock()

        with (
            patch(
                "app.api.v1.workflow.get_checkpointer_pool",
                return_value=mock_pool,
            ),
            patch("app.api.v1.workflow.get_graph", new_callable=AsyncMock, return_value=mock_graph),
        ):
            resp = await client.get("/api/v1/workflow/threads", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["threads"] == []
            assert data["total"] == 0

    async def test_delete_thread_unauthorized(self, client, auth_headers):
        """删除他人线程返回 403"""
        # 使用不属于当前用户的 thread_id
        resp = await client.delete(
            "/api/v1/workflow/threads/someotheruser_thread123",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    async def test_rename_thread(self, client, auth_headers):
        """重命名线程成功"""
        # 获取当前用户 ID 以构造合法的 thread_id 前缀
        me_resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = me_resp.json()["id"]
        thread_id = f"{user_id}_testthread"

        # mock 连接池
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.__aenter__.return_value = mock_conn
        mock_conn.__aexit__.return_value = None
        mock_cursor_cm = AsyncMock()
        mock_cur = AsyncMock()
        mock_cursor_cm.__aenter__.return_value = mock_cur
        mock_cursor_cm.__aexit__.return_value = None
        mock_conn.cursor = MagicMock(return_value=mock_cursor_cm)
        mock_pool.connection.return_value = mock_conn

        with patch(
            "app.api.v1.workflow.get_checkpointer_pool",
            return_value=mock_pool,
        ):
            resp = await client.patch(
                f"/api/v1/workflow/threads/{thread_id}/rename",
                json={"name": "新名称"},
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["name"] == "新名称"
