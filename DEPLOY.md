# 🚀 Deployment Guide

This project is designed to run on **Google Cloud Platform (GCP)** due to its use of Vertex AI and high-compute video rendering requirements.

## 📋 Prerequisites

1.  **Google Cloud Project**: You need an active GCP project.
2.  **APIs Enabled**:
    *   Vertex AI API (`aiplatform.googleapis.com`)
    *   Cloud Text-to-Speech API (`texttospeech.googleapis.com`)
    *   Cloud Run API (`run.googleapis.com`)
    *   Artifact Registry API (`artifactregistry.googleapis.com`)
    *   Cloud Build API (`cloudbuild.googleapis.com`)

## ☁️ Option A: Cloud Run (Serverless)

We use **Cloud Run Jobs** for the rendering pipeline because generating a video can take longer than the standard HTTP timeout.

### 1. Configure
Ensure your `.env` file (or environment variables) are ready.

### 2. Deploy
Run the included python deployment script. It uses your local `gcloud` credentials to build and deploy the code.

```bash
python deploy_gcp.py
```

### 3. Execute
Once deployed, you can trigger a job from the console or CLI:

```bash
gcloud run jobs execute human-override-renderer --region us-central1
```

## 💻 Option B: Virtual Machine (VM)

For full control, or if you want to use the **Streamlit UI** interactively.

### 1. Provision VM
Create a standard Ubuntu 22.04 VM (e.g., e2-standard-4) on Compute Engine.

### 2. Install
SSH into the machine and clone this repo. Then run:

```bash
./setup.sh
```

### 3. Run
Activate the environment and run the pipeline:

```bash
source venv/bin/activate
python main.py build
```

To run the Director Mode UI:
```bash
python main.py ui
```
(Ensure port 8501 is open in your firewall rules).

## 🛠 Troubleshooting

*   **FFmpeg errors:** Ensure `ffmpeg` is installed. `setup.sh` attempts to install it, but on some minimal images, you may need `sudo apt-get install ffmpeg` manually.
*   **Authentication:** If running on a VM, ensure the VM Service Account has permissions for Vertex AI and Text-to-Speech.
