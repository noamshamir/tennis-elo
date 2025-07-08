const express = require("express");
const router = express.Router();
const pool = require("./db_pool.js");
const { query, validationResult } = require("express-validator");

const validatePlayerHistoryQuery = [
    query("id").notEmpty().withMessage("Player id is required"),
];

router.get("/", validatePlayerHistoryQuery, async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const playerId = req.query.id;

    let conn;
    try {
        conn = await pool.getConnection();

        const sql = `
            SELECT 
                date, 
                elo_after as elo,
                won
            FROM player_entry
            WHERE player_id = ${playerId};
        `;

        const rows = await conn.query(sql);

        res.json({ rows });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Database error" });
    } finally {
        if (conn) conn.release();
    }
});

module.exports = router;
