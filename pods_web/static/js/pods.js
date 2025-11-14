/**
 * Pods Web Application - Main JavaScript File
 * Handles canvas rendering, interactions, and API communication
 */

class PodsApp {
    constructor() {
        // Canvas setup
        this.canvas = document.getElementById('podsCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.resizeCanvas();

        // Application state
        this.currentContainer = null;  // Current pod we're viewing inside
        this.pods = [];  // Pods in current view
        this.relationships = [];  // All relationships
        this.navigationHistory = [];  // For back button

        // Interaction state
        this.selectedPod = null;
        this.hoveredPod = null;
        this.dragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.lastClickTime = 0;
        this.doubleClickDelay = 300;  // ms

        // Relationship creation state
        this.creatingRelationship = false;
        this.relationshipSourcePod = null;
        this.tempRelationshipEnd = null;

        // Pan/Zoom state
        this.panOffsetX = 0;
        this.panOffsetY = 0;
        this.zoomScale = 1.0;

        // API base URL
        this.apiBase = '/api';

        // Initialize
        this.setupEventListeners();
        this.loadRootPod();
    }

    // ========== Canvas Setup ==========

    resizeCanvas() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
        this.render();
    }

    // ========== API Methods ==========

    async apiRequest(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async loadRootPod() {
        try {
            const rootPod = await this.apiRequest('/pods/root/');
            this.currentContainer = rootPod;
            await this.loadCurrentView();
        } catch (error) {
            console.error('Failed to load root pod:', error);
        }
    }

    async loadCurrentView() {
        try {
            // Load pods in current container
            let endpoint = '/pods/';
            if (this.currentContainer && this.currentContainer.id) {
                endpoint += `?parent=${this.currentContainer.id}`;
            } else {
                endpoint += '?parent=null';
            }

            this.pods = await this.apiRequest(endpoint);

            // Load relationships
            if (this.currentContainer) {
                this.relationships = await this.apiRequest(`/relationships/?container=${this.currentContainer.id}`);
            }

            this.updateBreadcrumbs();
            this.render();
        } catch (error) {
            console.error('Failed to load current view:', error);
        }
    }

    async createPod(data) {
        try {
            const pod = await this.apiRequest('/pods/', {
                method: 'POST',
                body: JSON.stringify(data),
            });
            return pod;
        } catch (error) {
            console.error('Failed to create pod:', error);
            throw error;
        }
    }

    async updatePod(id, data) {
        try {
            const pod = await this.apiRequest(`/pods/${id}/`, {
                method: 'PATCH',
                body: JSON.stringify(data),
            });
            return pod;
        } catch (error) {
            console.error('Failed to update pod:', error);
            throw error;
        }
    }

    async deletePod(id) {
        try {
            await this.apiRequest(`/pods/${id}/`, {
                method: 'DELETE',
            });
        } catch (error) {
            console.error('Failed to delete pod:', error);
            throw error;
        }
    }

    async createRelationship(sourceId, targetId, label = '') {
        try {
            const relationship = await this.apiRequest('/relationships/', {
                method: 'POST',
                body: JSON.stringify({
                    source: sourceId,
                    target: targetId,
                    label: label,
                }),
            });
            return relationship;
        } catch (error) {
            console.error('Failed to create relationship:', error);
            throw error;
        }
    }

    // ========== Rendering Methods ==========

    render() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Calculate offset to center view
        const offsetX = this.canvas.width / 2 + this.panOffsetX;
        const offsetY = this.canvas.height / 2 + this.panOffsetY;

        // Save context state
        this.ctx.save();
        this.ctx.translate(offsetX, offsetY);
        this.ctx.scale(this.zoomScale, this.zoomScale);

        // Render relationships first (below pods)
        this.renderRelationships();

        // Render temporary relationship line
        if (this.creatingRelationship && this.relationshipSourcePod && this.tempRelationshipEnd) {
            this.renderTempRelationship();
        }

        // Render pods
        this.renderPods();

        // Restore context
        this.ctx.restore();
    }

    renderPods() {
        for (const pod of this.pods) {
            this.renderPod(pod);
        }
    }

