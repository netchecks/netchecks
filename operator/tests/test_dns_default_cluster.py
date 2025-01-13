import json
import time
import subprocess


def test_dns_check_with_installed_operator(netchecks, k8s_namespace, test_file_path):
    # netchecks should be installed (via helm)
    # Confirm netchecks is running
    manifest = test_file_path("cluster-dns.yaml")
    name = "cluster-dns-should-work"

    subprocess.run(f"kubectl apply -n {k8s_namespace} -f {manifest}", shell=True, check=True)

    # Assert that a Job gets created in the same namespace
    for i in range(10):
        jobs_response = subprocess.run(
            f"kubectl get jobs -n {k8s_namespace}",
            shell=True,
            check=True,
            capture_output=True,
        )
        if name.encode() in jobs_response.stdout:
            break
        time.sleep(1.5**i)

    # Wait for the job to complete
    subprocess.run(
        f"kubectl wait Job/{name} -n {k8s_namespace} --for condition=complete --timeout=300s",
        shell=True,
        check=True,
    )

    # Assert that a PolicyReport gets created in the same namespace
    for i in range(10):
        policy_report_response = subprocess.run(
            f"kubectl get policyreports -n {k8s_namespace}",
            shell=True,
            check=True,
            capture_output=True,
        )
        if name.encode() in policy_report_response.stdout:
            break
        time.sleep(1.5**i)
    assert name.encode() in policy_report_response.stdout

    summary_filter = "jsonpath='{.summary}'"
    policy_report_summary = subprocess.run(
        f"""kubectl get policyreport/{name} -n {k8s_namespace} -o {summary_filter}""",
        shell=True,
        check=True,
        capture_output=True,
    )
    policy_report_summary = json.loads(policy_report_summary.stdout)

    assert policy_report_summary["pass"] >= 1
    assert "fail" not in policy_report_summary

    # Now get the detailed policy report results
    results_filter = "jsonpath='{.results}'"
    policy_report_results_response = subprocess.run(
        f"""kubectl get policyreport/{name} -n {k8s_namespace} -o {results_filter}""",
        shell=True,
        check=True,
        capture_output=True,
    )
    policy_report_results = json.loads(policy_report_results_response.stdout)

    for result in policy_report_results:
        assert result["category"] == "dns"
        assert result["result"] == "pass"
        assert result["source"] == "netchecks"

        json.loads(result["properties"]["spec"])
        json.loads(result["properties"]["data"])

    # Delete the network assertion
    subprocess.run(
        f"kubectl delete -n {k8s_namespace} -f {manifest} --timeout=30s",
        shell=True,
        check=True,
    )
