import datetime


def internal_check(
    timeout=5,
):
    """An internal no-op check"""

    test_spec = {
        "type": "internal",
        "timeout": timeout,
    }

    result_data = {
        "startTimestamp": datetime.datetime.now(datetime.UTC).isoformat(),
    }

    output = {"spec": test_spec, "data": result_data}

    result_data["endTimestamp"] = datetime.datetime.now(datetime.UTC).isoformat()

    return output
