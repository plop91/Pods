"""Search functionality for finding pods by name."""

import tkinter as tk
from tkinter import ttk
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..pod import Pod


class SearchManager:
    """Manages search dialog and pod search functionality."""

    def __init__(self, app):
        """Initialize search manager with reference to main app."""
        self.app = app
        self.search_dialog = None
        self.search_results: List[Tuple['Pod', str]] = []  # List of (pod, path_string) tuples
        self.search_result_index = 0

    def open_search_dialog(self):
        """Open the search dialog to find pods."""
        # If dialog already exists, just focus it
        if self.search_dialog and self.search_dialog.winfo_exists():
            self.search_dialog.focus()
            return

        # Create search dialog
        self.search_dialog = tk.Toplevel(self.app.root)
        self.search_dialog.title("Search Pods")
        self.search_dialog.geometry("450x400")
        self.search_dialog.transient(self.app.root)

        # Position near top-right of main window
        self.search_dialog.update_idletasks()
        x = self.app.root.winfo_x() + self.app.root.winfo_width() - 470
        y = self.app.root.winfo_y() + 50
        self.search_dialog.geometry(f"+{x}+{y}")

        # Search entry frame
        search_frame = tk.Frame(self.search_dialog)
        search_frame.pack(padx=10, pady=10, fill=tk.X)

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = tk.Entry(search_frame, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        search_entry.focus()

        # Search in current container or all toggle
        search_scope_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(search_frame, text="All", variable=search_scope_var,
                       command=lambda: self.perform_search(search_entry.get(), search_scope_var.get(), results_listbox, count_label)).pack(side=tk.LEFT)

        # Results count label
        count_label = tk.Label(self.search_dialog, text="0 results", fg="#666")
        count_label.pack(padx=10, pady=(0, 5))

        # Results listbox with scrollbar
        results_frame = tk.Frame(self.search_dialog)
        results_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        results_listbox = tk.Listbox(results_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=results_listbox.yview)

        # Bind search entry to perform search as user types
        def on_search_change(*args):
            self.perform_search(search_entry.get(), search_scope_var.get(), results_listbox, count_label)

        search_entry.bind("<KeyRelease>", on_search_change)

        # Bind double-click and Enter to navigate to result
        def on_result_select(event=None):
            selection = results_listbox.curselection()
            if selection and self.search_results:
                idx = selection[0]
                self.navigate_to_search_result(idx)

        results_listbox.bind("<Double-Button-1>", on_result_select)
        results_listbox.bind("<Return>", on_result_select)

        # Navigation buttons
        button_frame = tk.Frame(self.search_dialog)
        button_frame.pack(padx=10, pady=10, fill=tk.X)

        def go_previous():
            if self.search_results:
                self.search_result_index = (self.search_result_index - 1) % len(self.search_results)
                results_listbox.selection_clear(0, tk.END)
                results_listbox.selection_set(self.search_result_index)
                results_listbox.see(self.search_result_index)
                self.navigate_to_search_result(self.search_result_index)

        def go_next():
            if self.search_results:
                self.search_result_index = (self.search_result_index + 1) % len(self.search_results)
                results_listbox.selection_clear(0, tk.END)
                results_listbox.selection_set(self.search_result_index)
                results_listbox.see(self.search_result_index)
                self.navigate_to_search_result(self.search_result_index)

        ttk.Button(button_frame, text="Previous", command=go_previous).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Next", command=go_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.search_dialog.destroy).pack(side=tk.RIGHT, padx=5)

        # Bind Escape to close
        self.search_dialog.bind("<Escape>", lambda e: self.search_dialog.destroy())

        # Perform initial search if there's any text
        if search_entry.get():
            self.perform_search(search_entry.get(), search_scope_var.get(), results_listbox, count_label)

    def perform_search(self, query: str, search_all: bool, results_listbox: tk.Listbox, count_label: tk.Label):
        """Perform search and update results listbox."""
        from ..pod import Pod

        results_listbox.delete(0, tk.END)
        self.search_results.clear()
        self.search_result_index = 0

        if not query:
            count_label.config(text="0 results")
            return

        # Convert query to lowercase for case-insensitive search
        query_lower = query.lower()

        # Determine search root
        search_root = self.app.main_pod if search_all else self.app.current_container

        # Recursively search for matching pods
        def search_pods(pod: Pod, path: str = ""):
            current_path = f"{path}/{pod.name}" if path else pod.name

            # Check if this pod matches
            if query_lower in pod.name.lower():
                # Don't include the search root itself in results
                if pod != search_root:
                    self.search_results.append((pod, current_path))

            # Search children
            for child in pod.children:
                search_pods(child, current_path)

        # Perform search
        search_pods(search_root)

        # Populate results listbox
        for pod, path in self.search_results:
            results_listbox.insert(tk.END, path)

        # Update count label
        count = len(self.search_results)
        count_label.config(text=f"{count} result{'s' if count != 1 else ''}")

        # Auto-select first result
        if self.search_results:
            results_listbox.selection_set(0)

    def navigate_to_search_result(self, index: int):
        """Navigate to a search result and select the pod."""
        if not self.search_results or index >= len(self.search_results):
            return

        target_pod, path = self.search_results[index]

        # Build navigation path to the pod
        nav_path = []
        current = target_pod.parent
        while current and current != self.app.main_pod:
            nav_path.insert(0, current)
            current = current.parent

        # Navigate to the pod's container
        if target_pod.parent:
            # Clear current navigation history
            self.app.navigation_history.clear()

            # Build new navigation history
            current = self.app.main_pod
            for container in nav_path:
                self.app.navigation_history.append(current)
                current = container

            if nav_path:
                self.app.current_container = nav_path[-1]
            else:
                # Pod is directly in main
                self.app.current_container = self.app.main_pod

            # Update UI
            self.app.nav_label.config(text=f"Current: {self.app.current_container.name}")
            self.app.back_button.config(state=tk.NORMAL if self.app.navigation_history else tk.DISABLED)

            # Clear all selections
            for p in self.app.selected_pods:
                p.selected = False
            self.app.selected_pods.clear()

            # Select the target pod
            target_pod.selected = True
            self.app.selected_pod = target_pod
            self.app.selected_pods = [target_pod]

            # Reset view
            self.app.pan_offset_x = 0
            self.app.pan_offset_y = 0

            self.app.render()
