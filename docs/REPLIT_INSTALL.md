# Replit Install Guide

This path is for using a hosted dashboard or enrollment flow while keeping Raspberry Pi devices lightweight.

## 1. Prepare the hosted app

- Create or open your Replit project for the ME_CAM dashboard
- Configure the app URL you will use for device enrollment
- Store any secrets in Replit secrets, not in tracked files

## 2. Create device enrollment flow

For each device you plan to activate:

- Create a device slot in the hosted dashboard
- Generate a unique activation or enrollment code
- Record only the metadata you need for deployment
- Do not commit generated codes or tokens into the repository

## 3. Prepare the Raspberry Pi device

- Use a clean Raspberry Pi OS Lite image for Pi Zero 2W where possible
- Enable SSH and network connectivity
- Verify the device can reach the hosted dashboard URL

## 4. Run the device-side installer

Use your hosted quick-install or agent bootstrap flow. Keep the dashboard URL and activation code externalized.

Example shape:

```bash
curl -sSL "https://<your-dashboard>/api/quick-install?code=<activation-code>" | sudo bash
```

If your hosted flow uses a dedicated install script, document that exact endpoint in your deployment environment, not in tracked source files.

## 5. Verify registration

After the install:

- Confirm the device appears in the dashboard
- Confirm the local runtime reports healthy status
- Confirm the device receives a stable device identity and enrollment state

Typical checks:

```bash
sudo systemctl status me_cam
sudo journalctl -u me_cam -n 50 --no-pager
curl http://127.0.0.1:8080/api/health
```

## 6. Secure the hosted flow

- Rotate activation codes regularly
- Treat device tokens as secrets
- Avoid embedding device names, hostnames, passwords, or internal IPs in repo files
- Prefer revocable onboarding tokens over static credentials

## 7. Release hygiene reminder

Replit deployment helpers often produce temporary repair scripts and result snapshots during development. Do not include those artifacts in a public release. The repository workflow is designed to block that class of release once the legacy artifacts are cleaned out.
