import subprocess
import sys

STEPS = [
    ("init_db", "Initialize database"),
    ("load_data", "Load all games and movies"),
    ("load_aliases", "Insert canonical genre aliases"),
    ("map_flags", "Tag content with adult/multiplayer/TV flags"),
    ("build_genre_vectors", "Build genre vectors"),
    ("score_recommendations", "Score recommendations and populate table"),
]

def run_step(script, label):
    print(f"\n🚀 Running: python -m scripts.{script}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", f"scripts.{script}"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Step '{script}' failed. Halting setup.\n")
        sys.exit(1)
    print(f"✅ {label} completed.")

def main():
    for script, label in STEPS:
        run_step(script, label)
    print("\n🎉 All setup steps completed successfully!")

if __name__ == "__main__":
    main()
