import json
import urllib.error
import urllib.request


class HttpError(Exception):
    """
    Raised when an outbound HTTP call fails: connection error, timeout,
    a non-2xx status, or a body that is not valid JSON.
    """

    def __init__(self, message, status=None, body=None):
        super().__init__(message)
        self.status = status
        self.body = body


def post_json(url, data, headers=None, timeout=10, parse_response=True):
    """
    POST `data` as a JSON body and return the decoded JSON response.

    Returns None when the body is empty or `parse_response` is False — pass
    False for endpoints whose response is ignored, so a non-JSON body is not
    treated as a failure. Raises HttpError on any failure, so callers never
    have to inspect a status code themselves.
    """
    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={'Content-Type': 'application/json', **(headers or {})},
        method='POST',
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()

    except urllib.error.HTTPError as e:
        # 4xx/5xx: the body often carries the gateway's error description.
        body = e.read().decode(errors='replace')
        raise HttpError(f"{url} returned HTTP {e.code}", status=e.code, body=body) from e

    except (urllib.error.URLError, TimeoutError) as e:
        raise HttpError(f"could not reach {url}: {e}") from e

    if not parse_response or not payload:
        return None

    try:
        return json.loads(payload)
    except json.JSONDecodeError as e:
        raise HttpError(
            f"{url} returned a non-JSON body",
            body=payload.decode(errors='replace'),
        ) from e
