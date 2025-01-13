import os
import subprocess
import random
import string
import time
from typing import Optional

from pytest import fixture

NETCHECKS_CHART_DIR = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.path.pardir,
        "charts",
        "netchecks",
    )
)

NETCHECKS_EXAMPLES_DIR = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.path.pardir,
        "examples",
    )
)

TEST_DATA_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "testdata",
)


def random_lower_string(length: Optional[int] = 32) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


IMAGE_TAG = os.environ.get("NETCHECKS_IMAGE_TAG", "main")


@fixture()
def test_file_path():
    def get_test_file(filename):
        return os.path.join(TEST_DATA_DIR, filename)

    return get_test_file


@fixture()
def example_dir_path():
    def get_example_file(example_name):
        return os.path.join(NETCHECKS_EXAMPLES_DIR, example_name)

    return get_example_file


# @fixture(scope="session")
# def netchecks_crds():
#     crds_folder_path = os.path.join(NETCHECKS_CHART_DIR, "crds")
#     print(crds_folder_path)
#     subprocess.run(f"kubectl apply -f {crds_folder_path}", shell=True, check=True)
#     yield None
#     print("Deleting CRDs")
#     try:
#         subprocess.run(f"kubectl delete -f {crds_folder_path} --timeout=30s", shell=True, check=True)
#     except subprocess.CalledProcessError:
#         pass


@fixture(scope="session")
def netchecks(k8s_namespace):
    try:
        subprocess.run(
            f"""helm upgrade --install netchecks-operator {NETCHECKS_CHART_DIR} \
                -n {k8s_namespace} \
                --set operator.image.tag={IMAGE_TAG} \
                --set probeConfig.image.tag={IMAGE_TAG}
            """,
            shell=True,
            check=True,
        )
        subprocess.run(
            f"kubectl wait Deployment -n {k8s_namespace} -l app.kubernetes.io/instance=netchecks-operator --for condition=Available --timeout=30s",
            shell=True,
            check=True,
        )
        startup_log_output = subprocess.run(
            f"kubectl logs Deployment/netchecks-operator -n {k8s_namespace}",
            shell=True,
            capture_output=True,
        )
        print(startup_log_output.stdout.decode())

        yield None

    finally:
        print("Logs from netchecks-operator")
        operator_log_output = subprocess.run(
            f"kubectl logs Deployment/netchecks-operator -n {k8s_namespace}",
            shell=True,
            capture_output=True,
        )
        print(operator_log_output.stdout.decode())

        print("Uninstalling netchecks-operator")
        try:
            subprocess.run(
                "kubectl delete -A NetworkAssertions --all --timeout=30s",
                shell=True,
                check=True,
            )
            time.sleep(3)
            subprocess.run(
                "kubectl delete -A Jobs -l app.kubernetes.io/component=probe -l app.kubernetes.io/name=netchecks --timeout=30s",
                shell=True,
                check=True,
            )
            subprocess.run(
                f"helm uninstall netchecks-operator -n {k8s_namespace}",
                shell=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            pass


@fixture(scope="session")
def k8s_namespace():
    name = f"netchecks-test-{random_lower_string(length=6)}"
    subprocess.run(f"kubectl create namespace {name}", shell=True, check=True)
    yield name
    print("Trying to delete namespace")
    subprocess.run(f"kubectl delete namespace {name} --timeout=30s", shell=True, check=False)
