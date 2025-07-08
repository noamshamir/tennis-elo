const apiHome = "http://localhost:3000/api";

let playerName = "";
let playerInfo = {};
let eloHistoryData = [];
let matchData = [];
let eloChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
    playerName = decodeURIComponent(window.location.hash.substring(1));
    getInfo(playerName);
    document.querySelector(".profile-name").textContent = playerName;
});

window.addEventListener("hashchange", () => {
    playerName = decodeURIComponent(window.location.hash.substring(1));
    getInfo(playerName);
    document.querySelector(".profile-name").textContent = playerName;
});

async function getInfo(player_name) {
    try {
        const response = await fetch(`${apiHome}/players?name=${player_name}`);
        if (!response.ok) throw new Error(`${apiHome}/rankings`);
        const json = await response.json();
        playerInfo = json.rows[0];
        renderInfo();
    } catch (error) {
        console.error(error.message);
    }
}

function renderInfo() {
    document.querySelector(".profile-name").textContent = playerInfo.name;
    document.querySelector(".profile-country span").textContent =
        playerInfo.country || "—";

    const statusBadge = document.querySelector(".status-badge");
    statusBadge.textContent = playerInfo.is_active ? "Active" : "Inactive";
    statusBadge.classList.remove("active", "inactive");
    statusBadge.classList.add(playerInfo.is_active ? "active" : "inactive");

    if (playerInfo.image) {
        document.querySelector(".profile-image").src = playerInfo.image;
    } else {
        document.querySelector(".profile-image").src = "../images/default.svg";
    }

    document.querySelectorAll(".header-stat-value.elo")[0].textContent =
        playerInfo.peak_elo ?? "—";
    document.querySelectorAll(".header-stat-value.elo")[1].textContent =
        playerInfo.elo ?? "—";

    document.querySelectorAll(".header-stat-value.other")[0].textContent =
        (playerInfo.hand === "R" ? "Right" : "Left") ?? "—";
    document.querySelectorAll(".header-stat-value.other")[1].textContent =
        playerInfo.age ?? "—";
    document.querySelectorAll(".header-stat-value.other")[2].textContent =
        playerInfo.height ? `${playerInfo.height} cm` : "—";
    document.querySelectorAll(".header-stat-value.other")[3].textContent =
        `${playerInfo.wins}-${playerInfo.losses}` ?? "—";

    renderGraph(playerInfo.id);
    getMatches(playerInfo.id);
}

async function renderGraph(playerId) {
    try {
        const response = await fetch(
            `${apiHome}/player_history?id=${playerId}`
        );
        if (!response.ok) throw new Error("Failed to fetch Elo history");

        const json = await response.json();
        eloHistoryData = json.rows;

        const labels = eloHistoryData.map((row) => formatDate(row.date));
        const elos = eloHistoryData.map((row) => row.elo);
        const minElo = Math.min(...elos);
        const maxElo = Math.max(...elos);

        const thresholds = [2350, 2200, 2000];
        const visibleThresholds = thresholds.filter(
            (value) => value >= minElo - 100 && value <= maxElo + 100
        );

        const line_names = {
            2350: "Super Grand Master",
            2200: "Grand Master",
            2000: "International Master",
        };

        const peakIndex = elos.indexOf(playerInfo.peak_elo);
        const annotations = {};

        visibleThresholds.forEach((value) => {
            annotations[`line${value}`] = {
                type: "line",
                yMin: value,
                yMax: value,
                borderColor: "#d45c5c",
                borderWidth: 1.5,
                label: {
                    enabled: true,
                    content: line_names[value],
                    position: "start",
                    backgroundColor: "#121212",
                    color: "#fff",
                    font: { size: 14 },
                },
            };
        });

        const ctx = document.getElementById("eloChart").getContext("2d");
        if (eloChartInstance) {
            eloChartInstance.destroy();
        }

        eloChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels,
                datasets: [
                    {
                        label: "Elo Over Time",
                        data: elos,
                        borderColor: "#9cd365",
                        backgroundColor: "transparent",
                        tension: 0.3,
                        pointRadius: 0,
                        borderWidth: 4,
                    },
                    {
                        label: "Peak Elo",
                        data: labels.map((_, i) =>
                            i === peakIndex ? playerInfo.peak_elo : null
                        ),
                        borderColor: "#d45c5c",
                        pointRadius: 10,
                        pointHoverRadius: 10,
                        borderWidth: 2,
                        pointStyle: "star",
                        showLine: false,
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: { mode: "index", intersect: false },
                    annotation: { annotations },
                },
                scales: {
                    x: {
                        ticks: { color: "#ccc", font: { size: 14 } },
                        grid: {
                            color: "rgba(255,255,255,0.05)",
                            drawTicks: false,
                        },
                    },
                    y: {
                        ticks: { color: "#ccc", font: { size: 14 } },
                        grid: {
                            color: "rgba(255,255,255,0.05)",
                            drawTicks: false,
                        },
                        suggestedMin: 1500,
                    },
                },
            },
            plugins: [Chart.registry.getPlugin("annotation")],
        });
    } catch (err) {
        console.error("Chart rendering error:", err);
    }
}

