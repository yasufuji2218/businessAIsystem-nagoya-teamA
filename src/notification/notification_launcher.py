from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


# ============================================================
# パス設定
# ============================================================

# このファイルを次へ置く前提
# project-root/src/notification/notification_launcher.py
NOTIFICATION_DIR = Path(__file__).resolve().parent
SRC_DIR = NOTIFICATION_DIR.parent
PROJECT_ROOT = SRC_DIR.parent

BACKEND_DIR = SRC_DIR / "backend"

DETECTIONS_CSV = BACKEND_DIR / "detections.csv"

ANALYSIS_CSV_PATHS = {
    "daily": BACKEND_DIR / "daily_analysis.csv",
    "weekly": BACKEND_DIR / "weekly_analysis.csv",
    "monthly": BACKEND_DIR / "monthly_analysis.csv",
    "yearly": BACKEND_DIR / "yearly_analysis.csv",
}

EXCEL_PATH = (
    NOTIFICATION_DIR
    / "result"
    / "notification_database.xlsx"
)

# 前回処理したdetections.csvの状態を保存するファイル
STATE_FILE = NOTIFICATION_DIR / ".notification_launcher_state.json"

DEFAULT_POLL_INTERVAL_SECONDS = 3.0
DEFAULT_STABLE_WAIT_SECONDS = 1.0
DEFAULT_BATCH_TIMEOUT_SECONDS = 300
DEFAULT_BATCH_RETRY_COUNT = 3
DEFAULT_BATCH_RETRY_WAIT_SECONDS = 2.0


# ============================================================
# ログ設定
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "[%(levelname)s] "
        "%(message)s"
    ),
)

logger = logging.getLogger(__name__)


# ============================================================
# 例外
# ============================================================

class NotificationLauncherError(RuntimeError):
    """通知処理全体の制御中に発生したエラー。"""


# ============================================================
# ファイル状態
# ============================================================

def get_file_signature(path: Path) -> dict[str, int]:
    """
    ファイルの更新状態を表す情報を返す。

    mtime_ns:
        ナノ秒単位の更新日時。

    size:
        ファイルサイズ。
    """
    if not path.is_file():
        raise FileNotFoundError(
            f"必要なファイルが見つかりません: {path}"
        )

    stat = path.stat()

    return {
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
    }


def load_launcher_state() -> dict[str, Any]:
    """前回処理したファイル状態を読み込む。"""
    if not STATE_FILE.is_file():
        return {}

    try:
        with STATE_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            state = json.load(file)

    except (OSError, json.JSONDecodeError) as error:
        logger.warning(
            "状態ファイルを読み込めませんでした。"
            "初回実行として扱います: %s",
            error,
        )
        return {}

    if not isinstance(state, dict):
        return {}

    return state


def save_launcher_state(
    detections_signature: dict[str, int],
) -> None:
    """正常完了したdetections.csvの状態を保存する。"""
    STATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = STATE_FILE.with_suffix(".tmp")

    state = {
        "detections_csv": detections_signature,
        "processed_at": time.time(),
    }

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                state,
                file,
                ensure_ascii=False,
                indent=2,
            )

        os.replace(
            temporary_path,
            STATE_FILE,
        )

    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def is_new_detection_data(
    current_signature: dict[str, int],
    state: dict[str, Any],
) -> bool:
    """detections.csvが前回処理時から変化したか判定する。"""
    previous_signature = state.get("detections_csv")

    if not isinstance(previous_signature, dict):
        # 状態ファイルが存在しない初回実行
        return True

    return current_signature != previous_signature


def wait_until_file_is_stable(
    path: Path,
    wait_seconds: float,
    max_checks: int = 10,
) -> dict[str, int]:
    """
    CSV書き込み中に読み込まないよう、
    ファイルサイズと更新日時が安定するまで待つ。
    """
    previous_signature = get_file_signature(path)

    for _ in range(max_checks):
        time.sleep(wait_seconds)

        current_signature = get_file_signature(path)

        if current_signature == previous_signature:
            return current_signature

        previous_signature = current_signature

    raise NotificationLauncherError(
        f"ファイルの更新が終了しませんでした: {path}"
    )


