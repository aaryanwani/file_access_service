import pytest

from app import app, samples, files, grants


@pytest.fixture
def client():
    app.config["TESTING"] = True

    samples.clear()
    files.clear()
    grants.clear()

    samples["s1"] = {
        "id": "s1",
        "ownerId": "u1",
    }

    files["f1"] = {
        "id": "f1",
        "sampleId": "s1",
        "qcStatus": "pending",
    }

    files["f2"] = {
        "id": "f2",
        "sampleId": "s1",
        "qcStatus": "passed",
    }

    files["f3"] = {
        "id": "f3",
        "sampleId": "s1",
        "qcStatus": "failed",
    }

    with app.test_client() as client:
        yield client


def test_create_sample(client):
    response = client.post(
        "/samples",
        json={
            "id": "s2",
            "ownerId": "u2",
            "files": ["f4"],
        },
    )

    assert response.status_code == 201
    assert files["f4"]["qcStatus"] == "pending"


def test_grant_access(client):
    response = client.post(
        "/samples/s1/grants",
        json={"userId": "u2"},
    )

    assert response.status_code == 201
    assert ("u2", "s1") in grants


def test_qc_update(client):
    response = client.post(
        "/files/f1/qc",
        json={"status": "passed"},
    )

    assert response.status_code == 200
    assert files["f1"]["qcStatus"] == "passed"


def test_owner_can_download_passed_file(client):
    response = client.post(
        "/download",
        json={
            "userId": "u1",
            "fileId": "f2",
        },
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["allowed"] is True
    assert "url" in data


def test_user_with_grant_can_download(client):
    grants.add(("u2", "s1"))

    response = client.post(
        "/download",
        json={
            "userId": "u2",
            "fileId": "f2",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["allowed"] is True


def test_user_without_access(client):
    response = client.post(
        "/download",
        json={
            "userId": "u3",
            "fileId": "f2",
        },
    )

    data = response.get_json()

    assert response.status_code == 403
    assert data["reason"] == "no_access"


def test_pending_file_cannot_be_downloaded(client):
    response = client.post(
        "/download",
        json={
            "userId": "u1",
            "fileId": "f1",
        },
    )

    data = response.get_json()

    assert response.status_code == 409
    assert data["reason"] == "qc_pending"


def test_failed_file_cannot_be_downloaded(client):
    response = client.post(
        "/download",
        json={
            "userId": "u1",
            "fileId": "f3",
        },
    )

    data = response.get_json()

    assert response.status_code == 409
    assert data["reason"] == "qc_failed"


def test_missing_file(client):
    response = client.post(
        "/download",
        json={
            "userId": "u1",
            "fileId": "missing",
        },
    )

    assert response.status_code == 404
    assert response.get_json()["reason"] == "no_such_file"
