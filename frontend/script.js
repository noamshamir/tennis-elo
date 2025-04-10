playerData = [
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
    {
        player: "Jannik Siner",
        age: 22,
        elo: 2192,
        hardcourtElo: 2009,
        clayElo: 2230,
        grassElo: 2201,
        peakElo: 2215,
    },
];

table_body = document.querySelector("tbody");
for (i = 0; i < playerData.length; i++) {
    dataRow = playerData[i];
    tr = document.createElement("tr");
    tr.key = i + 1;

    indexTd = document.createElement("td");
    indexTd.textContent = i + 1;
    tr.appendChild(indexTd);

    playerNameTd = document.createElement("td");
    playerNameTd.textContent = dataRow.player;
    tr.appendChild(playerNameTd);

    ageTd = document.createElement("td");
    ageTd.textContent = dataRow.age;
    tr.appendChild(ageTd);

    eloTd = document.createElement("td");
    eloTd.textContent = dataRow.elo;
    tr.appendChild(eloTd);

    hEloTd = document.createElement("td");
    hEloTd.textContent = dataRow.hardcourtElo;
    tr.appendChild(hEloTd);

    cEloTd = document.createElement("td");
    cEloTd.textContent = dataRow.clayElo;
    tr.appendChild(cEloTd);

    gEloTd = document.createElement("td");
    gEloTd.textContent = dataRow.grassElo;
    tr.appendChild(gEloTd);
    table_body.appendChild(tr);

    peakTd = document.createElement("td");
    peakTd.textContent = dataRow.peakElo;
    tr.appendChild(peakTd);
    table_body.appendChild(tr);

    // console.log(row);
    // console.log(index);
}
