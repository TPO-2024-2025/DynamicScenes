import "https://unpkg.com/wired-card@2.1.0/lib/wired-card.js?module";
import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

class DynamicScenes extends LitElement {
  scenes = {}
  selectedScene = null;

  static get properties() {
    return {
      hass: { type: Object },
      narrow: { type: Boolean },
      route: { type: Object },
      panel: { type: Object },
      scenes: { type: Object },
      selectedScene: { type: String },
    };
  }

  // Called on init, gets scenes from HA API
  firstUpdated() {
    this.loadScenes();
  }

  render() {
    return html`
      <body>
        <div class="container">
            <div class="header">
                <h1>Dynamic Scene Editor</h1>
                <p>Customize your lighting scenes with ease.</p>
            </div>

            <div class="content">
                <!-- Scene Selection -->
                <div class="scene-selector">
                    <label for="sceneSelect">Scene:</label>
                    <select id="sceneSelect" @change=${this.onSceneChange}>
                        <option value="">Select a scene...</option>
                        ${Object.keys(this.scenes).map(sceneName =>
                            html`<option value="${sceneName}" ?selected=${this.selectedScene === sceneName}>
                                ${sceneName}
                            </option>`
                        )}
                    </select>

                    <button class="btn btn-primary" @click=${this.addNewScene}>
                        Add Scene
                    </button>

                    <button class="btn btn-danger" @click=${this.deleteScene} ?disabled=${!this.selectedScene}>
                        Delete Scene
                    </button>

                    <button class="btn btn-success" @click=${this.saveScenes} ?disabled=${!this.selectedScene}>
                        Save Changes
                    </button>
                </div>

                ${this.selectedScene ? this.renderSceneEditor() : html`
                    <div class="empty-state">
                        <h3>Select a scene to begin editing</h3>
                        <p>Choose a scene from the dropdown menu or create a new one</p>
                    </div>
                `}
            </div>
        </div>
      </body>
    `;
  }

  renderSceneEditor() {
    const scene = this.scenes[this.selectedScene];
    if (!scene) return html``;

    return html`
      <div class="scene-editor">
        <!-- Priority Setting -->
        <div class="priority-display">
            <label for="priorityInput">Priority:</label>
            <input type="number" id="priorityInput" min="1" max="10"
                   .value=${scene.priority || 1}
                   @change=${this.updatePriority}>
            <span>(Higher values take precedence)</span>
        </div>

        <!-- Time Slots -->
        <div class="time-slots-section">
            <div class="section-header">
                <h3>Time Slots</h3>
                <button class="btn btn-primary" @click=${this.addTimeSlot}>
                    Add Time Slot
                </button>
            </div>

            ${Object.keys(scene.times || {}).length === 0 ?
                html`<div class="empty-state">Nothing here. Add a time slot to start editing.</div>` :
                Object.entries(scene.times).map(([time, entities]) =>
                    this.renderTimeSlot(time, entities)
                )
            }
        </div>
      </div>
    `;
  }

  renderTimeSlot(time, entities) {
    return html`
      <div class="time-slot">
        <div class="time-slot-header">
          <div class="time-controls">
            <label>Time: <b>${time}</b></label>
          </div>
          <button class="btn btn-danger btn-sm" @click=${() => this.removeTimeSlot(time)}>
            Remove Time Slot
          </button>
        </div>

        <div class="time-slot-content">
          <div class="entities-section">
            <div class="section-header">
              <h4>Entity Groups</h4>
              <button class="btn btn-primary btn-sm" @click=${() => this.addEntityGroup(time)}>
                Add Entity Group
              </button>
            </div>

            </br>
            ${entities && entities.length > 0 ?
              entities.map((entityGroup, index) =>
                this.renderEntityGroup(time, index, entityGroup)
              ) :
              html`<div class="empty-state">No entity groups found. Add an entity group to start editing.</div>`
            }
          </div>
        </div>
      </div>
    `;
  }

