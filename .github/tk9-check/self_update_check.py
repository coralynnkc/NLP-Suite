"""Self-updater check, without clicking (docs/future-work.md §14), for a release that is not published yet.

    python self_update_check.py <old release zip> <candidate zip> <work dir>

1. Unzips the old release as the user's install, and the candidate a second time as the clean reference.
2. Adds what a user adds: a file under lib/, a folder of their own, a line in a config file.
3. Runs the OLD release's own update_zip_install() on its own python-env. Only two things are faked: GitHub's
   "latest release" answer (it points at the candidate zip, served from localhost) and the dialogs (Yes to
   the update question; every message printed; a warning or error fails the check). The download, the
   unpacking, the user-file scan and the swap script (PowerShell on Windows) are the release's real code.
4. Waits for the swap script, then checks: the install is the candidate (every candidate file there, same
   size), the user's three additions came over, the backup is marked complete.
5. Runs the NEW release's remove_previous_version() on its own python-env, as the menu does at start, and
   checks the backup is gone.
Exit 0 when every check passes. The swap script's log is printed at the end.
"""

import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

APP = "NLP_Suite"
USER_LIB_FILE = os.path.join("lib", "my_own_wordlist.txt")
USER_FOLDER_FILE = os.path.join("My corpus", "doc1.txt")
CONFIG_FILE = os.path.join("config", "NLP_default_IO_config.csv")
CONFIG_LINE = "self-update check line"

# Runs inside the old release's python-env. argv: app, url, size, version
INNER = r"""
import os, sys
app, url, size, version = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
sys.path.insert(0, os.path.join(app, "src"))
import tkinter.messagebox as mb
problems = []
def say(kind, bad):
    def f(title=None, message=None, **k):
        print(kind + ":", (message or "").replace("\n", " ")[:400])
        if bad:
            problems.append(message)
        return True
    return f
mb.askyesno = say("ASKED (answered Yes)", False)
mb.showinfo = say("INFO", False)
mb.showwarning = say("WARNING", True)
mb.showerror = say("ERROR", True)
import requests
real_get = requests.get
import NLP_setup_self_update_util as u
name = u.asset_name()
class Latest:
    def raise_for_status(self):
        pass
    def json(self):
        return {"tag_name": "v" + version,
                "assets": [{"name": name, "browser_download_url": url, "size": size, "state": "uploaded"}]}
def get(target, *a, **k):
    return Latest() if target == u.RELEASE_API_URL else real_get(target, *a, **k)
requests.get = get
reason = u.update_zip_install(app, version)
print("update_zip_install returned:", repr(reason))
sys.exit(1 if reason or problems else 0)
"""

REMOVE = r"""
import os, sys
app = sys.argv[1]
sys.path.insert(0, os.path.join(app, "src"))
import NLP_setup_self_update_util as u
u.remove_previous_version(app, background=False)
"""


def python_of(app):
    if sys.platform == "win32":
        return os.path.join(app, "python-env", "python.exe")
    return os.path.join(app, "python-env", "bin", "python3")


def unzip(zip_path, dest):
    if sys.platform == "win32":
        subprocess.run(["7z", "x", "-y", "-o" + dest, zip_path], check=True, stdout=subprocess.DEVNULL)
    else:  # keep permissions and symlinks
        subprocess.run(["ditto", "-x", "-k", zip_path, dest], check=True)
    return os.path.join(dest, APP)


def files_with_sizes(root):
    out = {}
    for d, _, names in os.walk(root):
        for n in names:
            p = os.path.join(d, n)
            if not os.path.islink(p):
                out[os.path.relpath(p, root)] = os.path.getsize(p)
    return out


