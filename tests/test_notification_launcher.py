from pathlib import Path

import notification.notification_launcher as launcher


def test_launcher_state_file(tmp_path: Path, monkeypatch):
    state_file = tmp_path / ".notification_launcher_state.json"
    monkeypatch.setattr(launcher, "STATE_FILE", state_file)

    signature = {"mtime_ns": 123, "size": 100}
    launcher.save_launcher_state(signature)

    loaded = launcher.load_launcher_state()
    assert loaded["detections_csv"] == signature
    assert launcher.is_new_detection_data(signature, loaded) is False

    changed = {"mtime_ns": 124, "size": 101}
    assert launcher.is_new_detection_data(changed, loaded) is True


def test_pipeline_order(tmp_path: Path, monkeypatch):
    calls = []
    workbook_path = tmp_path / "notification_database.xlsx"
    workbook_path.touch()

    monkeypatch.setattr(
        launcher, "capture_analysis_signatures",
        lambda: calls.append("capture") or {},
    )
    monkeypatch.setattr(
        launcher, "run_all_backend_batches",
        lambda timeout_seconds: calls.append("batch"),
    )
    monkeypatch.setattr(
        launcher, "validate_analysis_csv_files",
        lambda before_signatures: calls.append("validate"),
    )
    monkeypatch.setattr(
        launcher, "update_raw_sheets",
        lambda: calls.append("updater") or workbook_path,
    )
    monkeypatch.setattr(
        launcher, "calculate_notifications",
        lambda workbook_path: calls.append("calculator") or {
            "realtime_notification": [],
            "daily_notification": [],
            "weekly_notification": [],
            "monthly_notification": [],
            "yearly_notification": [],
        },
    )
    monkeypatch.setattr(
        launcher, "write_notification_sheets",
        lambda workbook_path, calculated_data: calls.append("writer"),
    )
    monkeypatch.setattr(
        launcher, "send_slack_notifications",
        lambda workbook_path: calls.append("sender") or {},
    )
    monkeypatch.setattr(
        launcher, "save_launcher_state",
        lambda detections_signature: calls.append("state"),
    )

    launcher.run_notification_pipeline(
        detections_signature={"mtime_ns": 1, "size": 1},
        batch_timeout_seconds=30,
    )

    assert calls == [
        "capture", "batch", "validate", "updater",
        "calculator", "writer", "sender", "state",
    ]