# ============================================================
# 入力検証
# ============================================================

def validate_environment() -> None:
    """通知処理に必要なフォルダ・ファイルを確認する。"""
    required_directories = [
        SRC_DIR,
        BACKEND_DIR,
        NOTIFICATION_DIR,
    ]

    for directory in required_directories:
        if not directory.is_dir():
            raise FileNotFoundError(
                f"必要なディレクトリがありません: {directory}"
            )

    batch_file = BACKEND_DIR / "batch.py"

    if not batch_file.is_file():
        raise FileNotFoundError(
            f"batch.pyが見つかりません: {batch_file}"
        )

    # notification_database.xlsxはUpdater側で
    # 新規生成しない設計なら、ここで存在確認する。
    if not EXCEL_PATH.is_file():
        raise FileNotFoundError(
            "notification_database.xlsxが見つかりません: "
            f"{EXCEL_PATH}"
        )

    logger.info("実行環境の確認が完了しました。")


# ============================================================
# backend.batch実行
# ============================================================

def build_subprocess_environment() -> dict[str, str]:
    """
    subprocess用の環境変数を作る。

    PowerShellの
    $env:PYTHONPATH = ".\\src"
    と同じ設定をPython側で行う。
    """
    environment = os.environ.copy()

    current_python_path = environment.get(
        "PYTHONPATH",
        "",
    )

    python_paths = [str(SRC_DIR)]

    if current_python_path:
        python_paths.append(current_python_path)

    environment["PYTHONPATH"] = os.pathsep.join(
        python_paths
    )

    return environment


def run_backend_batch(
    mode: str,
    timeout_seconds: int,
) -> None:
    """
    backend.batchを指定モードで実行する。

    実行例:
        python -m backend.batch daily
    """
    supported_modes = {
        "daily",
        "weekly",
        "monthly",
        "yearly",
    }

    if mode not in supported_modes:
        raise ValueError(
            f"未対応のバッチ種別です: {mode}"
        )

    command = [
        sys.executable,
        "-m",
        "backend.batch",
        mode,
    ]

    logger.info(
        "バックエンドバッチを実行します: %s",
        mode,
    )

    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            env=build_subprocess_environment(),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )

    except subprocess.TimeoutExpired as error:
        raise NotificationLauncherError(
            f"{mode}バッチがタイムアウトしました。"
        ) from error

    except subprocess.CalledProcessError as error:
        standard_output = error.stdout or ""
        standard_error = error.stderr or ""

        if (
            "PermissionError" in standard_error
            or "WinError 5" in standard_error
        ):
            raise NotificationLauncherError(
                f"{mode}バッチのCSV保存に失敗しました。\n"
                "分析CSVをExcel・VS CodeのCSVプレビュー・"
                "別プロセスで開いていないか確認してください。\n"
                f"対象ディレクトリ: {BACKEND_DIR}"
            ) from error

        raise NotificationLauncherError(
            f"{mode}バッチの実行に失敗しました。\n"
            f"標準出力:\n{standard_output}\n"
            f"標準エラー:\n{standard_error}"
        ) from error

    if result.stdout.strip():
        logger.info(
            "%sバッチ標準出力:\n%s",
            mode,
            result.stdout.strip(),
        )

    if result.stderr.strip():
        logger.warning(
            "%sバッチ標準エラー:\n%s",
            mode,
            result.stderr.strip(),
        )

    logger.info(
        "%sバッチが完了しました。",
        mode,
    )


def run_all_backend_batches(
    timeout_seconds: int,
) -> None:
    """日次・週次・月次・年次バッチを順番に実行する。"""
    for mode in (
        "daily",
        "weekly",
        "monthly",
        "yearly",
    ):
        run_backend_batch(
            mode=mode,
            timeout_seconds=timeout_seconds,
        )