  renderEntityGroup(time, groupIndex, entityGroup) {
    const lightEntities = this.hass ?
      Object.keys(this.hass.states).filter(id => id.startsWith('light.')) : [];

    return html`
      <div class="entity-group">
        <div class="entity-group-header">
          <h5>Entity Group ${groupIndex + 1}</h5>
          <button class="btn btn-danger btn-sm" @click=${() => this.removeEntityGroup(time, groupIndex)}>
            Remove Group
          </button>
        </div>

        <div class="controls-grid">
          <!-- Brightness Control -->
          <div class="control-group">
            <label>Brightness (0-255)</label>
            <input type="range" min="0" max="255"
                   .value=${entityGroup.brightness || 0}
                   @input=${(e) => this.updateEntityGroupProperty(time, groupIndex, 'brightness', parseInt(e.target.value))}
                   class="slider brightness-slider">
            <span class="value-display">${entityGroup.brightness || 0}</span>
          </div>

          <!-- Color Temperature Control -->
          <div class="control-group">
            <label>Color Temperature (153-500)</label>
            <input type="range" min="153" max="500"
                   .value=${entityGroup.color_temp || 200}
                   @input=${(e) => this.updateEntityGroupProperty(time, groupIndex, 'color_temp', parseInt(e.target.value))}
                   class="slider temp-slider">
            <span class="value-display">${entityGroup.color_temp || 200}</span>
          </div>

        <!-- Entity Selection -->
        <div class="entity-selection">
          <label>Select Entities:</label>
          <div class="entity-checkboxes">
            ${lightEntities.map(entityId => html`
              <div class="checkbox-item">
                <input type="checkbox"
                       .checked=${(entityGroup.entities || []).includes(entityId)}
                       @change=${(e) => this.toggleEntity(time, groupIndex, entityId, e.target.checked)}
                      ?disabled=${this.isEntityUsedElsewhere(time, groupIndex, entityId)}
                       >
                <label>${entityId}</label>
              </div>
            `)}
          </div>
        </div>
      </div>
    `;
  }

  static get styles() {
    return css`
      body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: #1c1c1c;
        min-height: 100vh;
        padding: 20px;
        margin: 0;
      }

      .container {
        max-width: 1200px;
        margin: 0 auto;
        background: #1c1c1c;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        overflow: hidden;
      }

      .header {
        background: #1c1c1c;
        color: white;
        padding: 30px;
        text-align: center;
      }

      .header h1 {
        font-size: 2.5rem;
        margin-bottom: 10px;
        margin-top: 0;
      }

      .content {
        padding: 30px;
        background: #1c1c1c;
      }

      .scene-selector {
        display: flex;
        gap: 15px;
        align-items: center;
        margin-bottom: 30px;
        flex-wrap: wrap;
      }

      .scene-selector label {
        font-weight: 600;
      }

      select, input[type="number"], input[type="time"], input[type="text"] {
        padding: 10px 15px;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        font-size: 14px;
        transition: all 0.3s ease;
      }

      select:focus, input:focus {
        outline: none;
        border-color: #03a9f4;
        box-shadow: 0 0 0 3px rgba(3, 169, 244, 0.2);
      }

      .btn {
        padding: 10px 20px;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        text-decoration: none;
      }

      .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .btn-sm {
        padding: 5px 10px;
        font-size: 12px;
      }

      .btn-primary {
        background: #03a9f4;
        color: white;
      }

      .btn-success {
        background: #4caf50;
        color: white;
      }

      .btn-danger {
        background: #f44336;
        color: white;
      }

      .priority-display {
        background: #1c1c1c;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .time-slots-section {
        margin-top: 20px;
        background: #1c1c1c;
      }

      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
      }

      .section-header h3, .section-header h4 {
        margin: 0;
      }

      .time-slot {
        background: #1c1c1c;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        margin-bottom: 25px;
        overflow: hidden;
      }

      .time-slot-header {
        background: #2196f3;
        color: white;
        padding: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .time-controls {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .time-slot-content {
        padding: 20px;
      }

      .entity-group {
        background: #1c1c1c;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
      }

      .entity-group-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
      }

      .entity-group-header h5 {
        margin: 0;
      }

      .controls-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 20px;
        margin-bottom: 20px;
      }

      @media (max-width: 768px) {
        .controls-grid {
          grid-template-columns: 1fr;
        }
      }

      .control-group {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .control-group label {
        font-weight: 600;
        color: white;
        font-size: 14px;
      }

      .slider {
        width: 100%;
        height: 8px;
        border-radius: 4px;
        outline: none;
        -webkit-appearance: none;
        appearance: none;
      }

      .brightness-slider {
        background: linear-gradient(to right, #000, #fff);
      }

      .temp-slider {
        background: linear-gradient(to right, #ff6b35, #f7931e, #ffcc02, #fff200, #c4e17f, #00bcd4);
      }

      .slider::-webkit-slider-thumb {
        appearance: none;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: #2196f3;
        cursor: pointer;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
      }

      .value-display {
        font-weight: bold;
        color: #2196f3;
        text-align: center;
      }

      .entity-selection {
        margin-top: 15px;
      }

      .entity-selection label {
        font-weight: 600;
        display: block;
      }

      .entity-checkboxes {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 10px;
        max-height: 200px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 10px;
      }

      .checkbox-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: #1c1c1c;
        border-radius: 6px;
        transition: background-color 0.2s;
      }

      .checkbox-item label {
        display: flex;
        vertical-align: middle;
        line-height: 1;
      }

      .checkbox-item:hover {
        background: #1c1c1c;
      }

      .checkbox-item input[type="checkbox"] {
        width: 16px;
        height: 16px;
        accent-color: #2196f3;
        vertical-align: middle;
        margin: 0;
        flex-shrink: 0;
      }

      .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: #9e9e9e;
      }

      .empty-state h3 {
        margin-top: 0;
      }
    `;
  }

