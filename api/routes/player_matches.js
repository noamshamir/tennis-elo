const express = require("express");
const router = express.Router();
const pool = require("./db_pool.js");
const { query, validationResult } = require("express-validator");

const validatePlayerMatchesQuery = [
    query("id").notEmpty().withMessage("Player id is required"),
];

router.get("/", validatePlayerMatchesQuery, async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const playerId = parseInt(req.query.id);

    let conn;
    try {
        conn = await pool.getConnection();

        const sql = `
            select 
                pe.player_id,
                pe.won as did_win,
                pe.elo_before as elo,
                pe.elo_after - pe.elo_before as elo_change,
                pe.date,
                pe.score,
                opp.elo_before as opponent_elo,
                p_opp.name as opponent_name,
                p_opp.image as opponent_image
            from player_entry pe
            join player_entry opp
                on pe.match_id = opp.match_id 
                and pe.player_id != opp.player_id
            join player p_opp
                on p_opp.id = opp.player_id
            where pe.player_id = ?
            order by pe.date desc
            limit 10;
         `;

        const rows = await conn.query(sql, [playerId]);

        res.json({ rows });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Database error" });
    } finally {
        if (conn) conn.release();
    }
});

module.exports = router;
