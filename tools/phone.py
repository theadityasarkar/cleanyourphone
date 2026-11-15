#!/usr/bin/env python3
"""ADB client and device inspector for Android Phones (over USB or Wi-Fi).

Works with native `adb` (in PATH or in tools/platform-tools/) or pure-Python `adb_shell`.
Default connection is USB debugging (plug phone into computer).
Set PHONE_HOST to phone's IP:port for Wireless ADB.
Set PHONE_SERIAL to target a specific device when multiple are connected.

Usage:
    python phone.py --probe
    python phone.py --backup <output_dir>
    python phone.py --screenshot <out.png>
    python phone.py --batch < commands.txt
    python phone.py --reboot
    python phone.py <shell command...>
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

USAGE = """usage:
    python phone.py --probe
    python phone.py --backup <output_dir>
    python phone.py --screenshot <out.png>
    python phone.py --batch < commands.txt
    python phone.py --reboot
    python phone.py --help
    python phone.py <shell command...>
"""

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
LOCAL_PLATFORM_TOOLS = os.path.join(SCRIPT_DIR, "platform-tools")


def find_adb_binary():
    """Locate the best available adb executable."""
    env_bin = os.environ.get("PHONE_ADB_BINARY") or os.environ.get("ADB_BINARY")
    if env_bin and os.path.isfile(env_bin):
        return env_bin

    # Check local platform-tools folder
    exe_name = "adb.exe" if os.name == "nt" else "adb"
    local_adb = os.path.join(LOCAL_PLATFORM_TOOLS, exe_name)
    if os.path.isfile(local_adb):
        return local_adb

    # Check system PATH
    system_adb = shutil.which("adb")
    if system_adb:
        return system_adb

    return None


ADB_BIN = find_adb_binary()
PHONE_HOST = os.environ.get("PHONE_HOST")
PHONE_SERIAL = os.environ.get("PHONE_SERIAL")


def build_adb_prefix():
    """Build the command prefix for adb calls."""
    if not ADB_BIN:
        return None
    cmd = [ADB_BIN]
    if PHONE_HOST:
        cmd.extend(["-s", PHONE_HOST])
    elif PHONE_SERIAL:
        cmd.extend(["-s", PHONE_SERIAL])
    return cmd


def ensure_device_connected():
    """Verify an ADB connection is available."""
    if not ADB_BIN:
        sys.stderr.write(
            "Error: ADB binary not found.\n"
            "Please run: powershell tools/get-platform-tools.ps1 (on Windows)\n"
            "         or bash tools/get-platform-tools.sh (on Linux/macOS)\n"
            "or ensure 'adb' is available in your PATH.\n"
        )
        sys.exit(2)

    # Check device list
    try:
        res = subprocess.run([ADB_BIN, "devices"], capture_output=True, text=True, check=True)
    except Exception as e:
        sys.stderr.write(f"Error starting adb: {e}\n")
        sys.exit(2)

    lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
    # Filter header
    devices = [l for l in lines[1:] if not l.startswith("* daemon")]
    
    if not devices:
        sys.stderr.write(
            "Error: No Android device detected via USB debugging.\n\n"
            "Checklist:\n"
            "1. Connect your phone via USB cable to this PC.\n"
            "2. Make sure Developer Options is unlocked (Settings > About phone > tap OS/MIUI version 7 times).\n"
            "3. Enable 'USB debugging' in Developer options.\n"
            "4. Check phone screen and accept 'Allow USB debugging?' RSA prompt.\n"
        )
        sys.exit(2)

    unauthorized = [d for d in devices if "unauthorized" in d]
    if unauthorized:
        sys.stderr.write(
            "Error: Device connected but 'unauthorized'.\n"
            "Please check your phone's screen and tap 'Allow USB debugging' / 'Always allow from this computer'.\n"
        )
        sys.exit(2)


def run_shell(cmd_str):
    """Run an adb shell command and return stdout."""
    prefix = build_adb_prefix()
    if not prefix:
        sys.stderr.write("ADB not configured.\n")
        sys.exit(2)
    full_cmd = prefix + ["shell", cmd_str]
    try:
        proc = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        return 1, "", str(e)


def cmd_probe():
    """Query and display device specifications."""
    ensure_device_connected()
    code, props_out, _ = run_shell("getprop")
    props = {}
    for line in props_out.splitlines():
        m = re.match(r"^\[(.*?)\]:\s*\[(.*?)\]", line.strip())
        if m:
            props[m.group(1)] = m.group(2)

    model = props.get("ro.product.model", "Unknown")
    brand = props.get("ro.product.brand", "Unknown")
    device = props.get("ro.product.device", "Unknown")
    marketname = props.get("ro.product.marketname", model)
    android_ver = props.get("ro.build.version.release", "Unknown")
    sdk = props.get("ro.build.version.sdk", "Unknown")
    miui_ver = props.get("ro.miui.ui.version.name", "")
    hyperos_ver = props.get("ro.mi.os.version.name", "")
    os_name = f"HyperOS ({hyperos_ver})" if hyperos_ver else (f"MIUI ({miui_ver})" if miui_ver else "Android")
    build_id = props.get("ro.build.display.id", props.get("ro.build.id", "Unknown"))
    soc = props.get("ro.soc.model", props.get("ro.board.platform", "Unknown"))

    # Memory / Storage
    _, meminfo, _ = run_shell("cat /proc/meminfo")
    total_ram_kb = 0
    for line in meminfo.splitlines():
        if line.startswith("MemTotal:"):
            parts = line.split()
            if len(parts) >= 2:
                total_ram_kb = int(parts[1])
            break
    ram_gb = round(total_ram_kb / (1024 * 1024), 1)

    # Battery
    _, battery_out, _ = run_shell("dumpsys battery")
    bat_level = "Unknown"
    bat_temp = "Unknown"
    for line in battery_out.splitlines():
        line = line.strip()
        if line.startswith("level:"):
            bat_level = f"{line.split(':')[1].strip()}%"
        elif line.startswith("temperature:"):
            t = float(line.split(':')[1].strip()) / 10.0
            bat_temp = f"{t}°C"

    # Display refresh rate
    _, display_out, _ = run_shell("dumpsys display | grep -E 'mBaseDisplayInfo|fps'")
    fps_match = re.search(r"(\d+(\.\d+)?)\s*fps", display_out)
    refresh_rate = f"{fps_match.group(1)} Hz" if fps_match else "Unknown"

    # Packages count
    _, pkgs_all, _ = run_shell("pm list packages --user 0")
    _, pkgs_dis, _ = run_shell("pm list packages -d --user 0")
    all_count = len([p for p in pkgs_all.splitlines() if p.startswith("package:")])
    dis_count = len([p for p in pkgs_dis.splitlines() if p.startswith("package:")])

    print("=" * 60)
    print(f" DEVICE PROBE: {brand.upper()} {marketname}")
    print("=" * 60)
    print(f" Brand / Model:    {brand} {model} (Codename: {device})")
    print(f" Marketing Name:   {marketname}")
    print(f" Chipset / Platform:{soc}")
    print(f" OS / Firmware:    {os_name} (Build: {build_id})")
    print(f" Android Version:  Android {android_ver} (API level {sdk})")
    print(f" Total RAM:        ~{ram_gb} GB ({'6GB Variant' if 5 <= ram_gb <= 6.5 else f'{ram_gb}GB'})")
    print(f" Battery Status:   {bat_level} (Temp: {bat_temp})")
    print(f" Screen Refresh:   {refresh_rate}")
    print(f" Installed Packages: {all_count} total ({dis_count} currently disabled)")
    print("=" * 60)


def cmd_backup(output_dir):
    """Save full package lists, getprop, and system settings to a directory."""
    ensure_device_connected()
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Starting backup to: {output_dir}")

    files = [
        ("packages_all.txt", "pm list packages -f --user 0"),
        ("packages_disabled.txt", "pm list packages -d --user 0"),
        ("packages_enabled.txt", "pm list packages -e --user 0"),
        ("packages_third_party.txt", "pm list packages -3 --user 0"),
        ("packages_system.txt", "pm list packages -s --user 0"),
        ("getprop.txt", "getprop"),
        ("settings_system.txt", "settings list system"),
        ("settings_secure.txt", "settings list secure"),
        ("settings_global.txt", "settings list global")
    ]

    for fname, shell_cmd in files:
        target_path = os.path.join(output_dir, fname)
        code, out, err = run_shell(shell_cmd)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"  [+] Saved {fname}")

    print(f"[OK] Backup completed successfully in {output_dir}\n")


def cmd_screenshot(out_png):
    """Capture a screenshot from phone and pull it locally."""
    ensure_device_connected()
    remote_tmp = "/sdcard/cyp_screen.png"
    print(f"[*] Capturing screenshot to {out_png}...")
    run_shell(f"screencap -p {remote_tmp}")
    prefix = build_adb_prefix()
    subprocess.run(prefix + ["pull", remote_tmp, out_png], capture_output=True, check=True)
    run_shell(f"rm -f {remote_tmp}")
    print(f"[OK] Screenshot saved to {out_png}")


def cmd_batch():
    """Read shell commands from stdin and execute them."""
    ensure_device_connected()
    for line in sys.stdin:
        cmd = line.strip()
        if not cmd or cmd.startswith("#"):
            continue
        code, out, err = run_shell(cmd)
        if out.strip():
            print(out.strip())
        if err.strip():
            sys.stderr.write(err.strip() + "\n")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(USAGE.strip())
        sys.exit(0)

    arg = sys.argv[1]
    if arg == "--probe":
        cmd_probe()
    elif arg == "--backup":
        if len(sys.argv) < 3:
            sys.stderr.write("Error: --backup requires an output directory path.\n")
            sys.exit(2)
        cmd_backup(sys.argv[2])
    elif arg == "--screenshot":
        if len(sys.argv) < 3:
            sys.stderr.write("Error: --screenshot requires an output PNG path.\n")
            sys.exit(2)
        cmd_screenshot(sys.argv[2])
    elif arg == "--batch":
        cmd_batch()
    elif arg == "--reboot":
        ensure_device_connected()
        print("[*] Rebooting device...")
        run_shell("reboot")
        print("[OK] Reboot signal sent.")
    else:
        # Run single command
        cmd_str = " ".join(sys.argv[1:])
        code, out, err = run_shell(cmd_str)
        if out:
            sys.stdout.write(out)
        if err:
            sys.stderr.write(err)
        sys.exit(code)


if __name__ == "__main__":
    main()
