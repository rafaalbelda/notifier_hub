import hassapi as hass
import helpermodule as h

"""
Class Phone_Manager handles sending call to voice notfyng service
"""

__NOTIFY__ = "notify/"
SUB_TTS = [(r"[\*\-\[\]_\(\)\{\~\|\}\s]+", r" ")]
HA_SIP_ADDON = "c7744bff_ha-sip"


class Phone_Manager(hass.Hass):
    def initialize(self):
        self.tts_language = self.args.get("tts_language")

    def send_voice_call(self, data, phone_name: str, sip_server_name: str):
        message = h.replace_regular(data["message"], SUB_TTS)
        called_number = data["called_number"]
        if called_number != "":
            called_number = "sip:{}@{}".format(called_number, sip_server_name)
            self.call_service(
                "hassio/addon_stdin",
                addon=HA_SIP_ADDON,
                input={
                    "command": "dial",
                    "number": called_number,
                    "menu": {
                        "message": message,
                        "language": self.get_state(self.tts_language),
                        "post_action": "hangup",
                    },
                },
            )
