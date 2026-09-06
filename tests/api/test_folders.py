from pathlib import Path

import pytest


@pytest.mark.parametrize("path", ["docs", "a/b/c"])
def test_create_folder(auth_client, path):
    client, _, workspace = auth_client

    response = client.post("/api/workspaces/test-ws/folders", json={"path": path})

    assert response.status_code == 200
    assert response.json() == {"path": path}
    assert (Path(workspace) / path / ".gitkeep").exists()


def test_create_folder_is_idempotent(auth_client):
    client, _, _ = auth_client
    client.post("/api/workspaces/test-ws/folders", json={"path": "docs"})

    response = client.post("/api/workspaces/test-ws/folders", json={"path": "docs"})

    assert response.status_code == 200
    assert response.json() == {"path": "docs"}


@pytest.mark.parametrize("path", ["../evil", "a//b", "my folder?", "."])
def test_create_folder_rejects_invalid_path(auth_client, path):
    response = auth_client.post("/api/workspaces/test-ws/folders", json={"path": path})

    assert response.status_code == 422
    assert response.json()["error"] == "FOLDER_PATH_INVALID"


@pytest.mark.parametrize("body", [{"path": ""}, {"path": "  "}, {}])
def test_create_folder_rejects_empty_path(auth_client, body):
    response = auth_client.post("/api/workspaces/test-ws/folders", json=body)

    assert response.status_code == 422
    assert response.json()["error"] == "FOLDER_PATH_REQUIRED"


def test_create_folder_rejects_array_body(auth_client):
    response = auth_client.post("/api/workspaces/test-ws/folders", json=["docs"])

    assert response.status_code == 422


def test_create_folder_rejects_symlink_escape(auth_client, tmp_path):
    # Segment/regex validation rejects a literal ".." in the path, but a symlink already
    # inside the workspace (e.g. from a pulled remote) can still point outside it --
    # create_folder's own ws_root containment check is what catches that case.
    client, _, workspace = auth_client
    outside = tmp_path / "outside"
    outside.mkdir()
    (Path(workspace) / "escape").symlink_to(outside, target_is_directory=True)

    response = client.post("/api/workspaces/test-ws/folders", json={"path": "escape/evil"})

    assert response.status_code == 422
    assert response.json()["error"] == "INVALID_FOLDER"
    assert not (outside / "evil" / ".gitkeep").exists()


@pytest.mark.parametrize(
    ("client_fixture", "expected_status"),
    [("anon_client", 401), ("no_access_client", 403)],
)
def test_create_folder_requires_authorized_workspace(request, client_fixture, expected_status):
    client = request.getfixturevalue(client_fixture)

    response = client.post("/api/workspaces/test-ws/folders", json={"path": "docs"})

    assert response.status_code == expected_status
