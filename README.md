# Hugging Face Upload Tool (Modernized)

A Python Tkinter application for uploading files and folders to the Hugging Face Hub, featuring a drag & drop interface, upload queue, and repository history. This tool simplifies the process of using `huggingface-cli upload` by providing a graphical user interface.

## Screenshot

![Image](https://github.com/user-attachments/assets/d9ffd278-6f55-4737-b0fb-2b0e7c2162d7)

## Key Features

*   **GUI for `huggingface-cli`**: Easily upload files/folders without complex command-line arguments.
*   **Drag & Drop**: Drag files or folders directly onto the application to specify paths.
*   **Browse Buttons**: Alternatively, use "Browse File" and "Browse Folder" buttons.
*   **Upload Queue**: Add multiple upload jobs to a queue, and they will be processed sequentially.
*   **Repository History**: Remembers previously used repository names for quick selection.
*   **Subfolder Support**: Specify a target subfolder within your Hugging Face repository.
*   **Progress Display**: Shows the progress of LFS uploads (if applicable).
*   **Status Updates**: Real-time status messages for ongoing operations and errors.

## Prerequisites

*   **Python 3.x**: The application is written in Python 3.
*   **`huggingface-cli`**: You must have the Hugging Face Hub command-line interface installed and configured.
    *   Install it via pip: `pip install -U "huggingface_hub[cli]"`
    *   Log in to your Hugging Face account: `huggingface-cli login` (or set up a token).

## Installation

1.  **Clone the repository (or download the script):**
    ```bash
    git clone https://your-github-repo-url/hf-uploader-tool.git
    cd hf-uploader-tool
    ```
    (Replace `https://your-github-repo-url/hf-uploader-tool.git` with the actual URL of your repository.)
    If you only have the script file (e.g., `hf_uploader_app.py`), save it to a directory on your computer.

2.  **Install required Python libraries:**
    This application uses `TkinterDnD2` for drag-and-drop functionality.
    Open your terminal or command prompt and run:
    ```bash
    pip install TkinterDnD2
    ```
    On some systems, especially Windows, you might need to use:
    ```bash
    python -m pip install TkinterDnD2
    ```
    No other external libraries beyond standard Python and `TkinterDnD2` are strictly required by this script itself (besides `huggingface-cli` which is a prerequisite).

## Usage

1.  **Run the application:**
    Navigate to the directory where you saved the script and run:
    ```bash
    python hf_uploader_app.py
    ```
    (Replace `hf_uploader_app.py` with the actual name of your Python script file if it's different.)

2.  **Fill in the details:**
    *   **Repository**: Enter your Hugging Face repository ID in the format `YourUsername/RepoName` or `OrganizationName/RepoName`. You can also select from previously used repositories in the dropdown.
    *   **Subfolder (optional)**: If you want to upload files into a specific subfolder within your repository, enter the path here (e.g., `models/version1` or `datasets/images`). If left blank, files will be uploaded to the root of the repository (or directly if a single file is uploaded without a subfolder) or into a folder matching the name of a dropped/selected folder.
    *   **File/Folder Paths**:
        *   **Drag & Drop**: Drag one or more files or folders from your file explorer and drop them onto this field.
        *   **Browse Buttons**:
            *   Click "Browse File" to select a single file.
            *   Click "Browse Folder" to select a single folder.
        The selected path(s) will appear in the entry field.

3.  **Add to Queue:**
    Once all details are filled, click the "Add to Queue" button. The upload job will be added to the "Upload Queue" list.

4.  **Manage the Queue:**
    *   The application will automatically start processing the first job in the queue.
    *   **Remove Selected**: Select a job from the *pending* queue (not the currently processing one) and click this button to remove it.
    *   **Clear Queue**: Click this button to remove all *pending* jobs from the queue. A confirmation will be asked.

5.  **Upload Process:**
    *   The tool constructs and executes the appropriate `huggingface-cli upload` command in the background.
    *   The status bar will show the current operation, progress (for LFS), and any success or error messages.
    *   A message box will appear upon successful completion of the last job in the queue, or on any upload failure.

## History File

The application saves a history of successfully used repository names in a file named `upload_history.txt` in the same directory as the script. This allows for quick selection of repositories in future sessions. You can safely delete this file if you want to clear the history.

## Notes

*   Ensure `huggingface-cli` is in your system's PATH environment variable.
*   The tool attempts to correctly determine the `path_in_repo` argument for `huggingface-cli upload` based on whether you're uploading single/multiple files/folders and if a subfolder is specified.
    *   **Single item (file/folder) + Subfolder:** Uploads to `subfolder/item_name`.
    *   **Single item (file/folder) + No Subfolder:** Uploads as `item_name` to the repository root.
    *   **Multiple items + Subfolder:** Uploads items into the specified `subfolder`.
    *   **Multiple items + No Subfolder:** Uploads items into the repository root (`.`).
*   Error messages from `huggingface-cli` will be displayed in the status bar and in error dialogs.

## Contributing (Optional)

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License (Optional)

[MIT](https://choosealicense.com/licenses/mit/)
*(Choose a license appropriate for your project, or remove this section if not applicable.)*
