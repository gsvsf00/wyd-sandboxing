"""
Dialog Utilities

Provides common dialog functions for the application.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional, Any, Callable, List

class CTkDialog(ctk.CTkToplevel):
    """
    Base dialog class for creating custom dialogs.
    """
    
    def __init__(self, parent, title="Dialog", width=400, height=200):
        """
        Initialize the dialog.
        
        Args:
            parent: Parent widget
            title: Dialog title
            width: Dialog width
            height: Dialog height
        """
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center dialog on parent
        if parent:
            x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
            y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
            self.geometry(f"+{x}+{y}")
        
        # Create content frame
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Handle dialog close
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Result variable
        self.result = None
        
    def on_close(self):
        """Handle dialog close."""
        self.destroy()
        
    def show(self):
        """Show the dialog and wait for it to close."""
        self.wait_window()
        return self.result

def show_info(parent=None, title: str = "Information", message: str = ""):
    """
    Show an information dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Dialog message
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("400x200")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    
    # Center dialog on parent
    if parent:
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 100
        dialog.geometry(f"+{x}+{y}")
    
    # Create content
    frame = ctk.CTkFrame(dialog)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Icon
    icon_label = ctk.CTkLabel(
        frame,
        text="ℹ️",
        font=ctk.CTkFont(size=48)
    )
    icon_label.pack(pady=(10, 5))
    
    # Message
    message_label = ctk.CTkLabel(
        frame,
        text=message,
        font=ctk.CTkFont(size=14),
        wraplength=350
    )
    message_label.pack(pady=10)
    
    # OK button
    ok_button = ctk.CTkButton(
        frame,
        text="OK",
        width=100,
        command=dialog.destroy
    )
    ok_button.pack(pady=10)
    
    # Handle dialog close
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    
    # Wait for dialog to close
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window()

def show_error(parent=None, title: str = "Error", message: str = "An error occurred"):
    """
    Show an error dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Dialog message
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("400x200")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    
    # Center dialog on parent
    if parent:
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 100
        dialog.geometry(f"+{x}+{y}")
    
    # Create content
    frame = ctk.CTkFrame(dialog)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Icon
    icon_label = ctk.CTkLabel(
        frame,
        text="❌",
        font=ctk.CTkFont(size=48),
        text_color=("red", "#F44336")
    )
    icon_label.pack(pady=(10, 5))
    
    # Message
    message_label = ctk.CTkLabel(
        frame,
        text=message,
        font=ctk.CTkFont(size=14),
        wraplength=350
    )
    message_label.pack(pady=10)
    
    # OK button
    ok_button = ctk.CTkButton(
        frame,
        text="OK",
        width=100,
        command=dialog.destroy
    )
    ok_button.pack(pady=10)
    
    # Handle dialog close
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    
    # Wait for dialog to close
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window()

def show_warning(parent=None, title: str = "Warning", message: str = ""):
    """
    Show a warning dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Dialog message
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("400x200")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    
    # Center dialog on parent
    if parent:
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 100
        dialog.geometry(f"+{x}+{y}")
    
    # Create content
    frame = ctk.CTkFrame(dialog)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Icon
    icon_label = ctk.CTkLabel(
        frame,
        text="⚠️",
        font=ctk.CTkFont(size=48),
        text_color=("orange", "#FF9800")
    )
    icon_label.pack(pady=(10, 5))
    
    # Message
    message_label = ctk.CTkLabel(
        frame,
        text=message,
        font=ctk.CTkFont(size=14),
        wraplength=350
    )
    message_label.pack(pady=10)
    
    # OK button
    ok_button = ctk.CTkButton(
        frame,
        text="OK",
        width=100,
        command=dialog.destroy
    )
    ok_button.pack(pady=10)
    
    # Handle dialog close
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    
    # Wait for dialog to close
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window()