    renderPod(pod) {
        const isSelected = this.selectedPod && this.selectedPod.id === pod.id;
        const isHovered = this.hoveredPod && this.hoveredPod.id === pod.id;

        // Get bounding box
        const x1 = pod.x - pod.width / 2;
        const y1 = pod.y - pod.height / 2;

        // Draw pod shape
        this.ctx.save();

        // Set colors
        const fillColor = pod.color || '#E8F4F8';
        const borderColor = pod.border_color || '#2C3E50';
        const textColor = pod.text_color || '#2C3E50';

        this.ctx.fillStyle = fillColor;
        this.ctx.strokeStyle = borderColor;
        this.ctx.lineWidth = isSelected ? 3 : (isHovered ? 2.5 : 2);

        // Draw shape
        if (pod.shape === 'rectangle') {
            this.ctx.fillRect(x1, y1, pod.width, pod.height);
            this.ctx.strokeRect(x1, y1, pod.width, pod.height);
        } else {
            // Oval
            this.ctx.beginPath();
            this.ctx.ellipse(pod.x, pod.y, pod.width / 2, pod.height / 2, 0, 0, 2 * Math.PI);
            this.ctx.fill();
            this.ctx.stroke();
        }

        // Draw text
        this.ctx.fillStyle = textColor;
        this.ctx.font = '14px sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';

        // Wrap text if too long
        const maxWidth = pod.width - 20;
        const text = this.wrapText(pod.name, maxWidth);
        const lineHeight = 18;
        const startY = pod.y - ((text.length - 1) * lineHeight) / 2;

        for (let i = 0; i < text.length; i++) {
            this.ctx.fillText(text[i], pod.x, startY + i * lineHeight);
        }

        // Draw selection highlight
        if (isSelected) {
            this.ctx.strokeStyle = '#3498DB';
            this.ctx.lineWidth = 3;
            this.ctx.setLineDash([5, 5]);

            if (pod.shape === 'rectangle') {
                this.ctx.strokeRect(x1 - 5, y1 - 5, pod.width + 10, pod.height + 10);
            } else {
                this.ctx.beginPath();
                this.ctx.ellipse(pod.x, pod.y, pod.width / 2 + 5, pod.height / 2 + 5, 0, 0, 2 * Math.PI);
                this.ctx.stroke();
            }
            this.ctx.setLineDash([]);
        }

        this.ctx.restore();
    }

    renderRelationships() {
        for (const rel of this.relationships) {
            this.renderRelationship(rel);
        }
    }

    renderRelationship(rel) {
        // Find source and target pods
        const sourcePod = this.pods.find(p => p.id === rel.source);
        const targetPod = this.pods.find(p => p.id === rel.target);

        if (!sourcePod || !targetPod) return;

        this.ctx.save();

        // Draw line
        this.ctx.strokeStyle = rel.color || '#34495E';
        this.ctx.lineWidth = rel.line_width || 2;
        this.ctx.beginPath();
        this.ctx.moveTo(sourcePod.x, sourcePod.y);
        this.ctx.lineTo(targetPod.x, targetPod.y);
        this.ctx.stroke();

        // Draw arrow if enabled
        if (rel.arrow) {
            this.drawArrow(sourcePod.x, sourcePod.y, targetPod.x, targetPod.y);
        }

        // Draw label if present
        if (rel.label) {
            const midX = (sourcePod.x + targetPod.x) / 2;
            const midY = (sourcePod.y + targetPod.y) / 2;

            this.ctx.fillStyle = 'white';
            this.ctx.fillRect(midX - 20, midY - 10, 40, 20);

            this.ctx.fillStyle = '#2C3E50';
            this.ctx.font = '12px sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(rel.label, midX, midY);
        }

        this.ctx.restore();
    }

    renderTempRelationship() {
        this.ctx.save();
        this.ctx.strokeStyle = '#3498DB';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        this.ctx.beginPath();
        this.ctx.moveTo(this.relationshipSourcePod.x, this.relationshipSourcePod.y);
        this.ctx.lineTo(this.tempRelationshipEnd.x, this.tempRelationshipEnd.y);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
        this.ctx.restore();
    }

    drawArrow(x1, y1, x2, y2) {
        const angle = Math.atan2(y2 - y1, x2 - x1);
        const arrowLength = 10;
        const arrowWidth = 6;

        this.ctx.save();
        this.ctx.translate(x2, y2);
        this.ctx.rotate(angle);
        this.ctx.beginPath();
        this.ctx.moveTo(0, 0);
        this.ctx.lineTo(-arrowLength, -arrowWidth);
        this.ctx.lineTo(-arrowLength, arrowWidth);
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.restore();
    }

