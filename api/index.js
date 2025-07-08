const express = require("express");
const cors = require("cors");
require("dotenv").config();

const playerRoutes = require("./routes/players");
const rankingsRoutes = require("./routes/rankings");
const detailedRankingsRoutes = require("./routes/detailed_rankings");
const playerHistoryRoutes = require("./routes/player_history");
const playerMatchesRoutes = require("./routes/player_matches");

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

app.get("/api", (req, res) => {
    res.json({
        message: "Welcome to the Tennis ELO API!",
        endpoints: {
            players: "/api/players",
            rankings: "/api/rankings",
            detailed_rankings: "/api/detailed_rankings",
            player_history: "/api/player_history",
            player_matches: "/api/player_matches",
        },
    });
});

app.use("/api/players", playerRoutes);
app.use("/api/rankings", rankingsRoutes);
app.use("/api/detailed_rankings", detailedRankingsRoutes);
app.use("/api/player_history", playerHistoryRoutes);
app.use("/api/player_matches", playerMatchesRoutes);

app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: "Something went wrong!" });
});

app.use((req, res) => {
    res.status(404).json({ error: "Route not found" });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
