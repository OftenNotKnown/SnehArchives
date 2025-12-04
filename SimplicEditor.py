import os
import sys
import subprocess

def launch_main():
    # Get current directory (same folder where this .exe lives)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_path = os.path.join(base_dir, "main.py")

    if not os.path.exists(main_path):
        print("main.py not found in folder:", base_dir)
        input("Press Enter to exit...")
        return

    # Run main.py using python embedded with pyinstaller
    subprocess.run([sys.executable, main_path])

if __name__ == "__main__":
    launch_main()
