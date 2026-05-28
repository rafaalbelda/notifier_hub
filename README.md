# Notifier Hub - integración personalizada de Home Assistant

Conversión de la aplicación AppDaemon `Centro Notifiche / Notifier` a una integración nativa de Home Assistant.

## Qué incluye

- Servicio `notifier_hub.send` para enviar mensajes.
- Listener del evento compatible `notifier`, para poder seguir usando llamadas tipo `event: notifier`.
- Notificaciones persistentes en Home Assistant.
- Notificaciones por servicios `notify.*`: Telegram, mobile_app, Pushover, Discord y otros servicios notify genéricos.
- Alexa Media Player: TTS, announce, push, reproducción de contenido, volumen temporal y restauración de volumen.
- Google/Cast: TTS mediante servicios `tts.*`, reproducción de contenido en `media_player`, volumen temporal y restauración de volumen.
- Llamada telefónica por `hassio.addon_stdin` con ha-sip.
- Sensores propios:
  - `sensor.notifier_hub_debug`
  - `sensor.notifier_hub_last_message`
  - `binary_sensor.notifier_hub_alexa_speak`
  - `binary_sensor.notifier_hub_google_speak`
- Interruptores propios para activar o desactivar canales:
  - `switch.notifier_hub_text_notifications`
  - `switch.notifier_hub_screen_notifications`
  - `switch.notifier_hub_speech_notifications`
  - `switch.notifier_hub_alexa_notifications`
  - `switch.notifier_hub_google_notifications`
  - `switch.notifier_hub_phone_notifications`
  - `switch.notifier_hub_home_assistant_event_notifications`
  - `switch.notifier_hub_auto_volume`
  - `switch.notifier_hub_dnd`
  - `switch.notifier_hub_guest_mode`
  - `switch.notifier_hub_priority_message`
- Auto volume nativo con horarios y volúmenes editables desde entidades `time.*` y `number.*`.

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

El formulario de configuración de la UI está organizado en secciones:

- Persons
- Notify Services
- Alexa
- Google
- Phone
- Notifications
- Auto Volume

## Dashboard

El archivo `notifier_hub_dashboard.yaml` incluye un panel Lovelace con estado, actividad TTS y botones de prueba.
Tambien incluye una tarjeta `Canales` con los interruptores de texto, persistente, voz, Alexa, Google y telefono.
Copialo a `/config/notifier_hub_dashboard.yaml` y registra el dashboard en `configuration.yaml`:

```yaml
lovelace:
  dashboards:
    notifier-hub:
      mode: yaml
      title: Notifier Hub
      icon: mdi:bell-ring
      show_in_sidebar: true
      filename: notifier_hub_dashboard.yaml
```

También puedes configurarla en `configuration.yaml`:

```yaml
notifier_hub:
  personal_assistant: Jarvis
  persons:
    - person.ana
    - person.carlos
  notify_services:
    - notify.mobile_app_mi_telefono
    - notify.telegram
  alexa_players:
    - media_player.echo_salon
    - media_player.echo_cocina
  google_players:
    - media_player.google_home_salon
  google_tts_service: tts.google_es_es
  google_notify_service: google_assistant
  sip_server_name: fritz.box:5060
  default_language: es-ES
  default_volume: 0.30
  tts_wait_time: 3
  text_notifications: true
  screen_notifications: true
  speech_notifications: true
  alexa_notifications: true
  google_notifications: true
  phone_notifications: false
  ha_event_notifications: true
  ha_event_notify_services:
    - notify.mobile_app_mi_telefono
  auto_volume: true
  auto_volume_exclude_players:
    - media_player.echo_dormitorio
  dnd_entity: switch.notifier_hub_dnd
  guest_mode_entity: switch.notifier_hub_guest_mode
  priority_message_entity: switch.notifier_hub_priority_message
  location_tracker: group.notifier_location_tracker
```

`persons` se puede configurar desde la UI con un selector de entidades `person.*`.
Cuando hay personas configuradas, Notifier Hub las usa para comprobar la ubicación de los mensajes con `location`.
Si `persons` está vacío, se mantiene la compatibilidad con `location_tracker`.

## Ubicacion

`location_tracker` permite filtrar mensajes segun una ubicacion.
Se compara el valor enviado en `location` con el estado de la entidad configurada:

```yaml
location_tracker: group.notifier_location_tracker
```

```yaml
action: notifier_hub.send
data:
  title: "Aviso casa"
  message: "Movimiento detectado"
  location: home
  alexa: true
```

