# Notifier Hub - TODO & Feature Roadmap

This document tracks feature requests, suggestions, and architectural improvements inspired by user feedback and comparisons with alternative notification tools (such as Universal Notifier).

---

## 1. Text vs. Voice Separation & Formatting
- [ ] **Automated Voice-Specific Stripping & Formatting**:
  - Automatically strip markdown, URLs, emojis, symbols, and formatting/prefixes (e.g., timestamps or technical tags) when dispatching messages to TTS/voice engines (Alexa / Google / Phone).
  - Retain rich markers and formatting for written text notifications (mobile app, Telegram, Pushover, Discord, etc.).
  - Allow per-channel or template-based text transformation so users can send a single payload without manually maintaining distinct versions or regex substitutions.

## 2. TTS Queuing & Concurrency Management
> *Note: AlexaManager and GoogleManager already implement internal `asyncio.Queue` workers, but concurrency across players or multi-target dispatches can still overlap under certain conditions.*
- [ ] **Cross-Manager / Global Media Player Queue**:
  - Review queue locking per `media_player` entity: ensure that if multiple automations trigger simultaneously on the same speaker (or across Alexa and Google platforms sharing speakers), notifications are cleanly queued per-device.
  - Implement sequential playback guarantees across shared targets to avoid cutting off or clipping simultaneous announcements.

## 3. Randomized Greetings & Humanized Speech
- [ ] **Greeting / Prefix Pools**:
  - Support configurable pools of randomized greetings or opening phrases (e.g., *"Hey there"*, *"Good morning"*, *"Attention"*, etc.).
  - Allow random phrase injection via service call parameters (e.g., `greeting: true` or `greeting_pool: [ ... ]`) or global configuration.
  - Optional time-of-day contextual greetings (morning, afternoon, evening).

## 4. Media Snapshot and Resume
- [ ] **Player State Snapshot & Restore**:
  - Before sending a TTS announcement or playing media, snapshot the target `media_player` state (current source, media track / URL, content type, app, playback state `playing`/`paused`, and volume).
  - Automatically resume playback of previous media after TTS has completed, rather than solely restoring the volume level.
  - Provide fallback / timeout handling if HA or speaker integrations do not cleanly report track completion.

## 5. RAW Companion App Command Support
- [ ] **Native Companion App Command Pass-through**:
  - Allow raw `command` mode payloads for Home Assistant Companion App notifications (e.g., `command_volume_level`, `command_screen_on`, `command_bluetooth`, TTS alarms, etc.).
  - Ensure raw payloads can bypass standard text notification wrapper formatting and pass custom `data` directly to `notify.mobile_app_*`.

## 6. Official Alexa Devices Integration & Entity-Based `notify.*` Support
- [ ] **Support Entity-Based `notify.*` Targets (`notify.send_message`) in Alexa and Text Channels**:
  - **Context**: `alexa_manager.py` currently assumes the legacy *Alexa Media Player* custom component which registers a `notify.alexa_media` service (`hass.services.async_call("notify", "alexa_media", ...)`). Home Assistant's official Alexa Devices integration (and modern HA notify architecture) does not register a legacy `notify.<service>` call, but instead creates per-device notify entities (e.g., `notify.<device>_speak`, `notify.<device>_announce`). Similarly, `notification_manager.py` (`send_notify`) assumes classic service names.
  - **Detection & Dispatch**:
    - Detect when a target/player/service string is a `notify.*` entity ID (or exists in the entity registry under the `notify` domain).
    - Route calls through `notify.send_message` with `{"entity_id": entity_id, "message": message}` (plus supported entity parameters) instead of `notify.<service>`.
  - **Alexa Channel Compatibility**:
    - Allow users who migrated from *Alexa Media Player* to the official *Alexa Devices* integration to use the `alexa:` channel by mapping announcements/TTS to `notify.<device>_announce` / `notify.<device>_speak`.
  - **Volume & Media Player Coupling Review**:
    - The Alexa channel currently has extra behavior tied specifically to `media_player.*` entities, such as temporary volume changes and volume restoration. Before switching or expanding to entity-based notify targets, review the best compatibility path to ensure volume adjustment/restoration or associated media player lookup can still function smoothly or degrade gracefully.

## 7. Integration with Home Assistant Marketplace / HACS Default Store
- [ ] **Home Assistant Marketplace / HACS Inclusion**:
  - **Prerequisites & Preparation**:
    - [x] Create a GitHub Release using semantic versioning (e.g. `1.0.4` or `v1.0.4`) matching the version in `manifest.json`.
    - [x] Add GitHub repository topics (`home-assistant`, `hacs`, `custom-component`, `alexa`, `tts`, `notifications`).
    - [x] Ensure GitHub Issues are enabled and consider adding standard `.github/ISSUE_TEMPLATE/` files (bug report, feature request).
    - [ ] *(Optional but recommended)* Submit logo & icon to the [home-assistant/brands](https://github.com/home-assistant/brands) repository under `custom_integrations/notifier_hub/` (`icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`).
  - **Submission Steps**:
    1. Fork the official [hacs/default](https://github.com/hacs/default) repository.
    2. Edit `repositories/integration` and add `"rafaalbelda/notifier_hub"` in alphabetical order.
    3. Open a Pull Request against `hacs/default`.
    4. Wait for automated CI action checks (`hacs.json`, `manifest.json`, repository release checks) to pass.
    5. Await HACS maintainer review and merge.

## 8. Bug Fix: Telegram Markdown Entity Parsing / Reserved Character Escaping
- [ ] **Escape Reserved MarkdownV2 Characters in Telegram Notifications (Lifecycle & Generic)**:
  - **Symptom**: When routing Home Assistant lifecycle events (or messages containing markdown titles like `*[Jarvis - 23:20:35] HomeAssistant Start!*`) to a Telegram notify service, Telegram fails with:
    ```text
    telegram.error.BadRequest: Can't parse entities: character '-' is reserved and must be escaped with the preceding '\'
    homeassistant.exceptions.HomeAssistantError: Action failed. Can't parse entities: character '-' is reserved and must be escaped with the preceding '\'
    ```
  - **Root Cause**:
    - In `notification_manager.py`, when `html` is false, `prepared_title` with formatting (such as `*[time - tag]*`) is passed directly without escaping reserved MarkdownV2 characters (e.g. `-`, `.`, `!`, `[`, `]`, `(`, `)`). Only `_` is currently escaped in `prepared_message`.
    - Lifecycle messages (`_send_ha_event_notification`) send formatted titles like `*[Jarvis - HH:MM:SS] HomeAssistant Start!*` with `html: False`, which triggers Telegram's strict Markdown/MarkdownV2 entity parser on unescaped hyphens and exclamation marks.
  - **Fix Required**:
    - Properly sanitize / escape Telegram Markdown reserved characters in both `title` and `message` when targeting `telegram`, or default Telegram messages to `parse_mode: html` / strip unsupported markdown syntax if Markdown parsing fails.
  - **Open issue in Github**:
    https://github.com/rafaalbelda/notifier_hub/issues/6


