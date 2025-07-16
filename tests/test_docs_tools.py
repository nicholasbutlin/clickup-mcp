import pytest
from unittest.mock import AsyncMock

from clickup_mcp.tools import ClickUpTools


class TestDocsTools:
    """Tests for doc related tools."""

    @pytest.fixture
    async def tools(self, mock_client):
        return ClickUpTools(mock_client)

    @pytest.mark.asyncio
    async def test_create_doc(self, tools, sample_document):
        from clickup_mcp.models import Document

        doc_obj = Document(**sample_document)
        tools.client.create_doc = AsyncMock(return_value=doc_obj)

        result = await tools.create_doc(folder_id="folder123", title="Doc", content="hi")

        assert result["id"] == sample_document["id"]
        assert result["name"] == sample_document["name"]
        tools.client.create_doc.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_doc(self, tools, sample_document):
        from clickup_mcp.models import Document

        doc_obj = Document(**sample_document)
        tools.client.get_doc = AsyncMock(return_value=doc_obj)

        result = await tools.get_doc("doc123")

        assert result["id"] == sample_document["id"]
        assert result["name"] == sample_document["name"]
        tools.client.get_doc.assert_called_once_with("doc123")

    @pytest.mark.asyncio
    async def test_update_doc(self, tools, sample_document):
        from clickup_mcp.models import Document

        updated = {**sample_document, "name": "Updated"}
        doc_obj = Document(**updated)
        tools.client.update_doc = AsyncMock(return_value=doc_obj)

        result = await tools.update_doc("doc123", title="Updated")

        assert result["id"] == sample_document["id"]
        assert result["name"] == "Updated"
        assert result["updated"] is True
        tools.client.update_doc.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_docs(self, tools, sample_document):
        from clickup_mcp.models import Document

        doc_obj = Document(**sample_document)
        tools.client.list_docs = AsyncMock(return_value=[doc_obj])

        result = await tools.list_docs(folder_id="folder123")

        assert result["count"] == 1
        assert result["docs"][0]["id"] == sample_document["id"]
        tools.client.list_docs.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_docs(self, tools, sample_document):
        from clickup_mcp.models import Document

        doc_obj = Document(**sample_document)
        tools.client.search_docs = AsyncMock(return_value=[doc_obj])

        result = await tools.search_docs(query="design")

        assert result["count"] == 1
        assert result["docs"][0]["id"] == sample_document["id"]
        tools.client.search_docs.assert_called_once()
