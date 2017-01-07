"""Module beacon provides data from NIST Randomness Beacon.

This module exposes a public function `get_beacons` which can be used to fetch
NIST Randomness Beacon values for a given time period.

Please see https://beacon.nist.gov/home for more information about Randomness
Beacon.
"""

import logging
import datetime
import xml.etree.ElementTree as ET
from requests_toolbelt.threaded import pool

URL_TEMPLATE = "https://beacon.nist.gov/rest/record/{:0.0f}"
MIN_EPOCH = 1378395540


class Beacon(dict):
    """Beacon is a simple dict-like structure which parses a beacon XML.

    Beacon fields (like outputValue or seedValue) are available as values of
    the dict.

    Usage:
      >>> b = Beacon("<?xml version="1.0" ... >")
      >>> b["frequency"]
      60
      >>>
    """
    def __init__(self, xml_string):
        try:
            tree = ET.fromstring(xml_string)
            for elem in tree.iter():
                tag = elem.tag.split("}", 1)[1]  # strip namespace
                self[tag] = elem.text
        except ET.ParseError as e:
            raise RuntimeError("Cannot parse '{}' as XML: {}".format(
                xml_string, e))


def get_beacons(dt_from, dt_to, timeout, concurrency):
    """Get Beacon objects for a given time period.

    This function yields Beacon objects for all beacons covered by a time
    period defined by two datetime objects - dt_from and dt_to (inclusive on
    both ends). Timestamps get truncated to the minute, since beacons are
    emitted every minute.

    Per-request timeout (in seconds) can be defined via `timeout` argument.

    An HTTP connection pool is used to fetch beacons, with its size defined by
    the `concurrency` argument.

    A RuntimeError is raised if an exception is encountered while fetching or
    parsing beacon data.
    """
    urls = list(_generate_urls(dt_from, dt_to))
    logging.debug("Fetching URLs: {}".format(urls))
    for response in _fetch_urls(urls, timeout, concurrency):
        yield Beacon(response.text)


def _fetch_urls(urls, timeout, concurrency):
    """Fetch a list of URLs using a connection pool.

    This function uses a connection pool (driven by a thread pool) to fetch
    a list of URLs. It yields requests.Response objects.

    Connection pool size is passed using `concurrency` argument, and
    per-request timeout (in seconds) via the `timeout` argument.

    If an exception is encountered while fetching any of the given URLs, a
    RuntimeError is raised.
    """
    p = pool.Pool.from_urls(
      urls, dict(timeout=timeout), num_processes=concurrency)
    p.join_all()
    for exc in p.exceptions():
        raise RuntimeError("Error while fetching'{}': {}".format(
          exc.request_kwargs["url"], exc.exception))

    for response in p.responses():
        yield response


def _generate_urls(dt_from, dt_to):
    """Generate a list of beacon URLs for a time period.

    This function yields NIST beacon URLs (in increasing timestamp order) for
    all beacons covered by a time period defined by two datetime objects -
    dt_from and dt_to (inclusive on both sides). Timestamps get truncated to
    the minute, since beacons are emitted every minute.
    """
    dt_from = _truncate_seconds(dt_from)
    while dt_from <= _truncate_seconds(dt_to):
        yield URL_TEMPLATE.format(dt_from.timestamp())
        dt_from = dt_from + datetime.timedelta(minutes=1)


def _truncate_seconds(dt):
    """Truncate a datetime object to the minute."""
    return dt.replace(second=0, microsecond=0)
