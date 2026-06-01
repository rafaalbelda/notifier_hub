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
  - `sensor.notifier_hub_personal_assistant`
  - `sensor.notifier_hub_home_people`
  - `binary_sensor.notifier_hub_alexa_speak`
  - `binary_sensor.notifier_hub_google_speak`
  - `binary_sensor.notifier_hub_home_occupied`
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

## Uso rapido

Notifier Hub se utiliza llamando al servicio `notifier_hub.send` desde una automatizacion, un script o desde:

```text
Herramientas para desarrolladores > Acciones
```

Antes de enviar mensajes, configura desde la UI los servicios `notify.*` y los reproductores Alexa o Google/Cast que quieras utilizar.

Ejemplo basico para enviar una notificacion de texto a los servicios configurados:

```yaml
action: notifier_hub.send
data:
  title: "Puerta"
  message: "Se ha abierto la puerta principal"
  notify: true
```

Para enviar tambien el mensaje por Alexa:

```yaml
action: notifier_hub.send
data:
  title: "Lavadora"
  message: "La lavadora ha terminado"
  notify: true
  alexa: true
```

Para utilizar Google/Cast:

```yaml
action: notifier_hub.send
data:
  message: "Hay alguien en la puerta"
  google: true
```

Los mensajes urgentes pueden saltarse los interruptores de canales, el filtro de ubicacion y el modo no molestar:

```yaml
action: notifier_hub.send
data:
  title: "Alarma"
  message: "Alarma activada"
  notify: true
  alexa: true
  priority: true
```

La integracion crea interruptores como `switch.notifier_hub_text_notifications`, `switch.notifier_hub_speech_notifications`, `switch.notifier_hub_alexa_notifications`, `switch.notifier_hub_google_notifications` y `switch.notifier_hub_dnd`. Puedes controlarlos desde el dashboard incluido o desde automatizaciones.

Consulta las secciones siguientes para configurar ubicacion, volumen automatico, llamadas telefonicas y opciones especificas de Alexa o Google/Cast.

El formulario de configuración de la UI está organizado en secciones:

- Persons
- Notify Services
- Alexa
- Google
- Phone
- Notifications
- Auto Volume

En la Configuración puedes activar `install_dashboard`.
Si esta opcion esta activada, la integracion copia automaticamente el dashboard a:

```text
/config/notifier_hub_dashboard.yaml
```

Tambien crea una notificacion persistente con el bloque `lovelace:` que debes anadir a `configuration.yaml` para mostrarlo en la barra lateral.

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

## Ubicacion

`persons` se puede configurar desde la UI con un selector de entidades `person.*`.
Cuando hay personas configuradas, Notifier Hub las usa para comprobar la ubicación de los mensajes con `location`.
Si `persons` está vacío, se mantiene la compatibilidad con `location_tracker`.

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

Notifier Hub tambien crea entidades agregadas de presencia:

| Entidad | Estado | Atributos utiles |
|---|---|---|
| `sensor.notifier_hub_home_people` | Numero de personas configuradas que estan en `home` | `total_count`, `away_count`, `is_home`, `home_persons`, `home_person_names`, `home_person_details`, `away_persons`, `away_person_names`, `away_person_details`, `persons` |
| `binary_sensor.notifier_hub_home_occupied` | `on` si hay al menos una persona en `home` | `home_count`, `total_count`, `home_persons`, `home_person_names`, `home_person_details`, `away_persons`, `away_person_names`, `away_person_details` |

Para mostrar personas en el mapa, usa las entidades `person.*` originales en una tarjeta `map`.
Las entidades agregadas de Notifier Hub resumen la presencia, pero no representan una posicion unica.

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

`notify_services` se usa para las notificaciones normales cuando un mensaje llega con `notify: true`.
`ha_event_notify_services` se usa solo para los avisos internos de Home Assistant (`Start`, `Stop`, `Final Write`, `Close` y `Restart`).
Esto permite enviar los eventos del sistema a un canal distinto, por ejemplo solo al movil:

```yaml
notify_services:
  - notify.telegram
  - notify.mobile_app_mi_telefono

ha_event_notify_services:
  - notify.mobile_app_mi_telefono
```

Si `ha_event_notify_services` esta vacio, Notifier Hub usa `notify_services` como fallback.

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