# ============================================================
# 分析CSV確認
# ============================================================

def capture_analysis_signatures() -> dict[str, dict[str, int] | None]:
    """分析CSVの現在状態を取得する。"""
    signatures: dict[str, dict[str, int] | None] = {}

    for mode, csv_path in ANALYSIS_CSV_PATHS.items():
        if csv_path.is_file():
            signatures[mode] = get_file_signature(csv_path)
        else:
            signatures[mode] = None

    return signatures


def validate_analysis_csv_files(
    before_signatures: dict[str, dict[str, int] | None],
) -> None:
    """
    バッチ実行後に4種類の分析CSVが存在し、
    更新されていることを確認する。
    """
    errors: list[str] = []

    for mode, csv_path in ANALYSIS_CSV_PATHS.items():
        if not csv_path.is_file():
            errors.append(
                f"{mode}: CSVが生成されていません: {csv_path}"
            )
            continue

        current_signature = get_file_signature(csv_path)
        previous_signature = before_signatures.get(mode)

        if previous_signature == current_signature:
            errors.append(
                f"{mode}: CSVが更新されていません: {csv_path}"
            )

        if current_signature["size"] <= 0:
            errors.append(
                f"{mode}: CSVが空です: {csv_path}"
            )

    if errors:
        raise NotificationLauncherError(
            "分析CSVの確認に失敗しました。\n"
            + "\n".join(errors)
        )

    logger.info(
        "日次・週次・月次・年次CSVの更新を確認しました。"
    )


# ============================================================
# 通知モジュール呼び出し
# ============================================================

def update_raw_sheets() -> Path:
    """
    CSVを読み込み、notification_database.xlsxの
    rawシートを更新する。

    今後作成するnotification_database_updater.py側に
    次の関数を実装する前提。

        update_notification_database() -> Path
    """
    try:
        from notification.notification_database_updater import (
            update_notification_database,
        )

    except ImportError as error:
        raise NotificationLauncherError(
            "notification_database_updater.pyを"
            "読み込めませんでした。"
        ) from error

    logger.info("Excelのrawシートを更新します。")

    workbook_path = update_notification_database()

    if workbook_path is None:
        workbook_path = EXCEL_PATH

    workbook_path = Path(workbook_path).resolve()

    if not workbook_path.is_file():
        raise NotificationLauncherError(
            "Updater実行後のExcelが見つかりません: "
            f"{workbook_path}"
        )

    logger.info(
        "rawシートの更新が完了しました: %s",
        workbook_path,
    )

    return workbook_path


def calculate_notifications(
    workbook_path: Path,
) -> dict[str, list[dict[str, object]]]:
    """
    通知用データを計算する。

    今後作成するnotification_calculator.py側に
    次の関数を実装する前提。

        calculate_all_notifications(
            workbook_path: Path,
        ) -> dict[str, list[dict[str, object]]]
    """
    try:
        from notification.notification_calculator import (
            calculate_all_notifications,
        )

    except ImportError as error:
        raise NotificationLauncherError(
            "notification_calculator.pyを"
            "読み込めませんでした。"
        ) from error

    logger.info("通知用データを計算します。")

    calculated_data = calculate_all_notifications(
        workbook_path=workbook_path,
    )

    if not isinstance(calculated_data, dict):
        raise NotificationLauncherError(
            "Calculatorの戻り値はdictである必要があります。"
        )

    logger.info("通知用データの計算が完了しました。")

    return calculated_data


def write_notification_sheets(
    workbook_path: Path,
    calculated_data: dict[str, list[dict[str, object]]],
) -> None:
    """
    計算結果をnotificationシートへ書き込む。

    今後作成するnotification_writer.py側に
    次の関数を実装する前提。

        write_all_notification_sheets(
            workbook_path: Path,
            notification_data: dict[...],
        ) -> None
    """
    try:
        from notification.notification_writer import (
            write_all_notification_sheets,
        )

    except ImportError as error:
        raise NotificationLauncherError(
            "notification_writer.pyを"
            "読み込めませんでした。"
        ) from error

    logger.info("notificationシートを更新します。")

    write_all_notification_sheets(
        workbook_path=workbook_path,
        notification_data=calculated_data,
    )

    logger.info(
        "notificationシートの更新が完了しました。"
    )


