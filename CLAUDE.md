# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pods is a visual idea organization tool with a hierarchical, graph-based structure.

**Core Concepts:**
- **Pods**: Containers representing ideas, people, groups, or any concept. Visually represented as ovals or rectangles.
- **Relationships**: Connections between pods that can represent any association (e.g., ownership, membership, dependencies). Visualized as lines between pods.
- **Hierarchy**: Pods can contain other pods. Double-clicking a pod enters it, revealing its internal structure.
- **Navigation**: The app starts in the "main" pod. Relationships can extend beyond the current view (lines going off-screen indicate connections to pods in other containers).

## Tech Stack

- **Language**: Python 3.x
- **GUI Framework**: Tkinter (included with Python standard library)
- **Dependencies**: None (tkinter is built-in)

## Project Structure

```
Pods/
├── main.py              # Entry point runner
├── src/                 # Source code package
│   ├── __init__.py
│   ├── pod.py          # Pod data model
│   ├── relationship.py # Relationship data model
│   └── app.py          # Main application class
└── CLAUDE.md
```

## Architecture

**Data Models (src/):**
- `src/pod.py`: Pod class representing containers for ideas. Each pod has position, size, shape (oval/rectangle), visual properties, and can contain child pods for hierarchical organization.
- `src/relationship.py`: Relationship class representing connections between pods with labels and visual properties.

**Application (src/):**
- `src/app.py`: Main application class (PodsApp) containing:
  - Canvas-based rendering system
  - Event handling for mouse interactions (click, drag, double-click)
  - Navigation system for moving between pod containers
  - Toolbar with navigation controls and pod creation
- `main.py`: Entry point runner that initializes the Tkinter window and starts the application.

**Key Design Patterns:**
- Center-based positioning: Pods use (x, y) for center coordinates with width/height
- Hierarchical navigation: Each pod can contain children; double-clicking enters a pod
- Offset rendering: Canvas coordinates are offset to center the current view
- UUIDs for tracking: Each pod and relationship has a unique ID for canvas tagging

## Development Commands

**Run the application:**
```bash
python main.py
```

**Python version requirement:**
- Python 3.6+ (for type hints and f-strings)

## User Interactions

- **Single Click**: Select a pod (enables dragging)
- **Drag**: Move selected pod to new position
- **Double Click**: Enter a pod (if it contains children)
- **Back Button**: Navigate to parent container
- **Add Pod Button**: Create new pod in current container
