import datetime
import logging

import dns.resolver
from dns.exception import Timeout

logger = logging.getLogger("netcheck.dns")


DEFAULT_DNS_VALIDATION_RULE = """
data['response-code'] == 'NOERROR' &&
size(data['A']) >= 1 && 
(timestamp(data['endTimestamp']) - timestamp(data['startTimestamp']) < duration('10s'))
"""


def get_A_records_by_dns_lookup(target, nameserver=None, timeout=60):
    # We always reset the default dns resolver
    dns.resolver.reset_default_resolver()
    resolver = dns.resolver.get_default_resolver()

    result = {}

    if nameserver is not None:
        resolver.nameservers = [nameserver]

    # this resolver can also be used with the default nameserver
    # search=True is required to use the OS search path!
    # E.g. `kubernetes` -> `kubernetes.default.svc.cluster.local`
    try:
        answer = resolver.resolve(target, "A", lifetime=timeout, search=True)

        # canonical name of the target
        result["canonical_name"] = answer.canonical_name.to_text()
        # answer.expiration is the TTL as a float timestamp
        result["expiration"] = answer.expiration

        # str(answer.response) is the raw DNS response
        result["response"] = str(answer.response)

        result["A"] = []
        for IPval in answer:
            result["A"].append(IPval.to_text())
        result["response-code"] = "NOERROR"
    except Timeout:
        result["response-code"] = "TIMEOUT"
    except dns.resolver.NXDOMAIN:
        result["response-code"] = "NXDOMAIN"
    except dns.exception.DNSException as e:
        result["response-code"] = "DNSERROR"
        result["exception-type"] = e.__class__.__name__
        result["exception"] = str(e)

    return result


def dns_lookup_check(host, server, timeout=10):
    test_spec = {
        "type": "dns",
        "nameserver": server,
        "host": host,
        "timeout": timeout,
    }
    startTimestamp = datetime.datetime.now(datetime.UTC).isoformat()

    try:
        result_data = get_A_records_by_dns_lookup(host, nameserver=server, timeout=timeout)

    except Exception as e:
        logger.info(f"Unexpected exception:\n\n{e}")
        raise

    result_data["startTimestamp"] = startTimestamp
    result_data["endTimestamp"] = datetime.datetime.now(datetime.UTC).isoformat()

    output = {"spec": test_spec, "data": result_data}
    return output
