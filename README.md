Hugging Face Upload Tool

This tool is a simple GUI application for uploading files to Hugging Face repositories.

*Features

Drag & drop file path input
Repository name history and auto-completion
Subfolder specification
File upload using Hugging Face CLI

*Requirements

Python 3.6 or higher
tkinter
tkinterdnd2
Hugging Face CLI

*Installation
Clone or download this repository.

git clone https://github.com/SDSDFFG-rgb/huggingface-upload-tool.git

*Install the required libraries.

pip install tkinterdnd2 huggingface_hub huggingface_cli

log in to the Hugging Face CLI.

huggingface-cli login

*Usage
Run the script.

python huggingface_upload_tool.py

The GUI window will open.
Enter the Hugging Face repository name in the "Repository" field.
Previously used repository names will appear in the dropdown list.
If needed, enter a subfolder name in the "Subfolder" field.
Drag & drop the files or folders you want to upload into the "File/Folder Paths" field.
Click the "Execute" button to start the upload.

*Notes

Make sure you're logged in to the Hugging Face CLI before using this tool.
Upload history is saved in the upload_history.txt file.

*License
This project is released under the MIT License.
*Contributing
Please report bugs or feature requests through GitHub Issues. Pull requests are welcome. Here's the updated code with English comments and variable names:
