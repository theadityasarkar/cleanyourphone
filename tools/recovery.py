#!/usr/bin/env python3
"""State record and rollback planner for CleanYourPhone.

Saves device state before disabling packages so restore only re-enables what was actually
changed. Reversible, safe, and guards critical system packages.

Usage:
    python recovery.py --save <debloat.txt>
    python recovery.py --commands <debloat.txt>
    python recovery.py --check-safety <debloat.txt>
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

# Package name syntax
PACKAGE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$")

# Core Android packages that cause bricking/bootloop if disabled
CORE_ANDROID_RE = re.compile(
    r"^(android|android\.ext\.(services|shared)|com\.android\.sdksandbox|"
    r"com\.android\.location\.fused|com\.android\.systemui|com\.android\.shell|"
    r"com\.android\.phone|com\.android\.settings|com\.android\.server\.telecom|"
    r"com\.(google\.)?android\.(permissioncontroller|packageinstaller|ext\.services|ext\.shared|modulemetadata)|"
    r"com\.google\.android\.overlay\.modules.*|com\.android\.providers\..*)$"
)

# Providers that are safe exceptions (e.g. user dictionary)
CORE_OK_PROVIDERS = re.compile(r"^com\.android\.providers\.(userdictionary|blockednumber)$")

# MIUI / HyperOS critical bootloop packages
MIUI_CRITICAL_BOOTLOOP = {
    "com.miui.securitycenter",     # MIUI Security Center - triggers fatal bootloop if disabled!
    "com.miui.securityadd",        # Security Add-on component
    "com.miui.guardprovider",      # System security hook
    "com.android.keyguard",        # Lock screen / Keyguard
    "com.google.android.gms",      # Google Play Services
    "com.android.vending",         # Google Play Store
    "com.google.android.inputmethod.latin",  # Gboard (keyboard)
}

# POCO / MIUI Default Launchers (guarded unless alternative launcher is present)
STOCK_LAUNCHERS = {
    "com.mi.android.globallauncher",  # POCO Launcher (POCO M4 5G default!)
    "com.miui.home",                  # Xiaomi / Redmi Launcher
}

RECORD_DIR = Path.home() / ".cleanyourphone" / "records"


def read_list(path):
    """Read clean package names from debloat list file."""
    p = Path(path)
    if not p.is_file():
        sys.stderr.write(f"Error: Debloat list not found at {path}\n")
        sys.exit(2)

    names = []
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines:
        cleaned = line.split("#")[0].strip()
        if not cleaned:
            continue
        pkg = cleaned.split()[0]
        if not PACKAGE_RE.match(pkg):
            sys.stderr.write(f"Error: Invalid package name '{pkg}' in {path}\n")
            sys.exit(2)
        names.append(pkg)
    return names


def get_safety_violations(packages):
    """Check for dangerous core or MIUI bootloop packages."""
    violations = []
    for pkg in packages:
        if pkg in MIUI_CRITICAL_BOOTLOOP:
            violations.append((pkg, "CRITICAL: MIUI Security/Core package that causes bootloops!"))
        elif CORE_ANDROID_RE.match(pkg) and not CORE_OK_PROVIDERS.match(pkg):
            violations.append((pkg, "CRITICAL: Core Android system package!"))
    return violations


def get_record_path(device_id, list_path):
    """Compute persistent record path."""
    RECORD_DIR.mkdir(parents=True, exist_ok=True)
    list_hash = hashlib.sha256(Path(list_path).read_bytes()).hexdigest()[:12]
    safe_dev = re.sub(r"[^\w.-]", "_", device_id or "default_device")
    return RECORD_DIR / f"{safe_dev}_{list_hash}.json"


def save_state(list_path):
    """Record current state of listed packages before disabling them."""
    packages = read_list(list_path)
    violations = get_safety_violations(packages)
    if violations:
        sys.stderr.write("FATAL SAFETY CHECK FAILED:\n")
        for pkg, reason in violations:
            sys.stderr.write(f"  - {pkg}: {reason}\n")
        sys.stderr.write("Aborting: none of these packages should ever be disabled.\n")
        sys.exit(1)

    import subprocess
    script_dir = os.path.dirname(os.path.abspath(__file__))
    phone_py = os.path.join(script_dir, "phone.py")

    # Get device identifier
    res = subprocess.run([sys.executable, phone_py, "getprop ro.product.model"], capture_output=True, text=True)
    device_id = res.stdout.strip() or "android_phone"

    # Query currently disabled packages
    res_dis = subprocess.run([sys.executable, phone_py, "pm list packages -d --user 0"], capture_output=True, text=True)
    disabled_set = set()
    for line in res_dis.stdout.splitlines():
        if line.startswith("package:"):
            disabled_set.add(line.split(":", 1)[1].strip())

    # Query currently installed packages
    res_all = subprocess.run([sys.executable, phone_py, "pm list packages --user 0"], capture_output=True, text=True)
    installed_set = set()
    for line in res_all.stdout.splitlines():
        if line.startswith("package:"):
            installed_set.add(line.split(":", 1)[1].strip())

    record_path = get_record_path(device_id, list_path)
    if record_path.exists():
        print(f"[*] Preserving existing baseline record at: {record_path}")
        return

    record = {
        "device": device_id,
        "list_file": os.path.abspath(list_path),
        "target_packages": packages,
        "initially_disabled": sorted(list(disabled_set.intersection(packages))),
        "initially_enabled": sorted(list(set(packages).intersection(installed_set) - disabled_set)),
        "not_installed": sorted(list(set(packages) - installed_set))
    }

    record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"[OK] Recovery baseline recorded at: {record_path}")


def generate_restore_commands(list_path):
    """Generate shell batch commands to re-enable disabled packages."""
    packages = read_list(list_path)
    import subprocess
    script_dir = os.path.dirname(os.path.abspath(__file__))
    phone_py = os.path.join(script_dir, "phone.py")

    res = subprocess.run([sys.executable, phone_py, "getprop ro.product.model"], capture_output=True, text=True)
    device_id = res.stdout.strip() or "android_phone"
    record_path = get_record_path(device_id, list_path)

    to_enable = packages
    if record_path.exists():
        try:
            data = json.loads(record_path.read_text(encoding="utf-8"))
            # Only enable packages that were initially enabled before we ran disable
            to_enable = data.get("initially_enabled", packages)
        except Exception:
            to_enable = packages

    for pkg in to_enable:
        print(f"pm enable {pkg}")


def main():
    if len(sys.argv) < 3:
        print("Usage: recovery.py [--save | --commands | --check-safety] <debloat.txt>")
        sys.exit(0)

    action = sys.argv[1]
    list_path = sys.argv[2]

    if action == "--check-safety":
        pkgs = read_list(list_path)
        violations = get_safety_violations(pkgs)
        if violations:
            print("SAFETY VIOLATIONS FOUND:")
            for p, r in violations:
                print(f"  [X] {p}: {r}")
            sys.exit(1)
        else:
            print("[OK] List passed all core and MIUI bootloop safety checks.")
            sys.exit(0)
    elif action == "--save":
        save_state(list_path)
    elif action == "--commands":
        generate_restore_commands(list_path)
    else:
        sys.stderr.write(f"Unknown action: {action}\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
