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
CONF_AUTO_VOLUME_CONTROL_PLAYERS = "auto_volume_control_players"
CONF_AUTO_VOLUME_EXCLUDE_PLAYERS = "auto_volume_exclude_players"
CONF_NIGHT_DND = "night_dnd"
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
EVENT_CONFIRMATION = "notifier_hub_confirmation"

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


def normalize_locale(language: str) -> str:
    """Normalize a locale code to ``ll`` or ``ll-CC`` form.

    Home Assistant may report locales in a variety of shapes
    (``pt_BR``, ``PT-br``, ``pt``). This normalizes the language subtag to
    lower case and the region subtag to upper case, using ``-`` as separator.

    Examples: ``pt_BR`` -> ``pt-BR``, ``PT-br`` -> ``pt-BR``, ``pt`` -> ``pt``.
    """
    if not language:
        return ""
    parts = language.replace("_", "-").split("-")
    lang = parts[0].lower()
    if len(parts) > 1 and parts[1]:
        return f"{lang}-{parts[1].upper()}"
    return lang
