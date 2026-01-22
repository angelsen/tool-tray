import tkinter as tk
from tkinter import ttk

from tool_tray.config import decode_config, save_config


def show_setup_dialog() -> bool:
    """Show GUI setup dialog for pasting config code.

    Returns:
        True if config was saved successfully, False if cancelled
    """
    result = {"saved": False}

    root = tk.Tk()
    root.title("Tool Tray Setup")
    root.resizable(False, False)

    # Center window on screen
    window_width = 400
    window_height = 180
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Main frame with padding
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # Label
    label = ttk.Label(frame, text="Paste configuration code:")
    label.pack(anchor=tk.W)

    # Entry field
    code_var = tk.StringVar()
    entry = ttk.Entry(frame, textvariable=code_var, width=50)
    entry.pack(fill=tk.X, pady=(5, 15))
    entry.focus_set()

    # Error label (hidden initially)
    error_var = tk.StringVar()
    error_label = ttk.Label(frame, textvariable=error_var, foreground="red")
    error_label.pack(anchor=tk.W)

    def on_ok(event: tk.Event | None = None) -> None:
        code = code_var.get().strip()
        if not code:
            error_var.set("Please enter a configuration code")
            return

        try:
            config = decode_config(code)
            save_config(config)
            result["saved"] = True
            root.destroy()
        except ValueError as e:
            error_var.set(str(e))

    def on_cancel() -> None:
        root.destroy()

    # Button frame
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill=tk.X, pady=(10, 0))

    cancel_btn = ttk.Button(btn_frame, text="Cancel", command=on_cancel)
    cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))

    ok_btn = ttk.Button(btn_frame, text="OK", command=on_ok)
    ok_btn.pack(side=tk.RIGHT)

    # Bind Enter key to OK
    root.bind("<Return>", on_ok)
    root.bind("<Escape>", lambda e: on_cancel())

    # Handle window close button
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    root.mainloop()

    return result["saved"]
