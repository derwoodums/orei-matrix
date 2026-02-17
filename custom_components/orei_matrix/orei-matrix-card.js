/**
 * OREI Matrix Card — Custom Lovelace card for OREI HDMI/HDBaseT matrix switcher.
 *
 * Two views: Matrix Grid and List. Power toggle and preset buttons at top.
 */

const CARD_VERSION = "1.2.0";

class OreiMatrixCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._view = "grid";
    this._built = false;
    this._lastStateHash = "";
    this._entityCache = null;
  }

  setConfig(config) {
    this._config = {
      title: config.title || "OREI Matrix",
      entity_prefix: config.entity_prefix || "orei_matrix",
      num_inputs: config.num_inputs || 4,
      num_outputs: config.num_outputs || 4,
      show_signal: config.show_signal !== false,
      ...config,
    };
    this._built = false;
  }

  static getStubConfig() {
    return { title: "OREI Matrix" };
  }

  set hass(hass) {
    this._hass = hass;

    // Discover entities once
    if (!this._entityCache) {
      this._discoverEntities();
    }

    // Build the DOM structure once, then only update values
    if (!this._built) {
      this._buildDom();
      this._built = true;
    }

    // Compute a hash of relevant state to avoid unnecessary updates
    const hash = this._computeStateHash();
    if (hash !== this._lastStateHash) {
      this._lastStateHash = hash;
      this._updateDom();
    }
  }

  // ── Entity discovery (runs once) ─────────────────────────────

  _discoverEntities() {
    if (!this._hass) return;

    this._entityCache = {
      power: null,
      outputs: [],
      inputSignals: [],
    };

    // Power switch
    for (const [id, e] of Object.entries(this._hass.states)) {
      if (id.startsWith("switch.") && id.includes("orei") && id.includes("power")) {
        this._entityCache.power = { id, entity: e };
        break;
      }
    }

    // Output select entities
    for (let i = 1; i <= this._config.num_outputs; i++) {
      const regex = new RegExp(`^select\\..*orei.*output_?${i}$`);
      for (const [id, e] of Object.entries(this._hass.states)) {
        if (regex.test(id)) {
          this._entityCache.outputs.push({ id, num: i });
          break;
        }
      }
    }
    // Fallback: find all orei select entities
    if (this._entityCache.outputs.length === 0) {
      for (const [id, e] of Object.entries(this._hass.states)) {
        if (id.startsWith("select.") && id.includes("orei")) {
          this._entityCache.outputs.push({ id, num: this._entityCache.outputs.length + 1 });
        }
      }
    }

    // Input signal sensors
    for (let i = 1; i <= this._config.num_inputs; i++) {
      const regex = new RegExp(`^binary_sensor\\..*orei.*input_?${i}_?signal$`);
      for (const [id, e] of Object.entries(this._hass.states)) {
        if (regex.test(id)) {
          this._entityCache.inputSignals.push({ id, num: i });
          break;
        }
      }
    }

    console.debug("OREI card entities:", this._entityCache);
  }

  _getState(entityId) {
    return this._hass ? this._hass.states[entityId] : null;
  }

  _computeStateHash() {
    if (!this._entityCache) return "";
    const parts = [];
    const pw = this._entityCache.power;
    if (pw) {
      const s = this._getState(pw.id);
      parts.push(s ? s.state : "?");
    }
    for (const out of this._entityCache.outputs) {
      const s = this._getState(out.id);
      parts.push(s ? s.state : "?");
    }
    for (const sig of this._entityCache.inputSignals) {
      const s = this._getState(sig.id);
      parts.push(s ? s.state : "?");
    }
    return parts.join(",");
  }

  // ── Actions ──────────────────────────────────────────────────

  _togglePower() {
    if (!this._entityCache?.power) return;
    this._hass.callService("switch", "toggle", {
      entity_id: this._entityCache.power.id,
    });
  }

  _selectSource(outputEntityId, sourceName) {
    this._hass.callService("select", "select_option", {
      entity_id: outputEntityId,
      option: sourceName,
    });
  }


  // ── Build DOM (runs once) ────────────────────────────────────

  _buildDom() {
    const root = this.shadowRoot;
    root.innerHTML = "";

    const style = document.createElement("style");
    style.textContent = this._styles();
    root.appendChild(style);

    const card = document.createElement("ha-card");
    root.appendChild(card);

    // Header
    const header = document.createElement("div");
    header.className = "card-header";
    header.innerHTML = `
      <span class="title">${this._config.title}</span>
      <div class="header-controls">
        <button class="view-toggle" id="viewToggle">
          ${this._view === "grid" ? "☰ List" : "▦ Grid"}
        </button>
        <button class="power-btn" id="powerBtn">⏻</button>
      </div>
    `;
    card.appendChild(header);

    header.querySelector("#viewToggle").addEventListener("click", () => {
      this._view = this._view === "grid" ? "list" : "grid";
      this._built = false;
      this._lastStateHash = "";
      this._buildDom();
      this._updateDom();
    });

    header.querySelector("#powerBtn").addEventListener("click", () => {
      this._togglePower();
    });

    // Content
    const content = document.createElement("div");
    content.className = "card-content";
    content.id = "content";
    card.appendChild(content);

    // Build grid or list
    if (this._view === "grid") {
      this._buildGrid(content);
    } else {
      this._buildList(content);
    }
  }

  _buildGrid(container) {
    const outputs = this._entityCache?.outputs || [];
    const numInputs = this._config.num_inputs;

    if (outputs.length === 0) {
      container.innerHTML += '<div class="empty">No output entities found</div>';
      return;
    }

    const table = document.createElement("table");
    const wrapper = document.createElement("div");
    wrapper.className = "matrix-grid";
    wrapper.appendChild(table);

    // Header row
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    headerRow.appendChild(document.createElement("th")); // empty corner
    for (let i = 1; i <= numInputs; i++) {
      const th = document.createElement("th");
      if (this._config.show_signal) {
        const dot = document.createElement("span");
        dot.className = "signal-dot";
        dot.id = `input-signal-${i}`;
        th.appendChild(dot);
      }
      const label = document.createElement("span");
      label.id = `input-name-${i}`;
      label.textContent = `Input ${i}`;
      th.appendChild(label);
      headerRow.appendChild(th);
    }
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Output rows
    const tbody = document.createElement("tbody");
    for (const out of outputs) {
      const tr = document.createElement("tr");
      const labelTd = document.createElement("td");
      labelTd.className = "row-label";
      labelTd.id = `output-name-${out.num}`;
      labelTd.textContent = `Output ${out.num}`;
      tr.appendChild(labelTd);

      for (let i = 1; i <= numInputs; i++) {
        const td = document.createElement("td");
        const cell = document.createElement("div");
        cell.className = "grid-cell";
        cell.id = `cell-${out.num}-${i}`;
        cell.textContent = "○";
        cell.addEventListener("click", () => {
          this._selectSource(out.id, this._getInputName(i));
        });
        td.appendChild(cell);
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    container.appendChild(wrapper);
  }

  _buildList(container) {
    const outputs = this._entityCache?.outputs || [];

    if (outputs.length === 0) {
      container.innerHTML += '<div class="empty">No output entities found</div>';
      return;
    }

    const listDiv = document.createElement("div");
    listDiv.className = "list-view";

    for (const out of outputs) {
      const row = document.createElement("div");
      row.className = "list-row";

      const label = document.createElement("span");
      label.className = "list-label";
      label.id = `list-output-name-${out.num}`;
      label.textContent = `Output ${out.num}`;
      row.appendChild(label);

      const arrow = document.createElement("span");
      arrow.className = "list-arrow";
      arrow.textContent = "→";
      row.appendChild(arrow);

      const select = document.createElement("select");
      select.className = "source-select";
      select.id = `list-select-${out.num}`;
      for (let i = 1; i <= this._config.num_inputs; i++) {
        const opt = document.createElement("option");
        opt.id = `list-opt-${out.num}-${i}`;
        opt.value = `input${i}`;
        opt.textContent = `Input ${i}`;
        select.appendChild(opt);
      }
      select.addEventListener("change", (e) => {
        this._selectSource(out.id, e.target.value);
      });
      row.appendChild(select);

      if (this._config.show_signal) {
        const dot = document.createElement("span");
        dot.className = "signal-dot";
        dot.id = `list-output-signal-${out.num}`;
        row.appendChild(dot);
      }

      listDiv.appendChild(row);
    }
    container.appendChild(listDiv);
  }

  // ── Update DOM (runs on state change, no innerHTML) ──────────

  _shortName(friendlyName, outputNum) {
    // friendly_name is like "OREI HDP-MXB44H150 (192.168.1.100) Output 1"
    // We want just the last part after the device name.
    // Strategy: take the last word(s) that look like an output name.
    if (!friendlyName) return `Output ${outputNum}`;

    // If the name contains "Output", grab from "Output" onward
    const outputMatch = friendlyName.match(/Output\s*\d+/i);
    if (outputMatch) return outputMatch[0];

    // If the name contains "hdmi output", clean it up
    const hdmiMatch = friendlyName.match(/hdmi\s*output\s*\d+/i);
    if (hdmiMatch) return `Output ${outputNum}`;

    // If it's a custom name the user set (e.g., "Great Room"),
    // it'll be at the end after the device prefix.
    // Split on the last known device-name-like pattern and take the remainder.
    const parts = friendlyName.split(/\)\s*/);
    if (parts.length > 1) {
      const tail = parts[parts.length - 1].trim();
      if (tail) return tail;
    }

    return `Output ${outputNum}`;
  }

  _getInputName(inputNum) {
    if (!this._entityCache?.outputs.length) return `input${inputNum}`;
    const firstOut = this._getState(this._entityCache.outputs[0].id);
    if (firstOut?.attributes?.options) {
      const list = firstOut.attributes.options;
      if (inputNum <= list.length) return list[inputNum - 1];
    }
    return `input${inputNum}`;
  }

  _updateDom() {
    if (!this._hass || !this._entityCache) return;

    const root = this.shadowRoot;

    // Power button
    const powerBtn = root.getElementById("powerBtn");
    if (powerBtn && this._entityCache.power) {
      const pw = this._getState(this._entityCache.power.id);
      const isOn = pw && pw.state === "on";
      powerBtn.className = `power-btn ${isOn ? "on" : "off"}`;
      powerBtn.textContent = `⏻ ${isOn ? "ON" : "OFF"}`;
    }

    // Get input names from first output entity's options
    const inputNames = [];
    if (this._entityCache.outputs.length > 0) {
      const firstOut = this._getState(this._entityCache.outputs[0].id);
      if (firstOut?.attributes?.options) {
        inputNames.push(...firstOut.attributes.options);
      }
    }
    if (inputNames.length === 0) {
      for (let i = 1; i <= this._config.num_inputs; i++) {
        inputNames.push(`input${i}`);
      }
    }

    // Update input name labels
    for (let i = 1; i <= this._config.num_inputs; i++) {
      const label = root.getElementById(`input-name-${i}`);
      if (label) label.textContent = inputNames[i - 1] || `Input ${i}`;
    }

    // Update input signal dots
    for (const sig of this._entityCache.inputSignals) {
      const dot = root.getElementById(`input-signal-${sig.num}`);
      if (dot) {
        const s = this._getState(sig.id);
        dot.className = `signal-dot ${s && s.state === "on" ? "active" : "inactive"}`;
      }
    }

    // Power state for disabling controls
    const pwState = this._entityCache.power ? this._getState(this._entityCache.power.id) : null;
    const isPowerOn = pwState && pwState.state === "on";

    // Update outputs
    for (const out of this._entityCache.outputs) {
      const s = this._getState(out.id);
      const currentSource = s?.state;
      // Use just the entity's own name, not the full friendly_name which
      // includes the device name prefix. Fall back to "Output N".
      const friendlyName = s?.attributes?.friendly_name || "";
      const outName = this._shortName(friendlyName, out.num);

      // Output name labels
      const nameEl = root.getElementById(`output-name-${out.num}`);
      if (nameEl) nameEl.textContent = outName;
      const listNameEl = root.getElementById(`list-output-name-${out.num}`);
      if (listNameEl) listNameEl.textContent = outName;

      if (this._view === "grid") {
        // Update grid cells
        for (let i = 1; i <= this._config.num_inputs; i++) {
          const cell = root.getElementById(`cell-${out.num}-${i}`);
          if (cell) {
            const isActive = currentSource === inputNames[i - 1];
            cell.className = `grid-cell ${isActive ? "active" : ""} ${!isPowerOn ? "disabled" : ""}`;
            cell.textContent = isActive ? "●" : "○";
          }
        }
      } else {
        // Update list dropdowns — only update if dropdown is not focused
        const select = root.getElementById(`list-select-${out.num}`);
        if (select && document.activeElement !== select && root.activeElement !== select) {
          select.disabled = !isPowerOn;
          // Update option labels
          for (let i = 1; i <= this._config.num_inputs; i++) {
            const opt = root.getElementById(`list-opt-${out.num}-${i}`);
            if (opt) {
              opt.value = inputNames[i - 1] || `input${i}`;
              opt.textContent = inputNames[i - 1] || `Input ${i}`;
              opt.selected = (inputNames[i - 1] === currentSource);
            }
          }
        }

        // Output signal dot
        if (this._config.show_signal) {
          const dot = root.getElementById(`list-output-signal-${out.num}`);
          if (dot) {
            const connected = s?.attributes?.signal_connected;
            dot.className = `signal-dot ${connected ? "active" : "inactive"}`;
          }
        }
      }
    }
  }

  _styles() {
    return `
      :host {
        --primary-color: var(--ha-card-header-color, #03a9f4);
        --active-color: #4caf50;
        --inactive-color: #9e9e9e;
        --cell-size: 40px;
      }

      ha-card {
        padding: 0;
      }

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 16px 8px;
      }

      .title {
        font-size: 1.2em;
        font-weight: 500;
      }

      .header-controls {
        display: flex;
        gap: 8px;
      }

      .view-toggle, .power-btn, .preset-btn {
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 4px;
        padding: 4px 12px;
        cursor: pointer;
        font-size: 0.85em;
        background: var(--card-background-color, #fff);
        color: var(--primary-text-color, #212121);
      }

      .view-toggle:hover, .preset-btn:hover {
        background: var(--secondary-background-color, #f5f5f5);
      }

      .power-btn.on {
        background: var(--active-color);
        color: white;
        border-color: var(--active-color);
      }

      .power-btn.off {
        background: var(--inactive-color);
        color: white;
        border-color: var(--inactive-color);
      }

      .card-content {
        padding: 0 16px 16px;
      }

      .matrix-grid {
        overflow-x: auto;
      }

      .matrix-grid table {
        width: 100%;
        border-collapse: collapse;
      }

      .matrix-grid th, .matrix-grid td {
        text-align: center;
        padding: 4px;
        font-size: 0.85em;
      }

      .matrix-grid th {
        font-weight: 500;
        white-space: nowrap;
      }

      .row-label {
        text-align: left !important;
        font-weight: 500;
        white-space: nowrap;
        padding-right: 12px !important;
      }

      .grid-cell {
        width: var(--cell-size);
        height: var(--cell-size);
        line-height: var(--cell-size);
        border-radius: 4px;
        cursor: pointer;
        margin: 2px auto;
        transition: background 0.2s;
        user-select: none;
      }

      .grid-cell:hover:not(.disabled) {
        background: var(--secondary-background-color, #f0f0f0);
      }

      .grid-cell.active {
        background: var(--active-color);
        color: white;
        font-weight: bold;
      }

      .grid-cell.disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }

      .list-view {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .list-row {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 8px;
      }

      .list-label {
        font-weight: 500;
        min-width: 120px;
        flex-shrink: 0;
      }

      .list-arrow {
        color: var(--inactive-color);
      }

      .source-select {
        flex: 1;
        padding: 6px 8px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 4px;
        background: var(--card-background-color, #fff);
        color: var(--primary-text-color, #212121);
        font-size: 0.9em;
      }

      .signal-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin: 0 2px;
        flex-shrink: 0;
      }

      .signal-dot.active {
        background: var(--active-color);
      }

      .signal-dot.inactive {
        background: var(--inactive-color);
      }

      .empty {
        text-align: center;
        color: var(--secondary-text-color, #757575);
        padding: 24px;
      }
    `;
  }

  getCardSize() {
    return 5;
  }
}

customElements.define("orei-matrix-card", OreiMatrixCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "orei-matrix-card",
  name: "OREI Matrix Card",
  description: "Control panel for OREI HDMI/HDBaseT matrix switcher",
  preview: true,
});

console.info(`%c OREI-MATRIX-CARD %c v${CARD_VERSION} `, "background:#03a9f4;color:white;font-weight:bold", "background:#eee;color:#03a9f4");
