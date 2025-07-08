const express = require("express");
const router = express.Router();
const pool = require("./db_pool.js");
const { query, validationResult } = require("express-validator");

const validateRankingsQuery = [
    query("start_year")
        .notEmpty()
        .withMessage("Start year is required")
        .isInt({ min: 1968, max: 2024 })
        .withMessage("Start year must be between 1968 and 2024"),
    query("end_year")
        .notEmpty()
        .withMessage("End year is required")
        .isInt({ min: 1968, max: 2024 })
        .withMessage("End year must be between 1968 and 2024")
        .custom((endYear, { req }) => {
            const startYear = parseInt(req.query.start_year);
            if (endYear < startYear) {
                throw new Error(
                    "End year must be greater than or equal to start year"
                );
            }
            return true;
        }),
    query("sortcolumn")
        .optional()
        .isIn(["rank", "name", "age", "elo", "peak_elo"])
        .withMessage("Invalid sort column"),
    query("sortdirection")
        .optional()
        .isIn(["asc", "desc"])
        .withMessage("Sort direction must be either asc or desc"),
];

router.get("/", validateRankingsQuery, async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const queryParams = req.query;
    const startYear = parseInt(queryParams.start_year);
    const endYear = parseInt(queryParams.end_year);
    const sortColumn = queryParams.sortcolumn || "elo";
    const sortDirection = queryParams.sortdirection || "desc";

    let conn;
    try {
        conn = await pool.getConnection();

        const query = `
            select 
                rank() over (partition by elo_history.range_from, elo_history.range_to order by ${
                    sortColumn == "peak_elo" ? "peak_elo" : "elo"
                } desc) as rank,
                elo_history.elo, 
                elo_history.peak_elo, 
                player.name, 
                timestampdiff(year, player.dob, current_date()) as age, 
                player.image,
                elo_history.last_match_date,
                elo_history.range_to,
                elo_history.is_active
            from elo_history 
            join player 
              ON elo_history.player_id = player.id 
            where
              elo_history.range_from = ${startYear} AND elo_history.range_to = ${endYear}
              ${sortColumn == "peak_elo" ? "" : "and is_active"}
            order by isnull(${sortColumn}), ${sortColumn} ${sortDirection}
            limit 10000
        `;

        const rows = await conn.query(query, [startYear, endYear]);

        res.json({ rows });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Database error" });
    } finally {
        if (conn) conn.release();
    }
});

module.exports = router;
