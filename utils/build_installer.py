import os
import subprocess
import sys  # Import the sys module

def get_data_directories():
    """
    Returns a list of all subdirectories in the current directory,
    excluding hidden directories and __pycache__.
    """
    items = os.listdir('.')
    directories = [
        item for item in items
        if os.path.isdir(item) and not item.startswith('.') and item.lower() != '__pycache__'
    ]
    return directories

def main():
    # Get all subdirectories to include as additional data
    directories = get_data_directories()

    # Build the list of --add-data arguments.
    add_data_args = []
    for directory in directories:
        # Use os.path.join for cross-platform compatibility
        add_data_args.extend(["--add-data", f"{directory}{os.pathsep}{directory}"])


    # Exclude unused modules
    excluded_modules = ["tkinter"]
    exclude_args = []
    for module in excluded_modules:
        exclude_args.extend(["--exclude-module", module])

    # --- Get the absolute path to the icon ---
    #  This is the most crucial fix!
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Absolute path to *this* script
    icon_path = os.path.join(script_dir, "data", "base.ico") # Absolute path to the icon


    # Construct the full PyInstaller command
    command = [
        "pyinstaller",
        "--onedir",
        "--noconsole",
        "--icon", f"{icon_path}" 
    ] + exclude_args + add_data_args + ["main.py"]

    print("Running PyInstaller with the following command:")
    print(" ".join(command))

    # Execute the command to build the installer
    subprocess.run(command, check=True)  # Added check=True for better error handling

if __name__ == "__main__":
    main()