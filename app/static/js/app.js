"use strict";
const API_BASE = "/api/v1";
const CACHE_TTL_MS = 30_000;

const state = {
    databases: null,
    databasesFetchedAt: 0,
    databasesRequest: null,

    schemas: new Map(),
    schemaRequests: new Map(),
    selectedDatabaseId: null,
    selectedObject: null,

    statistics: new Map(),
    statisticsRequests: new Map(),
    selectedStatisticsDatabaseId: null,

    selectedTableData: null,
    tableDataOffset: 0,
    tableDataLimit: 50,

    dataModalContent: "",
    dataModalView: "value",
    dataModalRecord: null,
};

const elements = {
    totalDatabases: document.querySelector("#total-databases"),
    totalStorage: document.querySelector("#total-storage"),
    totalTables: document.querySelector("#total-tables"),
    databaseCount: document.querySelector("#database-count"),
    databaseTableBody: document.querySelector("#database-table-body"),
    inventoryMessage: document.querySelector("#inventory-message"),
    lastUpdated: document.querySelector("#last-updated"),
    refreshButton: document.querySelector("#refresh-button"),
    uploadButton: document.querySelector("#upload-button"),
    notice: document.querySelector("#app-notice"),
    breadcrumb: document.querySelector("#breadcrumb-current"),
    navigation: document.querySelectorAll("[data-view]"),
    databaseFileInput: document.querySelector("#database-file-input"),
    schemaView: document.querySelector("#schema-view"),
    schemaDatabaseSelect: document.querySelector("#schema-database-select"),
    schemaDatabaseMeta: document.querySelector("#schema-database-meta"),
    schemaRefreshButton: document.querySelector("#schema-refresh-button"),
    schemaTableCount: document.querySelector("#schema-table-count"),
    schemaViewCount: document.querySelector("#schema-view-count"),
    schemaColumnCount: document.querySelector("#schema-column-count"),
    schemaIndexCount: document.querySelector("#schema-index-count"),
    schemaObjectList: document.querySelector("#schema-object-list"),
    schemaDetailTitle: document.querySelector("#schema-detail-title"),
    schemaDetailDescription: document.querySelector("#schema-detail-description"),
    schemaDetailContent: document.querySelector("#schema-detail-content"),
    statisticsView: document.querySelector("#statistics-view"),
    statisticsDatabaseSelect: document.querySelector("#statistics-database-select"),
    statisticsDatabaseMeta: document.querySelector("#statistics-database-meta"),
    statisticsRefreshButton: document.querySelector("#statistics-refresh-button"),
    statisticsTableCount: document.querySelector("#stats-table-count"),
    statisticsTotalRows: document.querySelector("#stats-total-rows"),
    statisticsTotalColumns: document.querySelector("#stats-total-columns"),
    statisticsStorage: document.querySelector("#stats-storage"),
    statisticsTableBody: document.querySelector("#statistics-table-body"),
    statisticsMessage: document.querySelector("#statistics-message"),
    statisticsLastUpdated: document.querySelector("#statistics-last-updated"),
    tableDataDescription: document.querySelector("#table-data-description"),
    tableDataRefreshButton: document.querySelector("#table-data-refresh-button"),
    tableDataMessage: document.querySelector("#table-data-message"),
    tableDataCount: document.querySelector("#table-data-count"),
    tableDataHead: document.querySelector("#table-data-head"),
    tableDataBody: document.querySelector("#table-data-body"),
    tableDataPage: document.querySelector("#table-data-page"),
    tableDataPrevious: document.querySelector("#table-data-previous"),
    tableDataNext: document.querySelector("#table-data-next"),
    dataModal: document.querySelector("#table-data-modal"),
    dataModalTitle: document.querySelector("#data-modal-title"),
    dataModalMeta: document.querySelector("#data-modal-meta"),
    dataModalClose: document.querySelector("#data-modal-close"),
    dataModalTabs: document.querySelectorAll("[data-modal-view]"),
    dataModalPanels: document.querySelectorAll("[data-modal-panel]"),
    dataModalValue: document.querySelector("#data-modal-value"),
    dataModalRow: document.querySelector("#data-modal-row"),
    dataModalJson: document.querySelector("#data-modal-json"),
    dataModalSize: document.querySelector("#data-modal-size"),
    dataModalCopy: document.querySelector("#data-modal-copy"),
};

