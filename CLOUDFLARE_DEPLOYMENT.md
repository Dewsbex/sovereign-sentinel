# Sovereign Terminal Deployment Protocol (Cloudflare Pages)

Status: **ACTIVE**
Method: **Root Override (Golden Path)**
Last Updated: 2026-02-10

## 🚨 CRITICAL PROTOCOL

Cloudflare Pages deploys from the **ROOT** directory by default. 
However, our build artifacts are in `dist/`.

**Golden Rule:**
> **To deploy, you must COPY `dist/index.html` to the project root `index.html` before pushing to GitHub.**
> NEVER modify the root `index.html` directly. Always modify `dist/index.html` and sync it.

## 🚀 How to Deploy

Use the automated script to ensure timestamps are updated and files are synced correctly:

```powershell
./deploy_frontend.ps1
```

This script will:
1. Update the buildup timestamp in `dist/index.html`
2. Sync `dist/index.html` -> `index.html` (Force Overwrite)
3. Commit both files to git
4. Push to `origin main` to trigger Cloudflare build

## Manual Fallback

If the script fails, perform these steps manually:

1. **Update Timestamp**: Edit `dist/index.html` footer to current time.
2. **Sync File**:
   ```powershell
   copy /Y dist\index.html index.html
   ```
3. **Commit & Push**:
   ```powershell
   git add dist/index.html index.html
   git commit -m "deploy: Manual sync for Cloudflare"
   git push origin main
   ```

## Verification

After ~2 minutes:
1. Visit [https://sovereign-sentinel.pages.dev/](https://sovereign-sentinel.pages.dev/)
2. **Hard Refresh** (`Ctrl+Shift+R`)
3.Check Footer Timestamp matches your deploy time.