    wrapText(text, maxWidth) {
        const words = text.split(' ');
        const lines = [];
        let currentLine = '';

        for (const word of words) {
            const testLine = currentLine + (currentLine ? ' ' : '') + word;
            const metrics = this.ctx.measureText(testLine);

            if (metrics.width > maxWidth && currentLine) {
                lines.push(currentLine);
                currentLine = word;
            } else {
                currentLine = testLine;
            }
        }

        if (currentLine) {
            lines.push(currentLine);
        }

        return lines;
    }

    // ========== Coordinate Conversion ==========

    screenToCanvas(screenX, screenY) {
        const rect = this.canvas.getBoundingClientRect();
        const offsetX = this.canvas.width / 2 + this.panOffsetX;
        const offsetY = this.canvas.height / 2 + this.panOffsetY;

        const canvasX = ((screenX - rect.left - offsetX) / this.zoomScale);
        const canvasY = ((screenY - rect.top - offsetY) / this.zoomScale);

        return { x: canvasX, y: canvasY };
    }

    // ========== Interaction Methods ==========

    getPodAtPoint(x, y) {
        // Check in reverse order (top pod first)
        for (let i = this.pods.length - 1; i >= 0; i--) {
            const pod = this.pods[i];
            const x1 = pod.x - pod.width / 2;
            const y1 = pod.y - pod.height / 2;
            const x2 = pod.x + pod.width / 2;
            const y2 = pod.y + pod.height / 2;

            if (x >= x1 && x <= x2 && y >= y1 && y <= y2) {
                return pod;
            }
        }
        return null;
    }

    async handleCanvasClick(event) {
        const pos = this.screenToCanvas(event.clientX, event.clientY);
        const clickedPod = this.getPodAtPoint(pos.x, pos.y);

        // Handle relationship creation
        if (this.creatingRelationship) {
            if (clickedPod) {
                if (!this.relationshipSourcePod) {
                    // First click - select source
                    this.relationshipSourcePod = clickedPod;
                } else if (clickedPod.id !== this.relationshipSourcePod.id) {
                    // Second click - create relationship
                    await this.createRelationship(this.relationshipSourcePod.id, clickedPod.id);
                    this.cancelRelationshipCreation();
                    await this.loadCurrentView();
                }
            }
            return;
        }

        // Check for double-click
        const now = Date.now();
        const isDoubleClick = (now - this.lastClickTime) < this.doubleClickDelay;
        this.lastClickTime = now;

        if (isDoubleClick && clickedPod) {
            // Double-click: navigate into pod
            await this.navigateToPod(clickedPod);
        } else {
            // Single click: select pod
            this.selectedPod = clickedPod;
            this.render();
        }
    }

    handleCanvasMouseDown(event) {
        if (this.creatingRelationship) return;

        const pos = this.screenToCanvas(event.clientX, event.clientY);
        const clickedPod = this.getPodAtPoint(pos.x, pos.y);

        if (clickedPod) {
            this.dragging = true;
            this.selectedPod = clickedPod;
            this.dragStartX = pos.x - clickedPod.x;
            this.dragStartY = pos.y - clickedPod.y;
            this.canvas.style.cursor = 'move';
        }
    }

    handleCanvasMouseMove(event) {
        const pos = this.screenToCanvas(event.clientX, event.clientY);

        // Handle dragging
        if (this.dragging && this.selectedPod) {
            this.selectedPod.x = pos.x - this.dragStartX;
            this.selectedPod.y = pos.y - this.dragStartY;
            this.render();
            return;
        }

        // Handle relationship creation preview
        if (this.creatingRelationship && this.relationshipSourcePod) {
            this.tempRelationshipEnd = pos;
            this.render();
            return;
        }

        // Handle hover
        const hoveredPod = this.getPodAtPoint(pos.x, pos.y);
        if (hoveredPod !== this.hoveredPod) {
            this.hoveredPod = hoveredPod;
            this.canvas.style.cursor = hoveredPod ? 'pointer' : 'default';
            this.render();
        }
    }

    async handleCanvasMouseUp(event) {
        if (this.dragging && this.selectedPod) {
            // Update pod position on server
            await this.updatePod(this.selectedPod.id, {
                x: this.selectedPod.x,
                y: this.selectedPod.y,
            });
            this.dragging = false;
            this.canvas.style.cursor = 'default';
        }
    }