function formatBytes(bytes) {
    if (!Number.isFinite(bytes) || bytes < 0) {
        return "—";
    }

    if (bytes === 0) {
        return "0 B";
    }

    const units = ["B", "KB", "MB", "GB", "TB"];
    const unitIndex = Math.min(
        Math.floor(Math.log(bytes) / Math.log(1024)),
        units.length - 1,
    );

    const value = bytes / (1024 ** unitIndex);
    const decimals = unitIndex === 0 ? 0 : 2;

    return `${value.toLocaleString("es-ES", {
        maximumFractionDigits: decimals,
    })} ${units[unitIndex]}`;
}

function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleTimeString("es-ES", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
}

function showNotice(message, type = "info") {
    elements.notice.textContent = message;
    elements.notice.dataset.type = type;
    elements.notice.hidden = false;
}

function hideNotice() {
    elements.notice.hidden = true;
    elements.notice.textContent = "";
}

function setLoading(isLoading) {
    elements.refreshButton.disabled = isLoading;
    elements.refreshButton.classList.toggle("is-loading", isLoading);
    elements.refreshButton.setAttribute(
        "aria-busy",
        String(isLoading),
    );
}

function createCell(text, className = "") {
    const cell = document.createElement("td");
    cell.textContent = text;
    if (className) {
        cell.className = className;
    }
    return cell;
}

function renderDatabases(databases) {
    elements.databaseTableBody.replaceChildren();

    if (databases.length === 0) {
        const row = document.createElement("tr");
        const cell = createCell(
            "No databases found in the configured directory.",
            "empty-state",
        );
        cell.colSpan = 5;
        row.appendChild(cell);
        elements.databaseTableBody.appendChild(row);
        return;
    }

    for (const database of databases) {
        const row = document.createElement("tr");

        const nameCell = createCell(database.name);
        nameCell.classList.add("database-name");
        row.appendChild(nameCell);

        row.appendChild(
            createCell(String(database.engine).toUpperCase()),
        );

        row.appendChild(
            createCell(formatBytes(database.size_bytes)),
        );

        const statusCell = document.createElement("td");
        const statusBadge = document.createElement("span");
        statusBadge.className = `status-badge status-${database.status}`;
        statusBadge.textContent = database.status;
        statusCell.appendChild(statusBadge);
        row.appendChild(statusCell);

        const actionCell = createCell("");
        const actionButton = document.createElement("button");
        actionButton.type = "button";
        actionButton.className = "table-action";
        actionButton.textContent = "Details";
        actionButton.setAttribute(
            "aria-label",
            `View details for ${database.name}`,
        );
        actionButton.addEventListener("click", () => {
            state.selectedDatabaseId = database.id;

            elements.schemaDatabaseSelect.value = database.id;

            const schemaNavigationItem = document.querySelector(
                '[data-view="schema"]'
            );

            schemaNavigationItem?.click();
        });
        actionCell.appendChild(actionButton);
        row.appendChild(actionCell);

        elements.databaseTableBody.appendChild(row);
    }
}

function renderDashboard(databases) {
    const totalStorage = databases.reduce(
        (sum, database) => sum + database.size_bytes,
        0,
    );

    elements.totalDatabases.textContent = String(databases.length);
    elements.totalStorage.textContent = formatBytes(totalStorage);
    elements.databaseCount.textContent = String(databases.length);

    // Statistics will be populated when the statistics view is implemented.
    elements.totalTables.textContent = "—";

    renderDatabases(databases);

    elements.inventoryMessage.textContent =
        `${databases.length} database${databases.length === 1 ? "" : "s"} found`;

    elements.lastUpdated.textContent =
        `Updated at ${formatTimestamp(state.databasesFetchedAt)}`;

    populateSchemaSelect(databases);
}

function populateStatisticsSelect(databases) {
    const select = elements.statisticsDatabaseSelect;
    const previousSelection = state.selectedStatisticsDatabaseId;

    select.replaceChildren();

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = databases.length
        ? "Select a database…"
        : "No databases available";

    select.appendChild(placeholder);

    databases.forEach((database) => {
        const option = document.createElement("option");
        option.value = database.id;
        option.textContent = database.name;
        select.appendChild(option);
    });

    const selectionExists = databases.some(
        (database) => database.id === previousSelection
    );

    const selectedId = selectionExists
        ? previousSelection
        : (databases[0]?.id ?? "");

    select.value = selectedId;
    state.selectedStatisticsDatabaseId = selectedId || null;
}

function populateSchemaSelect(databases) {
    const select = elements.schemaDatabaseSelect;
    const previousId = state.selectedDatabaseId;

    select.replaceChildren();

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = databases.length
        ? "Choose a database…"
        : "No databases available";
    select.appendChild(placeholder);

    for (const database of databases) {
        const option = document.createElement("option");
        option.value = database.id;
        option.textContent = database.name;
        select.appendChild(option);
    }

    const selectionExists = databases.some(
        (database) => database.id === previousId,
    );

    if (selectionExists) {
        select.value = previousId;
    } else {
        state.selectedDatabaseId = null;
        select.value = "";
    }
}

