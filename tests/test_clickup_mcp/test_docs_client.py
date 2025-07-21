from unittest.mock import AsyncMock

import pytest


class TestDocsClient:
    """Tests for ClickUpClient docs methods."""

    @pytest.mark.asyncio
    async def test_create_doc(self, mock_client, mock_response, sample_document):
        from clickup_mcp.models import CreateDocRequest, Document

        mock_client.client.request = AsyncMock(
            return_value=mock_response(200, sample_document)
        )

        doc_req = CreateDocRequest(name="Doc", content="hello")
        result = await mock_client.create_doc("folder123", doc_req)

        assert isinstance(result, Document)
        assert result.name == sample_document["name"]
        mock_client.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_doc(self, mock_client, mock_response, sample_document):
        from clickup_mcp.models import Document

        mock_client.client.request = AsyncMock(
            return_value=mock_response(200, sample_document)
        )

        result = await mock_client.get_doc("doc123")

        assert isinstance(result, Document)
        assert result.id == sample_document["id"]
        mock_client.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_doc(self, mock_client, mock_response, sample_document):
        from clickup_mcp.models import Document, UpdateDocRequest

        updated = {**sample_document, "name": "Updated"}
        mock_client.client.request = AsyncMock(return_value=mock_response(200, updated))

        req = UpdateDocRequest(name="Updated")
        result = await mock_client.update_doc("doc123", req)

        assert isinstance(result, Document)
        assert result.name == "Updated"
        mock_client.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_docs(self, mock_client, mock_response, sample_document):
        from clickup_mcp.models import Document

        docs_data = {"docs": [sample_document]}

        # Mock the _request_v3 method since list_docs now uses v3 API
        mock_client._request_v3 = AsyncMock(return_value=docs_data)

        result = await mock_client.list_docs(folder_id="folder123")

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Document)
        assert result[0].id == sample_document["id"]
        mock_client._request_v3.assert_called_once_with(
            "GET", "/workspaces/test_workspace/docs"
        )

    @pytest.mark.asyncio
    async def test_search_docs(self, mock_client, mock_response, sample_document):
        from clickup_mcp.models import Document

        docs_data = {"docs": [sample_document]}

        # Mock the _request_v3 method since search_docs now uses v3 API
        mock_client._request_v3 = AsyncMock(return_value=docs_data)

        result = await mock_client.search_docs(
            workspace_id="workspace123", query="design"
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Document)
        assert result[0].id == sample_document["id"]
        mock_client._request_v3.assert_called_once_with(
            "GET", "/workspaces/workspace123/docs", params={"query": "design"}
        )

    @pytest.mark.asyncio
    async def test_list_docs_no_workspace_id(
        self, mock_client, mock_response, sample_document
    ):
        """Test list_docs when no workspace_id is configured."""
        from clickup_mcp.models import Document

        # Set up mock client without default workspace
        mock_client.config.default_workspace_id = None

        # Mock get_workspaces to return a workspace
        workspace_data = {
            "teams": [
                {
                    "id": "workspace456",
                    "name": "Test Workspace",
                    "color": "#FF0000",
                    "avatar": None,
                    "members": [],
                }
            ]
        }
        mock_client._request = AsyncMock(return_value=workspace_data)

        docs_data = {"docs": [sample_document]}
        mock_client._request_v3 = AsyncMock(return_value=docs_data)

        result = await mock_client.list_docs(folder_id="folder123")

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Document)

        # Should have called get_workspaces first, then list docs
        mock_client._request.assert_called_once_with("GET", "/team")
        mock_client._request_v3.assert_called_once_with(
            "GET", "/workspaces/workspace456/docs"
        )

    @pytest.mark.asyncio
    async def test_search_docs_with_default_workspace(
        self, mock_client, mock_response, sample_document
    ):
        """Test search_docs using default workspace from config."""
        docs_data = {"docs": [sample_document]}
        mock_client._request_v3 = AsyncMock(return_value=docs_data)

        # Call without workspace_id - should use default
        result = await mock_client.search_docs(query="test")

        assert isinstance(result, list)
        assert len(result) == 1
        mock_client._request_v3.assert_called_once_with(
            "GET", "/workspaces/test_workspace/docs", params={"query": "test"}
        )

    @pytest.mark.asyncio
    async def test_list_docs_api_error_handling(self, mock_client):
        """Test that list_docs handles API errors gracefully."""
        from clickup_mcp.client import ClickUpAPIError

        # Mock _request_v3 to raise an error
        mock_client._request_v3 = AsyncMock(
            side_effect=ClickUpAPIError("API Error", 404)
        )

        result = await mock_client.list_docs(folder_id="folder123")

        # Should return empty list instead of raising error
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_docs_api_error_handling(self, mock_client):
        """Test that search_docs handles API errors gracefully."""
        from clickup_mcp.client import ClickUpAPIError

        # Mock _request_v3 to raise an error
        mock_client._request_v3 = AsyncMock(
            side_effect=ClickUpAPIError("API Error", 404)
        )

        result = await mock_client.search_docs(query="test")

        # Should return empty list instead of raising error
        assert isinstance(result, list)
        assert len(result) == 0
