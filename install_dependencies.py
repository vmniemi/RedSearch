import subprocess
import sys
import importlib.util


# Package name used by pip : module name used by Python import
REQUIRED_PACKAGES = {
    "requests": "requests",
    "vaderSentiment": "vaderSentiment",
    "scikit-learn": "sklearn",
    "detoxify": "detoxify",
    "torch": "torch"
}


def is_installed(module_name):
    """
    Checks if a Python module can be imported.
    """
    return importlib.util.find_spec(module_name) is not None


def install_package(package_name):
    """
    Installs a package using the same Python interpreter
    that is running this script.
    """
    print(f"[+] Installing {package_name}...")

    try:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            package_name
        ])
        print(f"[+] Installed {package_name}")
    except subprocess.CalledProcessError:
        print(f"[!] Failed to install {package_name}")


def main():
    print("RedSearch Dependency Checker")
    print("=" * 50)

    missing_packages = []

    for package_name, module_name in REQUIRED_PACKAGES.items():
        if is_installed(module_name):
            print(f"[OK] {package_name} is already installed")
        else:
            print(f"[MISSING] {package_name}")
            missing_packages.append(package_name)

    if not missing_packages:
        print("\n[+] All dependencies are installed.")
        return

    print("\nMissing packages:")
    for package in missing_packages:
        print(f"- {package}")

    choice = input("\nInstall missing packages? (y/n): ").strip().lower()

    if choice != "y":
        print("Installation cancelled.")
        return

    for package in missing_packages:
        install_package(package)

    print("\n[+] Dependency check complete.")


if __name__ == "__main__":
    main()