function renderSchemaSummary(schema) {
    const columnCount = schema.tables.reduce(
        (sum, table) => sum + table.columns.length,
        0,
    );

    const indexCount = schema.tables.reduce(
        (sum, table) => sum + table.indexes.length,
        0,
    );

    elements.schemaTableCount.textContent = String(schema.tables.length);
    elements.schemaViewCount.textContent = String(schema.views.length);
    elements.schemaColumnCount.textContent = String(columnCount);
    elements.schemaIndexCount.textContent = String(indexCount);
}

function renderSchemaObjects(schema) {
    const container = elements.schemaObjectList;
    container.replaceChildren();
    state.selectedObject = null;

    const objects = [
        ...schema.tables.map((table) => ({
            name: table.name,
            type: "table",
            rowCount: table.row_count,
            data: table,
        })),
        ...schema.views.map((name) => ({
            name,
            type: "view",
            rowCount: null,
            data: null,
        })),
    ];

    if (objects.length === 0) {
        const empty = document.createElement("div");
        empty.className = "schema-empty";
        empty.textContent = "This database contains no tables or views.";
        container.appendChild(empty);
        renderSchemaDetails(null);
        return;
    }

    for (const object of objects) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "schema-object";

        const icon = document.createElement("span");
        icon.className = "schema-object-icon";
        icon.textContent = object.type === "table" ? "▦" : "◫";

        const name = document.createElement("span");
        name.className = "schema-object-name";
        name.textContent = object.name;

        const meta = document.createElement("span");
        meta.className = "schema-object-meta";
        meta.textContent = object.type === "table"
            ? `${object.rowCount.toLocaleString("es-ES")} rows`
            : "VIEW";

        button.append(icon, name, meta);

        button.addEventListener("click", () => {
            container.querySelectorAll(".schema-object").forEach((item) => {
                item.classList.remove("active");
            });

            button.classList.add("active");
            
            const previousObject = state.selectedObject;

            const tableChanged =
                !previousObject ||
                previousObject.name !== object.name ||
                previousObject.type !== object.type;

            state.selectedObject = object;

            if (tableChanged) {
                state.tableDataOffset = 0;
            }

            renderSchemaDetails(object);
            loadTableData(object);
        });

        container.appendChild(button);
    }

    const firstTable = objects.find((object) => object.type === "table");
    const firstObject = firstTable ?? objects[0];

    const firstButton = [...container.children].find(
        (button) =>
            button.querySelector(".schema-object-name")?.textContent
            === firstObject.name,
    );

    firstButton?.click();
}

function renderSchemaDetails(object) {
    elements.schemaDetailContent.replaceChildren();

    if (!object) {
        elements.schemaDetailTitle.textContent = "Object details";
        elements.schemaDetailDescription.textContent =
            "Select a table or view above.";

        const empty = document.createElement("div");
        empty.className = "schema-empty";
        empty.textContent = "No object selected.";
        elements.schemaDetailContent.appendChild(empty);
        return;
    }

    elements.schemaDetailTitle.textContent = object.name;

    if (object.type === "view") {
        elements.schemaDetailDescription.textContent =
            "View selected. Column metadata is not currently provided by the API.";

        const message = document.createElement("div");
        message.className = "schema-empty";
        message.textContent =
            "View columns are not available in the current API response.";
        elements.schemaDetailContent.appendChild(message);
        return;
    }

    const table = object.data;

    elements.schemaDetailDescription.textContent =
        `${table.row_count.toLocaleString("es-ES")} rows · `
        + `${table.columns.length} columns · `
        + `${table.indexes.length} indexes · `
        + `${table.foreign_keys.length} foreign keys`;

    const wrapper = document.createElement("div");
    wrapper.className = "table-wrapper";

    const htmlTable = document.createElement("table");
    htmlTable.className = "schema-detail-table";

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    for (const label of ["COLUMN", "TYPE", "NULLABLE", "KEY", "DEFAULT"]) {
        const th = document.createElement("th");
        th.textContent = label;
        headerRow.appendChild(th);
    }

    thead.appendChild(headerRow);
    htmlTable.appendChild(thead);

    const tbody = document.createElement("tbody");

    for (const column of table.columns) {
        const row = document.createElement("tr");

        const key = column.primary_key_position > 0 ? "PRIMARY KEY" : "—";
        const defaultValue = column.default_value ?? "—";

        for (const value of [
            column.name,
            column.declared_type || "—",
            column.nullable ? "YES" : "NO",
            key,
            defaultValue,
        ]) {
            const cell = document.createElement("td");
            cell.textContent = String(value);
            row.appendChild(cell);
        }

        if (column.primary_key_position > 0) {
            row.children[3].replaceChildren();
            const badge = document.createElement("span");
            badge.className = "schema-tag primary";
            badge.textContent = key;
            row.children[3].appendChild(badge);
        }

        tbody.appendChild(row);
    }

    htmlTable.appendChild(tbody);
    wrapper.appendChild(htmlTable);
    elements.schemaDetailContent.appendChild(wrapper);

    if (table.indexes.length > 0 || table.foreign_keys.length > 0) {
        const extra = document.createElement("div");
        extra.className = "schema-empty";

        const parts = [];

        if (table.indexes.length > 0) {
            parts.push(
                "Indexes: " + table.indexes.map((index) =>
                    `${index.name} (${index.columns.join(", ")})`
                ).join("; "),
            );
        }

        if (table.foreign_keys.length > 0) {
            parts.push(
                "Foreign keys: " + table.foreign_keys.map((fk) =>
                    `${fk.source_column} → ${fk.referenced_table}.${fk.referenced_column ?? "—"}`
                ).join("; "),
            );
        }

        extra.textContent = parts.join(" | ");
        elements.schemaDetailContent.appendChild(extra);
    }
}