## Referencia de `notifier_hub.send`

### Configuracion global y precedencia

Notifier Hub combina configuracion global, interruptores runtime y parametros de cada llamada a `notifier_hub.send`.
No todos los parametros se comportan igual: algunos valores del mensaje sustituyen un valor global, mientras que los interruptores y filtros deciden si un canal puede ejecutarse.

La configuracion efectiva se obtiene en este orden:

1. Valores por defecto internos de la integracion.
2. Configuracion inicial guardada al instalar la integracion o importada desde YAML.
3. Opciones runtime guardadas desde la UI y desde las entidades editables. Estas opciones sobreescriben la configuracion inicial.
4. Parametros enviados a `notifier_hub.send`. Cuando existe una opcion equivalente, el valor del mensaje sobreescribe el valor global solo para esa llamada.

El servicio `notifier_hub.set_config` permite cambiar temporalmente valores runtime sin reiniciar Home Assistant.
Estos cambios permanecen en memoria hasta que se recargue la configuracion o se reinicie la integracion.

#### Valores globales usados como fallback

| Configuracion global | Parametro de `notifier_hub.send` que tiene preferencia | Comportamiento |
|---|---|---|
| `notify_services` | `notify` | Con `notify: true`, se usan los servicios globales. Si `notify` contiene un servicio o una lista, sustituye la lista global para ese mensaje. |
| `alexa_players` | `alexa.media_player` | Si el mensaje no indica reproductores Alexa, se usan los globales. |
| `google_players` | `google.media_player` o `google.player` | Si el mensaje no indica reproductores Google/Cast, se usan los globales. |
| `default_volume` | `alexa.volume` o `google.volume` | Se usa cuando no hay volumen explicito y `auto_volume` esta desactivado. |
| Volumen del periodo de `auto_volume` | `alexa.volume` o `google.volume` | Cuando `auto_volume` esta activo, sustituye a `default_volume`. Un volumen explicito en el mensaje tiene prioridad sobre ambos. |
| `tts_wait_time` | `alexa.wait_time` o `google.wait_time` | El margen indicado en el mensaje sustituye al global para calcular la espera antes de restaurar el volumen. |
| `default_language` | `alexa.language` o `google.language` | El idioma indicado en el mensaje sustituye al global. |
| `google_tts_service` | `google.tts_service`, `google.service`, `google.tts_entity` o `google.engine_id` | El motor indicado en el mensaje sustituye al global. `tts_entity` o `engine_id` fuerza una entidad `tts.*` concreta. |
| `google_notify_service` | `google.notify_service` | El servicio indicado en el mensaje sustituye al global cuando se usa modo Google Assistant o notify. |
| `called_number` | `called_number` | El numero indicado en el mensaje sustituye al global para esa llamada. |
| `persons` | `location` | `location` no sustituye la lista de personas: indica el estado que debe cumplir al menos una persona configurada. Si `persons` esta vacio, se usa `location_tracker` como fallback. |

`sip_server_name` no se puede sobrescribir por mensaje: siempre se utiliza el valor global.

#### Interruptores, filtros y excepciones

Los interruptores globales no son valores por defecto. Actuan como permisos para cada canal:

| Canal | Debe estar activado | Parametro del mensaje | Filtro de `location` | Bloqueado por DND |
|---|---|---|---|---|
| Texto `notify.*` | `text_notifications` | `notify` | Si | No |
| Persistente de Home Assistant | `screen_notifications` | Se crea salvo que uses `no_show: true` | No | No |
| Alexa | `speech_notifications` y `alexa_notifications` | `alexa` | Si | Si |
| Google/Cast | `speech_notifications` y `google_notifications` | `google` | Si | Si |
| Telefono | `phone_notifications` | `phone` | No | Si |

Reglas especiales:

- `priority: true` en el nivel general salta los interruptores de canales, `location` y DND para ese mensaje. Tambien fuerza la notificacion persistente aunque exista `no_show: true`.
- Para texto, Alexa y Google/Cast, la prioridad general no sustituye el selector del canal: `notify: false`, `alexa: false` o `google: false` siguen evitando ese envio.
- Para telefono, la prioridad general intenta realizar la llamada aunque `phone` sea `false`. Si hay un numero configurado y no quieres llamadas prioritarias, evita usar prioridad general o elimina el numero de telefono global.
- `switch.notifier_hub_priority_message` equivale a `priority: true` para el siguiente mensaje y se apaga automaticamente despues de procesarlo.
- `alexa.priority: true` o `google.priority: true` saltan los bloqueos solo para ese canal de voz.
- `switch.notifier_hub_guest_mode` permite Alexa y Google/Cast aunque no coincida `location`, pero no salta DND.
- `no_show: true` solo evita la notificacion persistente. No desactiva `notify.*`, Alexa, Google/Cast ni telefono.
- `notify: false`, `alexa: false`, `google: false` y `phone: false` desactivan sus respectivos canales para un mensaje normal.

Ejemplo: este mensaje usa los servicios notify globales, limita Alexa a un reproductor concreto y sustituye temporalmente el volumen automatico o global:

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

En este ejemplo, Alexa solo habla si los interruptores de voz y Alexa estan activados, no hay DND y la ubicacion coincide, salvo que se active alguna excepcion de prioridad o modo invitados.

### Parametros generales

El servicio acepta los siguientes campos generales:

| Campo | Tipo | Valor por defecto | Descripcion |
|---|---|---|---|
| `message` | cadena | Obligatorio | Texto principal del mensaje. |
| `title` | cadena | `""` | Titulo de la notificacion. |
| `notify` | booleano, cadena o lista | `true` | Envia una notificacion de texto. Con `true` usa `notify_services`. Tambien puedes indicar un servicio, por ejemplo `notify.telegram`, una lista o una cadena separada por comas. |
| `no_show` | booleano | `false` | Con `true`, evita crear la notificacion persistente en Home Assistant. |
| `priority` | booleano | `false` | Permite saltarse interruptores de canales, filtro de ubicacion y modo no molestar. |
| `location` | cadena | `""` | Solo envia los canales sujetos a ubicacion cuando coincide con alguna entidad de `persons` o con `location_tracker`. Un valor vacio no aplica filtro. |
| `alexa` | booleano o diccionario | `false` | Con `true`, envia el texto a los reproductores Alexa configurados. Usa un diccionario para personalizar el mensaje. |
| `google` | booleano o diccionario | `false` | Con `true`, envia el texto a los reproductores Google/Cast configurados. Usa un diccionario para personalizar el mensaje. |
| `phone` | booleano | `false` | Solicita una llamada telefonica mediante ha-sip. El canal debe estar activado o el mensaje debe ser prioritario. |
| `called_number` | cadena | Configuracion de la integracion | Numero de telefono al que llama ha-sip. Permite sobrescribir el numero configurado. |
| `image` | cadena | `""` | Imagen para Telegram, Pushover, Discord o `mobile_app`. Puede ser una ruta local o una URL, segun el servicio. |
| `caption` | cadena | `""` | Pie de foto para Telegram. Si esta vacio, se genera a partir del titulo y el mensaje. |
| `link` | cadena | `""` | Enlace añadido al texto. En Discord con `embed` se utiliza como URL del contenido embebido. En la UI aparece como **Enlace**. |
| `target` | cadena o lista | `""` | Destinatario concreto pasado al servicio `notify.*`, por ejemplo uno o varios identificadores de chat de Telegram. |
| `html` | booleano | `false` | Activa formato HTML para Telegram y genera el titulo en negrita. |

Los campos `telegram`, `pushover`, `mobile` y `discord` permiten añadir opciones especificas dentro de `data` para los servicios `notify.*` correspondientes:

| Campo | Tipo | Descripcion |
|---|---|---|
| `telegram` | diccionario | Payload adicional para Telegram. Con `html: true` añade `parse_mode: html`. |
| `pushover` | diccionario | Payload adicional para Pushover. Admite las opciones propias del servicio y recibe automaticamente `image` y `priority` cuando se indican. |
| `mobile` | diccionario | Payload adicional para `notify.mobile_app_*`. Con `tts: true`, envia el texto como TTS mediante `tts_text`. |
| `discord` | diccionario | Payload adicional para Discord. Cuando incluye la clave `embed`, utiliza `title`, `description`, `link` e `image` para crear el contenido embebido. |

Ejemplo de notificacion a un chat concreto de Telegram con HTML y enlace:

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

