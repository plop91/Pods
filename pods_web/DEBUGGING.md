# Debugging Guide for Pods Web Application

## Issue: White Screen / Buttons Not Working

If you're seeing the toolbar but a white canvas area, and the buttons don't work, this guide will help you debug the issue.

## What Was Fixed

The main issue was **REST API authentication**. The Django REST Framework was requiring CSRF tokens for all API requests, which prevented the JavaScript frontend from communicating with the backend.

### Changes Made:

1. **Updated `pods_project/settings.py`**:
   - Added `'DEFAULT_AUTHENTICATION_CLASSES': []` (no auth required)
   - Added `'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny']`
   - This allows the frontend to make API calls without authentication

2. **Enhanced `static/js/pods.js`**:
   - Added comprehensive `console.log()` statements
   - Added error alerts for failed initialization
   - Added fallback dimensions for canvas (800x600)
   - Better error handling throughout

3. **Created `test_page.html`**:
   - Simple test page to verify canvas and API work independently

## How to Debug

### Step 1: Open Browser Console

1. Open the application in your browser: `http://localhost:8000/`
2. Open Developer Tools:
   - **Chrome/Edge**: Press `F12` or `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac)
   - **Firefox**: Press `F12` or `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac)
   - **Safari**: Enable Developer menu first, then press `Cmd+Option+I`
3. Go to the **Console** tab

### Step 2: Check Console Logs

You should see logs like this if everything is working:

```
DOM Content Loaded - Starting Pods App
Pods App initializing...
Canvas initialized: 1200 x 650
Loading root pod...
Root pod loaded: {id: "...", name: "Main", ...}
Loading current view...
Fetching pods from: /pods/?parent=...
Loaded pods: [...]
Rendering canvas...
Render complete
Pods App created successfully
```

### Step 3: Identify Error Messages

If you see errors, they will appear in RED in the console. Common errors:

#### Error: "Canvas element not found!"
- **Problem**: HTML structure issue
- **Solution**: Verify the HTML template loaded correctly, reload the page

#### Error: "Failed to load root pod" or "API request failed"
- **Problem**: Backend API not accessible
- **Solution**:
  - Verify Django server is running: `python manage.py runserver`
  - Check server console for errors
  - Try accessing API directly: `http://localhost:8000/api/pods/root/`

#### Error: "Failed to fetch" or CORS errors
- **Problem**: CORS misconfiguration
- **Solution**: Verify `CORS_ALLOW_ALL_ORIGINS = True` is in settings.py

### Step 4: Check Network Tab

1. In Developer Tools, go to **Network** tab
2. Reload the page (`Ctrl+R` or `F5`)
3. Look for these requests:

| Request | Status | Type | Description |
|---------|--------|------|-------------|
| `/` | 200 | document | Main HTML page |
| `/static/css/style.css` | 200 | stylesheet | CSS file |
| `/static/js/pods.js` | 200 | script | JavaScript file |
| `/api/pods/root/` | 200 | xhr/fetch | Root pod API call |
| `/api/pods/?parent=...` | 200 | xhr/fetch | Pod list API call |

If any show **404** or **500** errors, click on them to see details.

### Step 5: Test API Independently

Open these URLs directly in your browser:

1. **Root Pod**: `http://localhost:8000/api/pods/root/`
   - Should return JSON with `{"id": "...", "name": "Main", ...}`

2. **All Pods**: `http://localhost:8000/api/pods/`
   - Should return JSON array of pods

3. **Test Page**: `http://localhost:8000/test_page.html`
   - Should show a blue circle with "Canvas Works!"
   - Click "Test API" button to verify API connectivity

### Step 6: Verify Canvas Rendering

If the console shows no errors but you still see a white screen:

1. Check canvas dimensions in console: `Canvas initialized: X x Y`
   - If `0 x 0`: CSS layout issue (verify flex container)
   - If `800 x 600` or larger: Canvas is fine, check if pods are rendering

2. Try resizing the browser window
   - This triggers `resizeCanvas()` which might fix layout issues

3. Check if pods exist in the database:
   ```bash
   python manage.py shell
   >>> from pods_app.models import Pod
   >>> Pod.objects.all()
   ```

## Common Solutions

### Solution 1: Clear Browser Cache

Sometimes old JavaScript files are cached:

1. Open Developer Tools (`F12`)
2. Right-click the Reload button
3. Select "Empty Cache and Hard Reload"

### Solution 2: Reset Database

If pods aren't rendering but API works:

```bash
cd pods_web
rm db.sqlite3
python manage.py migrate
python manage.py runserver
```

This creates a fresh database with a new root "Main" pod.

### Solution 3: Check Django Settings

Verify in `pods_project/settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],  # ← Must be empty
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # ← Must allow any
    ],
}

CORS_ALLOW_ALL_ORIGINS = True  # ← Must be True for development
```

### Solution 4: Check Static Files

If CSS/JS don't load (404 errors):

```bash
cd pods_web
python manage.py collectstatic --noinput
python manage.py runserver
```

## Still Not Working?

### Get Detailed Logs

In `settings.py`, enable debug logging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

### Export Console Logs

1. In browser console, right-click
2. Select "Save as..."
3. Share the console log file for further debugging

### Check Server Logs

The Django server console shows all HTTP requests:

```
[14/Nov/2025 23:45:02] "GET / HTTP/1.1" 200 4345
[14/Nov/2025 23:45:03] "GET /static/css/style.css HTTP/1.1" 200 0
[14/Nov/2025 23:45:03] "GET /static/js/pods.js HTTP/1.1" 200 0
[14/Nov/2025 23:45:04] "GET /api/pods/root/ HTTP/1.1" 200 358
```

All should return `200` (success). If you see `403`, `404`, or `500`, that's the problem.

## Expected Behavior

When working correctly:

1. Page loads with toolbar at top
2. Canvas fills the rest of the screen with gray background (#ECF0F1)
3. Console shows initialization logs (no errors)
4. If database has pods, they appear as shapes on canvas
5. Clicking "Add Pod" button opens a dialog
6. Creating a pod adds it to the canvas
7. Dragging a pod moves it
8. Double-clicking a pod navigates into it (if it has children)

## Contact

If you've tried all the above and it still doesn't work:

1. Check Django server is running: `python manage.py runserver`
2. Verify you're accessing: `http://localhost:8000/` (not file://)
3. Try a different browser
4. Check firewall isn't blocking localhost:8000

The comprehensive console logging added should pinpoint exactly where the issue occurs.