En este ejemplo, el mensaje pasa si `group.notifier_location_tracker` esta en estado `home`.
Si el mensaje no incluye `location`, no se aplica filtro de ubicacion.

La configuracion moderna recomendada es usar `persons`:

```yaml
persons:
  - person.ana
  - person.carlos
```

Si `persons` tiene entidades, Notifier Hub las usa primero y `location_tracker` queda como fallback.
Con `location: home`, el mensaje pasa si alguna de esas personas esta en `home`.

Notas:

- `priority: true` puede saltarse el filtro de ubicacion.
- `guest_mode_entity` en `on` permite voz aunque no coincida la ubicacion.
- `dnd_entity` sigue bloqueando voz y telefono salvo mensajes prioritarios.

## Controles de canales

Notifier Hub crea interruptores para activar y desactivar canales desde la UI, automatizaciones o el dashboard:

| Entidad | Configuración | Uso |
|---|---|---|
| `switch.notifier_hub_text_notifications` | `text_notifications` | Notificaciones por servicios `notify.*` |
| `switch.notifier_hub_screen_notifications` | `screen_notifications` | Notificaciones persistentes en Home Assistant |
| `switch.notifier_hub_speech_notifications` | `speech_notifications` | Interruptor maestro de voz/TTS |
| `switch.notifier_hub_alexa_notifications` | `alexa_notifications` | TTS/announce/push de Alexa |
| `switch.notifier_hub_google_notifications` | `google_notifications` | TTS o notify de Google/Cast |
| `switch.notifier_hub_phone_notifications` | `phone_notifications` | Llamadas telefonicas |
| `switch.notifier_hub_home_assistant_event_notifications` | `ha_event_notifications` | Eventos de ciclo de vida de Home Assistant |
| `switch.notifier_hub_auto_volume` | `auto_volume` | Ajuste automatico de volumen por periodo del dia |

`speech_notifications` debe estar activado para permitir voz normal en Alexa y Google.
Los mensajes con `priority: true` o prioridad especifica de Alexa/Google pueden saltarse los interruptores, igual que en la app original.

## Eventos de Home Assistant

La app original podia avisar de eventos `Start`, `Final Write`, `Close`, `Stop` y `Restart`.
La integracion nativa escucha esos eventos directamente:

- `homeassistant_started`
- `homeassistant_final_write`
- `homeassistant_close`
- `homeassistant_stop`
- llamada al servicio `homeassistant.restart`

Activalo o desactivalo con `ha_event_notifications` o con `switch.notifier_hub_home_assistant_event_notifications`.
Por defecto usa `notify_services`; si quieres separar esos avisos, define `ha_event_notify_services`.

## Auto Volume

Auto Volume ajusta los reproductores de Alexa y Google configurados en funcion del periodo del dia.
El dashboard incluye una tarjeta `Auto Volume` con:

- `sensor.notifier_hub_day_period`
- `sensor.notifier_hub_day_period_volume`
- entidades `time.notifier_hub_*_start` para fijar el inicio de cada periodo
- entidades `number.notifier_hub_*_volume` para fijar el volumen de cada periodo en porcentaje

Periodos por defecto:

| Periodo | Inicio | Volumen |
|---|---:|---:|
| Altas horas | `01:00` | `10%` |
| Primera hora | `05:00` | `20%` |
| Manana | `07:00` | `30%` |
| Tarde | `12:00` | `40%` |
| Atardecer | `18:00` | `30%` |
| Noche | `22:00` | `20%` |

Cuando `auto_volume` esta activo, los mensajes Alexa/Google sin `volume` explicito usan el volumen del periodo actual.
La integracion tambien actualiza periodicamente el volumen de los reproductores configurados.
Usa `auto_volume_exclude_players` para excluir reproductores concretos.

## No molestar

`dnd_entity` permite usar una entidad booleana como modo no molestar.
La integracion crea y asigna por defecto este switch:

```yaml
dnd_entity: switch.notifier_hub_dnd
```

Cuando esa entidad esta en `on`, Notifier Hub bloquea los canales que pueden molestar:

- Alexa
- Google/Cast
- llamadas telefonicas

Las notificaciones de texto `notify.*` y las notificaciones persistentes siguen funcionando.
Los mensajes con `priority: true` pueden saltarse el modo no molestar.

## Modo invitados

`guest_mode_entity` permite que los avisos de voz sigan funcionando aunque las personas configuradas no esten en casa.
La integracion crea y asigna por defecto este switch:

```yaml
guest_mode_entity: switch.notifier_hub_guest_mode
```

