import contextlib
import sys
from subprocess import run

import httpx

from envs import LICENSE_KEY


def __run(cmd: str) -> str | None:
    with contextlib.suppress(Exception):
        r = run(cmd, shell=True, capture_output=True, check=True, encoding="utf-8")
        return r.stdout.strip()


def __guid() -> str | None:
    if sys.platform == "darwin":
        cmd = "ioreg -d2 -c IOPlatformExpertDevice | awk -F\\\" '/IOPlatformUUID/{print $(NF-1)}'"
        return __run(cmd)
    if sys.platform in ["win32", "cygwin", "msys"]:
        return __run("wmic csproduct get uuid").split("\n")[2].strip()
    if sys.platform.startswith("linux"):
        return __run("cat /var/lib/dbus/machine-id") or __run("cat /etc/machine-id")


def __unique_guid() -> str:
    if guid := __guid():
        guid += "-" + LICENSE_KEY
        return guid
    return LICENSE_KEY


def checker() -> bool:
    r = httpx.post("http://65.109.64.76:5000/", cookies={"__guid": __unique_guid()})
    if r.status_code == 200:
        return r.json().get("result", False)
    return False


if __name__ == "__main__":
    print(__unique_guid())
