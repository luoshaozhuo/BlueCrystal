"""HTTP REST polling runner（HTTP GET 读取）。"""

from __future__ import annotations

import json
import time
from urllib.parse import urlencode
from urllib.request import build_opener, ProxyHandler

_no_proxy_opener = build_opener(ProxyHandler({}))

from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.runners.generic_polling import GenericPollingCapacityRunner, PollingReadSample
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan


class HttpRestPollingRunner(GenericPollingCapacityRunner):
    """HTTP REST polling runner。"""

    name = "http_rest_polling_runner"

    def read_once(self, spec: RunnerEndpointPlan, *, target_hz: float, config: CapacityScanConfig) -> PollingReadSample:
        path = str(spec.source.endpoint.params.get("http_path", "/points"))
        point_names = ",".join(point.address for point in spec.source.points)
        query = urlencode({"points": point_names})
        url = f"http://{spec.source.endpoint.host}:{spec.source.endpoint.port}{path}?{query}"
        try:
            with _no_proxy_opener.open(url, timeout=config.read_timeout_s) as response:
                body = response.read().decode("utf-8")
            payload = json.loads(body)
            if isinstance(payload, dict) and isinstance(payload.get("values"), list):
                value_count = len(payload["values"])
            elif isinstance(payload, list):
                value_count = len(payload)
            else:
                value_count = len(spec.source.points)
            return PollingReadSample(ok=True, value_count=value_count, response_timestamp_s=time.time())
        except Exception:
            return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="transport_error")
