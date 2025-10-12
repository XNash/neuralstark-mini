# Troubleshooting: "Root element not found" Error on Local Firefox

## Issue
Firefox browser showing endless "Root element not found. Retrying..." messages.

## Causes
1. Browser cache loading old version of the app
2. Service workers or cached scripts
3. Firefox extensions interfering with page load
4. Local DNS/network issues

## Solutions (Try in order)

### 1. Hard Refresh (Most Common Fix)
**Firefox:**
- Press `Ctrl + Shift + R` (Windows/Linux)
- Press `Cmd + Shift + R` (Mac)
- Or press `Ctrl + F5`

This forces Firefox to reload all assets without cache.

### 2. Clear Browser Cache Completely
1. Open Firefox Settings (`about:preferences`)
2. Go to Privacy & Security
3. Scroll to Cookies and Site Data
4. Click "Clear Data..."
5. Check both boxes and click "Clear"
6. Close and reopen Firefox
7. Navigate to `http://localhost:3000`

### 3. Disable Browser Extensions
1. Open Firefox Add-ons (`Ctrl + Shift + A` or `about:addons`)
2. Disable all extensions temporarily
3. Restart Firefox
4. Try loading the app again

### 4. Try Firefox Private Window
1. Press `Ctrl + Shift + P` (Windows/Linux) or `Cmd + Shift + P` (Mac)
2. In the private window, navigate to `http://localhost:3000`
3. This bypasses all cache and most extensions

### 5. Clear Service Workers
1. Open Firefox Developer Tools (`F12`)
2. Go to Storage tab
3. Find "Service Workers" in the left sidebar
4. Unregister all service workers for localhost
5. Refresh the page

### 6. Rebuild Frontend
```bash
cd /app/frontend
rm -rf node_modules/.cache
yarn start
```

### 7. Check Console for Specific Errors
1. Open Firefox Developer Tools (`F12`)
2. Go to Console tab
3. Look for any errors before the "Root element not found" messages
4. Share those errors if the problem persists

### 8. Try a Different Browser
Test in Chrome or Edge to verify it's Firefox-specific:
- Chrome/Edge: `Ctrl + Shift + N` for incognito mode
- Navigate to `http://localhost:3000`

## Verification
After trying any solution, you should see:
- The RAG Platform app loads with sidebar
- No "Root element not found" errors in console
- Welcome screen with feature cards visible

## Still Having Issues?
If none of these work, the issue might be:
1. Local network/firewall blocking connections
2. Antivirus software interfering
3. Corrupted Firefox profile

Try creating a new Firefox profile:
```
firefox -P
```
Create a new profile and test there.

## What Was Fixed
The server-side code has been updated to:
1. Remove infinite retry loop
2. Set WebSocket port to auto-detect (`WDS_SOCKET_PORT=0`)
3. Ensure proper DOM ready detection

These fixes are already applied in the repository.
