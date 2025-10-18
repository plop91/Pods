# Pods - Visual Idea Organization

A hierarchical visual organization tool for managing ideas, concepts, and their relationships through an intuitive drag-and-drop interface.

## Description

**Pods** is a visual idea organization tool that helps you structure and connect your thoughts. Each Pod is a container that can represent anything - a person, group, idea, or concept. Pods can contain other Pods, creating a hierarchical structure that lets you organize information at multiple levels of detail.

**Key Concepts:**

- **Pods**: Visual containers (ovals or rectangles) that represent ideas, entities, or concepts
- **Relationships**: Directional connections between Pods with customizable labels (e.g., "owns", "works on", "depends on")
- **Hierarchical Navigation**: Double-click any Pod to enter it and view/edit its contents
- **External Relationships**: Relationships can connect to Pods outside the current view, shown as lines extending off-screen

## Features

- **Drag-and-Drop Interface**: Click and drag Pods to reposition them on the canvas
- **Resizable Pods**: Selected Pods show 8 resize handles (corners and cardinal directions)
- **Hierarchical Organization**: Nest Pods within Pods for unlimited depth
- **Relationship Creation**: Click the green plus buttons on selected Pods to create relationships
- **Rich Descriptions**: Add detailed descriptions to both Pods and Relationships
- **Canvas Panning**: Click empty space and drag to pan around large diagrams
- **Context Menus**: Right-click Pods or Relationships to edit properties
- **Project Management**: Save, load, and create new projects with File menu
- **Keyboard Shortcuts**: Quick access to common operations (Ctrl+N, Ctrl+O, Ctrl+S)

## Installation

### Prerequisites

- Python 3.7 or higher
- tkinter (usually comes bundled with Python)

### Setup

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd Pods
   ```

2. **Verify Python installation:**

   ```bash
   python --version
   ```

3. **Verify tkinter is available:**

   ```bash
   python -m tkinter
   ```

   This should open a small test window. If it doesn't, you may need to install tkinter:
   - **Ubuntu/Debian**: `sudo apt-get install python3-tk`
   - **Fedora**: `sudo dnf install python3-tkinter`
   - **macOS**: tkinter comes with Python from python.org
   - **Windows**: tkinter comes with standard Python installation

4. **Run the application:**

   ```bash
   python main.py
   ```

## Usage

### Getting Started

When you launch Pods, you'll see the Main pod with several example pods already created.

### Basic Operations

**Creating Pods:**

- Click the "+ Add Pod" button in the toolbar
- A new Pod will appear at a random position in the current container

**Moving Pods:**

- Click and drag any Pod to reposition it
- Click empty space and drag to pan the entire canvas

**Resizing Pods:**

1. Select a Pod by clicking it (it will show a blue outline)
2. Drag any of the 8 resize handles (corners or edges)
3. The cursor will change to indicate resize direction

**Creating Relationships:**

1. Select a Pod by clicking it
2. Click one of the green plus (+) buttons on the cardinal directions (N, S, E, W)
3. Your cursor will change to a crosshair
4. Click on the target Pod to create the relationship
5. Press ESC to cancel relationship creation

**Navigating the Hierarchy:**

- Double-click any Pod to enter it and view its contents
- Click the "← Back" button to return to the parent Pod
- The current location is shown in the toolbar

**Editing Pods:**

1. Right-click a Pod to open the context menu
2. Select "Edit Name" to change the Pod's name
3. Check "Show Description" to enable description mode
   - This converts the Pod to a rectangle with a separator line
   - Select "Edit Description" to add detailed notes

**Editing Relationships:**

1. Click a relationship line to select it (it will turn blue and thicker)
2. Right-click the selected relationship
3. Choose "Edit Label" to change the relationship type (e.g., "owns", "manages")
4. Choose "Edit Description" to add notes (visible only when selected)

### File Operations

**New Project (Ctrl+N):**

- Creates a fresh empty project
- Prompts for confirmation if there are unsaved changes

**Open Project (Ctrl+O):**

- Load a previously saved project from a .json file
- Prompts for confirmation if there are unsaved changes

**Save Project (Ctrl+S):**

- Saves to the current file
- If the project hasn't been saved before, prompts for a location

**Save As (Ctrl+Shift+S):**

- Save the current project to a new file location

## Project Structure

```
Pods/
├── main.py              # Application entry point
├── src/
│   ├── __init__.py      # Package initialization
│   ├── app.py           # Main application class with UI and interaction handling
│   ├── pod.py           # Pod data model with serialization
│   └── relationship.py  # Relationship data model with serialization
├── README.md            # This file
├── CLAUDE.md            # Development documentation
├── requirements.txt     # Python dependencies (empty - uses built-in tkinter)
└── .gitignore           # Git ignore rules
```

## Project File Format

Projects are saved as JSON files with the following structure:

```json
{
  "version": "1.0",
  "main_pod": {
    "id": "uuid",
    "name": "Main",
    "x": 0,
    "y": 0,
    "width": 0,
    "height": 0,
    "shape": "oval",
    "description": "",
    "has_description": false,
    "color": "#E8F4F8",
    "border_color": "#2C3E50",
    "text_color": "#2C3E50",
    "children": [...]
  },
  "relationships": [
    {
      "id": "uuid",
      "source_id": "uuid",
      "target_id": "uuid",
      "label": "owns",
      "relationship_type": "default",
      "description": "",
      "color": "#34495E",
      "line_width": 2,
      "arrow": true
    }
  ]
}
```

## Tips and Tricks

- **Organization**: Use the hierarchy to organize complex projects - create top-level Pods for major categories, then drill down into details
- **Visual Clarity**: Use descriptions for important Pods that need context
- **Relationship Labels**: Keep labels concise (e.g., "uses", "depends on", "manages")
- **Pan and Zoom**: For large diagrams, use canvas panning (click-drag empty space) to navigate
- **Keyboard Shortcuts**: Learn the shortcuts (Ctrl+N/O/S) for faster workflow

## Known Limitations

- No zoom functionality (planned for future release)
- Undo/redo not yet implemented
- No copy/paste functionality
- Relationships cannot be deleted via UI (can be manually removed from JSON file)

## Contributing

This is a personal project, but suggestions and feedback are welcome! Please open an issue to discuss potential changes or improvements.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Author

Ian Sodersjerna (<iansodersjerna@gmail.com>)
