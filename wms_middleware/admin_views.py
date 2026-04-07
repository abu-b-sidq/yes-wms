from dataclasses import dataclass

from django.contrib import admin
from django.core.management import get_commands, load_command_class
from django.template.response import TemplateResponse

DOCKER_MANAGE_PREFIX = "docker compose exec wms-middleware python manage.py"
PROJECT_COMMAND_PREFIX = "app."


@dataclass(frozen=True)
class ManagementCommandEntry:
    name: str
    app_name: str
    help_text: str
    docker_command: str
    help_command: str


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
        app_name = command_map[command_name]
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


def management_commands_view(request):
    return TemplateResponse(
        request,
        "admin/management_commands.html",
        {
            **admin.site.each_context(request),
            "title": "Management Commands",
            "subtitle": "Docker command catalog",
            "sections": _build_command_sections(),
            "docker_manage_prefix": DOCKER_MANAGE_PREFIX,
        },
    )
