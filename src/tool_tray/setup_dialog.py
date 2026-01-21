from tool_tray.config import decode_config, save_config


def show_setup_dialog() -> bool:
    """Show CLI setup prompt for pasting config code.

    Returns:
        True if config was saved successfully, False if cancelled
    """
    print()
    print("Tool Tray Setup")
    print("-" * 40)
    print("Paste your configuration code (or 'q' to quit):")
    print()

    try:
        code = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return False

    if not code or code.lower() == "q":
        return False

    try:
        config = decode_config(code)
        save_config(config)
        print()
        print("Configuration saved!")
        return True
    except ValueError as e:
        print()
        print(f"Error: {e}")
        return False
