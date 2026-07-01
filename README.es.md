# Notifier Hub para Home Assistant

[English](README.md) | [Espanol](README.es.md)

Integracion personalizada de Home Assistant para centralizar notificaciones de texto, avisos persistentes, Alexa, Google/Cast y llamadas telefonicas.

Es la conversion nativa de la aplicacion AppDaemon [`Centro Notifiche`](https://github.com/caiosweet/Package-Notification-HUB-AppDaemon) / [`Notifier`](https://github.com/jumping2000/notifier). Mantiene compatibilidad con el evento antiguo `notifier`, pero para automatizaciones nuevas se recomienda usar el servicio `notifier_hub.send`.

## Contenido

- [Funciones principales](#funciones-principales)
- [Instalacion](#instalacion)
- [Primeros pasos](#primeros-pasos)
- [Configuracion global](#configuracion-global)
- [Como se decide cada envio](#como-se-decide-cada-envio)
- [Referencia de `notifier_hub.send`](#referencia-de-notifier_hubsend)
- [Guias por canal](#guias-por-canal)
- [Ubicacion y presencia](#ubicacion-y-presencia)
- [Controles globales](#controles-globales)
- [Auto Volume](#auto-volume)
- [Dashboard](#dashboard)
- [Entidades creadas](#entidades-creadas)
- [Eventos de Home Assistant](#eventos-de-home-assistant)
- [Compatibilidad con AppDaemon](#compatibilidad-con-appdaemon)
- [Notas de migracion](#notas-de-migracion)

## Funciones principales

- Servicio `notifier_hub.send` para enviar mensajes desde automatizaciones, scripts o herramientas de desarrollador.
- Notificaciones persistentes en Home Assistant.
- Notificaciones mediante servicios `notify.*`: Telegram, `mobile_app`, Pushover, Discord y servicios genericos.
- Alexa Media Player: TTS, announce, push, reproduccion multimedia, volumen temporal y restauracion de volumen.
- Google/Cast: TTS mediante entidades o servicios `tts.*`, modo notify, reproduccion multimedia, volumen temporal y restauracion de volumen.
- Llamadas telefonicas mediante el add-on ha-sip.
- Filtro por ubicacion basado en entidades `person.*` o en un tracker compatible con instalaciones antiguas.
- Interruptores para activar o desactivar canales, modo no molestar, modo invitados y prioridad.
- Auto Volume con periodos del dia editables desde entidades `time.*` y `number.*`.
- DND nocturno opcional usando los horarios de `Noche` y `Altas horas` de Auto Volume.
- Avisos opcionales para eventos del ciclo de vida de Home Assistant.
- Compatibilidad con automatizaciones antiguas que usan `event: notifier`.

## Instalacion

### HACS

Puedes instalar Notifier Hub desde HACS como repositorio personalizado:

[![Abrir tu instancia de Home Assistant y abrir este repositorio en HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=rafaalbelda&repository=notifier_hub&category=integration)

1. Abre HACS en Home Assistant.
2. Pulsa los tres puntos de la esquina superior derecha y entra en **Repositorios personalizados**.
3. Añade `https://github.com/rafaalbelda/notifier_hub`.
4. Selecciona la categoria **Integracion**.
5. Instala **Notifier Hub** y reinicia Home Assistant.
6. Añade la integracion desde:

```text
Ajustes > Dispositivos y servicios > Añadir integracion > Notifier Hub
```

### Instalacion manual

Copia la carpeta:

```text
custom_components/notifier_hub
```

en:

```text
/config/custom_components/notifier_hub
```

Reinicia Home Assistant y añade la integracion desde:

```text
Ajustes > Dispositivos y servicios > Añadir integracion > Notifier Hub
```

Solo puede existir una instancia de Notifier Hub por instalacion de Home Assistant.

El formulario de configuracion esta organizado en estas secciones:

- Persons
- Notify Services
- Alexa
- Google
- Phone
- Notifications
- Auto Volume

## Primeros pasos

Notifier Hub se usa llamando al servicio `notifier_hub.send` desde una automatizacion, un script o:

```text
Herramientas para desarrolladores > Acciones
```

Antes de enviar mensajes, configura desde la UI los servicios `notify.*` y los reproductores Alexa o Google/Cast que quieras utilizar.

### Notificacion de texto

`notify: true` usa los servicios configurados globalmente en `notify_services`.

```yaml
action: notifier_hub.send
data:
  title: "Puerta"
  message: "Se ha abierto la puerta principal"
  notify: true
```

### Texto y Alexa

```yaml
action: notifier_hub.send
data:
  title: "Lavadora"
  message: "La lavadora ha terminado"
  notify: true
  alexa: true
```

### Google/Cast

```yaml
action: notifier_hub.send
data:
  message: "Hay alguien en la puerta"
  google: true
```

### Mensaje urgente

```yaml
action: notifier_hub.send
data:
  title: "Alarma"
  message: "Alarma activada"
  notify: true
  alexa: true
  priority: true
```

`priority: true` permite saltarse interruptores, filtro de ubicacion y modo no molestar. Consulta [Prioridad](#prioridad) antes de usarlo con llamadas telefonicas.

## Configuracion global

La configuracion recomendada se realiza desde la UI. Tambien puedes importar una configuracion inicial desde `configuration.yaml`:

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
  called_number: "600123456"
  default_language: es-ES
  default_volume: 0.30
  tts_wait_time: 3
  text_notifications: true
  screen_notifications: true
  speech_notifications: true
  speech_home_only: false
  alexa_notifications: true
  google_notifications: true
  phone_notifications: false
  ha_event_notifications: true
  ha_event_notify_services:
    - notify.mobile_app_mi_telefono
  auto_volume: true
  night_dnd: false
  auto_volume_exclude_players:
    - media_player.echo_dormitorio
  dnd_entity: switch.notifier_hub_dnd
  guest_mode_entity: switch.notifier_hub_guest_mode
  priority_message_entity: switch.notifier_hub_priority_message
  location_tracker: group.notifier_location_tracker
  install_dashboard: true
```

### Orden de precedencia

Notifier Hub combina valores globales, opciones runtime e informacion enviada con cada mensaje.

La configuracion efectiva se obtiene en este orden:

1. Valores por defecto internos de la integracion.
2. Configuracion inicial guardada al instalar la integracion o importada desde YAML.
3. Opciones runtime guardadas desde la UI y desde las entidades editables. Estas opciones sobreescriben la configuracion inicial.
4. Parametros enviados a `notifier_hub.send`. Cuando existe una opcion equivalente, el valor del mensaje sobreescribe el global solo para esa llamada.

El servicio `notifier_hub.set_config` permite cambiar temporalmente valores runtime sin reiniciar Home Assistant:

```yaml
action: notifier_hub.set_config
data:
  config:
    default_volume: 0.25
```

Estos cambios permanecen en memoria hasta que se recargue la configuracion o se reinicie la integracion.

### Valores globales usados como fallback

| Configuracion global | Parametro del mensaje con preferencia | Comportamiento |
|---|---|---|
| `notify_services` | `notify` | Con `notify: true`, se usan los servicios globales. Un servicio o lista en `notify` sustituye la lista global para ese mensaje. |
| `alexa_players` | `alexa.media_player` | Si el mensaje no indica reproductores Alexa, se usan los globales. |
| `google_players` | `google.media_player` o `google.player` | Si el mensaje no indica reproductores Google/Cast, se usan los globales. |
| `default_volume` | `alexa.volume` o `google.volume` | Se usa si no hay volumen explicito y `auto_volume` esta desactivado. |
| Volumen del periodo de `auto_volume` | `alexa.volume` o `google.volume` | Con `auto_volume` activo, sustituye a `default_volume`. Un volumen explicito tiene prioridad sobre ambos. |
| `tts_wait_time` | `alexa.wait_time` o `google.wait_time` | El valor del mensaje sustituye el margen global usado antes de restaurar el volumen. |
| `default_language` | `alexa.language` o `google.language` | El idioma del mensaje sustituye al global. |
| `google_tts_service` | `google.tts_service`, `google.service`, `google.tts_entity` o `google.engine_id` | El motor indicado en el mensaje sustituye al global. |
| `google_notify_service` | `google.notify_service` | El servicio del mensaje sustituye al global en modo Google Assistant o notify. |
| `called_number` | `called_number` | El numero del mensaje sustituye al global para esa llamada. |
| `persons` | `location` | `location` indica el estado requerido. Si `persons` esta vacio, se usa `location_tracker` como fallback. |

`sip_server_name` solo se configura globalmente: no se puede sobrescribir por mensaje.

Si `speech_home_only` esta activo, los mensajes de voz sin `location` explicito se comportan como si incluyeran `location: home`. Un valor `location` enviado con el mensaje tiene prioridad.

## Como se decide cada envio

Los interruptores globales no son simples valores por defecto. Actuan como permisos para cada canal.

| Canal | Debe estar activado | Parametro del mensaje | Filtrado por `location` | Bloqueado por DND |
|---|---|---|---|---|
| Texto `notify.*` | `text_notifications` | `notify` | Si | No |
| Persistente de Home Assistant | `screen_notifications` | Se crea salvo que uses `no_show: true` | No | No |
| Alexa | `speech_notifications` y `alexa_notifications` | `alexa` | Si | Si |
| Google/Cast | `speech_notifications` y `google_notifications` | `google` | Si | Si |
| Telefono | `phone_notifications` | `phone` | No | Si |

Para los canales solicitables, el global indica que el canal puede usarse y el mensaje indica que quieres usarlo en esa llamada. Por ejemplo, Alexa solo se usa cuando `alexa_notifications` esta activo y el mensaje incluye `alexa: true` o un diccionario `alexa:`.

| Global del canal | Valor en el mensaje | Resultado normal |
|---|---|---|
| `true` | `true` o diccionario activo | Se usa el canal |
| `true` | `false` o ausente | No se usa el canal |
| `false` | `true` o diccionario activo | No se usa el canal |
| `false` | `false` o ausente | No se usa el canal |

La prioridad puede saltar bloqueos globales, `location` y DND, pero no convierte un selector de canal desactivado en activo. Consulta [Prioridad](#prioridad) para las excepciones exactas.

Ejemplo: este mensaje usa los servicios notify globales, limita Alexa a un reproductor concreto y sustituye temporalmente el volumen global o automatico:

```yaml
action: notifier_hub.send
data:
  title: "Puerta"
  message: "Se ha abierto la puerta principal"
  location: home
  notify: true
  alexa:
    media_player: media_player.echo_salon
    volume: 0.45
```

Alexa solo habla si los interruptores de voz y Alexa estan activados, no hay DND y la ubicacion coincide, salvo que se active alguna excepcion de prioridad o modo invitados.

### Voz solo si hay alguien en casa

Activa `speech_home_only` o el switch:

```text
switch.notifier_hub_speech_home_only
```

Cuando esta activo, Alexa y Google/Cast asumen `location: home` si una accion no incluye `location`. De este modo puedes silenciar globalmente la voz cuando no hay nadie en casa sin repetir `location: home` en cada automatizacion.

Un `location` explicito en el mensaje tiene prioridad. Por ejemplo, `location: oficina` sigue comprobando `oficina`.

Este filtro solo afecta a voz. No filtra notificaciones de texto, persistentes ni llamadas telefonicas.

### No molestar

La entidad configurada en `dnd_entity` bloquea Alexa, Google/Cast y telefono cuando esta en `on`.

Por defecto se usa:

```yaml
dnd_entity: switch.notifier_hub_dnd
```

Tambien puedes activar DND automaticamente durante los periodos `Noche` y `Altas horas` de Auto Volume con:

```yaml
night_dnd: true
```

o desde la entidad:

```text
switch.notifier_hub_night_dnd
```

Cuando esta activo, Notifier Hub aplica DND mientras `sensor.notifier_hub_day_period` corresponde a los periodos `Noche` o `Altas horas`. El inicio se configura con `time.notifier_hub_noche_start` y `time.notifier_hub_altas_horas_start`; termina cuando comienza el siguiente periodo de Auto Volume. El switch manual `switch.notifier_hub_dnd` sigue funcionando de forma independiente.

Las notificaciones de texto y las persistentes siguen funcionando.

### Modo invitados

La entidad configurada en `guest_mode_entity` permite que Alexa y Google/Cast hablen aunque `location` no coincida.

Por defecto se usa:

```yaml
guest_mode_entity: switch.notifier_hub_guest_mode
```

Es util cuando hay invitados en casa. No salta el modo no molestar y no afecta a las llamadas telefonicas.

### Prioridad

La prioridad general puede activarse con `priority: true` en el mensaje o encendiendo la entidad configurada en `priority_message_entity`:

```yaml
priority_message_entity: switch.notifier_hub_priority_message
```

`switch.notifier_hub_priority_message` se apaga automaticamente despues de procesar el siguiente mensaje.

Reglas especiales:

- La prioridad general salta interruptores, `location` y DND.
- Tambien fuerza la notificacion persistente aunque exista `no_show: true`.
- Para texto, Alexa y Google/Cast, la prioridad general no sustituye el selector del canal: `notify: false`, `alexa: false` o `google: false` siguen evitando ese envio.
- Para telefono, la prioridad general intenta realizar la llamada aunque `phone` sea `false`. Si existe un numero global y no quieres llamadas prioritarias, evita usar prioridad general o elimina el numero global.
- `alexa.priority: true` y `google.priority: true` saltan los bloqueos solo para ese canal de voz.

## Referencia de `notifier_hub.send`

### Parametros generales

| Campo | Tipo | Valor por defecto | Descripcion |
|---|---|---|---|
| `message` | cadena | Obligatorio | Texto principal del mensaje. |
| `title` | cadena | `""` | Titulo de la notificacion. |
| `notify` | booleano, cadena o lista | `true` | Envia texto mediante `notify.*`. Con `true` usa `notify_services`. Tambien admite un servicio, una lista o una cadena separada por comas. |
| `no_show` | booleano | `false` | Con `true`, evita crear la notificacion persistente. |
| `priority` | booleano | `false` | Activa prioridad general. |
| `location` | cadena | `""` | Estado requerido para los canales sujetos a ubicacion. Un valor vacio no aplica filtro. |
| `alexa` | booleano o diccionario | `false` | Solicita Alexa para este mensaje. Requiere `speech_notifications` y `alexa_notifications` activos, salvo prioridad. Un diccionario permite personalizar el envio. |
| `google` | booleano o diccionario | `false` | Solicita Google/Cast para este mensaje. Requiere `speech_notifications` y `google_notifications` activos, salvo prioridad. Un diccionario permite personalizar el envio. |
| `phone` | booleano | `false` | Solicita una llamada mediante ha-sip. El canal debe estar activado o el mensaje debe ser prioritario. |
| `called_number` | cadena | Configuracion global | Numero al que llama ha-sip. Permite sobrescribir el numero global. |
| `image` | cadena | `""` | Imagen para Telegram, Pushover, Discord o `mobile_app`. Puede ser una ruta local o una URL, segun el servicio. |
| `caption` | cadena | `""` | Pie de foto para Telegram. Si esta vacio, se genera con el titulo y el mensaje. |
| `link` | cadena | `""` | Enlace añadido al texto. En Discord con `embed` se usa como URL del contenido embebido. En la UI aparece como **Enlace**. |
| `target` | cadena o lista | `""` | Destinatario concreto pasado a `notify.*`, por ejemplo uno o varios chats de Telegram. |
| `html` | booleano | `false` | Activa formato HTML para Telegram y genera el titulo en negrita. |

### Payloads especificos para `notify.*`

Los siguientes campos permiten añadir opciones propias de cada proveedor:

| Campo | Tipo | Descripcion |
|---|---|---|
| `telegram` | diccionario | Payload adicional para Telegram. Con `html: true` añade `parse_mode: html`. |
| `pushover` | diccionario | Payload adicional para Pushover. Recibe automaticamente `image` y `priority` cuando se indican. |
| `mobile` | diccionario | Payload adicional para `notify.mobile_app_*`. Con `tts: true`, envia el texto mediante `tts_text`. |
| `discord` | diccionario | Payload adicional para Discord. Si incluye la clave `embed`, utiliza `title`, `description`, `link` e `image` para crear contenido embebido. |

### Opciones de `alexa`

Cuando `alexa` es un diccionario admite:

| Campo | Valor por defecto | Descripcion |
|---|---|---|
| `media_player` | `alexa_players` | Reproductor, lista, grupo, nombre amigable o `all`. |
| `message` | `message` general | Texto que se debe reproducir. |
| `message_tts` | `message` de Alexa | Texto TTS alternativo con prioridad sobre `message`. |
| `title` | `title` general | Titulo usado para push. |
| `volume` | Volumen actual de Notifier Hub | Volumen temporal entre `0.0` y `1.0`. |
| `wait_time` | `tts_wait_time` | Margen adicional antes de restaurar el volumen. |
| `type` | `tts` | Admite `tts`, `announce`, `push`, `dropin` o `dropin_notification`. |
| `method` | `all` | Metodo usado con `type: announce`. |
| `push` | `false` | Fuerza una notificacion push. |
| `priority` | `false` | Salta los bloqueos solo para Alexa. |
| `notifier` | `notify.alexa_media` | Servicio notify alternativo de Alexa Media Player. |
| `ssml` | `false` | Activa la generacion de etiquetas SSML. |
| `voice` | `Alexa` | Voz SSML alternativa. |
| `language` | `default_language` | Idioma SSML. |
| `audio` | `""` | URL o etiqueta `<audio>` SSML insertada antes del mensaje. |
| `rate` | `100` | Velocidad SSML en porcentaje. |
| `pitch` | `0` | Tono SSML en porcentaje. |
| `ssml_volume` | `0` | Ajuste de volumen SSML en dB. |
| `whisper` | `false` | Activa el modo susurro SSML. |
| `media_content_id` | `""` | URL o identificador multimedia reproducido en lugar del TTS. |
| `media_content_type` | Sin valor fijo | Tipo del contenido multimedia. |
| `extra` | `0` | Valor `timer` enviado al reproducir contenido multimedia. |
| `auto_volumes` | `false` | Ajusta el volumen sin reproducir TTS. |

### Opciones de `google`

Cuando `google` es un diccionario admite:

| Campo | Valor por defecto | Descripcion |
|---|---|---|
| `media_player` | `google_players` | Reproductor, lista, grupo o nombre amigable. Tambien admite el alias `player`. |
| `message` | `message` general | Texto que se debe reproducir. |
| `volume` | Volumen actual de Notifier Hub | Volumen temporal entre `0.0` y `1.0`. |
| `wait_time` | `tts_wait_time` | Margen adicional antes de restaurar el volumen. |
| `language` | `default_language` | Idioma del motor TTS. |
| `tts_service` | `google_tts_service` | Entidad moderna `tts.*` o servicio heredado. Tambien admite el alias `service`. |
| `tts_entity` | `""` | Entidad moderna `tts.*` explicita. Tambien admite el alias `engine_id`. |
| `mode` | `tts` | Usa `tts`, `notify`, `assistant` o `google assistant`. Tambien admite el alias `type`. |
| `notify_service` | `google_notify_service` | Servicio usado en modo Google Assistant o notify. |
| `priority` | `false` | Salta los bloqueos solo para Google/Cast. |
| `media_content_id` | `""` | URL o identificador multimedia reproducido en lugar del TTS. |
| `media_content_type` | `music` | Tipo del contenido multimedia. |

## Guias por canal

### Notificaciones de texto

`notify: true` envia el mensaje a todos los servicios configurados en `notify_services`.
Tambien puedes indicar servicios concretos:

```yaml
action: notifier_hub.send
data:
  title: "Aviso"
  message: "Mensaje de prueba"
  notify:
    - notify.telegram
    - notify.mobile_app_mi_telefono
```

### Telegram con HTML, enlace y destinatario

```yaml
action: notifier_hub.send
data:
  title: "Camara"
  message: "Se ha detectado <b>movimiento</b>"
  notify: notify.telegram
  target:
    - "123456789"
  link: "https://example.com/camara"
  html: true
```

### Telegram con imagen

```yaml
action: notifier_hub.send
data:
  title: "Camara"
  message: "Movimiento detectado"
  notify: notify.telegram
  image: /config/www/camara.jpg
  caption: "Movimiento detectado"
```

### Alexa

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

### Google/Cast

Para instalaciones recientes se recomienda usar la entidad `tts.*` creada por Google Translate, por ejemplo `tts.google_es_es`.

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

`google_tts_service` define el motor TTS global:

```yaml
google_tts_service: tts.google_es_es
```

Cuando envias `google: true`, Notifier Hub genera el audio con ese motor y lo reproduce en `google_players`.
Tambien puedes sobrescribirlo por mensaje con `google.tts_service`.

El valor legacy `google_translate_say` sigue soportado si usas el servicio heredado `tts.google_translate_say`. Si existe una entidad moderna, Notifier Hub intenta utilizarla automaticamente.

Tambien puedes reproducir contenido multimedia:

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

### Llamadas telefonicas

```yaml
action: notifier_hub.send
data:
  title: "Alerta"
  message: "Alarma activada"
  phone: true
  called_number: "+34600000000"
```

Las llamadas se envian mediante el add-on ha-sip de [`arnonym/ha-plugins`](https://github.com/arnonym/ha-plugins). La integracion no realiza la llamada directamente: envia el destino y el texto al add-on con `hassio.addon_stdin`.

El add-on esperado es `ha-sip`, identificado internamente como:

```text
c7744bff_ha-sip
```

Notifier Hub construye una URI SIP con este formato:

```text
sip:<called_number>@<sip_server_name>
```

Por ejemplo:

```yaml
sip_server_name: fritz.box:5060
called_number: "600123456"
```

genera:

```text
command: dial
number: sip:600123456@fritz.box:5060
menu:
  message: <mensaje>
  post_action: hangup
```

El valor por defecto `fritz.box:5060` esta pensado para un router FRITZ!Box con el puerto SIP estandar `5060`.

ha-sip requiere una instalacion de Home Assistant con Supervisor y add-ons. En Home Assistant Core o Container sin Supervisor no existe `hassio.addon_stdin`.

## Ubicacion y presencia

`location` permite filtrar texto, Alexa y Google/Cast segun la ubicacion. No filtra las notificaciones persistentes ni las llamadas telefonicas.

La configuracion recomendada es usar `persons`:

```yaml
persons:
  - person.ana
  - person.carlos
```

Con `location: home`, el mensaje pasa si al menos una persona configurada esta en `home`:

```yaml
action: notifier_hub.send
data:
  title: "Aviso casa"
  message: "Movimiento detectado"
  location: home
  alexa: true
```

Si `persons` esta vacio, Notifier Hub usa `location_tracker` como fallback:

```yaml
location_tracker: group.notifier_location_tracker
```

En ese caso compara `location` con el estado de la entidad configurada. Si el mensaje no incluye `location`, no aplica ningun filtro.

Entidades agregadas de presencia:

| Entidad | Estado | Atributos utiles |
|---|---|---|
| `sensor.notifier_hub_home_people` | Numero de personas configuradas que estan en `home` | `total_count`, `away_count`, `is_home`, `home_persons`, `home_person_names`, `home_person_details`, `away_persons`, `away_person_names`, `away_person_details`, `persons` |
| `binary_sensor.notifier_hub_home_occupied` | `on` si al menos una persona esta en `home` | `home_count`, `total_count`, `home_persons`, `home_person_names`, `home_person_details`, `away_persons`, `away_person_names`, `away_person_details` |

Para mostrar personas en un mapa, usa las entidades `person.*` originales. Las entidades agregadas resumen presencia, pero no representan una posicion unica.

## Controles globales

Notifier Hub crea interruptores que puedes usar desde la UI, el dashboard o automatizaciones:

| Entidad | Configuracion | Uso |
|---|---|---|
| `switch.notifier_hub_text_notifications` | `text_notifications` | Notificaciones mediante `notify.*`. |
| `switch.notifier_hub_screen_notifications` | `screen_notifications` | Notificaciones persistentes. |
| `switch.notifier_hub_speech_notifications` | `speech_notifications` | Interruptor maestro de voz. |
| `switch.notifier_hub_speech_home_only` | `speech_home_only` | Si una accion no incluye `location`, permite voz solo cuando alguien esta en `home`. |
| `switch.notifier_hub_alexa_notifications` | `alexa_notifications` | Alexa TTS, announce y push. |
| `switch.notifier_hub_google_notifications` | `google_notifications` | Google/Cast TTS o notify. |
| `switch.notifier_hub_phone_notifications` | `phone_notifications` | Llamadas telefonicas. |
| `switch.notifier_hub_home_assistant_event_notifications` | `ha_event_notifications` | Avisos del ciclo de vida de Home Assistant. |
| `switch.notifier_hub_auto_volume` | `auto_volume` | Volumen automatico segun periodo del dia. |
| `switch.notifier_hub_dnd` | `dnd_mode` | Modo no molestar. |
| `switch.notifier_hub_night_dnd` | `night_dnd` | Aplica DND automaticamente durante los periodos `Noche` y `Altas horas` de Auto Volume. |
| `switch.notifier_hub_guest_mode` | `guest_mode` | Permite voz cuando `location` no coincide. |
| `switch.notifier_hub_priority_message` | `priority_message` | Fuerza prioridad para el siguiente mensaje. |

## Auto Volume

Auto Volume ajusta los reproductores Alexa y Google configurados segun el periodo del dia.

Cuando `auto_volume` esta activo:

- Los mensajes Alexa y Google sin `volume` explicito usan el volumen del periodo actual.
- Un `volume` explicito en el mensaje tiene prioridad.
- La integracion actualiza periodicamente el volumen de los reproductores configurados.
- `auto_volume_exclude_players` permite excluir reproductores concretos.
- `night_dnd` permite reutilizar los periodos `Noche` y `Altas horas` para activar automaticamente DND.

Periodos por defecto:

| Periodo | Inicio | Volumen |
|---|---:|---:|
| Altas horas | `01:00` | `10%` |
| Primera hora | `05:00` | `20%` |
| Mañana | `07:00` | `30%` |
| Tarde | `12:00` | `40%` |
| Atardecer | `18:00` | `30%` |
| Noche | `22:00` | `20%` |

El dashboard incluye:

- `sensor.notifier_hub_day_period`
- `sensor.notifier_hub_day_period_volume`
- Entidades `time.notifier_hub_*_start` para editar el inicio de cada periodo.
- Entidades `number.notifier_hub_*_volume` para editar el volumen de cada periodo.

Si `switch.notifier_hub_night_dnd` esta activo, los periodos `Noche` y `Altas horas` tambien se usan como ventana de no molestar para voz y telefono.

## Dashboard

El archivo `notifier_hub_dashboard.yaml` incluye un panel Lovelace con estado, actividad TTS, botones de prueba, canales y controles de Auto Volume.

La opcion `install_dashboard` copia automaticamente el panel a:

```text
/config/notifier_hub_dashboard.yaml
```

Tambien crea una notificacion persistente con el bloque que debes añadir a `configuration.yaml`:

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

Si no usas `install_dashboard`, puedes copiar manualmente `notifier_hub_dashboard.yaml` a `/config/notifier_hub_dashboard.yaml` y registrar el mismo bloque.

Tambien se incluye una tarjeta compacta de ejemplo en:

```text
samples/notifier_hub_compact_card.yaml
```

Esa tarjeta esta pensada para pegarla dentro de `cards:` en una vista Lovelace existente. Usa las mismas entidades de Notifier Hub y muestra controles rapidos, Auto Volume, DND manual, DND durante la noche, estado de Alexa/Google y envio de mensajes desde el dashboard.

## Entidades creadas

### Sensores

| Entidad | Uso |
|---|---|
| `sensor.notifier_hub_debug` | Estado de depuracion y detalles de errores. |
| `sensor.notifier_hub_last_message` | Ultimo mensaje procesado. |
| `sensor.notifier_hub_personal_assistant` | Nombre configurado del asistente. |
| `sensor.notifier_hub_home_people` | Numero y detalles de personas en casa. |
| `sensor.notifier_hub_day_period` | Periodo actual de Auto Volume. |
| `sensor.notifier_hub_day_period_volume` | Volumen correspondiente al periodo actual. |

### Sensores binarios

| Entidad | Uso |
|---|---|
| `binary_sensor.notifier_hub_alexa_speak` | Indica si Alexa esta procesando voz. |
| `binary_sensor.notifier_hub_google_speak` | Indica si Google/Cast esta procesando voz. |
| `binary_sensor.notifier_hub_home_occupied` | Indica si al menos una persona configurada esta en casa. |

Las entidades `time.notifier_hub_*_start` y `number.notifier_hub_*_volume` permiten editar Auto Volume.
Consulta [Controles globales](#controles-globales) para ver los interruptores.

## Eventos de Home Assistant

Notifier Hub puede avisar de los eventos equivalentes a `Start`, `Final Write`, `Close`, `Stop` y `Restart` de la aplicacion original:

- `homeassistant_started`
- `homeassistant_final_write`
- `homeassistant_close`
- `homeassistant_stop`
- Llamada al servicio `homeassistant.restart`

Activalos o desactivalos con `ha_event_notifications` o `switch.notifier_hub_home_assistant_event_notifications`.

Por defecto usa `notify_services`. Para separar los avisos internos de los mensajes normales, configura `ha_event_notify_services`:

```yaml
notify_services:
  - notify.telegram
  - notify.mobile_app_mi_telefono

ha_event_notify_services:
  - notify.mobile_app_mi_telefono
```

Si `ha_event_notify_services` esta vacio, se usa `notify_services` como fallback.

## Compatibilidad con AppDaemon

Notifier Hub escucha el evento personalizado `notifier` para mantener compatibilidad con automatizaciones antiguas creadas para la aplicacion original de AppDaemon.

Los datos de `event_data` se procesan igual que los datos enviados mediante `notifier_hub.send`:

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

Para automatizaciones nuevas usa directamente:

```yaml
action: notifier_hub.send
data:
  title: "Lavadora"
  message: "La lavadora ha terminado"
  notify: true
```

## Notas de migracion

- Donde antes se usaba `script.my_notify`, ahora puede usarse `notifier_hub.send`.
- Donde antes se lanzaba `event: notifier`, puede mantenerse igual durante la migracion.
- Las entidades auxiliares antiguas (`input_boolean`, `input_select`, etc.) ya no son obligatorias.
- Si quieres conservar entidades propias para no molestar, invitados o prioridad, puedes indicarlas con `dnd_entity`, `guest_mode_entity` y `priority_message_entity`.
- Google/Cast se ha añadido como gestor nativo. Usa `google: true` o un diccionario `google:`.

## Cambios respecto a AppDaemon

Se han eliminado:

- La descarga automatica del paquete desde GitHub.
- La gestion de grupos creada por AppDaemon.