def send_slack_notifications(
    workbook_path: Path,
) -> dict[str, int]:
    """
    notificationシートのPENDING行をSlackへ送る。

    今後作成するnotification_sender.py側に
    次の関数を実装する前提。

        send_pending_notifications(
            workbook_path: Path,
        ) -> dict[str, int]
    """
    try:
        from notification.notification_sender import (
            send_pending_notifications,
        )

    except ImportError as error:
        raise NotificationLauncherError(
            "notification_sender.pyを"
            "読み込めませんでした。"
        ) from error

    logger.info("Slack通知を開始します。")

    result = send_pending_notifications(
        workbook_path=workbook_path,
    )

    if not isinstance(result, dict):
        raise NotificationLauncherError(
            "Senderの戻り値はdictである必要があります。"
        )

    logger.info(
        "Slack通知が完了しました: %s",
        result,
    )

    return result


# ============================================================
# 1回分の通知処理
# ============================================================

def run_notification_pipeline(
    detections_signature: dict[str, int],
    batch_timeout_seconds: int,
) -> None:
    """CSV更新後の通知処理を最初から最後まで実行する。"""
    logger.info("=" * 72)
    logger.info("通知処理を開始します。")
    logger.info("=" * 72)

    # バッチ前の分析CSV状態
    before_analysis_signatures = capture_analysis_signatures()

    # backend.batchを自動実行
    run_all_backend_batches(
        timeout_seconds=batch_timeout_seconds,
    )

    # 4つの分析CSVの生成・更新を確認
    validate_analysis_csv_files(
        before_signatures=before_analysis_signatures,
    )

    # rawシート更新
    workbook_path = update_raw_sheets()

    # 通知用データ計算
    calculated_data = calculate_notifications(
        workbook_path=workbook_path,
    )

    # notificationシート更新
    write_notification_sheets(
        workbook_path=workbook_path,
        calculated_data=calculated_data,
    )

    # Slack通知
    send_slack_notifications(
        workbook_path=workbook_path,
    )

    # 全処理成功後だけ状態を保存する
    save_launcher_state(
        detections_signature=detections_signature,
    )

    logger.info("=" * 72)
    logger.info("通知処理が正常に完了しました。")
    logger.info("=" * 72)


# ============================================================
# 監視処理
# ============================================================

