const apiHome = "http://localhost:3000/api";
const surfaces = ["hard", "grass", "clay", "carpet"];

let rankingsData = [];
let sortParams = "sortcolumn=elo&sortdirection=desc";
let currentPage = 1;
const rowsPerPage = 25;

// read current sort column (for highlighting)
function getSortColumn() {
    return sortParams
        .split("&")
        .find((p) => p.startsWith("sortcolumn="))
        .split("=")[1];
}

// read filters
function getFilters() {
    return {
        start_year: +document.getElementById("start_year").value,
        end_year: +document.getElementById("end_year").value,
        expanded: document.getElementById("expanded_view").checked,
        surfaceMode: document.getElementById("surface_mode").value,
    };
}

// sorting
function sortTable(column, direction, btn) {
    document
        .querySelectorAll(".sort-buttons button")
        .forEach((b) => b.classList.remove("asc", "desc"));
    btn.classList.add(direction);
    sortParams = `sortcolumn=${column}&sortdirection=${direction}`;
    getRankings();
}

// pagination controls
function goToPage(page) {
    const totalPages = Math.ceil(rankingsData.length / rowsPerPage) || 1;
    let p = parseInt(page, 10);
    if (isNaN(p) || p < 1) p = 1;
    if (p > totalPages) p = totalPages;
    currentPage = p;
    document.getElementById("page-number").value = currentPage;
    updatePageInfo();
    renderTable(getFilters().expanded);
}

function goToNext() {
    goToPage(currentPage + 1);
}

function goToPrevious() {
    goToPage(currentPage - 1);
}

function goToFirst() {
    goToPage(1);
}

function updatePageInfo() {
    const totalPages = Math.ceil(rankingsData.length / rowsPerPage) || 1;
    document.getElementById("page-info").textContent = `/${totalPages}`;

    const btnFirst = document.querySelector(".first-page");
    const btnPrev = document.querySelector(".previous-page");
    const btnNext = document.querySelector(".next-page");

    const isFirstPage = currentPage === 1;
    const isLastPage = currentPage === totalPages;

    btnFirst.classList.toggle("disabled", isFirstPage);
    btnPrev.classList.toggle("disabled", isFirstPage);
    btnNext.classList.toggle("disabled", isLastPage);
}

// grey‐out the “Current/Peak” toggle when not in expanded view
function updateModeToggleState() {
    const expanded = document.getElementById("expanded_view").checked;
    const modeContainer = document.querySelector(".mode-toggle");
    modeContainer.classList.toggle("hidden", !expanded);
}

// fetch data
async function getRankings() {
    const { start_year, end_year, expanded } = getFilters();
    const base = `${apiHome}/${expanded ? "detailed_rankings" : "rankings"}`;
    const url = `${base}?start_year=${start_year}&end_year=${end_year}&${sortParams}&limit=1000`;

    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`Fetch error ${resp.status}`);
    const { rows } = await resp.json();
    rankingsData = rows;
    currentPage = 1;
    document.getElementById("page-number").value = currentPage;
    renderTable(expanded);
    updatePageInfo();
    updateModeToggleState();
}

// helper to replace empty values
function formatCell(val) {
    return val === 0 || val == null ? "-" : val;
}

// render table
function renderTable(expanded) {
    const { surfaceMode } = getFilters();
    const headRow = document.getElementById("header-row");

    // build headers
    let html = "";
    html += makeHeaderCell("Rank", "rank");
    html += makeHeaderCell("Player", "name");
    html += makeHeaderCell("Age", "age");
    html += makeHeaderCell("Elo", "elo");
    html += makeHeaderCell("Peak Elo", "peak_elo");
    headRow.innerHTML = html;

    if (expanded) {
        surfaces.forEach((surf) => {
            const label = surf.charAt(0).toUpperCase() + surf.slice(1);
            const key = `${surf}_${surfaceMode === "current" ? "elo" : "peak"}`;
            headRow.insertAdjacentHTML("beforeend", makeHeaderCell(label, key));
        });
    }

    // populate rows
    const tbody = document.getElementById("table-content");
    tbody.innerHTML = "";

    const startIdx = (currentPage - 1) * rowsPerPage;
    const pageData = rankingsData.slice(startIdx, startIdx + rowsPerPage);

    pageData.forEach((row) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${row.rank}</td>
            <td>
              <div class="player-name-content">
                <img src="${row.image || "../images/default.svg"}"
                     class="player-image ${
                         row.is_active ? "active" : "inactive"
                     }"/>
                <div class="player-name-row">${row.name}</div>
              </div>
            </td>
            <td>${formatCell(row.age)}</td>
            <td>${formatCell(row.elo)}</td>
            <td>${formatCell(row.peak_elo)}</td>
        `;

        if (expanded) {
            surfaces.forEach((surf) => {
                const key = `${surf}_${
                    surfaceMode === "current" ? "elo" : "peak"
                }`;
                tr.insertAdjacentHTML(
                    "beforeend",
                    `<td>${formatCell(row[key])}</td>`
                );
            });
        }

        tr.addEventListener("click", () => toggleDetailRow(tr, expanded));
        tbody.appendChild(tr);
    });
}

function makeHeaderCell(label, key) {
    return `
    <th>
      <div class="th-content">
        ${label}
        <span class="sort-buttons" data-key="${key}">
          <button class="asc"  onclick="sortTable('${key}','asc', this)">▲</button>
          <button class="desc" onclick="sortTable('${key}','desc',this)">▼</button>
        </span>
      </div>
    </th>`;
}

function toggleDetailRow(row, expanded) {
    const next = row.nextElementSibling;
    if (next?.classList.contains("detail-row")) {
        next.remove();
        row.classList.remove("expanded");
        return;
    }
    document.querySelectorAll(".detail-row").forEach((r) => r.remove());
    document
        .querySelectorAll("tr.expanded")
        .forEach((r) => r.classList.remove("expanded"));
    row.classList.add("expanded");

    const colspan = 5 + (getFilters().expanded ? surfaces.length : 0);
    const detail = document.createElement("tr");
    detail.classList.add("detail-row");
    detail.innerHTML = `<td colspan="${colspan}">…detail content…</td>`;
    row.parentNode.insertBefore(detail, row.nextSibling);
}

function setSurfaceMode(mode) {
    document.getElementById("surface_mode").value = mode;
    document
        .getElementById("current_btn")
        .classList.toggle("active", mode === "current");
    document
        .getElementById("peak_btn")
        .classList.toggle("active", mode === "peak");

    // adjust sort column if it’s a surface stat
    const [prefix, dir] = sortParams.split("&sortdirection=");
    const col = prefix.split("=")[1];
    if (col.endsWith("_elo") || col.endsWith("_peak")) {
        const base = col.split("_")[0];
        const suffix = mode === "current" ? "elo" : "peak";
        sortParams = `sortcolumn=${base}_${suffix}&sortdirection=${dir}`;
    }

    getRankings();
}

document.addEventListener("DOMContentLoaded", () => {
    document
        .querySelectorAll("#start_year,#end_year")
        .forEach((i) => i.addEventListener("change", getRankings));

    document.getElementById("expanded_view").addEventListener("change", () => {
        updateModeToggleState();
        getRankings();
    });

    document
        .getElementById("page-number")
        .addEventListener("change", (e) => goToPage(e.target.value));

    // initialize toggle state + load data
    updateModeToggleState();
    getRankings();
});