  // Event Handlers
  onSceneChange(e) {
    this.selectedScene = e.target.value || null;
    this.requestUpdate();
  }

  addNewScene() {
    const sceneName = prompt('Enter new scene name:');
    if (sceneName && !this.scenes[sceneName]) {
      this.scenes = {
        ...this.scenes,
        [sceneName]: {
          priority: 1,
          times: {}
        }
      };
      this.selectedScene = sceneName;
      this.requestUpdate();
    }
  }

  deleteScene() {
    if (!this.selectedScene) return;

    if (confirm(`Are you sure you want to delete scene "${this.selectedScene}"?`)) {
      const newScenes = { ...this.scenes };
      delete newScenes[this.selectedScene];
      this.scenes = newScenes;

      const sceneNames = Object.keys(this.scenes);
      this.selectedScene = sceneNames.length > 0 ? sceneNames[0] : null;
      this.requestUpdate();
    }
  }

  updatePriority(e) {
    if (this.selectedScene && this.scenes[this.selectedScene]) {
      this.scenes[this.selectedScene].priority = parseInt(e.target.value) || 1;
      this.requestUpdate();
    }
  }

  addTimeSlot() {
    if (!this.selectedScene) return;

    const timeSlot = prompt('Enter time (HH:MM format):', '08:00');
    if (timeSlot && this.scenes[this.selectedScene]) {
      if (!this.scenes[this.selectedScene].times[timeSlot]) {
        this.scenes[this.selectedScene].times[timeSlot] = [];
        this.requestUpdate();
      }
    }
  }

  removeTimeSlot(time) {
    if (this.selectedScene && this.scenes[this.selectedScene]?.times[time]) {
      delete this.scenes[this.selectedScene].times[time];
      this.requestUpdate();
    }
  }

  addEntityGroup(time) {
    if (!this.selectedScene || !this.scenes[this.selectedScene]?.times[time]) return;

    this.scenes[this.selectedScene].times[time].push({
      brightness: 100,
      color_temp: 200,
      entities: []
    });
    this.requestUpdate();
  }

  removeEntityGroup(time, groupIndex) {
    if (!this.selectedScene || !this.scenes[this.selectedScene]?.times[time]) return;

    this.scenes[this.selectedScene].times[time].splice(groupIndex, 1);
    this.requestUpdate();
  }

  updateEntityGroupProperty(time, groupIndex, property, value) {
    if (!this.selectedScene || !this.scenes[this.selectedScene]?.times[time]) return;

    this.scenes[this.selectedScene].times[time][groupIndex][property] = value;
    this.requestUpdate();
  }

  toggleEntity(time, groupIndex, entityId, checked) {
    if (!this.selectedScene || !this.scenes[this.selectedScene]?.times[time]) return;

    const entities = this.scenes[this.selectedScene].times[time][groupIndex].entities || [];

    if (checked && !entities.includes(entityId)) {
      entities.push(entityId);
    } else if (!checked && entities.includes(entityId)) {
      const index = entities.indexOf(entityId);
      entities.splice(index, 1);
    }

    this.scenes[this.selectedScene].times[time][groupIndex].entities = entities;
    this.requestUpdate();
  }

  // API Methods
  async loadScenes() {
    console.log("Loading scenes from API...");
    try {
      const response = await this.hass.callApi("get", "dynamic_scenes/data");
      this.scenes = response || {};

      const sceneNames = Object.keys(this.scenes);
      if (sceneNames.length > 0 && !this.selectedScene) {
        this.selectedScene = sceneNames[0];
      }

      this.requestUpdate();
      console.log("Scenes loaded:", this.scenes);
    } catch (error) {
      console.error("Failed to load scenes:", error);
      alert("Failed to load scenes. Please check the console for details.");
    }
  }

  async saveScenes() {
    console.log("Saving scenes to API...");
    try {
      await this.hass.callApi("post", "dynamic_scenes/data", this.scenes);
      alert("Scenes saved successfully!");
      console.log("Scenes saved:", this.scenes);
    } catch (error) {
      console.error("Failed to save scenes:", error);
      alert("Failed to save scenes. Please check the console for details.");
    }
  }

  // Helper Method
  // Returns whether an entity has been selected in the different entity group under the same timeslot
  isEntityUsedElsewhere(time, currentGroupIndex, entityId) {
    if (!this.selectedScene || !this.scenes[this.selectedScene]?.times[time]) return false;

    const entityGroups = this.scenes[this.selectedScene].times[time];
    return entityGroups.some((group, index) =>
      index !== currentGroupIndex && (group.entities || []).includes(entityId)
    );
  }

}

customElements.define("dynamic-scenes", DynamicScenes);