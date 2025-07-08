const express = require("express");
const router = express.Router();
const pool = require("./db_pool.js");
const { query, validationResult } = require("express-validator");

const validatePlayerQuery = [
    query("name").notEmpty().withMessage("Player name is required"),
];

router.get("/", validatePlayerQuery, async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const playerName = req.query.name;

    let conn;
    try {
        conn = await pool.getConnection();

        const sql = `
            SELECT 
                p.id,
                p.name,
                TIMESTAMPDIFF(YEAR, p.dob, CURRENT_DATE()) AS age, 
                p.image,
                p.hand,
                p.ioc AS country,
                p.height,
                eh.peak_elo,
                eh.elo,
                eh.is_active,
                SUM(CASE WHEN pe.won = 1 THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN pe.won = 0 THEN 1 ELSE 0 END) AS losses
            FROM player p
            JOIN elo_history eh ON p.id = eh.player_id
            LEFT JOIN player_entry pe ON p.id = pe.player_id
            WHERE p.name = ?
              AND eh.range_from = 1968
              AND eh.range_to = 2024
            GROUP BY p.id;
        `;

        const rows = await conn.query(sql, [playerName]);

        res.json({ rows });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Database error" });
    } finally {
        if (conn) conn.release();
    }
});

module.exports = router;
