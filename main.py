"""Entry point for the Pods application."""

import tkinter as tk
from src.app import PodsApp


def main():
    """Initialize and run the Pods application."""
    root = tk.Tk()
    app = PodsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
