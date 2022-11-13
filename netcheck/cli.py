import json
import logging
from enum import Enum
from pathlib import Path
from rich import print, print_json
from rich.console import Console
import typer
import requests

from netcheck.dns import get_A_records_by_dns_lookup

app = typer.Typer()
logger = logging.getLogger("netcheck")
#logging.basicConfig(level=logging.DEBUG)

err_console = Console(stderr=True)


@app.command()
def run(
        config: Path = typer.Option(..., exists=True, file_okay=True, help='Config file with netcheck assertions'),
        verbose: bool = typer.Option(False, '-v')
        ):
    """Carry out all network assertions in given config file.
    """
    logger.info(f"Loading assertions from {config}")
    with config.open() as f:
        data = json.load(f)

    # TODO: Validate the config format

    print(f"Loaded {len(data['assertions'])} assertions")

    # Run each test
    for test in data['assertions']:
        print(f"Running test '{test['name']}'")
        for rule in test['rules']:
            check_individual_assertion(
                rule['type'],
                rule,
                should_fail=rule['expected'] != 'pass',
                verbose=verbose
            )

    # TODO summary output

    # pass count
    # fail count
    # warn count ?
    # error count
    # skip count


class NetcheckHttpMethod(str, Enum):
    get = 'get'
    post = 'post'
    patch = 'patch'
    put = 'put'
    delete = 'delete'


class NetcheckTestType(str, Enum):
    dns = "dns"
    http = 'http'


@app.command()
def http(
        url: str = typer.Option('https://github.com/status', help="URL to request", rich_help_panel="http test"),
        method: NetcheckHttpMethod = typer.Option(NetcheckHttpMethod.get, help="HTTP method", rich_help_panel='http test'),
        should_fail: bool = typer.Option(False, "--should-fail/--should-pass"),
        verbose: bool = typer.Option(False, '-v', '--verbose')
):
    """Carry out a http network check"""

    test_config = {
        "url": url,
        'method': method
    }

    check_individual_assertion(
        NetcheckTestType.http,
        test_config,
        should_fail,
        verbose=verbose
    )


@app.command()
def dns(
        server: str = typer.Option(None, help="DNS server to use for dns tests.", rich_help_panel="dns test"),
        host: str = typer.Option('github.com', help='Host to search for', rich_help_panel="dns test"),
        should_fail: bool = typer.Option(False, "--should-fail/--should-pass"),
        verbose: bool = typer.Option(False, '-v', '--verbose')
):
    """Carry out a dns check"""

    test_config = {
        "server": server,
        "host": host,
    }

    check_individual_assertion(
        NetcheckTestType.dns,
        test_config,
        should_fail,
        verbose=verbose
    )


def check_individual_assertion(test_type, test_config, should_fail, verbose=False):
    match test_type:
        case 'dns':
            if verbose:
                print(f"DNS check with nameserver {test_config['server']} looking up host '{test_config['host']}'")
            failed, test_detail = dns_lookup_check(test_config['host'], test_config['server'])
        case 'http':
            if verbose:
                print(f"http check with url '{test_config['url']}'")
            failed, test_detail = http_request_check(test_config['url'], test_config.get('method', 'get'))
        case _:
            logger.warning("Unhandled test type")
            raise NotImplemented("Unknown test type")
    notify_for_unexpected_test_result(failed, should_fail, test_detail, verbose=verbose)


def notify_for_unexpected_test_result(failed, should_fail, test_detail, verbose=False):
    if failed:
        if not should_fail:
            err_console.print("[bold red]:boom: Failed but was expected to pass[/]")
            print_json(data=test_detail)
        else:
            logging.debug("Failed (as expected)")
            if verbose:
                err_console.print("[yellow]:cross_mark: Failed. As expected.[/]")
                print_json(data=test_detail)
    else:
        if not should_fail:
            logging.debug("Passed (as expected)")
            if verbose:
                err_console.print("[green]✔ Passed (as expected)[/]")
                print_json(data=test_detail)
        else:
            err_console.print("[bold red]:bomb: The network test worked but was expected to fail![/]")
            print_json(data=test_detail)


def http_request_check(url, method: NetcheckHttpMethod = 'get'):
    failed = False
    details = {
        'type': 'http',
        'method': method,
        'url': url,
        'result': {}
    }
    try:
        response = getattr(requests, method)(url, timeout=30)
        details['result']['status-code'] = response.status_code
        response.raise_for_status()
    except Exception as e:
        failed = True
        logger.info(f"Caught exception:\n\n{e}")
        details['result']['exception-type'] = e.__class__.__name__
        details['result']['exception'] = str(e)

    return failed, details


def dns_lookup_check(host, server, timeout=10):
    failed = False
    detail = {
        'type': 'dns',
        'nameserver': server,
        'host': host,
        'timeout': timeout
    }
    result = {}
    try:
        ip_addresses = get_A_records_by_dns_lookup(host, nameserver=server, timeout=timeout)
        result['A'] = ip_addresses
    except Exception as e:
        logger.info(f"Caught exception:\n\n{e}")
        failed = True

        result['exception-type'] = e.__class__.__name__
        result['exception'] = str(e)

    detail['result'] = result
    return failed, detail


if __name__ == '__main__':
    app()
