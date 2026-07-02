DOMAIN = "notifier_hub"

CONF_PERSONAL_ASSISTANT = "personal_assistant"
CONF_PERSONS = "persons"
CONF_NOTIFY_SERVICES = "notify_services"
CONF_ALEXA_PLAYERS = "alexa_players"
CONF_GOOGLE_PLAYERS = "google_players"
CONF_GOOGLE_TTS_SERVICE = "google_tts_service"
CONF_GOOGLE_NOTIFY_SERVICE = "google_notify_service"
CONF_SIP_SERVER_NAME = "sip_server_name"
CONF_DEFAULT_LANGUAGE = "default_language"
CONF_DEFAULT_VOLUME = "default_volume"
CONF_TTS_WAIT_TIME = "tts_wait_time"
CONF_DEBUG = "debug"
CONF_TEXT_NOTIFICATIONS = "text_notifications"
CONF_SCREEN_NOTIFICATIONS = "screen_notifications"
CONF_SPEECH_NOTIFICATIONS = "speech_notifications"
CONF_SPEECH_HOME_ONLY = "speech_home_only"
CONF_ALEXA_NOTIFICATIONS = "alexa_notifications"
CONF_GOOGLE_NOTIFICATIONS = "google_notifications"
CONF_PHONE_NOTIFICATIONS = "phone_notifications"
CONF_HA_EVENT_NOTIFICATIONS = "ha_event_notifications"
CONF_HA_EVENT_NOTIFY_SERVICES = "ha_event_notify_services"
CONF_AUTO_VOLUME = "auto_volume"
CONF_AUTO_VOLUME_EXCLUDE_PLAYERS = "auto_volume_exclude_players"
CONF_NIGHT_DND = "night_dnd"
CONF_INSTALL_DASHBOARD = "install_dashboard"
CONF_DND_ENTITY = "dnd_entity"
CONF_GUEST_MODE_ENTITY = "guest_mode_entity"
CONF_PRIORITY_MESSAGE_ENTITY = "priority_message_entity"
CONF_DND_MODE = "dnd_mode"
CONF_GUEST_MODE = "guest_mode"
CONF_PRIORITY_MESSAGE = "priority_message"

STATE_DASHBOARD_MESSAGE = "dashboard_message"

DEFAULT_DND_ENTITY = "switch.notifier_hub_dnd"
DEFAULT_GUEST_MODE_ENTITY = "switch.notifier_hub_guest_mode"
DEFAULT_PRIORITY_MESSAGE_ENTITY = "switch.notifier_hub_priority_message"

AUTO_VOLUME_PERIODS = {
    "late_night": ("Altas horas", "01:00:00", 10),
    "early_morning": ("Primera hora", "05:00:00", 20),
    "morning": ("Mañana", "07:00:00", 30),
    "afternoon": ("Tarde", "12:00:00", 40),
    "evening": ("Atardecer", "18:00:00", 30),
    "night": ("Noche", "22:00:00", 20),
}
NIGHT_DND_PERIOD_KEYS = {"night", "late_night"}

DEFAULT_PERSONAL_ASSISTANT = "Assistant"
DEFAULT_SIP_SERVER_NAME = "fritz.box:5060"
DEFAULT_LANGUAGE = "es-ES"
DEFAULT_VOLUME = 0.30
DEFAULT_TTS_WAIT_TIME = 3.0
DEFAULT_GOOGLE_TTS_SERVICE = "google_translate_say"
DEFAULT_GOOGLE_NOTIFY_SERVICE = "google_assistant"
DEFAULT_HA_SIP_ADDON = "c7744bff_ha-sip"

SERVICE_SEND = "send"
SERVICE_SET_CONFIG = "set_config"
EVENT_NOTIFIER = "notifier"

DASHBOARD_DEFAULT_LANGUAGE = "en"
DASHBOARD_AVAILABLE_LANGUAGES = ("en", "es", "pt", "pt-BR")

