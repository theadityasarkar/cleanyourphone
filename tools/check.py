#!/usr/bin/env python3
"""Check bloat status or firmware update drift on an Android phone.

Compares installed/enabled packages against a debloat list.
Can automatically re-disable items that reappeared after an OTA firmware update with `--fix`.

Usage:
    python check.py <debloat.txt>
    python check.py --fix <debloat.txt>
"""
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import recovery  # noqa: E402


def run_phone_py(args):
    phone_py = os.path.join(SCRIPT_DIR, "phone.py")
    cmd = [sys.executable, phone_py] + args
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return res.returncode, res.stdout, res.stderr


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage:\n  python check.py <debloat.txt>\n  python check.py --fix <debloat.txt>")
        sys.exit(0)

    fix_mode = False
    list_path = sys.argv[1]
    if list_path == "--fix":
        fix_mode = True
        if len(sys.argv) < 3:
            sys.stderr.write("Error: --fix requires a debloat list path.\n")
            sys.exit(2)
        list_path = sys.argv[2]

    packages = recovery.read_list(list_path)
    violations = recovery.get_safety_violations(packages)
    if violations:
        sys.stderr.write("Safety check failed: Debloat list contains unsafe packages.\n")
        sys.exit(1)

    print(f"[*] Checking device status against: {list_path} ({len(packages)} packages)")

    # Query currently disabled packages
    _, dis_out, _ = run_phone_py(["pm list packages -d --user 0"])
    disabled_pkgs = set()
    for l in dis_out.splitlines():
        if l.startswith("package:"):
            disabled_pkgs.add(l.split(":", 1)[1].strip())

    # Query all packages
    _, all_out, _ = run_phone_py(["pm list packages --user 0"])
    installed_pkgs = set()
    for l in all_out.splitlines():
        if l.startswith("package:"):
            installed_pkgs.add(l.split(":", 1)[1].strip())

    active_bloat = []
    already_clean = []
    not_on_device = []

    for pkg in packages:
        if pkg in disabled_pkgs:
            already_clean.append(pkg)
        elif pkg in installed_pkgs:
            active_bloat.append(pkg)
        else:
            not_on_device.append(pkg)

    print("\n" + "=" * 60)
    print(" BLOAT AUDIT REPORT")
    print("=" * 60)
    print(f" [+] Already Disabled / Clean:   {len(already_clean)}")
    print(f" [-] Not Present On This Device: {len(not_on_device)}")
    print(f" [!] Active Bloat / Telemetry:   {len(active_bloat)}")
    print("=" * 60)

    if active_bloat:
        print("\nActive bloat detected on device:")
        for b in active_bloat:
            print(f"  * {b}")

        if fix_mode:
            print("\n[*] Applying fix: Disabling active bloat...")
            for b in active_bloat:
                code, out, err = run_phone_py([f"pm disable-user --user 0 {b}"])
                print(f"  -> Disabling {b}: {out.strip() if out.strip() else 'OK'}")
            print("\n[OK] Fix completed. Re-running verification...")
            main()
            return
        else:
            print("\nRun with --fix to automatically disable remaining bloat:")
            print(f"  python check.py --fix {list_path}")
            sys.exit(1)
    else:
        print("\n[SUCCESS] Device is 100% clean according to this list!")
        sys.exit(0)


if __name__ == "__main__":
    main()
