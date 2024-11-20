<div align="center">

# Netchecks

</div>

<p align="center">
  <img alt="Netchecks Logo" src="https://raw.githubusercontent.com/hardbyte/netchecks/main/.github/logo.png" width="150" />
</p>

<div align="center">

![Kubernetes](https://img.shields.io/badge/k8s-%23326ce5.svg?style=flat-square&logo=kubernetes&logoColor=white)
[![HELM](https://img.shields.io/badge/helm-%23326ce5.svg?style=flat-square&logo=helm&logoColor=white)](https://artifacthub.io/packages/helm/netchecks/netchecks)
[![ArtifactHub - Netchecks](https://img.shields.io/badge/ArtifactHub-Netchecks-informational?style=flat-square&logo=artifacthub)](https://artifacthub.io/packages/helm/netchecks/netchecks)
[![GitHub release (with filter)](https://img.shields.io/github/v/release/hardbyte/netchecks?style=flat-square&logo=github)](https://github.com/hardbyte/netchecks/releases/latest)
[![PyPI](https://img.shields.io/pypi/v/netcheck.svg?style=flat-square&logo=pypi)](https://pypi.org/project/netcheck/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/netcheck?style=flat-square&logo=python)
[![Coverage Status](https://img.shields.io/coverallsCoverage/github/hardbyte/netchecks?branch=main&style=flat-square&logo=coveralls)](https://coveralls.io/github/hardbyte/netcheck?branch=main)
[![CI status](https://img.shields.io/github/actions/workflow/status/hardbyte/netchecks/ci.yaml?branch=main&style=flat-square&logo=github)](https://github.com/hardbyte/netchecks/actions?query=branch%3Amain)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Fdocs.netchecks.io%2F&style=flat-square&label=docs.netchecks.io)](https://docs.netchecks.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)
[![PyPI Downloads](https://static.pepy.tech/badge/netcheck)](https://pypi.org/project/netcheck?style=flat-square)
[![License](https://img.shields.io/github/license/hardbyte/netchecks?style=flat-square)](/LICENSE)

</div>

**Netchecks** is a set of tools for testing network conditions and asserting that they are as expected.

There are two main components:
- **Netchecks Operator** - Kubernetes Operator that runs network checks and reports results as `PolicyReport` resources. See the [operator README](https://github.com/hardbyte/netchecks/blob/main/operator/README.md) for more details and the full documentation can be found at [https://docs.netchecks.io](https://docs.netchecks.io)
- **Netcheck CLI and Python Library** - Command line tool for running network checks and asserting that they are as expected. Keep reading for the quickstart guide.


# Netcheck Command Line Tool

`netcheck` is a configurable command line application for testing network conditions are as expected. It can be used to validate DNS and HTTP connectivity and can be configured to assert that the results are as expected, for example:

```shell
netcheck http --url=https://github.com/status --validation-rule "data.body.contains('GitHub lives!') && data['status-code'] in [200, 201]"
```

## Installation

Install the Python package from PyPi:

```
pip install netcheck
```

The cli can also be run via Docker:

```shell
docker run -it ghcr.io/hardbyte/netchecks:main
```

### Individual Assertions

By default `netcheck` outputs a JSON result to stdout including response details: 

```shell
$ netcheck dns
```

```json
{
  "spec": {
    "type": "dns",
    "nameserver": null,
    "host": "github.com",
    "timeout": 30.0
  },
  "data": {
    "canonical_name": "github.com.",
    "expiration": 1675825244.2986872,
    "response": "id 6176\nopcode QUERY\nrcode NOERROR\nflags QR RD RA\nedns 0\npayload 65494\n;QUESTION\ngithub.com. IN A\n;ANSWER\ngithub.com. 60 IN A 20.248.137.48\n;AUTHORITY\n;ADDITIONAL",
    "A": [
      "20.248.137.48"
    ],
    "startTimestamp": "2023-02-08T02:59:44.248174",
    "endTimestamp": "2023-02-08T02:59:44.298773"
  },
  "status": "pass"
}

```

Pass the `-v` flag to see log messages.

Each check can be configured, e.g. you can specify the `server` and `host` for a `dns` check, and
tell `netcheck` whether a particular configuration is expected to pass or fail:


```shell
netcheck dns --server 1.1.1.1 --host hardbyte.nz --should-pass
```

```json
{
  "spec": {
    "type": "dns",
    "nameserver": "1.1.1.1",
    "host": "hardbyte.nz",
    "timeout": 30.0,
    "pattern": "\ndata['response-code'] == 'NOERROR' &&\nsize(data['A']) >= 1 && \n(timestamp(data['endTimestamp']) - timestamp(data['startTimestamp']) < duration('10s'))\n"
  },
  "data": {
    "canonical_name": "hardbyte.nz.",
    "expiration": 1683241225.5542665,
    "response": "id 53196\nopcode QUERY\nrcode NOERROR\nflags QR RD RA\n;QUESTION\nhardbyte.nz. IN A\n;ANSWER\nhardbyte.nz. 3600 IN A 209.58.165.79\n;AUTHORITY\n;ADDITIONAL",
    "A": [
      "209.58.165.79"
    ],
    "response-code": "NOERROR",
    "startTimestamp": "2023-05-04T22:00:24.491750",
    "endTimestamp": "2023-05-04T22:00:25.554344"
  },
  "status": "pass"
}
```

Netcheck can handle checks that are expected to fail:
```shell
$ netcheck dns --server=1.1.1.1 --host=made.updomain --should-fail
```

Note the resulting status will show **pass** if the check fails as expected, and **fail** if the check passes unexpectedly!

netcheck has built in default validation for each check type. For example, the `dns` check will pass if the DNS response code is `NOERROR`, there is at least one `A` record, and resolver responds in under 10 seconds. Custom validation is also possible, see the [Custom Validation](#custom-validation) section below.


## Custom Validation

Custom validation can be added to checks by providing a `validation-rule` option on the command line, or a `validation` key in the rules of a test spec when configuring via json. 

For example to override the default validation for the `dns` check to check that the A record resolves to a particular IP:

```shell
netcheck dns --host github.com --validation-rule "data['A'].contains('20.248.137.48')"
```

The validation rule is a CEL expression that is evaluated with the `data` returned by the check and `spec` objects in scope. For an introduction to CEL see https://github.com/google/cel-spec/blob/master/doc/intro.md



## http checks

`http` checks are also available:

Assert that GitHub's status page includes the text "GitHub lives!" and that the response code is 200:

```shell
netcheck http --url=https://github.com/status --validation-rule "data.body.contains('GitHub lives!') && data['status-code'] in [200, 201]"
```

Provide a header with a request:

```shell
netcheck http --url https://pie.dev/headers --header "X-Header:special"
```

Validate that the response body is valid JSON and includes a `headers` object containing the `X-Header` key with the value `special`:

```shell
netcheck http --url https://pie.dev/headers \
  --header "X-Header:special" \
  --validation-rule "parse_json(data.body).headers['X-Header'] == 'special'"
```


Ensure that a POST request fails:

```shell
$ netcheck http --method=post --url=https://s3.ap-southeast-2.amazonaws.com --should-fail
```


## Configuration via file

The main way to run `netcheck` is passing in a list of assertions. 
A json file can be provided with a list of assertions to be checked:

```json
{
  "assertions": [
    {
      "name":  "deny-cloudflare-dns", 
      "rules": [
        {"type": "dns", "server":  "1.1.1.1", "host": "github.com"}
      ]
    }
  ]
}
```

And the `run` command can be called:


```shell
$ netcheck run --config tests/testdata/dns-config.json
```

The output should be valid JSON containing results for each assertion.

Multiple assertions with multiple rules can be specified in the config file,
configuration can be provided to each rule such as headers and custom validation:

```json
{
  "assertions": [
    {"name":  "get-with-header", "rules": [
      {"type": "http", "url": "https://pie.dev/headers", "headers": {"X-Test-Header":  "value"}},
      {"type": "http", "url": "https://pie.dev/headers", "headers": {"X-Header": "secret"}, "validation": "parse_json(data.body).headers['X-Header'] == 'secret'" }
    ]}
  ]
}
```

## External Data

Finally, external context can be referenced to inject data. The following example is a valid config file, if a bit contrived:

```json
{
  "assertions": [
    {
      "name": "example-assertion",
      "rules": [
        {
          "type": "http",
          "url": "{{customdata.url}}",
          "headers": {"{{customdata.header}}": "{{ b64decode(token) }}"},
          "validation": "parse_json(data.body).headers['X-Header'] == 'secret'"
        }
      ]
    }
  ],
  "contexts": [
    {"name": "customdata", "type": "inline", "data": {"url": "https://pie.dev/headers", "header": "X-Header"}},
    {"name": "token", "type": "inline", "data": "c2VjcmV0=="},
    {"name": "selfref", "type": "file", "path": "example-config.json"}
  ]
}
```

In the above example the `customdata` and `token` contexts are injected into the rule.
The `customdata.url` is used as the URL for the request, `customdata.header` is used as the name of the header.
The `token` is base64 decoded and used as the value of the header.
The `selfref` context is unused but shows how to load data an external JSON file which is used extensively by the
Kubernetes operator to inject data.

## Development

Update version in `pyproject.toml`, push to `main` and create a release on GitHub. Pypi release will be carried
out by GitHub actions. 

Install dev dependencies with `uv`:

```shell
uv sync
```

### Testing

Pytest is used for testing. 

```shell
uv run pytest
```
