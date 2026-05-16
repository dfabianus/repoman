"""Unit tests for GitHub listing route selection."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from github import UnknownObjectException

from repoman.remotes.github_client import GithubRemoteClient


def test_list_namespace_uses_authenticated_repos_for_own_login() -> None:
    mock_g = MagicMock()
    auth_user = MagicMock()
    auth_user.login = "alice"
    auth_user.get_repos.return_value = []
    mock_g.get_user.return_value = auth_user
    mock_g.get_organization.side_effect = UnknownObjectException(404, {}, None)

    with patch("repoman.remotes.github_client.Github", return_value=mock_g):
        client = GithubRemoteClient(base_url=None, token="test-token")
        client.list_namespace_repositories("alice")

    auth_user.get_repos.assert_called_once_with(affiliation="owner")
    mock_g.get_user.assert_called_with()


def test_list_namespace_uses_named_user_for_other_login() -> None:
    mock_g = MagicMock()
    auth_user = MagicMock()
    auth_user.login = "alice"
    named_bob = MagicMock()
    named_bob.get_repos.return_value = []

    def get_user(login: str | None = None) -> MagicMock:
        if login is None:
            return auth_user
        assert login == "bob"
        return named_bob

    mock_g.get_user.side_effect = get_user
    mock_g.get_organization.side_effect = UnknownObjectException(404, {}, None)

    with patch("repoman.remotes.github_client.Github", return_value=mock_g):
        client = GithubRemoteClient(base_url=None, token="test-token")
        client.list_namespace_repositories("bob")

    named_bob.get_repos.assert_called_once_with(type="owner")
