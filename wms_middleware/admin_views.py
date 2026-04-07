from collections.abc import Callable
from dataclasses import dataclass
from io import StringIO
import json
from pathlib import Path
from queue import Queue
import threading
from typing import Any

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.management import call_command, get_commands, load_command_class
from django.core.management.base import CommandError
from django.http import HttpResponseNotAllowed, JsonResponse, StreamingHttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from app.masters.models import Organization

DOCKER_MANAGE_PREFIX = "docker compose exec wms-middleware python manage.py"
PROJECT_COMMAND_PREFIX = "app."
DEFAULT_KNOWLEDGE_DIR = Path(settings.BASE_DIR) / "knowledge"


class IndexExistingDataForm(forms.Form):
    org = forms.ModelChoiceField(
        label="Organization",
        queryset=Organization.objects.order_by("name", "id"),
        empty_label="Select organization",
    )
    content_type = forms.ChoiceField(
        label="Content Type",
        choices=[
            ("all", "All"),
            ("transaction", "Transactions"),
            ("sku", "SKUs"),
        ],
        initial="all",
    )


class IndexKnowledgeForm(forms.Form):
    org = forms.ModelChoiceField(
        label="Organization",
        queryset=Organization.objects.order_by("name", "id"),
        empty_label="Select organization",
    )
    knowledge_dir = forms.CharField(
        label="Knowledge Directory",
        max_length=1024,
        initial=str(DEFAULT_KNOWLEDGE_DIR),
    )


@dataclass(frozen=True)
class ManagementCommandEntry:
    name: str
    app_name: str
    help_text: str
    docker_command: str
    help_command: str


@dataclass(frozen=True)
class RunnableCommandConfig:
    name: str
    title: str
    description: str
    form_class: type[forms.Form]
    build_kwargs: Callable[[dict[str, Any]], dict[str, Any]]

    @property
    def docker_command(self) -> str:
        return f"{DOCKER_MANAGE_PREFIX} {self.name}"

    @property
    def help_command(self) -> str:
        return f"{self.docker_command} --help"


@dataclass(frozen=True)
class CommandExecutionResult:
    command_name: str
    success: bool
    stdout: str
    stderr: str


@dataclass(frozen=True)
class StreamEvent:
    event: str
    stream: str | None = None
    text: str | None = None
    success: bool | None = None


class StreamingCommandWriter:
    def __init__(self, event_queue: Queue[StreamEvent], stream_name: str):
        self.event_queue = event_queue
        self.stream_name = stream_name

    def write(self, text: str) -> int:
        if text:
            self.event_queue.put(StreamEvent(event="chunk", stream=self.stream_name, text=text))
        return len(text)

    def flush(self) -> None:
        return None


def _build_index_existing_data_kwargs(cleaned_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "org_id": cleaned_data["org"].id,
        "content_type": cleaned_data["content_type"],
    }


def _build_index_knowledge_kwargs(cleaned_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "org_id": cleaned_data["org"].id,
        "knowledge_dir": cleaned_data["knowledge_dir"],
    }


RUNNABLE_COMMANDS: dict[str, RunnableCommandConfig] = {
    "index_existing_data": RunnableCommandConfig(
        name="index_existing_data",
        title="Run Existing Data Embedding Index",
        description="Backfill transaction and SKU embeddings for a single organization.",
        form_class=IndexExistingDataForm,
        build_kwargs=_build_index_existing_data_kwargs,
    ),
    "index_knowledge": RunnableCommandConfig(
        name="index_knowledge",
        title="Run Knowledge Embedding Index",
        description="Embed markdown knowledge files for a single organization.",
        form_class=IndexKnowledgeForm,
        build_kwargs=_build_index_knowledge_kwargs,
    ),
}


def _get_command_help_text(app_name: str, command_name: str) -> str:
    try:
        command = load_command_class(app_name, command_name)
    except Exception:
        return "Help unavailable."

    help_text = getattr(command, "help", "") or "No help text provided."
    return str(help_text)


def _build_command_entry(command_name: str, app_name: str) -> ManagementCommandEntry:
    return ManagementCommandEntry(
        name=command_name,
        app_name=app_name,
        help_text=_get_command_help_text(app_name, command_name),
        docker_command=f"{DOCKER_MANAGE_PREFIX} {command_name}",
        help_command=f"{DOCKER_MANAGE_PREFIX} {command_name} --help",
    )


def _build_command_sections() -> list[dict[str, object]]:
    command_map = get_commands()
    project_commands: list[ManagementCommandEntry] = []
    framework_commands: list[ManagementCommandEntry] = []

    for command_name in sorted(command_map):
        app_name = command_map[command_name] or "unknown"
        entry = _build_command_entry(command_name, app_name)
        if app_name.startswith(PROJECT_COMMAND_PREFIX):
            project_commands.append(entry)
        else:
            framework_commands.append(entry)

    return [
        {
            "title": "YES WMS Commands",
            "description": "Commands defined in this workspace.",
            "commands": project_commands,
        },
        {
            "title": "Framework And Third-Party Commands",
            "description": "Commands provided by Django and installed packages.",
            "commands": framework_commands,
        },
    ]


