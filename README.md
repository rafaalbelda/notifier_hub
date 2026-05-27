# Notifier Hub - integración personalizada de Home Assistant

Conversión de la aplicación AppDaemon `Centro Notifiche / Notifier` a una integración nativa de Home Assistant.

## Qué incluye

- Servicio `notifier_hub.send` para enviar mensajes.
- Listener del evento compatible `notifier`, para poder seguir usando llamadas tipo `event: notifier`.
- Notificaciones persistentes en Home Assistant.
- Notificaciones por servicios `notify.*`: Telegram, mobile_app, Pushover, Discord y otros servicios notify genéricos.
- Alexa Media Player: TTS, announce, push, reproducción de contenido, volumen temporal y restauración de volumen.
- Google/Cast: TTS mediante servicios `tts.*`, reproducción de contenido en `media_player`, volumen temporal y restauración de volumen.
- Llamada telefónica por `hassio.addon_stdin` con DSS VoIP o `shell_command.telegram_call` para CallMeBot.
- Sensores propios:
  - `sensor.notifier_hub_debug`
  - `sensor.notifier_hub_last_message`
  - `binary_sensor.notifier_hub_alexa_speak`

## Qué se ha eliminado

- Descarga automática del paquete desde GitHub.
- Gestión de grupos creada por AppDaemon.

## Instalación

Copia la carpeta:

```text
custom_components/notifier_hub
```

en:

```text
/config/custom_components/notifier_hub
```

Reinicia Home Assistant y añade la integración desde:

```text
Ajustes > Dispositivos y servicios > Añadir integración > Notifier Hub
```

También puedes configurarla en `configuration.yaml`:

```yaml
notifier_hub:
  personal_assistant: Jarvis
  notify_services:
    - notify.mobile_app_mi_telefono
    - notify.telegram
  alexa_players:
    - media_player.echo_salon
    - media_player.echo_cocina
  alexa_skill_id: ""
  google_players:
    - media_player.google_home_salon
  google_tts_service: google_translate_say
  google_notify_service: google_assistant
  sip_server_name: fritz.box:5060
  default_language: es-ES
  default_volume: 0.30
  tts_wait_time: 3
  text_notifications: true
  screen_notifications: true
  speech_notifications: true
  phone_notifications: false
  dnd_entity: binary_sensor.notifier_dnd
  guest_mode_entity: input_boolean.notifier_guest_mode
  priority_message_entity: input_boolean.notifier_priority_message
  location_tracker: group.notifier_location_tracker
```

## Uso como servicio

```yaml
action: notifier_hub.send
data:
  title: "Puerta"
  message: "Se ha abierto la puerta principal"
  notify: true
  alexa:
    media_player:
      - media_player.echo_salon
    type: tts
    volume: 0.35
```

## Uso compatible con evento AppDaemon

```yaml
event: notifier
event_data:
  title: "Lavadora"
  message: "La lavadora ha terminado"
  notify: true
  alexa:
    media_player: media_player.echo_salon
    type: announce
    method: all
    volume: 0.4
```

## Uso con Google/Cast

```yaml
action: notifier_hub.send
data:
  title: "Aviso"
  message: "Mensaje enviado por Google Cast"
  notify: false
  google:
    media_player: media_player.google_home_salon
    volume: 0.35
    tts_service: google_translate_say
```

También puedes reproducir contenido multimedia:

```yaml
action: notifier_hub.send
data:
  title: "Audio"
  message: ""
  notify: false
  google:
    media_player: media_player.google_home_salon
    media_content_id: "https://example.com/audio.mp3"
    media_content_type: music
```

## Ejemplo con imagen en Telegram

```yaml
action: notifier_hub.send
data:
  title: "Cámara"
  message: "Movimiento detectado"
  notify: notify.telegram
  image: /config/www/camara.jpg
  caption: "Movimiento detectado"
```

## Ejemplo de llamada

```yaml
action: notifier_hub.send
data:
  title: "Alerta"
  message: "Alarma activada"
  phone: true
  called_number: "+34600000000"
```

## Notas de migración

- Donde antes se usaba `script.my_notify`, ahora puede usarse `notifier_hub.send`.
- Donde antes se lanzaba `event: notifier`, puede mantenerse igual.
- Las entidades auxiliares existentes (`input_boolean`, `input_select`, etc.) ya no son obligatorias. Si quieres conservar lógica de no molestar, invitados o prioridad, indícalas en la configuración.
- La parte Google/Cast se ha añadido como gestor nativo. Usa `google: true` o un diccionario `google:` en el servicio/evento.
