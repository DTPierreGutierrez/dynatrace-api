import logging

from ruxit.api.base_plugin import RemoteBasePlugin
from dynatrace_api import DynatraceAPI

import pingparsing

log = logging.getLogger(__name__)


class PingExtension(RemoteBasePlugin):
    def initialize(self, **kwargs):
        # The Dynatrace API client
        self.client = DynatraceAPI(
            self.config.get("api_url"), self.config.get("api_token"), log=log, proxies=self.build_proxy_url()
        )
        self.executions = 0

    def build_proxy_url(self):
        proxy_address = self.config.get("proxy_address")
        proxy_username = self.config.get("proxy_username")
        proxy_password = self.config.get("proxy_password")

        if proxy_address:
            protocol, address = proxy_address.split("://")
            proxy_url = f"{protocol}://"
            if proxy_username:
                proxy_url += proxy_username
            if proxy_password:
                proxy_url += f":{proxy_password}"
            proxy_url += f"@{address}"
            log.info(f"Built proxy url: {proxy_url}")
            return {"https": proxy_url}

        return {}

    def query(self, **kwargs) -> None:

        log.setLevel(self.config.get("log_level"))

        name = self.config.get("test_name")
        target = self.config.get("test_target")
        location = self.config.get("test_location", "") if self.config.get("test_location") else "ActiveGate"
        frequency = int(self.config.get("frequency")) if self.config.get("frequency") else 15

        if self.executions % frequency == 0:
            ping_result = ping(target)
            log.info(ping_result.as_dict())

            self.client.report_simple_test(
                name,
                location,
                ping_result.packet_loss_rate is not None and ping_result.packet_loss_rate == 0,
                ping_result.rtt_avg or 0,
                interval=frequency * 60,
                edit_link=f"#settings/customextension;id={self.plugin_info.name}",
            )

            if ping_result.packet_loss_rate is None or ping_result.packet_loss_rate > 0:
                self.client.report_simple_event(name, f"Ping failed for {name}, target: {target}", location)
            else:
                self.client.report_simple_event(name, f"Ping failed for {name}, target: {target}", location, state="resolved")

        self.executions += 1


def ping(host: str) -> pingparsing.PingStats:
    ping_parser = pingparsing.PingParsing()
    transmitter = pingparsing.PingTransmitter()
    transmitter.destination = host
    transmitter.count = 2
    transmitter.timeout = 2000
    return ping_parser.parse(transmitter.ping())
