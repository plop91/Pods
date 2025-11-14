# Pods Web Application - Quick Start Guide

## What's New

Your Pods application has been converted to a Django web application! It now runs in the browser with all the features you love, plus automatic database persistence.

## Getting Started in 3 Steps

### 1. Navigate to the Project

```bash
cd /home/user/Pods/pods_web
```

### 2. Install Dependencies (if not already installed)

```bash
pip install -r requirements.txt
```

### 3. Run the Server

```bash
python manage.py runserver
```

The application will be available at: **http://localhost:8000/**

## Features

### Core Features (from Desktop App)
- ✅ **Interactive Canvas**: Create and organize visual pods
- ✅ **Drag & Drop**: Move pods by dragging
- ✅ **Hierarchical Navigation**: Double-click pods to enter them
- ✅ **Relationships**: Create visual connections between pods
- ✅ **Back Button**: Navigate back to parent containers
- ✅ **Pod Properties**: Customize colors, shapes, and sizes

### New Web Features
- 🌐 **Browser-Based**: Access from any device with a web browser
- 💾 **Auto-Save**: All changes saved automatically to database
- 🔄 **REST API**: Full programmatic access via JSON API
- 📱 **Responsive Design**: Works on desktop and mobile
- 🗄️ **Database Backend**: SQLite (easily upgradable to PostgreSQL)
- 👥 **Multi-User Ready**: Can be extended for multiple users

## How to Use

### Creating Pods
1. Click **"Add Pod"** button in toolbar
2. Enter pod name, select shape and color
3. Click **"Create"**

### Moving Pods
- Click and drag any pod to reposition it
- Changes are saved automatically

### Navigating
- **Double-click** a pod to see its contents (if it has children)
- Click **"Back"** button to return to parent container
- Breadcrumbs show your current location

### Creating Relationships
1. Click **"Add Link"** button
2. Click on the **source pod**
3. Click on the **target pod**
4. Relationship is created with an arrow

### Deleting Pods
- Select a pod (single click)
- Press **Delete** key on keyboard
- Confirm deletion

## API Access

The web app includes a full REST API. Examples:

### Get All Pods
```bash
curl http://localhost:8000/api/pods/
```

### Create a Pod
```bash
curl -X POST http://localhost:8000/api/pods/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Idea",
    "x": 100,
    "y": 100,
    "width": 120,
    "height": 80,
    "shape": "oval"
  }'
```

### Create a Relationship
```bash
curl -X POST http://localhost:8000/api/relationships/ \
  -H "Content-Type: application/json" \
  -d '{
    "source": "<source-pod-id>",
    "target": "<target-pod-id>",
    "label": "relates to"
  }'
```

## Database Management

### View Data in Admin Panel

1. Create an admin user:
   ```bash
   python manage.py createsuperuser
   ```

2. Access admin at: **http://localhost:8000/admin/**

3. View and edit pods and relationships directly

### Reset Database (if needed)

```bash
rm db.sqlite3
python manage.py migrate
```

## File Structure

```
pods_web/
├── manage.py              # Django management commands
├── db.sqlite3             # Database (created after first run)
├── pods_project/          # Django project settings
├── pods_app/              # Main application
│   ├── models.py         # Database models
│   ├── views.py          # API endpoints
│   └── serializers.py    # API serializers
├── templates/             # HTML templates
│   └── pods_app/
│       └── index.html    # Main application page
└── static/                # CSS and JavaScript
    ├── css/
    │   └── style.css     # Application styles
    └── js/
        └── pods.js       # Canvas rendering & interactions
```

## Keyboard Shortcuts

- **Delete**: Delete selected pod
- **Escape**: Cancel dialogs

## Troubleshooting

### Port Already in Use

If port 8000 is busy, run on a different port:
```bash
python manage.py runserver 8080
```

### Static Files Not Loading

Ensure you're running from the `pods_web` directory:
```bash
cd /home/user/Pods/pods_web
python manage.py runserver
```

### Database Errors

Reset and recreate the database:
```bash
rm db.sqlite3
python manage.py migrate
```

## Next Steps

### Deploy to Production

For production deployment:
1. Update `settings.py` (set `DEBUG=False`, configure `ALLOWED_HOSTS`)
2. Use PostgreSQL instead of SQLite
3. Set up static file serving (WhiteNoise or Nginx)
4. Use Gunicorn as WSGI server
5. Enable HTTPS

### Add Features

The codebase is well-structured for adding:
- User authentication
- Collaborative editing
- Export/import functionality
- Advanced search and filtering
- Undo/redo functionality
- Mobile app integration

## Support

For issues or questions:
- Check the full README.md for detailed documentation
- Review the Django documentation at https://docs.djangoproject.com/
- Inspect browser console for JavaScript errors
- Check Django server logs for backend errors

## Comparison: Desktop vs Web

| Feature | Desktop (Tkinter) | Web (Django) |
|---------|-------------------|--------------|
| Platform | Desktop only | Any browser |
| Installation | Python + Tkinter | Python + Django |
| Data Storage | JSON files | Database |
| Multi-user | No | Possible |
| Remote Access | No | Yes |
| Mobile Support | No | Yes |
| Auto-save | Manual | Automatic |

Enjoy your new web-based Pods application! 🎉
