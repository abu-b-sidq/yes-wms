from types import SimpleNamespace

from app.core.config import get_runtime_settings
import wms_middleware.settings as settings_module


def _clear_runtime_settings_cache() -> None:
    get_runtime_settings.cache_clear()


def test_log_destination_defaults_to_file(monkeypatch):
    monkeypatch.delenv("LOG_DESTINATION", raising=False)
    monkeypatch.delenv("LOG_FILE_PATH", raising=False)

    _clear_runtime_settings_cache()
    runtime = get_runtime_settings()

    assert runtime.log_destination == "file"
    assert runtime.log_file_path == "/app/logs/yes-wms.log"


def test_invalid_log_destination_falls_back_to_file(monkeypatch):
    monkeypatch.setenv("LOG_DESTINATION", "invalid")

    _clear_runtime_settings_cache()
    runtime = get_runtime_settings()

    assert runtime.log_destination == "file"


def test_firehose_log_destination(monkeypatch):
    monkeypatch.setenv("LOG_DESTINATION", "firehose")

    _clear_runtime_settings_cache()
    runtime = get_runtime_settings()

    assert runtime.log_destination == "firehose"


def test_build_logging_handler_for_firehose(monkeypatch):
    """Without FIREHOSE_DELIVERY_STREAM_NAME, firehose destination uses stdout."""
    monkeypatch.setattr(settings_module, "LOG_DESTINATION", "firehose")
    monkeypatch.setattr(
        settings_module,
        "RUNTIME_SETTINGS",
        SimpleNamespace(firehose_delivery_stream_name=""),
    )

    handler = settings_module._build_logging_handler("json")

    assert handler["class"] == "logging.StreamHandler"
    assert handler["formatter"] == "json"


def test_build_logging_handler_for_firehose_push(monkeypatch):
    """With FIREHOSE_DELIVERY_STREAM_NAME set, firehose destination uses FirehoseHandler."""
    monkeypatch.setattr(settings_module, "LOG_DESTINATION", "firehose")
    monkeypatch.setattr(
        settings_module,
        "RUNTIME_SETTINGS",
        SimpleNamespace(
            firehose_delivery_stream_name="my-delivery-stream",
            firehose_region="us-east-1",
            firehose_batch_size=20,
            firehose_flush_interval_seconds=5.0,
        ),
    )

    handler = settings_module._build_logging_handler("json")

    assert handler["()"] == "app.core.firehose_handler.FirehoseHandler"
    assert handler["delivery_stream_name"] == "my-delivery-stream"
    assert handler["region_name"] == "us-east-1"
    assert handler["batch_size"] == 20
    assert handler["flush_interval_seconds"] == 5.0
    assert handler["formatter"] == "json"


def test_build_logging_handler_for_file(monkeypatch, tmp_path):
    monkeypatch.setattr(settings_module, "LOG_DESTINATION", "file")
    monkeypatch.setattr(settings_module, "LOG_FILE_PATH", str(tmp_path / "service.log"))
    monkeypatch.setattr(settings_module, "LOG_FILE_MAX_BYTES", 52_428_800)
    monkeypatch.setattr(settings_module, "LOG_FILE_BACKUP_COUNT", 10)

    handler = settings_module._build_logging_handler("json")

    assert handler["class"] == "logging.handlers.RotatingFileHandler"
    assert handler["formatter"] == "json"
    assert handler["filename"] == str(tmp_path / "service.log")
    assert handler["maxBytes"] == 52_428_800
    assert handler["backupCount"] == 10


def test_build_llm_prompt_logging_handler_uses_llm_prompts_file(monkeypatch, tmp_path):
    monkeypatch.setattr(settings_module, "LOG_FILE_PATH", str(tmp_path / "service.log"))
    monkeypatch.setattr(settings_module, "LOG_FILE_MAX_BYTES", 52_428_800)
    monkeypatch.setattr(settings_module, "LOG_FILE_BACKUP_COUNT", 10)
    monkeypatch.delenv("LLM_PROMPT_LOG_FILE_PATH", raising=False)

    handler = settings_module._build_llm_prompt_logging_handler("json")

    assert handler["class"] == "logging.handlers.RotatingFileHandler"
    assert handler["formatter"] == "json"
    assert handler["filename"] == str(tmp_path / "llm_prompts")
    assert handler["maxBytes"] == 52_428_800
    assert handler["backupCount"] == 10


def test_build_llm_prompt_logging_handler_honors_override(monkeypatch, tmp_path):
    custom_path = tmp_path / "custom-llm-prompts.log"
    monkeypatch.setattr(settings_module, "LOG_FILE_PATH", str(tmp_path / "service.log"))
    monkeypatch.setattr(settings_module, "LOG_FILE_MAX_BYTES", 52_428_800)
    monkeypatch.setattr(settings_module, "LOG_FILE_BACKUP_COUNT", 10)
    monkeypatch.setenv("LLM_PROMPT_LOG_FILE_PATH", str(custom_path))

    handler = settings_module._build_llm_prompt_logging_handler("json")

    assert handler["filename"] == str(custom_path)


def test_build_logging_handler_falls_back_to_tmp_when_directory_is_not_writable(monkeypatch):
    monkeypatch.setattr(settings_module, "LOG_DESTINATION", "file")
    monkeypatch.setattr(settings_module, "LOG_FILE_PATH", "/app/logs/yes-wms.log")
    monkeypatch.setattr(settings_module, "LOG_FILE_MAX_BYTES", 52_428_800)
    monkeypatch.setattr(settings_module, "LOG_FILE_BACKUP_COUNT", 10)

    def raise_os_error(*args, **kwargs):
        raise OSError("cannot create directory")

    monkeypatch.setattr(settings_module.os, "makedirs", raise_os_error)

    handler = settings_module._build_logging_handler("json")

    assert handler["filename"] == "/tmp/yes-wms.log"


def test_build_llm_prompt_logging_handler_falls_back_to_tmp_when_directory_is_not_writable(monkeypatch):
    monkeypatch.setattr(settings_module, "LOG_FILE_PATH", "/app/logs/yes-wms.log")
    monkeypatch.setattr(settings_module, "LOG_FILE_MAX_BYTES", 52_428_800)
    monkeypatch.setattr(settings_module, "LOG_FILE_BACKUP_COUNT", 10)
    monkeypatch.delenv("LLM_PROMPT_LOG_FILE_PATH", raising=False)

    def raise_os_error(*args, **kwargs):
        raise OSError("cannot create directory")

    monkeypatch.setattr(settings_module.os, "makedirs", raise_os_error)

    handler = settings_module._build_llm_prompt_logging_handler("json")

    assert handler["filename"] == "/tmp/llm_prompts"
