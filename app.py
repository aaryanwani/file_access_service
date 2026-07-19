from flask import Flask, jsonify, request
import time

app = Flask(__name__)

# In-memory storage
samples = {}
files = {}
grants = set()


@app.route("/samples", methods=["POST"])
def create_sample():
    data = request.get_json()

    if not data:
        return jsonify({"error": "invalid_request"}), 400

    sample_id = data.get("id")
    owner_id = data.get("ownerId")
    file_ids = data.get("files", [])

    if not sample_id or not owner_id:
        return jsonify({"error": "missing_required_fields"}), 400

    if sample_id in samples:
        return jsonify({"error": "sample_already_exists"}), 409

    samples[sample_id] = {
        "id": sample_id,
        "ownerId": owner_id,
    }

    for file_id in file_ids:
        if file_id in files:
            continue

        files[file_id] = {
            "id": file_id,
            "sampleId": sample_id,
            "qcStatus": "pending",
        }

    return jsonify({
        "id": sample_id,
        "ownerId": owner_id,
        "files": file_ids,
    }), 201


@app.route("/samples/<sample_id>/grants", methods=["POST"])
def grant_access(sample_id):
    data = request.get_json()

    if sample_id not in samples:
        return jsonify({"error": "no_such_sample"}), 404

    if not data or not data.get("userId"):
        return jsonify({"error": "missing_user_id"}), 400

    user_id = data["userId"]

    grants.add((user_id, sample_id))

    return jsonify({
        "userId": user_id,
        "sampleId": sample_id,
        "granted": True,
    }), 201


@app.route("/files/<file_id>/qc", methods=["POST"])
def update_qc(file_id):
    data = request.get_json()

    file = files.get(file_id)

    if not file:
        return jsonify({"error": "no_such_file"}), 404

    if not data:
        return jsonify({"error": "invalid_request"}), 400

    new_status = data.get("status")

    if new_status not in ["passed", "failed"]:
        return jsonify({"error": "invalid_qc_status"}), 400

    # Files begin as pending and can then move to passed or failed
    if file["qcStatus"] != "pending":
        return jsonify({"error": "qc_already_completed"}), 409

    file["qcStatus"] = new_status

    return jsonify({
        "fileId": file_id,
        "qcStatus": new_status,
    }), 200


def can_download(user_id, file_id):
    file = files.get(file_id)

    if not file:
        return {
            "allowed": False,
            "reason": "no_such_file",
        }

    sample = samples.get(file["sampleId"])

    if not sample:
        return {
            "allowed": False,
            "reason": "no_such_sample",
        }

    is_owner = sample["ownerId"] == user_id
    has_grant = (user_id, sample["id"]) in grants

    if not is_owner and not has_grant:
        return {
            "allowed": False,
            "reason": "no_access",
        }

    qc_status = file["qcStatus"]

    if qc_status == "pending":
        return {
            "allowed": False,
            "reason": "qc_pending",
        }

    if qc_status == "failed":
        return {
            "allowed": False,
            "reason": "qc_failed",
        }

    expires_at = int(time.time()) + 300

    return {
        "allowed": True,
        "url": (
            f"https://downloads.example.com/{file_id}"
            f"?expires={expires_at}"
        ),
    }


@app.route("/download", methods=["POST"])
def request_download():
    data = request.get_json()

    if not data:
        return jsonify({"error": "invalid_request"}), 400

    user_id = data.get("userId")
    file_id = data.get("fileId")

    if not user_id or not file_id:
        return jsonify({"error": "missing_required_fields"}), 400

    decision = can_download(user_id, file_id)

    if decision["allowed"]:
        return jsonify(decision), 200

    reason = decision["reason"]

    if reason in ["no_such_file", "no_such_sample"]:
        return jsonify(decision), 404

    if reason == "no_access":
        return jsonify(decision), 403

    return jsonify(decision), 409


if __name__ == "__main__":
    app.run(debug=True)
