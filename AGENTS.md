# Notifier Hub Integration - AI Agent Guidelines

This is a **Home Assistant custom integration** that provides a centralized notification hub supporting multiple channels: text notifications, Alexa TTS, Google TTS, phone calls, and persistent notifications.

## Quick Architecture

```
NotifierHub (coordinator)
├── NotificationManager (text/persistent messages)
├── AlexaManager (TTS + media playback)
├── GoogleManager (TTS + media playback)
└── PhoneManager (voice calls)
```

**Entry Point**: [__init__.py](custom_components/notifier_hub/__init__.py) initializes the hub, registers services, and coordinates message dispatch.

## Key Patterns & Conventions

### Manager Pattern
- **AlexaManager** and **GoogleManager** use `asyncio.Queue` for sequential TTS processing (prevents overlapping playback)
- **Worker Pattern**: Each manager has an async task consuming queue items one at a time
- **Volume Management**: Saves current volume → plays TTS → restores original volume
- **Task Cleanup**: Always cancel tasks on unload with proper error handling

### Text Processing
- Use helper functions from [helpers.py](custom_components/notifier_hub/helpers.py):
  - `check_bool()` - Convert string/value to boolean
  - `return_list()` - Convert comma-separated strings/lists/tuples to list
  - `remove_tags()` - Strip HTML/SSML tags for TTS
  - `has_numbers()` - Detect time/large numbers for duration estimation
  - `estimate_speech_duration()` - Calculate TTS playback time (formula: words × 0.42 + adjustments)
- Service-specific cleanup: Telegram needs captions, Pushover needs URLs, Discord needs embeds

### Configuration
- **Merged Config**: Combines `entry.data` (setup) + `entry.options` (runtime updates)
- **Constants**: All magic strings in [const.py](custom_components/notifier_hub/const.py)
- **Validation**: Voluptuous schemas with sensible defaults
- **Config Flow**: [config_flow.py](custom_components/notifier_hub/config_flow.py) uses entity selectors for media players

### State-Based Routing
Messages are routed through state checks:
- **Location**: Checks `location_tracker` entity (can suppress notifications)
- **DND**: Blocks TTS and phone if `dnd_entity` is "on"
- **Guest Mode**: Overrides location check if enabled
- **Priority**: Bypasses all toggles if `priority_message_entity` is "on"
- **Toggles**: `text_notifications`, `screen_notifications`, `speech_notifications`, `phone_notifications`

## Common Development Tasks

### Adding a New Notification Channel
1. Create a new manager class in `custom_components/notifier_hub/` extending the manager pattern
2. Initialize it in [__init__.py](custom_components/notifier_hub/__init__.py) during setup
3. Add config options to [const.py](custom_components/notifier_hub/const.py)
4. Update config schema in [__init__.py](custom_components/notifier_hub/__init__.py)
5. Update [services.yaml](custom_components/notifier_hub/services.yaml) with new service fields
6. Add routing logic to `NotifierHub.dispatch()` method

### Modifying TTS Processing
- **Alexa**: [alexa_manager.py](custom_components/notifier_hub/alexa_manager.py) handles SSML generation with voice, prosody, language tagging, speechcons
- **Google**: [google_manager.py](custom_components/notifier_hub/google_manager.py) routes to configurable `tts.*` service
- **Player Resolution**: Both managers support entity IDs, friendly names, groups, and sensor values
- **Speech Duration**: [helpers.py](custom_components/notifier_hub/helpers.py) `estimate_speech_duration()` used for timing

### Updating Text Notification Services
- [notification_manager.py](custom_components/notifier_hub/notification_manager.py) handles dispatch to `notify.*` services
- Each service has a payload builder: Telegram (photos), Pushover (priority), Discord (embeds), mobile_app (TTS injection), generic
- Text substitution chains apply regex replacements before sending (see `SUB_NOWRAP`, `SUB_WRAP`)

