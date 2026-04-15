#!/usr/bin/env python3
"""
Webhook server - Allows the dashboard to trigger GitHub Actions workflow.

Usage: python tools/webhook_server.py
Then make requests to: http://localhost:5000/trigger-update
"""

import os
import json
import logging
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "thinkrconsulting-marc"
REPO_NAME = "claude-code-videos"
WORKFLOW_ID = "daily_update.yml"


@app.route('/trigger-update', methods=['POST'])
def trigger_update():
    """Trigger the GitHub Actions workflow."""

    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN not set in .env")
        return jsonify({
            "status": "error",
            "message": "GITHUB_TOKEN not configured"
        }), 500

    try:
        # GitHub API endpoint to trigger workflow dispatch
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_ID}/dispatches"

        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }

        payload = {
            "ref": "main"
        }

        logger.info(f"Triggering workflow: {WORKFLOW_ID}")

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 204:
            logger.info("Workflow triggered successfully")
            return jsonify({
                "status": "success",
                "message": "Workflow triggered! Check GitHub Actions for details."
            }), 200
        else:
            logger.error(f"GitHub API error: {response.status_code} - {response.text}")
            return jsonify({
                "status": "error",
                "message": f"Failed to trigger workflow: {response.status_code}",
                "details": response.text
            }), response.status_code

    except Exception as e:
        logger.error(f"Error triggering workflow: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/status', methods=['GET'])
def status():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "message": "Webhook server is running"
    }), 200


if __name__ == "__main__":
    logger.info(f"Starting webhook server for {REPO_OWNER}/{REPO_NAME}")
    logger.info("Server running on http://localhost:5000")
    logger.info("Trigger update at: POST http://localhost:5000/trigger-update")
    app.run(debug=False, port=5000)
