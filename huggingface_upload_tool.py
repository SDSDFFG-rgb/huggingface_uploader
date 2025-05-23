import tkinter as tk
from tkinter import ttk, messagebox, END, W, filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES
import subprocess
import os
import threading
import shlex
from collections import deque
import re
import traceback
from dataclasses import dataclass

# --- Constants ---
HISTORY_FILE = "upload_history.txt"
MAX_HISTORY_ITEMS = 10
APP_TITLE = "Hugging Face Upload Tool (Modernized) with Queue" # Keep as is or change if preferred

@dataclass
class UploadJob:
    id: int
    repository: str
    subfolder: str
    file_paths_display_str: str

    def __str__(self):
        files_preview = self.file_paths_display_str
        if len(files_preview) > 40:
            files_preview = files_preview[:37] + "..."
        sub = self.subfolder if self.subfolder else "<root>"
        return f"ID:{self.id} Repo: {self.repository}, Sub: {sub}, Files: {files_preview}"

class HuggingFaceUploaderApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title(APP_TITLE)

        self.upload_queue = deque()
        self.current_job_id_counter = 0
        self.current_processing_job: UploadJob | None = None
        self.is_processing_lock = threading.Lock()

        style = ttk.Style()
        # style.theme_use('clam') # Uncomment if you prefer this theme

        self.repository_var = tk.StringVar()
        self.subfolder_var = tk.StringVar()
        self.file_paths_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready") # English: Initial status
        self.progress_var = tk.DoubleVar(value=0.0)

        self.repository_history = deque(maxlen=MAX_HISTORY_ITEMS)

        self._setup_ui()
        self._load_history()
        self._update_repository_dropdown()
        self._update_queue_buttons_state()

    def _setup_ui(self):
        outer_frame = ttk.Frame(self.root, padding="5")
        outer_frame.grid(row=0, column=0, sticky=(W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        input_frame = ttk.Frame(outer_frame, padding="10")
        input_frame.grid(row=0, column=0, sticky=(W, tk.E, tk.N, tk.S))
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text='Repository (e.g., YourUsername/RepoName):').grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.repository_dropdown = ttk.Combobox(input_frame, textvariable=self.repository_var, width=47)
        self.repository_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky=(W, tk.E))
        self.repository_dropdown.bind('<<ComboboxSelected>>', self._on_repo_selected)
        self.repository_dropdown.bind('<Return>', lambda e: self._on_repo_selected(e, enter_key=True))

        ttk.Label(input_frame, text='Subfolder (in-repo path, optional):').grid(row=1, column=0, padx=5, pady=5, sticky=W)
        self.subfolder_entry = ttk.Entry(input_frame, textvariable=self.subfolder_var)
        self.subfolder_entry.grid(row=1, column=1, padx=5, pady=5, sticky=(W, tk.E))

        ttk.Label(input_frame, text='File/Folder Paths (Drag & Drop or Browse):').grid(row=2, column=0, padx=5, pady=5, sticky=W)
        
        file_path_controls_frame = ttk.Frame(input_frame)
        file_path_controls_frame.grid(row=2, column=1, padx=5, pady=5, sticky=(W, tk.E))
        file_path_controls_frame.columnconfigure(0, weight=1)

        self.file_paths_entry = ttk.Entry(file_path_controls_frame, textvariable=self.file_paths_var)
        self.file_paths_entry.grid(row=0, column=0, sticky=(W, tk.E))
        self.file_paths_entry.drop_target_register(DND_FILES)
        self.file_paths_entry.dnd_bind('<<Drop>>', self._on_drop_files)

        self.browse_file_button = ttk.Button(file_path_controls_frame, text="Browse File", command=self._browse_for_file, width=12)
        self.browse_file_button.grid(row=0, column=1, padx=(5, 0), sticky=W)

        self.browse_folder_button = ttk.Button(file_path_controls_frame, text="Browse Folder", command=self._browse_for_folder, width=12)
        self.browse_folder_button.grid(row=0, column=2, padx=(5, 0), sticky=W)

        self.add_to_queue_button = ttk.Button(input_frame, text='Add to Queue', command=self._add_to_queue)
        self.add_to_queue_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.progress_bar = ttk.Progressbar(input_frame, orient=tk.HORIZONTAL,
                                            length=300, mode='determinate',
                                            variable=self.progress_var)
        self.progress_bar.grid(row=4, column=0, columnspan=2, sticky=(W, tk.E), pady=(5,0))

        self.status_label = ttk.Label(input_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=W, wraplength=480)
        self.status_label.grid(row=5, column=0, columnspan=2, sticky=(W, tk.E), pady=(5,0))

        queue_frame = ttk.LabelFrame(outer_frame, text="Upload Queue", padding="10")
        queue_frame.grid(row=1, column=0, sticky=(W, tk.E, tk.N, tk.S), pady=(10,0))
        outer_frame.rowconfigure(1, weight=1)
        queue_frame.columnconfigure(0, weight=1)

        self.queue_listbox = tk.Listbox(queue_frame, height=6, selectmode=tk.SINGLE)
        self.queue_listbox.grid(row=0, column=0, columnspan=2, sticky=(W, tk.E, tk.N, tk.S), pady=5)
        queue_frame.rowconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.queue_listbox.yview)
        scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S, W), pady=5)
        self.queue_listbox.config(yscrollcommand=scrollbar.set)

        queue_button_frame = ttk.Frame(queue_frame)
        queue_button_frame.grid(row=1, column=0, columnspan=2, sticky=(W, tk.E))

        self.remove_button = ttk.Button(queue_button_frame, text="Remove Selected", command=self._remove_selected_from_queue)
        self.remove_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(queue_button_frame, text="Clear Queue", command=self._clear_queue)
        self.clear_button.pack(side=tk.LEFT, padx=5)

    def _browse_for_file(self):
        filepath = filedialog.askopenfilename(
            title="Select file to upload"
        )
        if filepath:
            self.file_paths_var.set(shlex.quote(filepath))

    def _browse_for_folder(self):
        folderpath = filedialog.askdirectory(
            title="Select folder to upload",
            mustexist=True
        )
        if folderpath:
            self.file_paths_var.set(shlex.quote(folderpath))

    def _on_repo_selected(self, event, enter_key=False):
        selected_value = self.repository_dropdown.get()
        self.repository_var.set(selected_value)
        if enter_key:
            self.subfolder_entry.focus()

    def _on_drop_files(self, event):
        self.file_paths_var.set("")
        try:
            raw_paths = self.root.tk.splitlist(event.data)
            quoted_paths_for_display = [shlex.quote(str(p)) for p in raw_paths]
            self.file_paths_var.set(" ".join(quoted_paths_for_display))
        except Exception as e:
            self.file_paths_var.set(event.data)
            self._update_status(f"Drop processing error: {e}", error=True)

    def _add_to_queue(self):
        repository_value = self.repository_var.get().strip()
        file_paths_display_str = self.file_paths_var.get().strip()
        subfolder_value = self.subfolder_var.get().strip()

        if not repository_value:
            messagebox.showerror("Input Error", "Please specify the Repository (e.g., YourUsername/RepoName).")
            return
        
        # Removed repository format warning

        if not file_paths_display_str:
            messagebox.showerror("Input Error", "Please specify or drag & drop/select File/Folder Paths.")
            return

        self.current_job_id_counter += 1
        job = UploadJob(id=self.current_job_id_counter,
                        repository=repository_value,
                        subfolder=subfolder_value,
                        file_paths_display_str=file_paths_display_str)
        self.upload_queue.append(job)
        self._update_queue_listbox_display()
        self._update_status(f"Job ID:{job.id} added to queue.", processing=True)
        
        self._process_next_in_queue_if_idle()

    def _process_next_in_queue_if_idle(self):
        with self.is_processing_lock:
            if self.current_processing_job is None and self.upload_queue:
                self.current_processing_job = self.upload_queue.popleft()
                self._update_queue_listbox_display()
                
                self.progress_var.set(0)
                self._update_status(f"Processing queue: Job ID:{self.current_processing_job.id} ({self.current_processing_job.repository})", processing=True)

                thread = threading.Thread(target=self._execute_upload_command_for_job,
                                          args=(self.current_processing_job,),
                                          daemon=True)
                thread.start()
            elif not self.upload_queue and self.current_processing_job is None:
                 self._update_status("Queue is empty. Ready.", processing=False)

    def _execute_upload_command_for_job(self, job: UploadJob):
        all_stdout_lines = []
        all_stderr_lines = []
        process = None
        success = False
        message = ""
        try:
            repository = job.repository
            file_paths_display_str = job.file_paths_display_str
            subfolder_val = job.subfolder

            command_parts = ["huggingface-cli", "upload"]
            command_parts.append(repository)
            actual_paths = shlex.split(file_paths_display_str)
            
            if not actual_paths:
                message = f"Job ID:{job.id} Error: No files specified for upload."
                self.root.after(0, self._handle_job_completion, job, False, message)
                return

            path_in_repo_str = ""
            if len(actual_paths) == 1:
                local_item_path = actual_paths[0]
                base_item_name = os.path.basename(local_item_path)
                if subfolder_val.strip():
                    clean_subfolder = subfolder_val.strip().replace("\\", "/")
                    if not clean_subfolder.endswith('/'):
                        clean_subfolder += '/'
                    path_in_repo_str = clean_subfolder + base_item_name
                else:
                    path_in_repo_str = base_item_name
            elif len(actual_paths) > 1:
                path_in_repo_str = subfolder_val.strip().replace("\\", "/") if subfolder_val.strip() else "."
                if not path_in_repo_str: path_in_repo_str = "."
            else:
                 message = f"Job ID:{job.id} Error: Parsed file paths are empty."
                 self.root.after(0, self._handle_job_completion, job, False, message)
                 return

            command_parts.extend(actual_paths)
            command_parts.append(path_in_repo_str)
            
            # print(f"DEBUG: Executing for Job ID:{job.id}: {command_parts}") 

            display_command_str = " ".join([shlex.quote(part) for part in command_parts])
            self.root.after(0, lambda cmd_str=display_command_str, jid=job.id: self._update_status(f"Job ID:{jid} Executing: {cmd_str}"))
            self.root.after(0, self.progress_var.set, 0)

            progress_regex = re.compile(r"(\d{1,3})\s*%\|")

            process = subprocess.Popen(command_parts, shell=False,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, encoding='utf-8', errors='replace', bufsize=1)

            if process.stderr:
                for line in iter(process.stderr.readline, ''):
                    line_strip = line.strip()
                    all_stderr_lines.append(line)
                    current_status_message = f"Job ID:{job.id} Processing: {line_strip[:80]}"
                    if len(line_strip) > 80: current_status_message += "..."
                    self.root.after(0, lambda msg=current_status_message: self._update_status(msg, processing=True))
                    match = progress_regex.search(line_strip)
                    if match:
                        percentage = int(match.group(1))
                        self.root.after(0, self.progress_var.set, percentage)
                process.stderr.close()
            
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    all_stdout_lines.append(line)
                process.stdout.close()

            process.wait()
            return_code = process.returncode
            final_stdout = "".join(all_stdout_lines)
            final_stderr = "".join(all_stderr_lines)

            if return_code == 0:
                success = True
                message_detail = final_stdout.strip()
                if not message_detail and final_stderr.strip():
                    message_detail = final_stderr.strip()
                message = f"Job ID:{job.id} Upload successful.\n{message_detail}"
                message = message[:1000] + "..." if len(message) > 1000 else message
            else:
                error_details = final_stderr.strip()
                if not error_details and final_stdout.strip():
                    error_details = final_stdout.strip()
                error_message_content = f"Error (code: {return_code}):\n{error_details}"
                message = f"Job ID:{job.id} {error_message_content}"
                message = message[:1000] + "..." if len(message) > 1000 else message
                # print(f"--- UPLOAD FAILED (Job ID:{job.id}) ---\nFull error message:\n{error_message_content}\nSTDOUT:\n{final_stdout}\n------------------------------------")

        except FileNotFoundError:
            message = f"Job ID:{job.id} Error: huggingface-cli not found. Check your PATH."
            # print(f"--- ERROR (Job ID:{job.id}): huggingface-cli not found ---")
            traceback.print_exc()
        except Exception as e:
            # print(f"--- AN UNEXPECTED ERROR OCCURRED (Job ID:{job.id}) ---")
            traceback.print_exc()
            tb_str = traceback.format_exc()
            error_msg_for_dialog = f"Unexpected Error:\n{e}\n\nTraceback (first 500 chars):\n{tb_str[:500]}..." if len(tb_str) > 500 else f"Unexpected Error:\n{e}\n\nTraceback:\n{tb_str}"
            message = f"Job ID:{job.id} {error_msg_for_dialog}"
        finally:
            rc = process.returncode if process and hasattr(process, 'returncode') else -1
            current_progress = self.progress_var.get()
            if success and current_progress < 100 :
                 self.root.after(0, self.progress_var.set, 100)
            elif not success and current_progress > 0 :
                 self.root.after(0, self.progress_var.set, 0)
            self.root.after(0, self._handle_job_completion, job, success, message)

    def _handle_job_completion(self, job: UploadJob, success: bool, message: str):
        with self.is_processing_lock:
            if self.current_processing_job and self.current_processing_job.id == job.id:
                self.current_processing_job = None
            # else:
                # print(f"Warning: Job completion for ID:{job.id} but current_processing_job is {self.current_processing_job}")

        if success:
            self.root.after(0, self.progress_var.set, 100)
            self._update_status(f"Job ID:{job.id} Upload successful!", success=True)
            if not self.upload_queue:
                messagebox.showinfo(f"Job ID:{job.id} Upload Successful", message)
            self._add_to_history(job.repository)
            self._save_history()
            self._update_repository_dropdown()
        else:
            if self.progress_var.get() > 0:
                self.root.after(0, self.progress_var.set, 0)
            self._update_status(f"Job ID:{job.id} Upload failed.", error=True)
            messagebox.showerror(f"Job ID:{job.id} Upload Failed", message)
        
        self._process_next_in_queue_if_idle()

    def _update_status(self, message, processing=False, success=False, error=False):
        self.status_var.set(message)
        fg_color = "black"
        if hasattr(self.status_label, 'tk') and self.status_label.winfo_exists():
            try:
                style_name = self.status_label.winfo_class()
                current_style_fg = ttk.Style().lookup(style_name, 'foreground')
                if current_style_fg:
                    fg_color = current_style_fg
            except tk.TclError:
                 pass
        if success:
            fg_color = "green"
        elif error:
            fg_color = "red"
        elif processing:
            fg_color = "blue"
        self.status_label.config(foreground=fg_color)

    def _load_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding='utf-8') as f:
                    loaded_history = []
                    seen = set()
                    for line in reversed(f.readlines()):
                        repo = line.strip()
                        if repo and repo not in seen:
                            loaded_history.append(repo)
                            seen.add(repo)
                            if len(loaded_history) >= MAX_HISTORY_ITEMS:
                                break
                    self.repository_history.clear()
                    for repo in reversed(loaded_history):
                         self.repository_history.append(repo)
        except IOError as e:
            self._update_status(f"Error loading history file: {e}", error=True)

    def _add_to_history(self, repository_name):
        if repository_name in self.repository_history:
            self.repository_history.remove(repository_name)
        self.repository_history.append(repository_name)

    def _save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding='utf-8') as f:
                for repo in list(self.repository_history):
                    f.write(f"{repo}\n")
        except IOError as e:
            self._update_status(f"Error writing history file: {e}", error=True)

    def _update_repository_dropdown(self):
        history_list = list(self.repository_history)
        self.repository_dropdown["values"] = list(reversed(history_list))
        current_repo_val = self.repository_var.get()
        if history_list:
            if not current_repo_val or current_repo_val not in history_list:
                last_used_repo = history_list[-1]
                self.repository_var.set(last_used_repo)
        elif not current_repo_val:
             self.repository_var.set("")
             self.repository_dropdown["values"] = []

    def _update_queue_listbox_display(self):
        self.queue_listbox.delete(0, END)
        if self.current_processing_job:
            self.queue_listbox.insert(END, f"[Processing] {str(self.current_processing_job)}")
        for job in self.upload_queue:
            self.queue_listbox.insert(END, str(job))
        self._update_queue_buttons_state()

    def _remove_selected_from_queue(self):
        selected_indices = self.queue_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Deletion Error", "Please select an item from the queue to remove.")
            return

        selected_index_in_listbox = selected_indices[0]
        if self.current_processing_job and selected_index_in_listbox == 0:
             messagebox.showinfo("Information", "The currently processing job cannot be removed. Please wait for completion.")
             return

        actual_deque_index = selected_index_in_listbox
        if self.current_processing_job:
            actual_deque_index -=1

        if 0 <= actual_deque_index < len(self.upload_queue):
            temp_list = list(self.upload_queue)
            job_to_remove = temp_list.pop(actual_deque_index)
            self.upload_queue = deque(temp_list)
            self._update_queue_listbox_display()
            self._update_status(f"Job ID:{job_to_remove.id} removed from queue.", processing=True)
        else:
            messagebox.showerror("Error", "Could not remove selected item from queue. Index out of range.")
        self._update_queue_buttons_state()

    def _clear_queue(self):
        if not self.upload_queue:
            messagebox.showinfo("Information", "The pending queue is already empty.")
            return
        if messagebox.askyesno("Clear Queue", "Are you sure you want to remove all pending jobs from the queue?\n(The currently processing job will not be removed.)"):
            self.upload_queue.clear()
            self._update_queue_listbox_display()
            self._update_status("Pending queue cleared.", processing=True)
            if not self.current_processing_job:
                 self._update_status("Ready", processing=False)
        self._update_queue_buttons_state()

    def _update_queue_buttons_state(self):
        has_selection_in_listbox = bool(self.queue_listbox.curselection())
        can_remove_selected = False
        if has_selection_in_listbox:
            selected_index_in_listbox = self.queue_listbox.curselection()[0]
            if self.current_processing_job and selected_index_in_listbox == 0:
                can_remove_selected = False
            else:
                actual_deque_index = selected_index_in_listbox
                if self.current_processing_job: actual_deque_index -= 1
                if 0 <= actual_deque_index < len(self.upload_queue):
                    can_remove_selected = True
        self.remove_button.config(state=tk.NORMAL if can_remove_selected else tk.DISABLED)
        self.clear_button.config(state=tk.NORMAL if len(self.upload_queue) > 0 else tk.DISABLED)

if __name__ == '__main__':
    root = TkinterDnD.Tk() # This is the main window from TkinterDnD
    app = HuggingFaceUploaderApp(root)
    root.mainloop()
