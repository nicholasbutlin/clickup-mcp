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
        mock_client.client.request = AsyncMock(
            return_value=mock_response(200, docs_data)
        )

        result = await mock_client.list_docs(folder_id="folder123")

        assert isinstance(result, list)
        assert isinstance(result[0], Document)
        mock_client.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_docs(self, mock_client, mock_response, sample_document):
        from clickup_mcp.models import Document

        docs_data = {"docs": [sample_document]}
        mock_client.client.request = AsyncMock(
            return_value=mock_response(200, docs_data)
        )

        result = await mock_client.search_docs(
            workspace_id="workspace123", query="design"
        )

        assert isinstance(result, list)
        assert isinstance(result[0], Document)
        mock_client.client.request.assert_called_once()
