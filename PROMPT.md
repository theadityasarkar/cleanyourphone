# The Assistant Prompt for CleanYourPhone

Paste this prompt into your coding assistant (Antigravity CLI, Claude Code, Gemini CLI, Codex, etc.) on a computer connected to your phone via USB cable (with USB debugging turned on).

---

```markdown
I want to debloat and optimize my Android phone using CleanYourPhone over USB debugging.
My phone model is: POCO M4 5G (6GB RAM / 128GB Storage, Model 22041219I/G, MediaTek Dimensity 700).

Work on the real device step by step, and verify everything you do. Ask me before anything that touches optional apps or preferences.

1. Connect & Verify
- Check if `adb` is available. If not, run `tools/get-platform-tools.ps1` (or `tools/get-platform-tools.sh`).
- Run `python tools/phone.py --probe` to verify the phone connection, battery level, Android/MIUI version, and RAM/storage specifications.
- Tell me when the "Allow USB debugging?" RSA confirmation dialog will appear on my phone screen so I can tap "Always allow" and "OK".
- If multiple devices or emulators are connected, identify the POCO M4 5G serial number and set PHONE_SERIAL.

2. Safety Check & Backup First
- Before touching or disabling any package on the phone, execute:
  `python tools/phone.py --backup backup/`
  to save the complete list of installed packages, disabled packages, getprop outputs, and system settings.
- Run `python tools/recovery.py --check-safety examples/poco-m4-5g/debloat-safe.txt` to confirm no bootloop or critical system package is touched.
- Never touch: `com.miui.securitycenter`, `com.miui.securityadd`, `com.android.phone`, `com.android.systemui`, `com.android.settings`, `com.mi.android.globallauncher`, `com.google.android.gms`, or `com.android.vending`.
- Run `python tools/recovery.py --save examples/poco-m4-5g/debloat-safe.txt` to create the recovery baseline record before applying changes.

3. Debloat (Safe List)
- Apply the safe debloat list using:
  `tools/disable.ps1 examples/poco-m4-5g/debloat-safe.txt` (on Windows) or
  `./tools/disable.sh examples/poco-m4-5g/debloat-safe.txt` (on Linux/macOS).
- Packages must only be disabled for user 0 (`pm disable-user --user 0`), NEVER permanently uninstalled (`pm uninstall`).
- Disable in structured batches:
  Batch A: Telemetry, MSA (MIUI System Ads), Analytics, Daemon, Joyose.
  Batch B: Wallpaper Carousel / Glance, Quick Apps, YellowPages.
  Batch C: Bloat apps (Mi Browser, Mi Video, Mi Music, GetApps/Mi Picks, Clean Master, ShareMe).
  Batch D: Facebook system background services & partner bloatware.

4. Optional Customization (Ask First)
- Ask me with a checklist question whether I want to disable any optional apps from `examples/poco-m4-5g/debloat-optional.txt`:
  * Xiaomi Cloud Sync (if I only use Google Drive/Google Photos)
  * Mi Notes / Mi Sound Recorder / Mi Calculator
  * Google preloads (Google Meet/Duo, Google TV, YouTube Music, Digital Wellbeing)
- Only disable the items I explicitly confirm.

5. Optimization & Verification
- Check the remaining bloat status with `python tools/check.py examples/poco-m4-5g/debloat-safe.txt`.
- Take a screenshot with `python tools/phone.py --screenshot screen_after_debloat.png` to verify the phone remains responsive and healthy.
- Run `python tools/phone.py "sync"` to flush disk caches.
- Provide a summary of how much RAM was freed, and remind me of the one-line restore command (`tools/restore.ps1 examples/poco-m4-5g/debloat-safe.txt`).
```
