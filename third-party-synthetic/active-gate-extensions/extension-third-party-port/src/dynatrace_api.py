from datetime import datetime
from typing import List, Dict

import json
import logging
import requests

default_logger = logging.getLogger(__name__)

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SyntheticTestStep:
    def __init__(self, step_id, title):
        self.id = step_id
        self.title = title

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class ThirdPartySyntheticLocation:
    def __init__(self, location_id, name, ip=None):
        self.id = location_id
        self.name = name
        if ip is not None:
            self.ip = ip

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class ThirdPartySyntheticMonitor:
    def __init__(
        self,
        test_id: str,
        title: str,
        scheduleIntervalInSeconds: int,
        description: str = None,
        testSetup: str = None,
        expirationTimestamp: str = None,
        drilldownLink: str = None,
        editLink: str = None,
        enabled: bool = True,
        deleted: bool = False,
        locations: List[ThirdPartySyntheticLocation] = None,
        steps: List[SyntheticTestStep] = None,
        noDataTimeout: int = None,
    ):
        self.id = test_id
        self.title = title
        self.scheduleIntervalInSeconds = scheduleIntervalInSeconds
        if description is not None:
            self.description = description
        if testSetup is not None:
            self.testSetup = testSetup
        if expirationTimestamp is not None:
            self.expirationTimestamp = expirationTimestamp
        if drilldownLink is not None:
            self.drilldownLink = drilldownLink
        if editLink is not None:
            self.editLink = editLink
        self.enabled = enabled
        self.deleted = deleted

        if locations is not None:
            self.locations = locations

        if steps is not None:
            self.steps = steps

        if noDataTimeout is not None:
            self.noDataTimeout = noDataTimeout

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class SyntheticMonitorError:
    def __init__(self, message, code):
        self.message = message
        self.code = code

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class SyntheticMonitorStepResult:
    def __init__(self, step_id: int, startTimestamp: datetime, responseTimeMillis=None, error: SyntheticMonitorError = None):
        self.id = step_id
        self.startTimestamp: int = int(startTimestamp.timestamp() * 1000)

        if responseTimeMillis is not None:
            self.responseTimeMillis = responseTimeMillis

        if error is not None:
            self.error = error

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class ThirdPartySyntheticLocationTestResult:
    def __init__(
        self,
        location_id: str,
        startTimestamp: datetime,
        success: bool,
        responseTimeMillis=None,
        stepResults: List[SyntheticMonitorStepResult] = None,
    ):
        self.id = location_id
        self.startTimestamp: int = int(startTimestamp.timestamp() * 1000)
        self.success = success
        if responseTimeMillis is not None:
            self.responseTimeMillis = responseTimeMillis
        if stepResults is not None:
            self.stepResults = stepResults

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class ThirdPartySyntheticTestResult:
    def __init__(self, test_result_id, totalStepCount, locationResults: List[ThirdPartySyntheticLocationTestResult]):
        self.id = test_result_id
        self.totalStepCount = totalStepCount
        self.locationResults = locationResults

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class ThirdPartyEventResolvedNotification:
    def __init__(self, testId, eventId, endTimestamp: datetime):
        self.testId = testId
        self.eventId = eventId
        self.endTimestamp = int(endTimestamp.timestamp() * 1000)

    def json(self):
        return json.loads(json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4))


class ThirdPartyEventOpenNotification:
    def __init__(
        self, testId, eventId, name, eventType, reason, locations: List[ThirdPartySyntheticLocation], startTimestamp: datetime
    ):
        self.testId = testId
        self.eventId = eventId
        self.name = name
        self.eventType = eventType
        self.reason = reason
        self.locationIds = [location.id for location in locations]
        self.startTimestamp = int(startTimestamp.timestamp() * 1000)

    def json(self):
        return json.loads(json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4))


class ThirdPartySyntheticEvents:
    def __init__(
        self,
        syntheticEngineName,
        open: List[ThirdPartyEventOpenNotification],
        resolved: List[ThirdPartyEventResolvedNotification],
    ):
        self.syntheticEngineName = syntheticEngineName
        self.open = open
        self.resolved = resolved

    def json(self):
        return json.loads(json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4))