    // ========== Navigation Methods ==========

    async navigateToPod(pod) {
        // Save current location to history
        if (this.currentContainer) {
            this.navigationHistory.push(this.currentContainer);
        }

        // Navigate to new pod
        this.currentContainer = pod;
        await this.loadCurrentView();
        this.updateBackButton();
    }

    async navigateBack() {
        if (this.navigationHistory.length > 0) {
            const previousContainer = this.navigationHistory.pop();
            this.currentContainer = previousContainer;
            await this.loadCurrentView();
            this.updateBackButton();
        }
    }

    updateBackButton() {
        const backBtn = document.getElementById('backBtn');
        backBtn.disabled = this.navigationHistory.length === 0;
    }

    updateBreadcrumbs() {
        const breadcrumbsDiv = document.getElementById('breadcrumbs');
        breadcrumbsDiv.innerHTML = '';

        if (!this.currentContainer) return;

        // Build breadcrumb path
        const path = [this.currentContainer];
        // In a full implementation, we'd build the full path from root
        // For now, just show current container

        // Create breadcrumb items
        const item = document.createElement('span');
        item.className = 'breadcrumb-item';
        item.textContent = this.currentContainer.name || 'Main';
        breadcrumbsDiv.appendChild(item);
    }

    // ========== UI Event Handlers ==========

    async showAddPodDialog() {
        const dialog = document.getElementById('addPodDialog');
        dialog.classList.remove('hidden');
        document.getElementById('podName').focus();
    }

    hideAddPodDialog() {
        const dialog = document.getElementById('addPodDialog');
        dialog.classList.add('hidden');
        document.getElementById('addPodForm').reset();
    }

    async handleAddPodSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);

        try {
            // Create pod at center of view
            const pod = await this.createPod({
                name: formData.get('name'),
                shape: formData.get('shape'),
                color: formData.get('color'),
                parent: this.currentContainer ? this.currentContainer.id : null,
                x: 0,
                y: 0,
                width: 100,
                height: 60,
            });

            this.hideAddPodDialog();
            await this.loadCurrentView();
        } catch (error) {
            alert('Failed to create pod: ' + error.message);
        }
    }

    startRelationshipCreation() {
        this.creatingRelationship = true;
        this.relationshipSourcePod = null;
        this.tempRelationshipEnd = null;
        this.canvas.classList.add('creating-relationship');
        document.getElementById('addRelationshipDialog').classList.remove('hidden');
    }

    cancelRelationshipCreation() {
        this.creatingRelationship = false;
        this.relationshipSourcePod = null;
        this.tempRelationshipEnd = null;
        this.canvas.classList.remove('creating-relationship');
        document.getElementById('addRelationshipDialog').classList.add('hidden');
        this.render();
    }

    async handleSave() {
        // In this version, changes are saved automatically to the database
        alert('All changes are saved automatically!');
    }

    // ========== Event Listeners Setup ==========

    setupEventListeners() {
        // Window resize
        window.addEventListener('resize', () => this.resizeCanvas());

        // Canvas events
        this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
        this.canvas.addEventListener('mousedown', (e) => this.handleCanvasMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleCanvasMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleCanvasMouseUp(e));

        // Toolbar buttons
        document.getElementById('backBtn').addEventListener('click', () => this.navigateBack());
        document.getElementById('addPodBtn').addEventListener('click', () => this.showAddPodDialog());
        document.getElementById('addRelationshipBtn').addEventListener('click', () => this.startRelationshipCreation());
        document.getElementById('saveBtn').addEventListener('click', () => this.handleSave());

        // Dialog buttons
        document.getElementById('addPodForm').addEventListener('submit', (e) => this.handleAddPodSubmit(e));
        document.getElementById('cancelAddPod').addEventListener('click', () => this.hideAddPodDialog());
        document.getElementById('cancelAddRelationship').addEventListener('click', () => this.cancelRelationshipCreation());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideAddPodDialog();
                this.cancelRelationshipCreation();
            }
            if (e.key === 'Delete' && this.selectedPod) {
                if (confirm('Delete this pod?')) {
                    this.deletePod(this.selectedPod.id).then(() => {
                        this.selectedPod = null;
                        this.loadCurrentView();
                    });
                }
            }
        });
    }
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.podsApp = new PodsApp();
});
