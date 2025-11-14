# Pods Web Application

A Django-based web version of the Pods visual idea organization tool.

## Features

- **Interactive Canvas**: Visual pod organization with HTML5 Canvas
- **Hierarchical Structure**: Navigate through nested pods by double-clicking
- **Drag & Drop**: Move pods by dragging them on the canvas
- **Relationships**: Create connections between pods with visual links
- **REST API**: Full CRUD operations via Django REST Framework
- **Real-time Persistence**: All changes automatically saved to database
- **Responsive Design**: Works on desktop and mobile browsers

## Tech Stack

- **Backend**: Django 4.2+ with Django REST Framework
- **Frontend**: Vanilla JavaScript with HTML5 Canvas
- **Database**: SQLite (default, can be changed to PostgreSQL/MySQL)
- **API**: RESTful JSON API

## Installation

### 1. Install Dependencies

```bash
cd pods_web
pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
python manage.py runserver
```

### 5. Access the Application

Open your browser and navigate to:
- **Main App**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **API Root**: http://localhost:8000/api/

## Usage

### Basic Operations

- **Add Pod**: Click the "Add Pod" button in the toolbar
- **Select Pod**: Single-click on a pod
- **Move Pod**: Drag a pod to reposition it
- **Navigate Into Pod**: Double-click a pod to see its contents
- **Go Back**: Click the "Back" button to return to parent container
- **Create Relationship**: Click "Add Link", then click source pod and target pod
- **Delete Pod**: Select a pod and press Delete key

### API Endpoints

#### Pods

- `GET /api/pods/` - List all pods (filter by `?parent=<id>`)
- `POST /api/pods/` - Create a new pod
- `GET /api/pods/<id>/` - Get pod details
- `PATCH /api/pods/<id>/` - Update pod
- `DELETE /api/pods/<id>/` - Delete pod
- `GET /api/pods/root/` - Get or create root pod
- `GET /api/pods/<id>/tree/` - Get pod with all children
- `GET /api/pods/<id>/children/` - Get pod's children
- `POST /api/pods/<id>/move/` - Move pod to new position

#### Relationships

- `GET /api/relationships/` - List all relationships
- `POST /api/relationships/` - Create a new relationship
- `GET /api/relationships/<id>/` - Get relationship details
- `PATCH /api/relationships/<id>/` - Update relationship
- `DELETE /api/relationships/<id>/` - Delete relationship

### Example API Usage

#### Create a Pod

```bash
curl -X POST http://localhost:8000/api/pods/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Idea",
    "x": 100,
    "y": 100,
    "width": 120,
    "height": 80,
    "shape": "oval",
    "color": "#E8F4F8",
    "parent": null
  }'
```

#### Create a Relationship

```bash
curl -X POST http://localhost:8000/api/relationships/ \
  -H "Content-Type: application/json" \
  -d '{
    "source": "<source-pod-id>",
    "target": "<target-pod-id>",
    "label": "relates to"
  }'
```

## Project Structure

```
pods_web/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── pods_project/             # Django project settings
│   ├── __init__.py
│   ├── settings.py          # Project settings
│   ├── urls.py              # Project URL configuration
│   ├── wsgi.py              # WSGI application
│   └── asgi.py              # ASGI application
├── pods_app/                 # Main Django app
│   ├── __init__.py
│   ├── models.py            # Pod and Relationship models
│   ├── views.py             # API views and endpoints
│   ├── serializers.py       # DRF serializers
│   ├── urls.py              # App URL configuration
│   ├── admin.py             # Admin interface config
│   └── apps.py              # App configuration
├── templates/                # HTML templates
│   └── pods_app/
│       └── index.html       # Main application template
└── static/                   # Static files
    ├── css/
    │   └── style.css        # Application styles
    └── js/
        └── pods.js          # Canvas rendering and interactions
```

## Database Models

### Pod Model

- `id` (UUID): Unique identifier
- `name` (String): Pod name
- `description` (Text): Pod description
- `x, y` (Float): Center position
- `width, height` (Float): Dimensions
- `shape` (String): "oval" or "rectangle"
- `color, border_color, text_color` (String): Visual properties
- `parent` (ForeignKey): Parent pod (for hierarchy)

### Relationship Model

- `id` (UUID): Unique identifier
- `source` (ForeignKey): Source pod
- `target` (ForeignKey): Target pod
- `label` (String): Relationship label
- `relationship_type` (String): Type of relationship
- `color` (String): Line color
- `line_width` (Integer): Line thickness
- `arrow` (Boolean): Show arrow or not

## Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations pods_app
python manage.py migrate
```

### Accessing Django Shell

```bash
python manage.py shell
```

## Production Deployment

For production deployment, you should:

1. Change `DEBUG = False` in `settings.py`
2. Set a secure `SECRET_KEY`
3. Configure `ALLOWED_HOSTS`
4. Use a production database (PostgreSQL recommended)
5. Set up static file serving with WhiteNoise or serve via Nginx
6. Use a production WSGI server like Gunicorn
7. Enable HTTPS

## License

This project follows the same license as the original Pods desktop application.

## Contributing

Feel free to submit issues and pull requests!
