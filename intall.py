import os
import sys
import subprocess
import venv
from pathlib import Path
import platform


def drop_root_if_linux():
    # Only drop root on Linux systems
    if platform.system() == "Linux" and os.geteuid() == 0:
        sudo_user = os.getenv("SUDO_USER")
        if not sudo_user:
            print("Running as root but no SUDO_USER found. Exiting for safety.")
            sys.exit(1)

        print(f"Detected Linux and root user. Restarting script as normal user: {sudo_user}")

        # Relaunch the script as the original user
        cmd = ["sudo", "-u", sudo_user, sys.executable] + sys.argv
        os.execvp("sudo", cmd)

    # Otherwise continue normally
    print("Running as normal user or on non-Linux OS.")


def create_venv(venv_path: Path):
    print(f"Creating virtual environment at: {venv_path}")
    venv.EnvBuilder(with_pip=True).create(str(venv_path))


def run_in_venv(venv_path: Path, args):
    python_bin = (
        venv_path / "Scripts" / "python.exe"
        if os.name == "nt"
        else venv_path / "bin" / "python"
    )

    cmd = [str(python_bin)] + args
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)


def main():
    # --- Drop root before anything else ---
    drop_root_if_linux()

    venv_path = Path("venv")

    # Create venv
    if not venv_path.exists():
        create_venv(venv_path)
    else:
        print("Virtual environment already exists.")

    # Install requirements
    if Path("requirements.txt").exists():
        print("Installing dependencies...")
        run_in_venv(venv_path, ["-m", "pip", "install", "-r", "requirements.txt"])
    else:
        print("No requirements.txt found.")

    # Run game.py
    if Path("game.py").exists():
        print("Running game.py...")
        run_in_venv(venv_path, ["game.py"])
    else:
        print("game.py not found.")


if __name__ == "__main__":
    main()
