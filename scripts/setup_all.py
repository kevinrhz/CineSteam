import subprocess

def run(command):
    print(f"\n🚀 Running: {command}")
    subprocess.run(command, shell=True)

if __name__ == "__main__":
    run("python -m scripts.init_db")
    run("python -m scripts.load_data")
    run("python -m scripts.load_aliases")
    run("python -m scripts.map_flags")

    print("\n✅ All steps completed successfully.")
