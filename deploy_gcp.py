import os
import sys
import subprocess

def check_gcloud():
    """Check if gcloud CLI is installed."""
    try:
        subprocess.run(["gcloud", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        print("Error: 'gcloud' CLI is not installed. Please install the Google Cloud SDK.")
        return False

def deploy():
    """Deploy the application to Google Cloud Run as a Job."""
    if not check_gcloud():
        return

    app_name = "human-override-renderer"
    region = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    print(f"🚀 Deploying '{app_name}' to Cloud Run (Region: {region})...")
    print("NOTE: This uses Google Cloud Buildpacks to build the image automatically.")

    # 1. Build and Submit (using source deploy)
    # We use 'gcloud run jobs deploy' with --source .
    # IMPORTANT: We override the entrypoint to ensure it runs the pipeline, not the web server.
    cmd = [
        "gcloud", "run", "jobs", "deploy", app_name,
        "--source", ".",
        "--region", region,
        "--task-timeout", "60m",  # Long timeout for rendering
        "--set-env-vars", "PYTHONUNBUFFERED=1",
        "--command", "python",
        "--args", "main.py,build"
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Deployment Successful! Job '{app_name}' created.")
        print(f"To run the job:")
        print(f"  gcloud run jobs execute {app_name} --region {region}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Deployment Failed: {e}")

if __name__ == "__main__":
    deploy()
