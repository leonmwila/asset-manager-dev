/** @odoo-module **/

let scanBuffer = "";
let lastKeyTs = 0;
let isProcessing = false;

function getHashParam(name) {
    const hash = window.location.hash || "";
    const params = new URLSearchParams(hash.replace(/^#/, ""));
    return params.get(name);
}

function isLotListScreen() {
    const model = getHashParam("model");
    const viewType = getHashParam("view_type");

    if (model !== "stock.lot") {
        return false;
    }
    if (viewType && viewType !== "list") {
        return false;
    }
    return Boolean(document.querySelector(".o_list_view"));
}

function isSearchInputFocused() {
    const active = document.activeElement;
    if (!active) {
        return false;
    }
    if (active.classList?.contains("o_searchview_input")) {
        return true;
    }
    return Boolean(active.closest?.(".o_searchview"));
}

async function callKw(model, method, args = [], kwargs = {}) {
    const response = await fetch(`/web/dataset/call_kw/${model}/${method}`, {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params: {
                model,
                method,
                args,
                kwargs,
            },
        }),
    });

    const payload = await response.json();
    if (payload.error) {
        throw payload.error;
    }
    return payload.result;
}

function runUiSearch(searchValue) {
    const searchInput = document.querySelector(".o_searchview .o_searchview_input, .o_searchview input");
    if (!searchInput) {
        return;
    }

    searchInput.value = searchValue;
    searchInput.dispatchEvent(new Event("input", { bubbles: true }));
    searchInput.dispatchEvent(
        new KeyboardEvent("keydown", {
            key: "Enter",
            bubbles: true,
            cancelable: true,
        })
    );
}

async function markLotLabelled(scannedCode) {
    if (!scannedCode || isProcessing) {
        return;
    }
    isProcessing = true;

    try {
        let records = await callKw("stock.lot", "search_read", [], {
            domain: ["|", ["name", "=", scannedCode], ["ref", "=", scannedCode]],
            fields: ["id", "labelled"],
            limit: 1,
        });

        if (!records.length) {
            records = await callKw("stock.lot", "search_read", [], {
                domain: ["|", ["name", "ilike", scannedCode], ["ref", "ilike", scannedCode]],
                fields: ["id", "labelled"],
                limit: 1,
            });
        }

        if (!records.length) {
            return;
        }

        const lot = records[0];
        if (!lot.labelled) {
            await callKw("stock.lot", "write", [[lot.id], { labelled: true }], {});
        }

        runUiSearch(scannedCode);
    } catch (error) {
        console.warn("Asset labelling barcode scan failed", error);
    } finally {
        isProcessing = false;
    }
}

function clearBuffer() {
    scanBuffer = "";
    lastKeyTs = 0;
}

function onGlobalKeydown(ev) {
    if (!isLotListScreen()) {
        clearBuffer();
        return;
    }

    if (isSearchInputFocused()) {
        clearBuffer();
        return;
    }

    if (ev.ctrlKey || ev.altKey || ev.metaKey) {
        return;
    }

    const now = Date.now();
    if (now - lastKeyTs > 120) {
        scanBuffer = "";
    }
    lastKeyTs = now;

    if (ev.key === "Enter") {
        const scanned = scanBuffer.trim();
        clearBuffer();
        if (scanned.length >= 3) {
            ev.preventDefault();
            markLotLabelled(scanned);
        }
        return;
    }

    if (ev.key === "Escape") {
        clearBuffer();
        return;
    }

    if (ev.key.length === 1) {
        scanBuffer += ev.key;
    }
}

document.addEventListener("keydown", onGlobalKeydown, true);
