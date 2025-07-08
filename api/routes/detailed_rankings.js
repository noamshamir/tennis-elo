const express = require("express");
const { query, validationResult } = require("express-validator");
const pool = require("./db_pool.js");
const router = express.Router();

const validate = [
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
        .custom((end, { req }) => {
            if (end < +req.query.start_year) {
                throw new Error("End year must be ≥ start year");
            }
            return true;
        }),
    query("sortcolumn")
        .optional()
        .isIn([
            "rank",
            "name",
            "age",
            "elo",
            "peak_elo",
            "hard_elo",
            "hard_peak",
            "grass_elo",
            "grass_peak",
            "clay_elo",
            "clay_peak",
            "carpet_elo",
            "carpet_peak",
        ])
        .withMessage("Invalid sort column"),
    query("sortdirection")
        .optional()
        .isIn(["asc", "desc"])
        .withMessage("Sort direction must be asc or desc"),
];

router.get("/", validate, async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const {
        start_year,
        end_year,
        sortcolumn = "elo",
        sortdirection = "desc",
    } = req.query;
    const s0 = +start_year,
        s1 = +end_year;

    const sql = `
    SELECT
      p.id,
      p.name,
      TIMESTAMPDIFF(YEAR, p.dob, CURRENT_DATE()) AS age,
      p.image,
      eh.surface,
      eh.elo,
      eh.peak_elo,
      eh.last_match_date
    FROM player p
    JOIN player_range_elo eh
      ON eh.player_id  = p.id
     AND eh.range_from = ?
     AND eh.range_to   = ?
     AND eh.surface    IN ('overall','hard','grass','clay','carpet')
  `;

    let conn;
    try {
        conn = await pool.getConnection();
        const flat = await conn.query(sql, [s0, s1]);
        conn.release();

        // pivot by player, using lowercase keys for surfaces
        const byId = {};
        flat.forEach((r) => {
            if (!byId[r.id]) {
                byId[r.id] = {
                    id: r.id,
                    name: r.name,
                    age: r.age,
                    image: r.image,
                    is_active: false,
                    // overall
                    elo: 0,
                    peak_elo: 0,
                    // surfaces in lowercase
                    hard_elo: 0,
                    hard_peak: 0,
                    grass_elo: 0,
                    grass_peak: 0,
                    clay_elo: 0,
                    clay_peak: 0,
                    carpet_elo: 0,
                    carpet_peak: 0,
                };
            }

            const p = byId[r.id];
            if (r.surface === "overall") {
                p.elo = r.elo;
                p.peak_elo = r.peak_elo;

                // compute is_active: last_match_date within 1 year before end_year
                if (r.last_match_date) {
                    const lastDate = new Date(r.last_match_date);

                    const cutoff = new Date(`${s1}-12-31`);
                    if (r.id == "104918") {
                        console.log(cutoff);
                        console.log(lastDate);
                    }
                    cutoff.setFullYear(cutoff.getFullYear() - 1);
                    p.is_active = lastDate >= cutoff;
                }
            } else {
                const surf = r.surface.toLowerCase();
                p[`${surf}_elo`] = r.elo;
                p[`${surf}_peak`] = r.peak_elo;
            }
        });

        // filter inactive (unless sorting by peak_elo)
        let rows = Object.values(byId).filter(
            (p) =>
                sortcolumn.endsWith("peak") ||
                sortcolumn === "peak_elo" ||
                p.is_active
        );

        // **NEW**: drop anyone who has no value for the sort column
        rows = rows.filter((p) => {
            const v = p[sortcolumn];
            return v != null && v !== 0;
        });

        // now sort by requested column
        rows.sort((a, b) => {
            const va = a[sortcolumn],
                vb = b[sortcolumn];
            if (va < vb) return sortdirection === "asc" ? -1 : 1;
            if (va > vb) return sortdirection === "asc" ? 1 : -1;
            return 0;
        });

        // assign rank & limit to top 100
        rows = rows.slice(0, 10000).map((p, i) => ({
            rank: i + 1,
            ...p,
        }));
        // console.log(rows);

        // console.log(rows);
        res.json({ rows });
    } catch (err) {
        console.error("DB error:", err);
        if (conn) conn.release();
        res.status(500).json({ error: "Database error" });
    }
});

module.exports = router;