async function getMatches(playerId) {
    try {
        const response = await fetch(
            `${apiHome}/player_matches?id=${playerId}`
        );
        if (!response.ok) throw new Error("Failed to fetch matches");

        const json = await response.json();
        matchData = json.rows;
        renderMatches(matchData);
    } catch (err) {
        console.error("Match fetch error:", err);
    }
}

function renderMatches(matches) {
    const matchElements = document.querySelectorAll(
        ".matches-container .match"
    );

    matches.forEach((match, i) => {
        const el = matchElements[i];
        if (!el) return;

        const profileChange = match.elo_change;
        const opponentChange = -profileChange;

        const formattedDate = new Date(match.date).toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
        });

        el.querySelector(".match-header .match-date").textContent =
            formattedDate;

        const [playerRow, opponentRow] = el.querySelectorAll(".match-row");

        const [p1Scores, p2Scores] = parseTennisScore(match.score);
        const maxSets = Math.max(p1Scores.length, p2Scores.length);

        function didProfileWinMatch(p1Scores, p2Scores) {
            let p1Wins = 0;
            let p2Wins = 0;
            for (let i = 0; i < maxSets; i++) {
                const s1 = parseInt(p1Scores[i]);
                const s2 = parseInt(p2Scores[i]);
                if (!isNaN(s1) && !isNaN(s2)) {
                    if (s1 > s2) p1Wins++;
                    else if (s2 > s1) p2Wins++;
                }
            }
            return p1Wins > p2Wins;
        }

        const profileIsWinner = didProfileWinMatch(p1Scores, p2Scores);

        const setCols1 = Array.from({ length: maxSets }, (_, idx) => {
            const val1 = p1Scores[idx] ?? "–";
            const val2 = p2Scores[idx] ?? "–";
            const isWin = parseInt(val1) > parseInt(val2);
            return `<span class="set-cell${
                profileIsWinner && isWin ? " winner" : ""
            }">${val1}</span>`;
        }).join("");

        const setCols2 = Array.from({ length: maxSets }, (_, idx) => {
            const val1 = p1Scores[idx] ?? "–";
            const val2 = p2Scores[idx] ?? "–";
            const isWin = parseInt(val2) > parseInt(val1);
            return `<span class="set-cell${
                !profileIsWinner && isWin ? " winner" : ""
            }">${val2}</span>`;
        }).join("");

        playerRow.innerHTML = `
            <span class="elo">${match.elo}</span>
            <span class="player-name">${playerInfo.name}</span>
            <div class="set-group">${setCols1}</div>
            <span class="elo-change ${
                profileChange >= 0 ? "positive" : "negative"
            }">
                ${profileChange >= 0 ? "+" : ""}${profileChange}
            </span>
        `;

        opponentRow.innerHTML = `
            <span class="elo">${match.opponent_elo}</span>
            <span class="player-name">
                <a href="player.html#${encodeURIComponent(
                    match.opponent_name
                )}" class="opponent-link">
                    ${match.opponent_name}
                </a>
            </span>
            <div class="set-group">${setCols2}</div>
            <span class="elo-change ${
                opponentChange >= 0 ? "positive" : "negative"
            }">
                ${opponentChange >= 0 ? "+" : ""}${opponentChange}
            </span>
        `;
    });
}

function formatDate(dateStr) {
    return new Date(dateStr).getFullYear().toString();
}

function parseTennisScore(scoreStr) {
    const sets = scoreStr.trim().split(/\s+/);
    const player1 = [];
    const player2 = [];

    for (const set of sets) {
        if (set.toUpperCase() === "RET") continue;
        const match = set.match(/^(\d+)-(\d+)(?:\(\d+\))?$/);
        if (match) {
            player1.push(match[1]);
            player2.push(match[2]);
        } else {
            player1.push("");
            player2.push("");
        }
    }

    return [player1, player2];
}