class ThirdPartySyntheticTests:
    def __init__(
        self,
        syntheticEngineName,
        messageTimestamp: datetime,
        locations: List[ThirdPartySyntheticLocation],
        tests: List[ThirdPartySyntheticMonitor],
        testResults: List[ThirdPartySyntheticTestResult] = None,
        syntheticEngineIconUrl: str = None,
    ):
        self.syntheticEngineName = syntheticEngineName
        self.messageTimestamp: int = int(messageTimestamp.timestamp() * 1000)
        self.locations = locations
        self.tests = tests

        if testResults is not None:
            self.testResults = testResults

        if syntheticEngineIconUrl is not None:
            self.syntheticEngineIconUrl = syntheticEngineIconUrl

    def json(self):
        return json.loads(json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4))


class DynatraceAPI(object):
    def __init__(self, url: str, token: str, log=default_logger, open_events=None, proxies=None):
        self.base_url = url
        self.proxies = proxies
        if self.proxies is None:
            self.proxies = {}

        self.open_events = open_events
        if open_events is None:
            self.open_events = dict()

        self.auth_header = {"Authorization": f"Api-Token {token}"}
        self.log = log

    def _make_request(self, url, body=None, params=None, headers=None, method="GET"):
        url = f"{self.base_url}{url}"

        if headers is None:
            headers = {}
        headers.update(self.auth_header)
        retries = 0
        response = None
        while retries < 5:
            retries += 1
            self.log.debug(f"Making {method} request to '{url}'. Attempt: {retries}/5, Body: {body}")
            r = requests.request(method, url, json=body, headers=headers, params=params, verify=False, proxies=self.proxies)
            self.log.debug(f"Received response '{r}'")
            response = {}
            if r.text:
                self.log.debug(f"Response: {r.text}")
                response = r.json()
            if r.status_code >= 400:
                self.log.error(f"Error making request. Url:'{url}', body:{body}, params:{params}, response: '{r.text}'")
            else:
                return response
        return response

    def post_thirdparty_synthetic_tests(self, tests: ThirdPartySyntheticTests):
        url = "/api/v1/synthetic/ext/tests"
        return self._make_request(url, body=tests.json(), method="POST")

    def post_thirdparty_synthetic_event(self, events: ThirdPartySyntheticEvents):
        url = "/api/v1/synthetic/ext/events"
        return self._make_request(url, body=events.json(), method="POST")

    def report_simple_test(
        self,
        name: str,
        location_name: str,
        success: bool,
        response_time: int,
        timestamp: datetime = None,
        test_type="Ping",
        interval: int = 60,
        edit_link: str = None,
    ):
        test_id = f'custom_thirdparty_{name.lower().replace(" ", "_")}'
        if timestamp is None:
            timestamp = datetime.now()
        step_id = 1
        location = ThirdPartySyntheticLocation(location_name, location_name)
        step = SyntheticTestStep(step_id, name)
        monitor = ThirdPartySyntheticMonitor(
            test_id, name, interval, description=name, locations=[location], steps=[step], editLink=edit_link
        )
        step_result = SyntheticMonitorStepResult(1, timestamp, response_time)
        loc_result = ThirdPartySyntheticLocationTestResult(location_name, timestamp, success, stepResults=[step_result])
        test_res = ThirdPartySyntheticTestResult(test_id, 0, [loc_result])
        test = ThirdPartySyntheticTests(test_type, timestamp, locations=[location], tests=[monitor], testResults=[test_res])
        return self.post_thirdparty_synthetic_tests(test)

    def report_simple_event(
        self, name: str, description, location_name, timestamp: datetime = None, state="open", test_type="Ping"
    ):
        test_id = f'custom_thirdparty_{name.lower().replace(" ", "_")}'
        if timestamp is None:
            timestamp = datetime.now()
        open = []
        resolved = []
        if state == "open":
            if test_id in self.open_events:
                self.open_events[test_id] += 1
            else:
                self.open_events[test_id] = 1
            event_id = f"{test_id}_{self.open_events[test_id]}"
            open.append(
                ThirdPartyEventOpenNotification(
                    test_id,
                    event_id,
                    name,
                    "testOutage",
                    description,
                    [ThirdPartySyntheticLocation(location_name, location_name)],
                    timestamp,
                )
            )

        elif state == "resolved":
            if test_id in self.open_events:
                event_ids = [f"{test_id}_{i + 1}" for i in range(self.open_events[test_id])]
                for event_id in event_ids:
                    resolved.append(ThirdPartyEventResolvedNotification(test_id, event_id, timestamp))
                del self.open_events[test_id]

        events = ThirdPartySyntheticEvents(test_type, open, resolved)

        if open or resolved:
            return self.post_thirdparty_synthetic_event(events)