async function loadTableData(object, { force = false } = {}) {
    if (!object || object.type !== "table") {
        state.selectedTableData = null;
        state.tableDataOffset = 0;

        elements.tableDataDescription.textContent =
            "Select a table to browse its records.";

        elements.tableDataMessage.textContent =
            object?.type === "view"
                ? "Views are not supported by the table-data endpoint yet."
                : "No table selected.";

        elements.tableDataCount.textContent = "—";
        elements.tableDataHead.replaceChildren();
        elements.tableDataBody.replaceChildren();

        elements.tableDataRefreshButton.disabled = true;
        elements.tableDataPrevious.disabled = true;
        elements.tableDataNext.disabled = true;
        elements.tableDataPage.textContent = "Page 1";

        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.className = "empty-state";
        cell.textContent = object?.type === "view"
            ? "Table data is currently available for tables only."
            : "Select a table to view its records.";
        row.appendChild(cell);
        elements.tableDataBody.appendChild(row);

        return;
    }

    const databaseId = state.selectedDatabaseId;
    if (!databaseId) {
        return;
    }

    const tableName = object.name;
    const limit = state.tableDataLimit;
    const offset = state.tableDataOffset;

    state.selectedTableData = {
        databaseId,
        tableName,
    };

    elements.tableDataDescription.textContent =
        `${tableName} · ${limit} records per page`;

    elements.tableDataMessage.textContent = "Loading table data…";
    elements.tableDataRefreshButton.disabled = true;
    elements.tableDataPrevious.disabled = true;
    elements.tableDataNext.disabled = true;

    const url =
        `${API_BASE}/databases/${encodeURIComponent(databaseId)}` +
        `/tables/${encodeURIComponent(tableName)}/rows` +
        `?limit=${limit}&offset=${offset}`;

    try {
        const response = await fetch(url, {
            cache: force ? "reload" : "default",
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(
                error.detail || `Request failed (${response.status})`
            );
        }

        const data = await response.json();

        // Ignore results if the user selected another table while loading.
        if (
            state.selectedDatabaseId !== databaseId ||
            state.selectedObject?.name !== tableName ||
            state.selectedObject?.type !== "table"
        ) {
            return;
        }

        renderTableData(data);
    } catch (error) {
        if (
            state.selectedDatabaseId !== databaseId ||
            state.selectedObject?.name !== tableName
        ) {
            return;
        }

        console.error("Failed to load table data:", error);
        elements.tableDataMessage.textContent =
            `Unable to load table data: ${error.message}`;
        elements.tableDataCount.textContent = "—";
        elements.tableDataRefreshButton.disabled = false;
        elements.tableDataPrevious.disabled = offset === 0;
        elements.tableDataNext.disabled = true;
    }
}

function renderTableData(data) {
    const head = elements.tableDataHead;
    const body = elements.tableDataBody;

    head.replaceChildren();
    body.replaceChildren();

    const headerRow = document.createElement("tr");

    for (const column of data.columns) {
        const th = document.createElement("th");
        th.textContent = column;
        headerRow.appendChild(th);
    }

    head.appendChild(headerRow);

    if (data.rows.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = Math.max(data.columns.length, 1);
        cell.className = "empty-state";
        cell.textContent = "No records found on this page.";

        row.appendChild(cell);
        body.appendChild(row);
    } else {
        for (const record of data.rows) {
            const row = document.createElement("tr");

            for (const column of data.columns) {
                const cell = document.createElement("td");
                const value = record[column];

                const displayValue =
                    value === null || value === undefined
                        ? "NULL"
                        : String(value);

                if (value === null || value === undefined) {
                    cell.classList.add("null-value");
                    cell.textContent = "NULL";
                } else if (displayValue.length > 120) {
                    const preview = document.createElement("button");
                    preview.type = "button";
                    preview.className = "data-cell-trigger";
                    preview.textContent =
                        `${displayValue.slice(0, 100)}…`;
                    preview.title = "Click to inspect full value";
                    preview.setAttribute(
                        "aria-label",
                        `Inspect full value of column ${column}`
                    );

                    preview.addEventListener("click", () => {
                        openDataModal(value, column, record);
                    });

                    cell.appendChild(preview);
                } else {
                    cell.textContent = displayValue;
                }

                row.appendChild(cell);
            }

            body.appendChild(row);
        }
    }

    const firstRow = data.total_rows === 0
        ? 0
        : data.offset + 1;

    const lastRow = Math.min(
        data.offset + data.rows.length,
        data.total_rows
    );

    elements.tableDataMessage.textContent =
        `${data.rows.length} records loaded.`;

    elements.tableDataCount.textContent =
        `${data.total_rows} total records`;

    elements.tableDataPage.textContent =
        `Rows ${firstRow}–${lastRow}`;

    elements.tableDataRefreshButton.disabled = false;
    elements.tableDataPrevious.disabled = data.offset === 0;
    elements.tableDataNext.disabled =
        data.offset + data.rows.length >= data.total_rows;
}

function setupTableDataControls() {
    elements.tableDataPrevious.addEventListener("click", () => {
        if (
            !state.selectedTableData ||
            elements.tableDataPrevious.disabled
        ) {
            return;
        }

        state.tableDataOffset = Math.max(
            0,
            state.tableDataOffset - state.tableDataLimit
        );

        loadTableData(state.selectedObject);
    });

    elements.tableDataNext.addEventListener("click", () => {
        if (
            !state.selectedTableData ||
            elements.tableDataNext.disabled
        ) {
            return;
        }

        state.tableDataOffset += state.tableDataLimit;

        loadTableData(state.selectedObject);
    });

    elements.tableDataRefreshButton.addEventListener("click", () => {
        if (!state.selectedTableData) {
            return;
        }

        loadTableData(state.selectedObject, { force: true });
    });
}

function setDataModalView(view) {
    state.dataModalView = view;

    for (const tab of elements.dataModalTabs) {
        const active = tab.dataset.modalView === view;
        tab.classList.toggle("active", active);
        tab.setAttribute("aria-selected", String(active));
    }

    for (const panel of elements.dataModalPanels) {
        panel.hidden = panel.dataset.modalPanel !== view;
    }

    if (view === "value") {
        state.dataModalContent = elements.dataModalValue.textContent;
    } else if (view === "row") {
        state.dataModalContent = JSON.stringify(
            state.dataModalRecord,
            null,
            2
        );
    } else {
        state.dataModalContent = elements.dataModalJson.textContent;
    }
}

function openDataModal(value, column, record) {
    const displayValue = value === null || value === undefined
        ? "NULL"
        : String(value);

    // Keep only the selected field instead of the entire row.
    const selectedField = {
        [column]: value
    };

    state.dataModalRecord = selectedField;

    elements.dataModalTitle.textContent = column;
    elements.dataModalMeta.textContent =
        `${state.selectedTableData?.tableName ?? "Table"} · ${column}`;

    elements.dataModalValue.textContent = displayValue;
    elements.dataModalJson.textContent = JSON.stringify(
        selectedField,
        null,
        2
    );

    elements.dataModalRow.replaceChildren();

    const fieldElement = document.createElement("div");
    fieldElement.className = "data-modal-row-field";
    fieldElement.textContent = column;

    const valueElement = document.createElement("div");
    valueElement.className = "data-modal-row-value";
    valueElement.textContent = displayValue;

    elements.dataModalRow.append(fieldElement, valueElement);

    elements.dataModalSize.textContent =
        `${displayValue.length.toLocaleString()} characters`;

    setDataModalView("value");
    elements.dataModal.setAttribute("aria-label", `Inspect ${column}`);

    if (!elements.dataModal.open) {
        elements.dataModal.showModal();
    }
}

function setupDataModal() {
    for (const tab of elements.dataModalTabs) {
        tab.addEventListener("click", () => {
            setDataModalView(tab.dataset.modalView);
        });
    }

    elements.dataModalClose.addEventListener("click", () => {
        elements.dataModal.close();
    });

    elements.dataModal.addEventListener("click", (event) => {
        if (event.target === elements.dataModal) {
            elements.dataModal.close();
        }
    });

    elements.dataModalCopy.addEventListener("click", async () => {
        try {
            await navigator.clipboard.writeText(state.dataModalContent);
            elements.dataModalCopy.textContent = "Copied!";

            window.setTimeout(() => {
                elements.dataModalCopy.textContent = "Copy content";
            }, 1500);
        } catch (error) {
            console.error("Unable to copy modal content:", error);
            elements.dataModalCopy.textContent = "Copy failed";
        }
    });
}

async function loadSchema(databaseId, { force = false } = {}) {
    if (!databaseId) {
        elements.schemaDatabaseMeta.textContent = "";
        elements.schemaObjectList.replaceChildren();
        renderSchemaSummary({ tables: [], views: [] });
        renderSchemaDetails(null);
        return;
    }

    elements.schemaDatabaseMeta.textContent = "Loading schema…";
    elements.schemaObjectList.textContent = "Loading schema…";

    try {
        const schema = await fetchSchema(databaseId, { force });

        state.selectedDatabaseId = databaseId;

        const database = state.databases?.find(
            (item) => item.id === databaseId,
        );

        elements.schemaDatabaseMeta.textContent = database
            ? `${database.name} · ${formatBytes(database.size_bytes)}`
            : databaseId;

        renderSchemaSummary(schema);
        renderSchemaObjects(schema);
    } catch (error) {
        console.error("Unable to load database schema:", error);
        elements.schemaDatabaseMeta.textContent = "Schema unavailable";
        elements.schemaObjectList.replaceChildren();

        const message = document.createElement("div");
        message.className = "schema-empty";
        message.textContent = error.message;
        elements.schemaObjectList.appendChild(message);

        renderSchemaSummary({ tables: [], views: [] });
        renderSchemaDetails(null);
    }
}

async function fetchDatabases({ force = false } = {}) {
    const cacheIsFresh =
        state.databases !== null &&
        Date.now() - state.databasesFetchedAt < CACHE_TTL_MS;

    if (!force && cacheIsFresh) {
        return state.databases;
    }

    // Reuse an existing request instead of issuing duplicate HTTP calls.
    if (state.databasesRequest) {
        return state.databasesRequest;
    }

    state.databasesRequest = (async () => {
        const response = await fetch(`${API_BASE}/databases`, {
            headers: {
                Accept: "application/json",
            },
        });

        if (!response.ok) {
            throw new Error(
                `The API returned HTTP ${response.status}.`,
            );
        }

        const payload = await response.json();

        if (
            !payload ||
            !Array.isArray(payload.items) ||
            typeof payload.total !== "number"
        ) {
            throw new Error("The API returned an unexpected response.");
        }

        state.databases = payload.items;
        state.databasesFetchedAt = Date.now();

        return state.databases;
    })();

    try {
        return await state.databasesRequest;
    } finally {
        state.databasesRequest = null;
    }
}

async function fetchSchema(databaseId, { force = false } = {}) {
    const cached = state.schemas.get(databaseId);
    const cacheIsFresh =
        cached && Date.now() - cached.fetchedAt < CACHE_TTL_MS;

    if (!force && cacheIsFresh) {
        return cached.data;
    }

    if (state.schemaRequests.has(databaseId)) {
        return state.schemaRequests.get(databaseId);
    }

    const request = (async () => {
        const response = await fetch(
            `${API_BASE}/databases/${encodeURIComponent(databaseId)}/schema`,
            { headers: { Accept: "application/json" } },
        );

        if (!response.ok) {
            throw new Error(
                `Schema request failed (HTTP ${response.status}).`,
            );
        }

        const schema = await response.json();

        if (
            !schema ||
            !Array.isArray(schema.tables) ||
            !Array.isArray(schema.views)
        ) {
            throw new Error("The API returned an unexpected schema response.");
        }

        state.schemas.set(databaseId, {
            data: schema,
            fetchedAt: Date.now(),
        });

        return schema;
    })();

    state.schemaRequests.set(databaseId, request);

    try {
        return await request;
    } finally {
        state.schemaRequests.delete(databaseId);
    }
}

function renderStatistics(data) {
    const summary = data.summary ?? {};
    const tables = data.tables ?? [];

    elements.statisticsTableCount.textContent =
        summary.table_count ?? 0;

    elements.statisticsTotalRows.textContent =
        Number(summary.total_rows ?? 0).toLocaleString("en-US");

    elements.statisticsTotalColumns.textContent =
        Number(summary.total_columns ?? 0).toLocaleString("en-US");

    elements.statisticsStorage.textContent =
        formatBytes(summary.size_bytes ?? 0);

    elements.statisticsTableBody.replaceChildren();

    if (tables.length === 0) {
        const row = document.createElement("tr");
        const cell = createCell("No tables found.");
        cell.colSpan = 5;
        cell.classList.add("empty-state");
        row.appendChild(cell);
        elements.statisticsTableBody.appendChild(row);
    } else {
        tables.forEach((table) => {
            const row = document.createElement("tr");

            row.appendChild(createCell(table.name));
            row.appendChild(createCell(
                Number(table.row_count ?? 0).toLocaleString("en-US")
            ));
            row.appendChild(createCell(table.column_count ?? 0));
            row.appendChild(createCell(table.index_count ?? 0));
            row.appendChild(createCell(table.foreign_key_count ?? 0));

            elements.statisticsTableBody.appendChild(row);
        });
    }

    elements.statisticsMessage.textContent =
        `${tables.length} table(s) analysed.`;

    elements.statisticsLastUpdated.textContent =
        `Updated ${new Date().toLocaleTimeString()}`;
}

async function loadStatistics(databaseId, { force = false } = {}) {
    if (!databaseId) {
        elements.statisticsDatabaseMeta.textContent =
            "No database selected.";

        elements.statisticsTableCount.textContent = "—";
        elements.statisticsTotalRows.textContent = "—";
        elements.statisticsTotalColumns.textContent = "—";
        elements.statisticsStorage.textContent = "—";
        elements.statisticsTableBody.replaceChildren();

        const row = document.createElement("tr");
        const cell = createCell("Select a database to view statistics.");
        cell.colSpan = 5;
        cell.classList.add("empty-state");
        row.appendChild(cell);
        elements.statisticsTableBody.appendChild(row);

        elements.statisticsMessage.textContent =
            "No statistics loaded.";

        elements.statisticsLastUpdated.textContent = "Not updated yet";
        return;
    }

    state.selectedStatisticsDatabaseId = databaseId;
    elements.statisticsDatabaseMeta.textContent = "Loading statistics…";
    elements.statisticsMessage.textContent = "Loading…";

    try {
        const data = await fetchStatistics(databaseId, { force });

        renderStatistics(data);

        const database = (state.databases ?? []).find(
            (item) => item.id === databaseId
        );

        elements.statisticsDatabaseMeta.textContent =
            database ? `${database.name} · ${database.engine}` : databaseId;
    } catch (error) {
        console.error("Could not load statistics:", error);

        elements.statisticsDatabaseMeta.textContent =
            "Statistics unavailable.";

        elements.statisticsMessage.textContent =
            error.message || "An unexpected error occurred.";
    }
}

async function fetchStatistics(databaseId, { force = false } = {}) {
    const cached = state.statistics.get(databaseId);

    if (
        !force &&
        cached &&
        Date.now() - cached.fetchedAt < CACHE_TTL_MS
    ) {
        return cached.data;
    }

    const pending = state.statisticsRequests.get(databaseId);

    if (pending) {
        return pending;
    }

    const request = (async () => {
        const response = await fetch(
            `${API_BASE}/databases/${encodeURIComponent(databaseId)}/statistics`
        );

        if (!response.ok) {
            throw new Error(
                `Could not load statistics (HTTP ${response.status}).`
            );
        }

        const data = await response.json();

        state.statistics.set(databaseId, {
            data,
            fetchedAt: Date.now(),
        });

        return data;
    })();

    state.statisticsRequests.set(databaseId, request);

    try {
        return await request;
    } finally {
        state.statisticsRequests.delete(databaseId);
    }
}

async function loadDatabases({ force = false } = {}) {
    hideNotice();
    setLoading(true);
    elements.inventoryMessage.textContent = "Loading database inventory…";

    try {
        const databases = await fetchDatabases({ force });
        renderDashboard(databases);
    } catch (error) {
        console.error("Unable to load database inventory:", error);

        if (state.databases !== null) {
            renderDashboard(state.databases);
            showNotice(
                "Unable to refresh the inventory. Showing the last cached data.",
                "error",
            );
        } else {
            elements.databaseTableBody.replaceChildren();

            const row = document.createElement("tr");
            const cell = createCell(
                "Could not load databases. Check that the API is running and retry.",
                "empty-state",
            );
            cell.colSpan = 5;
            row.appendChild(cell);
            elements.databaseTableBody.appendChild(row);

            elements.inventoryMessage.textContent = "Inventory unavailable";
            showNotice(error.message, "error");
        }
    } finally {
        setLoading(false);
    }
}

function setupNavigation() {
    const labels = {
        dashboard: "Dashboard",
        databases: "Databases",
        schema: "Schema Explorer",
        statistics: "Statistics",
    };

    function showView(view) {
        
        const isSchema = view === "schema";
        const isStatistics = view === "statistics";
        const isDashboard = view === "dashboard" || view === "databases";

        document.querySelector("#dashboard").hidden = !isDashboard;
        elements.schemaView.hidden = !isSchema;
        elements.statisticsView.hidden = !isStatistics;


        elements.schemaView.hidden = !isSchema;
        document.querySelector("#dashboard").hidden = !isDashboard;

        elements.navigation.forEach((item) => {
            item.classList.toggle(
                "active",
                item.dataset.view === view,
            );
        });

        elements.breadcrumb.textContent = labels[view] ?? "Dashboard";

        if (isDashboard) {
            loadDatabases();
        }

        if (isSchema) {
            loadDatabases().then(() => {
                populateSchemaSelect(state.databases ?? []);

                const databaseId = state.selectedDatabaseId
                    ?? elements.schemaDatabaseSelect.value;

                if (databaseId) {
                    elements.schemaDatabaseSelect.value = databaseId;
                    loadSchema(databaseId);
                } else {
                    loadSchema("");
                }
            });
        }

        if (view === "statistics") {
            hideNotice();

            loadDatabases().then(() => {
                const databases = state.databases ?? [];

                populateStatisticsSelect(databases);

                loadStatistics(
                    elements.statisticsDatabaseSelect.value
                );
            });
        } else {
            hideNotice();
        }
    }

    elements.navigation.forEach((item) => {
        item.addEventListener("click", (event) => {
            event.preventDefault();
            showView(item.dataset.view);
        });
    });

    elements.schemaDatabaseSelect.addEventListener("change", () => {
        const databaseId = elements.schemaDatabaseSelect.value;
        state.selectedDatabaseId = databaseId || null;
        loadSchema(databaseId);
    });

    elements.schemaRefreshButton.addEventListener("click", () => {
        const databaseId = elements.schemaDatabaseSelect.value;

        if (databaseId) {
            loadSchema(databaseId, { force: true });
        }
    });

    elements.statisticsDatabaseSelect.addEventListener("change", () => {
        const databaseId = elements.statisticsDatabaseSelect.value;
        loadStatistics(databaseId);
    });

    elements.statisticsRefreshButton.addEventListener("click", () => {
        const databaseId = elements.statisticsDatabaseSelect.value;

        if (databaseId) {
            loadStatistics(databaseId, { force: true });
        }
    });

    // Keep the initial dashboard as the default view.
    showView("dashboard");
}

elements.refreshButton.addEventListener("click", () => {
    loadDatabases({ force: true });
});

elements.uploadButton.addEventListener("click", () => {
    elements.databaseFileInput.click();
});

elements.databaseFileInput.addEventListener("change", async () => {
    const file = elements.databaseFileInput.files[0];

    if (!file) {
        return;
    }

    const allowedExtensions = [".db", ".sqlite", ".sqlite3"];
    const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();

    if (!allowedExtensions.includes(extension)) {
        showNotice("Unsupported database file extension.", "error");
        elements.databaseFileInput.value = "";
        return;
    }

    const maxSize = 100 * 1024 * 1024;

    if (file.size > maxSize) {
        showNotice("Maximum upload size is 100 MiB.", "error");
        elements.databaseFileInput.value = "";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    elements.uploadButton.disabled = true;
    elements.uploadButton.textContent = "Uploading…";
    hideNotice();

    try {
        const response = await fetch(`${API_BASE}/databases/upload`, {
            method: "POST",
            body: formData,
        });

        const payload = await response.json();

        if (!response.ok) {
            throw new Error(
                typeof payload.detail === "string"
                    ? payload.detail
                    : `Upload failed (HTTP ${response.status}).`,
            );
        }

        // Invalidate the cached inventory after a successful upload.
        state.databases = null;
        state.databasesFetchedAt = 0;

        await loadDatabases({ force: true });

        showNotice(
            `Database "${payload.name}" uploaded successfully.`,
            "success",
        );
    } catch (error) {
        console.error("Database upload failed:", error);
        showNotice(error.message, "error");
    } finally {
        elements.uploadButton.disabled = false;
        elements.uploadButton.textContent = "＋ Add database";
        elements.databaseFileInput.value = "";
    }
});

setupNavigation();
setupTableDataControls();
setupDataModal();
loadDatabases();