def serve(folder):
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=folder, **k)  # noqa: E731
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main(old_zip, cand_zip, work):
    fails = []

    def check(ok, what):
        print(("ok    " if ok else "FAIL  ") + what)
        if not ok:
            fails.append(what)

    os.makedirs(work, exist_ok=True)
    install = unzip(old_zip, os.path.join(work, "install"))
    clean = unzip(cand_zip, os.path.join(work, "clean"))
    with open(os.path.join(clean, "lib", "release_version.txt"), encoding="utf-8") as f:
        version = f.read().strip()
    with open(os.path.join(install, "lib", "release_version.txt"), encoding="utf-8") as f:
        old_version = f.read().strip()
    print(f"installed {old_version}; updating to the candidate, whose release_version.txt says {version}")

    # what a user adds
    for rel, text in ((USER_LIB_FILE, "my words\n"), (USER_FOLDER_FILE, "my document\n")):
        os.makedirs(os.path.dirname(os.path.join(install, rel)), exist_ok=True)
        with open(os.path.join(install, rel), "w", encoding="utf-8") as f:
            f.write(text)
    os.makedirs(os.path.join(install, "config"), exist_ok=True)
    with open(os.path.join(install, CONFIG_FILE), "a", encoding="utf-8") as f:
        f.write(CONFIG_LINE + "\n")

    served = os.path.join(work, "served")
    os.makedirs(served, exist_ok=True)
    name = os.path.basename(cand_zip)
    shutil.copy(cand_zip, os.path.join(served, name))
    httpd = serve(served)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/{name}"

    log = os.path.join(tempfile.gettempdir(), "NLP_Suite_update.log")
    if os.path.exists(log):
        os.remove(log)
    env = dict(os.environ, NLP_SUITE_UPDATE_QUIET="1", PYTHONDONTWRITEBYTECODE="1", DO_NOT_TRACK="1")
    p = subprocess.run(
        [python_of(install), "-c", INNER, install, url, str(os.path.getsize(cand_zip)), version],
        cwd=work,
        env=env,
        timeout=3600,
    )
    check(p.returncode == 0, "the old release's updater downloaded, unpacked and started the swap, no warnings")

    # the swap script waits for the updater's process (it ran from inside the install) to exit
    stage = install + "_update"
    backup = install + "_previous"
    end = time.time() + 1800
    while time.time() < end and os.path.exists(stage):
        time.sleep(5)
    time.sleep(5)
    check(not os.path.exists(stage), "the swap script finished (staging folder gone)")
    text = ""
    if os.path.exists(log):
        with open(log, encoding="utf-8", errors="replace") as f:
            text = f.read()
    check("FAILED" not in text, "the swap script's log has no FAILED line")

    want = files_with_sizes(clean)
    have = files_with_sizes(install) if os.path.isdir(install) else {}
    missing = [r for r in want if r not in have and not r.startswith("config" + os.sep)]
    resized = [r for r in want if r in have and have[r] != want[r] and not r.startswith("config" + os.sep)]
    check(not missing, f"every candidate file is in the install ({len(missing)} missing: {missing[:5]})")
    check(not resized, f"and has the candidate's size ({len(resized)} differ: {resized[:5]})")
    with open(os.path.join(install, "lib", "release_version.txt"), encoding="utf-8") as f:
        check(f.read().strip() == version, "lib/release_version.txt is the candidate's")
    check(os.path.isfile(os.path.join(install, USER_LIB_FILE)), f"the user's {USER_LIB_FILE} came over")
    check(os.path.isfile(os.path.join(install, USER_FOLDER_FILE)), f"the user's {USER_FOLDER_FILE} came over")
    cfg = os.path.join(install, CONFIG_FILE)
    check(os.path.isfile(cfg) and CONFIG_LINE in open(cfg, encoding="utf-8").read(), "the user's config line came over")
    check(os.path.isfile(os.path.join(backup, "NLP_Suite_previous_version.txt")), "the backup is marked complete")

    r = subprocess.run([python_of(install), "-c", REMOVE, install], cwd=work, env=env, timeout=900)
    check(r.returncode == 0 and not os.path.exists(backup), "the new release's remove_previous_version deleted the backup")

    httpd.shutdown()
    print("\n----- " + log + "\n" + (text or "(no log)"))
    print(f"\n{len(fails)} check(s) failed" if fails else "\nall checks passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