Si esta entidad esta en `on`, Alexa y Google/Cast pueden hablar aunque la comprobacion de `persons` o `location_tracker` no coincida con la `location` del mensaje.
Es util cuando hay invitados en casa o quieres mantener los avisos domesticos aunque tu ubicacion no sea `home`.

Ejemplo:

```yaml
action: notifier_hub.send
data:
  title: "Puerta"
  message: "Se ha abierto la puerta"
  location: home
  alexa: true
```

Si no hay ninguna persona configurada en `home`, normalmente la voz no saldria.
Con `guest_mode_entity` en `on`, la voz puede salir igualmente.
`dnd_entity` sigue teniendo prioridad: si el modo no molestar esta activo, bloquea voz y telefono salvo mensajes prioritarios.

## Mensajes prioritarios

`priority_message_entity` permite usar una entidad booleana para forzar el siguiente mensaje como prioritario.
La integracion crea y asigna por defecto este switch:

```yaml
priority_message_entity: switch.notifier_hub_priority_message
```

Cuando esa entidad esta en `on`, Notifier Hub trata el mensaje como si llevara:

```yaml
priority: true
```

Un mensaje prioritario puede saltarse interruptores de canales, comprobacion de ubicacion y modo no molestar.
Despues de procesar el mensaje, Notifier Hub apaga automaticamente `priority_message_entity`.

Ejemplo:

```yaml
action: switch.turn_on
target:
  entity_id: switch.notifier_hub_priority_message
```

```yaml
action: notifier_hub.send
data:
  title: "Alarma"
  message: "Alarma activada"
  notify: true
  alexa: true
  phone: true
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
    tts_service: tts.google_es_es
```

Para instalaciones recientes de Home Assistant, usa la entidad TTS creada por la integración Google Translate, por ejemplo `tts.google_es_es`. El servicio heredado `google_translate_say` sigue funcionando si tienes configurada la plataforma antigua en YAML; si existe la entidad moderna, Notifier Hub la usará automáticamente.

### `google_tts_service`

`google_tts_service` define el motor TTS usado por defecto para los mensajes Google/Cast.
En instalaciones recientes de Home Assistant se recomienda usar una entidad `tts.*`:

```yaml
google_tts_service: tts.google_es_es
```

Cuando envias:

```yaml
action: notifier_hub.send
data:
  message: "Prueba de voz"
  google: true
```

Notifier Hub genera el audio con `google_tts_service` y lo reproduce en los `google_players` configurados.
Tambien puedes sobrescribirlo por mensaje:

```yaml
action: notifier_hub.send
data:
  message: "Prueba con otro TTS"
  google:
    media_player: media_player.google_home_salon
    tts_service: tts.google_es_es
```

El valor legacy `google_translate_say` sigue soportado si usas el servicio antiguo `tts.google_translate_say`.

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

### Llamadas VoIP/SIP y `sip_server_name`

Las llamadas telefónicas se envían mediante el add-on ha-sip de [`arnonym/ha-plugins`](https://github.com/arnonym/ha-plugins). La integración no realiza la llamada SIP directamente: envía el destino y el texto al add-on de Home Assistant con el servicio `hassio.addon_stdin`.

El add-on esperado es `ha-sip`, identificado internamente como:

```text
c7744bff_ha-sip
```

Notifier Hub construye una URI SIP con este formato:

```text
sip:<called_number>@<sip_server_name>
```

Por ejemplo, con:

```yaml
sip_server_name: fritz.box:5060
called_number: "600123456"
```

se enviaría al add-on:

```text
command: dial
number: sip:600123456@fritz.box:5060
menu:
  message: <mensaje>
  post_action: hangup
```

El valor por defecto `fritz.box:5060` está pensado para un router FRITZ!Box usando el puerto SIP estándar `5060`.

ha-sip como add-on requiere una instalación de Home Assistant con Supervisor y add-ons; en Home Assistant Core o Container sin Supervisor no estará disponible el servicio `hassio.addon_stdin`.

## Notas de migración

- Donde antes se usaba `script.my_notify`, ahora puede usarse `notifier_hub.send`.
- Donde antes se lanzaba `event: notifier`, puede mantenerse igual.
- Las entidades auxiliares existentes (`input_boolean`, `input_select`, etc.) ya no son obligatorias. Si quieres conservar lógica de no molestar, invitados o prioridad, indícalas en la configuración.
- La parte Google/Cast se ha añadido como gestor nativo. Usa `google: true` o un diccionario `google:` en el servicio/evento.
