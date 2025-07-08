const mariadb = require("mariadb");

const pool = mariadb.createPool({
    host: "localhost",
    user: "noamshamir",
    password: "noampass",
    database: "noams",
    connectionLimit: 5,
    bigIntAsNumber: true,
});

module.exports = pool;