### Opciones de `alexa`

Cuando `alexa` es un diccionario admite estas opciones:

| Campo | Valor por defecto | Descripcion |
|---|---|---|
| `media_player` | `alexa_players` | Reproductor, lista, grupo, nombre amigable o `all`. |
| `message` | `message` general | Texto que se debe reproducir. |
| `message_tts` | `message` de Alexa | Texto TTS alternativo con prioridad sobre `message`. |
| `title` | `title` general | Titulo usado para notificaciones push. |
| `volume` | Volumen actual de Notifier Hub | Volumen temporal entre `0.0` y `1.0`. |
| `wait_time` | `tts_wait_time` | Margen adicional usado para calcular cuanto esperar antes de restaurar el volumen. |
| `type` | `tts` | Tipo de envio. Admite `tts`, `announce`, `push`, `dropin` o `dropin_notification`. |
| `method` | `all` | Metodo usado cuando `type` es `announce`. |
| `push` | `false` | Fuerza una notificacion push. |
| `priority` | `false` | Permite que este mensaje Alexa salte los bloqueos normales del canal. |
| `notifier` | `notify.alexa_media` | Servicio notify alternativo para Alexa Media Player. |
| `ssml` | `false` | Activa la generacion de etiquetas SSML. |
| `voice` | `Alexa` | Voz SSML alternativa. |
| `language` | `default_language` | Idioma usado para SSML. |
| `audio` | `""` | URL o etiqueta `<audio>` SSML que se inserta antes del mensaje. |
| `rate` | `100` | Velocidad SSML en porcentaje. |
| `pitch` | `0` | Tono SSML en porcentaje. |
| `ssml_volume` | `0` | Ajuste de volumen SSML en dB. |
| `whisper` | `false` | Reproduce el mensaje en modo susurro SSML. |
| `media_content_id` | `""` | URL o identificador multimedia que se reproduce en lugar del TTS. |
| `media_content_type` | Sin valor fijo | Tipo del contenido multimedia. |
| `extra` | `0` | Valor `timer` enviado al reproducir contenido multimedia. |
| `auto_volumes` | `false` | Ajusta el volumen sin reproducir TTS. |

### Opciones de `google`

Cuando `google` es un diccionario admite estas opciones:

| Campo | Valor por defecto | Descripcion |
|---|---|---|
| `media_player` | `google_players` | Reproductor, lista, grupo o nombre amigable. Tambien se acepta el alias `player`. |
| `message` | `message` general | Texto que se debe reproducir. |
| `volume` | Volumen actual de Notifier Hub | Volumen temporal entre `0.0` y `1.0`. |
| `wait_time` | `tts_wait_time` | Margen adicional usado para calcular cuanto esperar antes de restaurar el volumen. |
| `language` | `default_language` | Idioma del motor TTS. |
| `tts_service` | `google_tts_service` | Entidad moderna `tts.*` o servicio TTS heredado. Tambien se acepta el alias `service`. |
| `tts_entity` | `""` | Entidad moderna `tts.*` usada de forma explicita. Tambien se acepta el alias `engine_id`. |
| `mode` | `tts` | Usa `tts` para voz o `notify`, `assistant` o `google assistant` para enviar mediante un servicio notify. Tambien se acepta el alias `type`. |
| `notify_service` | `google_notify_service` | Servicio usado por los modos Google Assistant o notify. |
| `priority` | `false` | Permite que este mensaje Google/Cast salte los bloqueos normales del canal. |
| `media_content_id` | `""` | URL o identificador multimedia que se reproduce en lugar del TTS. |
| `media_content_type` | `music` | Tipo del contenido multimedia. |

## Uso compatible con evento AppDaemon

Notifier Hub escucha el evento personalizado `notifier` para mantener compatibilidad con automatizaciones antiguas creadas para la aplicacion original de AppDaemon.
Los datos de `event_data` se procesan igual que los datos enviados mediante `notifier_hub.send`.

Para automatizaciones nuevas se recomienda llamar directamente al servicio `notifier_hub.send`.
El formato con `event: notifier` permite migrar instalaciones existentes gradualmente, sin tener que modificar todas las automatizaciones antiguas de inmediato.

Ejemplo compatible con AppDaemon:

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