### Adding Entities
- Extend `NotifierHubEntity` from [entity.py](custom_components/notifier_hub/entity.py)
- Sensors go in [sensor.py](custom_components/sensor.py) (debug status, last message)
- Binary sensors go in [binary_sensor.py](custom_components/notifier_hub/binary_sensor.py) (Alexa/Google speaking states)
- No polling needed (`_attr_should_poll = False`)
- Update via `async_update_state()` which calls `async_write_ha_state()`

## File Structure & Purposes

| File | Purpose |
|------|---------|
| [__init__.py](custom_components/notifier_hub/__init__.py) | Integration entry point, setup, services, events, config merging |
| [notification_manager.py](custom_components/notifier_hub/notification_manager.py) | Text notifications, persistent messages, notify.* service dispatch |
| [alexa_manager.py](custom_components/notifier_hub/alexa_manager.py) | Alexa TTS, SSML generation, voice selection, media playback |
| [google_manager.py](custom_components/notifier_hub/google_manager.py) | Google/Cast TTS, flexible service routing, media playback |
| [phone_manager.py](custom_components/notifier_hub/phone_manager.py) | VoIP calls (DSS VoIP, CallMeBot), voice language mapping |
| [config_flow.py](custom_components/notifier_hub/config_flow.py) | Configuration UI and YAML import |
| [entity.py](custom_components/notifier_hub/entity.py) | Base entity class with common setup |
| [sensor.py](custom_components/notifier_hub/sensor.py) | Debug and last-message sensors |
| [binary_sensor.py](custom_components/notifier_hub/binary_sensor.py) | Alexa/Google speaking state sensors |
| [const.py](custom_components/notifier_hub/const.py) | Constants, config keys, defaults |
| [helpers.py](custom_components/notifier_hub/helpers.py) | Utility functions (text processing, normalization, duration estimation) |
| [services.yaml](custom_components/notifier_hub/services.yaml) | Service schema definitions |
| [manifest.json](custom_components/notifier_hub/manifest.json) | Integration metadata |

## Testing & Debugging

**Debug Sensor**: Enable debug mode in config to populate `sensor.notifier_hub_debug` with status and error details.

**Event Listener**: Integration listens to `notifier` events for AppDaemon compatibility:
```python
event: notifier
event_data:
  title: "Example"
  message: "Message content"
  notify: true
  alexa: { media_player: ..., type: tts, volume: 0.35 }
```

**Service Call**: Primary interface is `notifier_hub.send` service with full payload options.

**Queue Processing**: Both Alexa and Google managers process TTS sequentially—use binary sensors to monitor when playback is happening.

## Important Notes

- **Single Instance**: Only one notifier_hub integration per Home Assistant instance (unique_id enforced)
- **No External Dependencies**: Uses only built-in HA services (notify.*, tts.*, media_player.*)
- **Async-First**: All I/O operations are async-safe
- **Language Support**: Configurable defaults (default_language: es-ES) with per-message overrides
- **Volume Control**: TTS automatically manages volume—never sends bare volume commands
- **Timing**: `tts_wait_time` config provides buffer for speech duration estimation

## Common Pitfalls to Avoid

1. **Blocking the Queue**: Don't add long-running operations to manager queues—they block subsequent TTS
2. **Missing Task Cleanup**: Always cancel async tasks in unload methods
3. **Hardcoded Strings**: Use constants from [const.py](custom_components/notifier_hub/const.py)
4. **Direct Entity Updates**: Use `async_update_state()` instead of directly setting `_attr_state`
5. **Ignoring Config Merging**: Always check both `entry.data` and `entry.options` for settings
6. **Service Resolution**: Use helper functions instead of assuming entity_id format

## References

- [README.md](README.md) - Full user documentation with examples
- [example_automation.yaml](example_automation.yaml) - Real-world usage examples
- [Home Assistant Integration Documentation](https://developers.home-assistant.io/docs/creating_component_index/)