def _build_runnable_forms(
    data: dict[str, Any] | None = None,
    selected_command: str | None = None,
) -> dict[str, forms.Form]:
    forms_by_name: dict[str, forms.Form] = {}
    for command_name, config in RUNNABLE_COMMANDS.items():
        if data is not None and command_name == selected_command:
            forms_by_name[command_name] = config.form_class(data=data, prefix=command_name)
        else:
            forms_by_name[command_name] = config.form_class(prefix=command_name)
    return forms_by_name


def _execute_command(command_name: str, cleaned_data: dict[str, Any]) -> CommandExecutionResult:
    config = RUNNABLE_COMMANDS[command_name]
    stdout_buffer = StringIO()
    stderr_buffer = StringIO()

    try:
        call_command(
            command_name,
            stdout=stdout_buffer,
            stderr=stderr_buffer,
            **config.build_kwargs(cleaned_data),
        )
        return CommandExecutionResult(
            command_name=command_name,
            success=True,
            stdout=stdout_buffer.getvalue().strip(),
            stderr=stderr_buffer.getvalue().strip(),
        )
    except CommandError as exc:
        if not stderr_buffer.getvalue().strip():
            stderr_buffer.write(str(exc))
        return CommandExecutionResult(
            command_name=command_name,
            success=False,
            stdout=stdout_buffer.getvalue().strip(),
            stderr=stderr_buffer.getvalue().strip(),
        )
    except Exception as exc:
        if not stderr_buffer.getvalue().strip():
            stderr_buffer.write(str(exc))
        return CommandExecutionResult(
            command_name=command_name,
            success=False,
            stdout=stdout_buffer.getvalue().strip(),
            stderr=stderr_buffer.getvalue().strip(),
        )


def _build_runnable_command_context(forms_by_name: dict[str, forms.Form]) -> list[dict[str, object]]:
    return [
        {
            "name": config.name,
            "title": config.title,
            "description": config.description,
            "docker_command": config.docker_command,
            "help_command": config.help_command,
            "form": forms_by_name[config.name],
        }
        for config in RUNNABLE_COMMANDS.values()
    ]


def _stream_command_output(command_name: str, cleaned_data: dict[str, Any]):
    config = RUNNABLE_COMMANDS[command_name]
    event_queue: Queue[StreamEvent] = Queue()

    def _worker() -> None:
        stdout_writer = StreamingCommandWriter(event_queue, "stdout")
        stderr_writer = StreamingCommandWriter(event_queue, "stderr")
        success = True

        try:
            call_command(
                command_name,
                stdout=stdout_writer,
                stderr=stderr_writer,
                **config.build_kwargs(cleaned_data),
            )
        except CommandError as exc:
            success = False
            stderr_writer.write(f"{exc}\n")
        except Exception as exc:
            success = False
            stderr_writer.write(f"{exc}\n")
        finally:
            event_queue.put(StreamEvent(event="complete", success=success))

    worker = threading.Thread(target=_worker, daemon=True)
    worker.start()

    while True:
        event = event_queue.get()
        payload = {
            "event": event.event,
            "stream": event.stream,
            "text": event.text,
            "success": event.success,
        }
        yield f"{json.dumps(payload)}\n"
        if event.event == "complete":
            break


def management_commands_stream_view(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    selected_command = request.POST.get("command_name")
    forms_by_name = _build_runnable_forms(request.POST, selected_command)

    if selected_command not in RUNNABLE_COMMANDS:
        return JsonResponse({"error": "Unsupported management command."}, status=400)

    selected_form = forms_by_name[selected_command]
    if not selected_form.is_valid():
        return JsonResponse({"error": "Invalid command parameters.", "errors": selected_form.errors}, status=400)

    response = StreamingHttpResponse(
        _stream_command_output(selected_command, selected_form.cleaned_data),
        content_type="application/x-ndjson",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@ensure_csrf_cookie
def management_commands_view(request):
    selected_command = request.POST.get("command_name") if request.method == "POST" else None
    forms_by_name = _build_runnable_forms(request.POST if request.method == "POST" else None, selected_command)
    execution_result: CommandExecutionResult | None = None

    if request.method == "POST":
        if selected_command not in RUNNABLE_COMMANDS:
            messages.error(request, "Unsupported management command.")
        else:
            selected_form = forms_by_name[selected_command]
            if selected_form.is_valid():
                execution_result = _execute_command(selected_command, selected_form.cleaned_data)
                if execution_result.success:
                    messages.success(request, f"{selected_command} completed.")
                else:
                    messages.error(request, f"{selected_command} failed.")
            else:
                messages.error(request, "Please correct the form errors and try again.")

    return TemplateResponse(
        request,
        "admin/management_commands.html",
        {
            **admin.site.each_context(request),
            "title": "Management Commands",
            "subtitle": "Docker command catalog",
            "stream_url": "admin_management_commands_stream",
            "runnable_commands": _build_runnable_command_context(forms_by_name),
            "execution_result": execution_result,
            "sections": _build_command_sections(),
            "docker_manage_prefix": DOCKER_MANAGE_PREFIX,
        },
    )
