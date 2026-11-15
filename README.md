# CleanYourPhone

> **Your phone, minus the ads, bloatware, and background tracking.**
> Strip out telemetry, sponsored push ads, and junk background services from any Android phone over USB debugging.
> **No root · No unlocked bootloader · Nothing permanently uninstalled · 100% reversible with a single command.**

---

## ⚡ Quick Start: Clean Your Phone with Antigravity / AI Assistant

You can let **Antigravity** (or any AI coding assistant with terminal access) do the entire job safely for you:

### 1. Enable USB Debugging on Your Phone
* Go to **Settings → About phone**.
* Tap **MIUI / OS / Build version** 7 times until you see *"You are now a developer!"*.
* Go to **Settings → Additional settings (or System) → Developer options** and turn ON **USB debugging**.
* Connect your phone to your computer via USB cable.
* Check your phone screen, tick *"Always allow from this computer"*, and tap **OK**.

### 2. Clone and Open in Antigravity
```bash
git clone https://github.com/theadityasarkar/cleanyourphone.git
cd cleanyourphone
```

### 3. Prompt Your Assistant
Copy and paste this into Antigravity:

```text
I want to debloat and optimize my phone using CleanYourPhone.
My phone model is: POCO M4 5G (6GB RAM / 128GB Storage).
Follow PROMPT.md step by step, verify device connection, run a backup first, check safety guards, and guide me through the cleanup.
```
*(If you have a different phone model, simply replace `POCO M4 5G` with your device name).*

Your assistant will probe your device, back up all settings and packages, check safety guards, disable the bloat in batches, and verify everything with screenshots.

---

## 🛠️ Doing It by Hand (Manual CLI)

If you prefer to run the commands yourself:

### 1. Check Connection & Device Specs
```powershell
# Windows
python tools\phone.py --probe

# Linux / macOS
python3 tools/phone.py --probe
```
*Note: If you don't have ADB installed, running `powershell tools\get-platform-tools.ps1` (or `bash tools/get-platform-tools.sh`) will automatically download the official Google Android platform tools.*

### 2. Backup Device State
```powershell
python tools\phone.py --backup backup\
```

### 3. Run the Safe Debloat
```powershell
# Windows (PowerShell)
.\tools\disable.ps1 examples\poco-m4-5g\debloat-safe.txt

# Linux / macOS (Bash)
./tools/disable.sh examples/poco-m4-5g/debloat-safe.txt
```

### 4. Check Status & Re-Apply After Firmware Updates
```powershell
# Audit remaining bloat
python tools\check.py examples\poco-m4-5g\debloat-safe.txt

# Automatically re-disable bloat restored by an OTA update
python tools\check.py --fix examples\poco-m4-5g\debloat-safe.txt
```

### 5. Restore / Undo Everything
```powershell
# Windows
.\tools\restore.ps1 examples\poco-m4-5g\debloat-safe.txt

# Linux / macOS
./tools/restore.sh examples/poco-m4-5g/debloat-safe.txt
```

---

## 📱 Specific Profile: POCO M4 5G (6GB RAM / 128GB Storage)

The included profile in `examples/poco-m4-5g/` is specifically tuned for the **POCO M4 5G** (Model `22041219I` / `22041219G`, Codename `light`, MediaTek Dimensity 700):

| Category | Packages Disabled | Benefit |
|---|---|---|
| **System Ads & Telemetry** | `com.miui.msa.global`, `com.miui.analytics`, `com.miui.daemon`, `com.miui.miservice` | Stops sponsored banner ads, recommendation popups, and battery-draining telemetry daemons. |
| **Performance Governor** | `com.xiaomi.joyose` | Eliminates artificial thermal and gaming throttling, preventing frame drops and UI stutters. |
| **Lock Screen Adware** | `com.miui.android.fashiongallery` (Glance / Carousel) | Removes sponsored lock screen stories and saves background data. |
| **Redundant Stores & Apps** | `com.xiaomi.mipicks` (GetApps), `com.mi.globalbrowser`, `com.miui.videoplayer`, `com.miui.player`, `com.miui.cleanmaster` | Frees up background memory and removes spam push notifications. |
| **Partner Trackers** | `com.facebook.appmanager`, `com.facebook.services`, `com.facebook.system`, `com.netflix.partner.activation` | Removes preloaded third-party background services. |

### 🚀 Performance Gains on 6GB / 128GB:
* **~1.5GB to 2.0GB Free RAM:** Idle RAM usage drops from ~3.8GB down to ~1.8GB, leaving **~4.0GB+ of real physical RAM free** for smooth multitasking.
* **Turn OFF Virtual RAM (Memory Extension):** On POCO M4 5G, go to **Settings → Additional settings → Memory extension** and set it to **OFF**. Virtual RAM uses slow flash storage (UFS 2.2) as swap, introducing micro-stutters and unnecessary flash wear. With real RAM freed up by CleanYourPhone, virtual swap is unnecessary.
* **Smooth 90Hz Display:** Set **Settings → Display → Refresh rate** to **90Hz** for a stutter-free visual experience.

---

## 🛡️ Safety Guards & Bootloop Protection

CleanYourPhone includes built-in safety validation rules in `tools/recovery.py` and `tools/disable.ps1`:

> [!CAUTION]
> **Bootloop Prevention:** Disabling `com.miui.securitycenter` or `com.miui.securityadd` on MIUI/HyperOS will cause an immediate bootloop into recovery mode! CleanYourPhone's safety guard automatically blocks these packages.
> 
> Core Android telephony (`com.android.phone`), system interface (`com.android.systemui`), default launcher (`com.mi.android.globallauncher`), and Google Play Services (`com.google.android.gms`) are strictly protected.

---

## 📂 Project Structure

```text
cleanyourphone/
├── README.md                          # Full guide and quick start
├── PROMPT.md                          # Prompt for Antigravity / Claude Code / Gemini CLI
├── tools/
│   ├── phone.py                       # Device probe, inspector, batch runner, screenshot grabber
│   ├── recovery.py                    # Safety validator & rollback manager (records initial state)
│   ├── check.py                       # Bloat audit tool & OTA update drift fixer (--fix)
│   ├── disable.ps1 / disable.sh       # Safe debloat script with automatic baseline backup
│   ├── restore.ps1 / restore.sh       # One-line rollback script to re-enable packages
│   ├── get-platform-tools.ps1 / .sh   # Automatic Google ADB platform-tools installer
│   └── requirements.txt               # Optional python dependencies
└── examples/
    └── poco-m4-5g/                    # Dedicated profile for POCO M4 5G (6/128)
        ├── phone.json                 # Device specifications (MT6833, 90Hz, 6GB LPDDR4X)
        ├── debloat-safe.txt           # 100% safe debloat list for MIUI / HyperOS
        ├── debloat-optional.txt       # Optional apps (Mi Cloud, Mi Notes, Google preloads)
        └── README.md                  # Detailed POCO M4 5G optimization walkthrough
```

---

## 🤝 Contributing

Contributions for new phone models (Samsung One UI, OnePlus OxygenOS, Motorola, Realme, Pixel, Vivo) are welcome!
To contribute a new phone profile:
1. Create a new folder under `examples/<brand>-<model>/`.
2. Add `phone.json`, `debloat-safe.txt`, and `README.md`.
3. Submit a pull request!
