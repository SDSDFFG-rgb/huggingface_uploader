from tkinter import *
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
import subprocess
import os

# History file name
HISTORY_FILE = "upload_history.txt"

def drop(event, entry_widget):
    entry_widget.delete(0, END)
    paths = event.data
    entry_widget.insert(0, paths)

def execute_command(repository, subfolder, file_paths):
    command = f"huggingface-cli upload {repository} {file_paths} {subfolder}"
    subprocess.run(command, shell=True)

def execute_upload():
    repository_value = repository_var.get()
    subfolder_value = subfolder_var.get()
    file_paths_value = file_paths_var.get()

    if repository_value and file_paths_value:
        execute_command(repository_value, subfolder_value, file_paths_value)

        # Save history to text file
        with open(HISTORY_FILE, "a") as f:
            f.write(f"{repository_value}\n")

        # Update dropdown list
        update_repository_dropdown()

def update_repository_dropdown():
    # Load last 10 entries from history file
    try:
        with open(HISTORY_FILE, "r") as f:
            history = [line.strip() for line in f.readlines()[-10:]]
    except FileNotFoundError:
        history = []

    # Update dropdown list
    if history:
        repository_dropdown["values"] = history
        repository_dropdown.current(0)
        repository_var.set(history[0])
    else:
        repository_dropdown["values"] = []
        repository_var.set("")

# Create main window
root = TkinterDnD.Tk()
root.title('Hugging Face Upload Tool')

# Repository input field and dropdown
repository_label = Label(root, text='Repository:')
repository_var = StringVar()
repository_dropdown = ttk.Combobox(root, textvariable=repository_var, width=37)
repository_label.grid(row=0, column=0, padx=10, pady=5, sticky=W)
repository_dropdown.grid(row=0, column=1, padx=10, pady=5, columnspan=2)

# Subfolder input field
subfolder_label = Label(root, text='Subfolder:')
subfolder_var = StringVar()
subfolder_entry = Entry(root, textvariable=subfolder_var, width=40)
subfolder_label.grid(row=1, column=0, padx=10, pady=5, sticky=W)
subfolder_entry.grid(row=1, column=1, padx=10, pady=5, columnspan=2)

# File drop area
file_paths_label = Label(root, text='File/Folder Paths:')
file_paths_var = StringVar()
file_paths_entry = Entry(root, textvariable=file_paths_var, width=40)
file_paths_label.grid(row=2, column=0, padx=10, pady=5, sticky=W)
file_paths_entry.drop_target_register(DND_FILES)
file_paths_entry.dnd_bind('<<Drop>>', lambda event: drop(event, file_paths_entry))
file_paths_entry.grid(row=2, column=1, padx=10, pady=5, columnspan=2)

# Execute button
execute_button = Button(root, text='Execute', command=execute_upload)
execute_button.grid(row=3, column=1, pady=10)

# Initialize history dropdown
update_repository_dropdown()

# Display window
root.mainloop()
