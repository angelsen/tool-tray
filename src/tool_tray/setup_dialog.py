import tkinter as tk
from tkinter import messagebox, ttk

from tool_tray.config import decode_config, save_config


def show_setup_dialog() -> bool:
    """Show setup dialog for pasting config code.

    Returns:
        True if config was saved successfully, False if cancelled
    """
    result = {"success": False}

    root = tk.Tk()
    root.title("Tool Tray Setup")
    root.resizable(False, False)

    # Center window
    width, height = 450, 200
    x = (root.winfo_screenwidth() - width) // 2
    y = (root.winfo_screenheight() - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

    # Main frame with padding
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    # Instructions
    label = ttk.Label(
        frame,
        text="Paste the configuration code from Teams/SharePoint:",
        wraplength=400,
    )
    label.pack(anchor="w", pady=(0, 10))

    # Text entry
    entry = ttk.Entry(frame, width=50)
    entry.pack(fill="x", pady=(0, 10))
    entry.focus_set()

    # Status label
    status_var = tk.StringVar()
    status_label = ttk.Label(frame, textvariable=status_var, foreground="gray")
    status_label.pack(anchor="w", pady=(0, 10))

    def validate_and_save() -> None:
        code = entry.get().strip()
        if not code:
            status_var.set("Please paste a config code")
            status_label.config(foreground="red")
            return

        try:
            config = decode_config(code)
            save_config(config)
            result["success"] = True
            root.destroy()
        except ValueError as e:
            status_var.set(str(e))
            status_label.config(foreground="red")

    def on_cancel() -> None:
        root.destroy()

    # Buttons
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill="x", pady=(10, 0))

    cancel_btn = ttk.Button(btn_frame, text="Cancel", command=on_cancel)
    cancel_btn.pack(side="right", padx=(5, 0))

    ok_btn = ttk.Button(btn_frame, text="OK", command=validate_and_save)
    ok_btn.pack(side="right")

    # Bind Enter key
    entry.bind("<Return>", lambda e: validate_and_save())

    # Handle window close
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    root.mainloop()
    return result["success"]


def show_setup_success() -> None:
    """Show success message after setup."""
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "Setup Complete",
        "Configuration saved successfully!\n\nTool Tray is now ready to use.",
    )
    root.destroy()


def show_setup_error(message: str) -> None:
    """Show error message."""
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Setup Error", message)
    root.destroy()