def show_question(parent=None, title: str = "Question", message: str = "") -> bool:
    """
    Show a question dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Dialog message
        
    Returns:
        bool: True if user clicked Yes, False otherwise
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("400x200")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    
    # Center dialog on parent
    if parent:
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 100
        dialog.geometry(f"+{x}+{y}")
    
    # Create content
    frame = ctk.CTkFrame(dialog)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Icon
    icon_label = ctk.CTkLabel(
        frame,
        text="❓",
        font=ctk.CTkFont(size=48)
    )
    icon_label.pack(pady=(10, 5))
    
    # Message
    message_label = ctk.CTkLabel(
        frame,
        text=message,
        font=ctk.CTkFont(size=14),
        wraplength=350
    )
    message_label.pack(pady=10)
    
    # Result variable
    result = tk.BooleanVar(value=False)
    
    # Buttons frame
    buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
    buttons_frame.pack(pady=10)
    
    # Yes button
    yes_button = ctk.CTkButton(
        buttons_frame,
        text="Yes",
        width=100,
        command=lambda: [result.set(True), dialog.destroy()]
    )
    yes_button.pack(side="left", padx=10)
    
    # No button
    no_button = ctk.CTkButton(
        buttons_frame,
        text="No",
        width=100,
        command=lambda: [result.set(False), dialog.destroy()]
    )
    no_button.pack(side="left", padx=10)
    
    # Handle dialog close
    dialog.protocol("WM_DELETE_WINDOW", lambda: [result.set(False), dialog.destroy()])
    
    # Wait for dialog to close
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window()
    
    return result.get()

def show_input_dialog(parent=None, title: str = "Input", message: str = "", default_value: str = "") -> Optional[str]:
    """
    Show an input dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Dialog message
        default_value: Default value for the input field
        
    Returns:
        str: User input, or None if canceled
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("400x200")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    
    # Center dialog on parent
    if parent:
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 100
        dialog.geometry(f"+{x}+{y}")
    
    # Create content
    frame = ctk.CTkFrame(dialog)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Message
    message_label = ctk.CTkLabel(
        frame,
        text=message,
        font=ctk.CTkFont(size=14),
        wraplength=350
    )
    message_label.pack(pady=10)
    
    # Input field
    input_var = tk.StringVar(value=default_value)
    input_field = ctk.CTkEntry(
        frame,
        width=300,
        textvariable=input_var
    )
    input_field.pack(pady=10)
    input_field.focus_set()
    
    # Result variable
    result = [None]  # Use list to store result (mutable)
    
    # Buttons frame
    buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
    buttons_frame.pack(pady=10)
    
    # OK button
    ok_button = ctk.CTkButton(
        buttons_frame,
        text="OK",
        width=100,
        command=lambda: [result.__setitem__(0, input_var.get()), dialog.destroy()]
    )
    ok_button.pack(side="left", padx=10)
    
    # Cancel button
    cancel_button = ctk.CTkButton(
        buttons_frame,
        text="Cancel",
        width=100,
        command=dialog.destroy
    )
    cancel_button.pack(side="left", padx=10)
    
    # Handle dialog close
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    
    # Handle Enter key
    input_field.bind("<Return>", lambda event: [result.__setitem__(0, input_var.get()), dialog.destroy()])
    
    # Wait for dialog to close
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window()
    
    return result[0]

def show_options(parent=None, title: str = "Options", message: str = "", options: List[str] = None) -> Optional[str]:
    """
    Show a dialog with multiple options.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Dialog message
        options: List of option strings
        
    Returns:
        str: Selected option, or None if canceled
    """
    if options is None:
        options = []
        
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("400x300")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    
    # Center dialog on parent
    if parent:
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 150
        dialog.geometry(f"+{x}+{y}")
    
    # Create content
    frame = ctk.CTkFrame(dialog)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Message
    message_label = ctk.CTkLabel(
        frame,
        text=message,
        font=ctk.CTkFont(size=14),
        wraplength=350
    )
    message_label.pack(pady=10)
    
    # Result variable
    result = [None]  # Use list to store result (mutable)
    
    # Options frame
    options_frame = ctk.CTkFrame(frame, fg_color="transparent")
    options_frame.pack(pady=10, fill="both", expand=True)
    
    # Create buttons for each option
    for option in options:
        option_button = ctk.CTkButton(
            options_frame,
            text=option,
            width=300,
            command=lambda opt=option: [result.__setitem__(0, opt), dialog.destroy()]
        )
        option_button.pack(pady=5)
    
    # Cancel button
    cancel_button = ctk.CTkButton(
        frame,
        text="Cancel",
        width=100,
        command=dialog.destroy
    )
    cancel_button.pack(pady=10)
    
    # Handle dialog close
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    
    # Wait for dialog to close
    if parent:
        parent.wait_window(dialog)
    else:
        dialog.wait_window()
    
    return result[0] 