def monitor_detections_csv(
    poll_interval_seconds: float,
    stable_wait_seconds: float,
    batch_timeout_seconds: int,
    run_once: bool,
    process_existing: bool,
    reset_baseline: bool,
) -> None:
    """detections.csvを監視し、更新時に通知処理を開始する。"""
    logger.info(
        "監視対象: %s",
        DETECTIONS_CSV,
    )

    logger.info(
        "監視間隔: %.1f秒",
        poll_interval_seconds,
    )

    # 監視開始前から存在するdetections.csvを誤処理しない。
    # Launcher起動後、動画解析APIがCSVを追加・更新した時だけ処理する。
    if DETECTIONS_CSV.is_file():
        state = load_launcher_state()

        if (
            not process_existing
            and (
                reset_baseline
                or not isinstance(state.get("detections_csv"), dict)
            )
        ):
            baseline_signature = wait_until_file_is_stable(
                path=DETECTIONS_CSV,
                wait_seconds=stable_wait_seconds,
            )
            save_launcher_state(
                detections_signature=baseline_signature,
            )
            logger.info(
                "現在のdetections.csvを監視開始時点の基準として登録しました。"
            )
            logger.info(
                "動画解析ジョブによる次回のCSV追加・更新を待機します。"
            )

    while True:
        try:
            if not DETECTIONS_CSV.is_file():
                logger.info(
                    "detections.csvの生成を待っています: %s",
                    DETECTIONS_CSV,
                )

                if run_once:
                    raise FileNotFoundError(
                        f"detections.csvがありません: "
                        f"{DETECTIONS_CSV}"
                    )

                time.sleep(poll_interval_seconds)
                continue

            state = load_launcher_state()
            current_signature = get_file_signature(
                DETECTIONS_CSV
            )

            if not is_new_detection_data(
                current_signature=current_signature,
                state=state,
            ):
                logger.debug(
                    "detections.csvに更新はありません。"
                )

                if run_once:
                    logger.info(
                        "未処理の更新がないため終了します。"
                    )
                    return

                time.sleep(poll_interval_seconds)
                continue

            logger.info(
                "detections.csvの新規作成・更新を検知しました。"
            )

            stable_signature = wait_until_file_is_stable(
                path=DETECTIONS_CSV,
                wait_seconds=stable_wait_seconds,
            )

            run_notification_pipeline(
                detections_signature=stable_signature,
                batch_timeout_seconds=batch_timeout_seconds,
            )

            if run_once:
                return

        except KeyboardInterrupt:
            logger.info("通知監視を終了します。")
            return

        except Exception:
            logger.exception(
                "通知処理中にエラーが発生しました。"
            )

            if run_once:
                raise

        time.sleep(poll_interval_seconds)


# ============================================================
# CLI
# ============================================================

def parse_args() -> argparse.Namespace:
    """コマンドライン引数を読み込む。"""
    parser = argparse.ArgumentParser(
        description=(
            "backend/detections.csvを監視し、"
            "統計バッチ・Excel更新・Slack通知を自動実行します。"
        )
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help=(
            "常時監視せず、未処理のdetections.csvを"
            "1回だけ処理します。"
        ),
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help=(
            "detections.csvを確認する間隔。"
            f"既定値: {DEFAULT_POLL_INTERVAL_SECONDS}秒"
        ),
    )

    parser.add_argument(
        "--stable-wait",
        type=float,
        default=DEFAULT_STABLE_WAIT_SECONDS,
        help=(
            "CSVの書き込み完了確認に使う待機時間。"
            f"既定値: {DEFAULT_STABLE_WAIT_SECONDS}秒"
        ),
    )

    parser.add_argument(
        "--batch-timeout",
        type=int,
        default=DEFAULT_BATCH_TIMEOUT_SECONDS,
        help=(
            "各backend.batchのタイムアウト秒数。"
            f"既定値: {DEFAULT_BATCH_TIMEOUT_SECONDS}秒"
        ),
    )

    parser.add_argument(
        "--process-existing",
        action="store_true",
        help=(
            "監視開始時点ですでに存在するdetections.csvも"
            "直ちに処理します。通常は指定せず、次回更新を待ちます。"
        ),
    )

    parser.add_argument(
        "--reset-baseline",
        action="store_true",
        help=(
            "現在のdetections.csvを監視開始時点の基準として再登録し、"
            "その後の次回更新だけを待ちます。"
        ),
    )

    return parser.parse_args()


def main() -> None:
    """通知システムの起動処理。"""
    args = parse_args()

    if args.interval <= 0:
        raise ValueError(
            "--intervalは0より大きくしてください。"
        )

    if args.stable_wait <= 0:
        raise ValueError(
            "--stable-waitは0より大きくしてください。"
        )

    if args.batch_timeout <= 0:
        raise ValueError(
            "--batch-timeoutは0より大きくしてください。"
        )

    validate_environment()

    monitor_detections_csv(
        poll_interval_seconds=args.interval,
        stable_wait_seconds=args.stable_wait,
        batch_timeout_seconds=args.batch_timeout,
        run_once=args.once,
        process_existing=args.process_existing,
        reset_baseline=args.reset_baseline,
    )


if __name__ == "__main__":
    main()