DASHBOARD_INSTALL_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "title": "Notifier Hub dashboard",
        "message": (
            "The Notifier Hub dashboard has been copied to"
            " `/config/notifier_hub_dashboard.yaml`.\n\n"
            "To show it in the sidebar, add this to `configuration.yaml`"
            " and restart Home Assistant:\n\n"
            "```yaml\nlovelace:\n  dashboards:\n    notifier-hub:\n"
            "      mode: yaml\n      title: Notifier Hub\n"
            "      icon: mdi:bell-ring\n      show_in_sidebar: true\n"
            "      filename: notifier_hub_dashboard.yaml\n```"
        ),
    },
    "es": {
        "title": "Panel de Notifier Hub",
        "message": (
            "El dashboard de Notifier Hub se ha copiado a"
            " `/config/notifier_hub_dashboard.yaml`.\n\n"
            "Para mostrarlo en la barra lateral, anade esto a `configuration.yaml`"
            " y reinicia Home Assistant:\n\n"
            "```yaml\nlovelace:\n  dashboards:\n    notifier-hub:\n"
            "      mode: yaml\n      title: Notifier Hub\n"
            "      icon: mdi:bell-ring\n      show_in_sidebar: true\n"
            "      filename: notifier_hub_dashboard.yaml\n```"
        ),
    },
    "pt": {
        "title": "Painel do Notifier Hub",
        "message": (
            "O painel do Notifier Hub foi copiado para"
            " `/config/notifier_hub_dashboard.yaml`.\n\n"
            "Para o mostrar na barra lateral, adicione isto ao `configuration.yaml`"
            " e reinicie o Home Assistant:\n\n"
            "```yaml\nlovelace:\n  dashboards:\n    notifier-hub:\n"
            "      mode: yaml\n      title: Notifier Hub\n"
            "      icon: mdi:bell-ring\n      show_in_sidebar: true\n"
            "      filename: notifier_hub_dashboard.yaml\n```"
        ),
    },
    "pt-BR": {
        "title": "Painel do Notifier Hub",
        "message": (
            "O painel do Notifier Hub foi copiado para"
            " `/config/notifier_hub_dashboard.yaml`.\n\n"
            "Para exibi-lo na barra lateral, adicione isto ao `configuration.yaml`"
            " e reinicie o Home Assistant:\n\n"
            "```yaml\nlovelace:\n  dashboards:\n    notifier-hub:\n"
            "      mode: yaml\n      title: Notifier Hub\n"
            "      icon: mdi:bell-ring\n      show_in_sidebar: true\n"
            "      filename: notifier_hub_dashboard.yaml\n```"
        ),
    },
}

HA_EVENT_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "started": "Home Assistant is running.",
        "stop": "Home Assistant is stopping.",
        "final_write": "Home Assistant has completed the final write.",
        "close": "Home Assistant is closing.",
        "restart": "Manual Home Assistant restart requested.",
    },
    "es": {
        "started": "Home Assistant esta operativo.",
        "stop": "Home Assistant se esta deteniendo.",
        "final_write": "Home Assistant ha completado la escritura final.",
        "close": "Home Assistant esta cerrando.",
        "restart": "Reinicio manual de Home Assistant solicitado.",
    },
    "pt": {
        "started": "O Home Assistant está operacional.",
        "stop": "O Home Assistant está a parar.",
        "final_write": "O Home Assistant concluiu a escrita final.",
        "close": "O Home Assistant está a fechar.",
        "restart": "Reinício manual do Home Assistant solicitado.",
    },
    "pt-BR": {
        "started": "O Home Assistant está em operação.",
        "stop": "O Home Assistant está parando.",
        "final_write": "O Home Assistant concluiu a gravação final.",
        "close": "O Home Assistant está fechando.",
        "restart": "Reinício manual do Home Assistant solicitado.",
    },
}


def resolve_dashboard_language(language: str) -> str:
    """Resolve a hass.config.language value to one of DASHBOARD_AVAILABLE_LANGUAGES."""
    if language in DASHBOARD_AVAILABLE_LANGUAGES:
        return language
    primary = (language or "").split("-")[0]
    for candidate in DASHBOARD_AVAILABLE_LANGUAGES:
        if candidate.split("-")[0] == primary:
            return candidate
    return DASHBOARD_DEFAULT_LANGUAGE
