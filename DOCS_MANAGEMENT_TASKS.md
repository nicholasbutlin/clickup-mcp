# Docs Management Feature Tasks

These tasks track the work required to add ClickUp Docs support to the MCP server.

- [ ] **Add failing tests**
  - Create `tests/test_docs_client.py` with tests for `create_doc`, `get_doc`, `update_doc`, `list_docs`, and `search_docs` methods of `ClickUpClient` (expected to fail initially).
  - Create `tests/test_docs_tools.py` to exercise new doc-related tools in `ClickUpTools`.
  - Update `tests/test_server.py` to check that the tool registry includes the new docs tools and adjust the expected tool count.
- [ ] **Extend models**
  - Add `Document` and related models (e.g., `DocumentFolder`) to `src/clickup_mcp/models.py`.
- [ ] **Client methods**
  - Implement docs endpoints in `src/clickup_mcp/client.py` for creating, retrieving, updating, listing, and searching documents.
- [ ] **Tool implementations**
  - Add corresponding methods in `src/clickup_mcp/tools.py` and register them in `_tools`.
- [ ] **Documentation updates**
  - Update `README.md` to remove Docs from the "Not supported" section and document the new tools.
- [ ] **Tests passing**
  - Ensure all new and existing tests pass (`pre-commit` and `pytest`).
- [ ] **Changelog**
  - Document the addition of Docs management in `CHANGELOG.md`.

