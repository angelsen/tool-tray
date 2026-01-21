import subprocess
import sys
from pathlib import Path


def _get_tooltray_path() -> str:
    """Get the path to tooltray executable."""
    try:
        result = subprocess.run(
            ["uv", "tool", "list", "--show-paths"],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            if line.startswith("- tooltray ") or line.startswith("- tool-tray "):
                start = line.find("(")
                end = line.find(")")
                if start != -1 and end != -1:
                    return line[start + 1 : end]
    except subprocess.CalledProcessError:
        pass
    # Fallback to assuming it's in PATH
    return "tooltray"


def _linux_autostart_enable() -> bool:
    """Add tooltray to Linux autostart."""
    desktop_file = Path.home() / ".config/autostart/tooltray.desktop"
    desktop_file.parent.mkdir(parents=True, exist_ok=True)
    exe = _get_tooltray_path()
    desktop_file.write_text(f"""[Desktop Entry]
Type=Application
Name=Tool Tray
Comment=System tray tool manager
Exec={exe}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
""")
    print(f"Autostart enabled: {desktop_file}")
    return True


def _linux_autostart_disable() -> bool:
    """Remove tooltray from Linux autostart."""
    desktop_file = Path.home() / ".config/autostart/tooltray.desktop"
    if desktop_file.exists():
        desktop_file.unlink()
        print(f"Autostart disabled: {desktop_file}")
        return True
    print("Autostart was not enabled")
    return False


def _macos_autostart_enable() -> bool:
    """Add tooltray to macOS autostart via LaunchAgent."""
    plist = Path.home() / "Library/LaunchAgents/com.tooltray.plist"
    plist.parent.mkdir(parents=True, exist_ok=True)
    exe = _get_tooltray_path()
    plist.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tooltray</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>""")
    subprocess.run(["launchctl", "load", str(plist)], check=False)
    print(f"Autostart enabled: {plist}")
    return True


def _macos_autostart_disable() -> bool:
    """Remove tooltray from macOS autostart."""
    plist = Path.home() / "Library/LaunchAgents/com.tooltray.plist"
    if plist.exists():
        subprocess.run(["launchctl", "unload", str(plist)], check=False)
        plist.unlink()
        print(f"Autostart disabled: {plist}")
        return True
    print("Autostart was not enabled")
    return False


def _windows_autostart_enable() -> bool:
    """Add tooltray to Windows autostart via registry."""
    try:
        import winreg
    except ImportError:
        print("winreg not available (not Windows)")
        return False

    exe = _get_tooltray_path()
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, "ToolTray", 0, winreg.REG_SZ, exe)
        winreg.CloseKey(key)
        print("Autostart enabled via registry")
        return True
    except OSError as e:
        print(f"Failed to enable autostart: {e}")
        return False


def _windows_autostart_disable() -> bool:
    """Remove tooltray from Windows autostart."""
    try:
        import winreg
    except ImportError:
        print("winreg not available (not Windows)")
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, "ToolTray")
        winreg.CloseKey(key)
        print("Autostart disabled")
        return True
    except FileNotFoundError:
        print("Autostart was not enabled")
        return False
    except OSError as e:
        print(f"Failed to disable autostart: {e}")
        return False


def enable_autostart() -> bool:
    """Add tooltray to system autostart."""
    if sys.platform == "darwin":
        return _macos_autostart_enable()
    elif sys.platform == "win32":
        return _windows_autostart_enable()
    else:
        return _linux_autostart_enable()


def disable_autostart() -> bool:
    """Remove tooltray from system autostart."""
    if sys.platform == "darwin":
        return _macos_autostart_disable()
    elif sys.platform == "win32":
        return _windows_autostart_disable()
    else:
        return _linux_autostart_disable()


def is_autostart_enabled() -> bool:
    """Check if autostart is currently enabled."""
    if sys.platform == "darwin":
        plist = Path.home() / "Library/LaunchAgents/com.tooltray.plist"
        return plist.exists()
    elif sys.platform == "win32":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ,
            )
            winreg.QueryValueEx(key, "ToolTray")
            winreg.CloseKey(key)
            return True
        except (ImportError, FileNotFoundError, OSError):
            return False
    else:
        desktop_file = Path.home() / ".config/autostart/tooltray.desktop"
        return desktop_file.exists()
