const sqlite3 = require('sqlite3').verbose();

// Connect to the SQLite database
const db = new sqlite3.Database('./users.db', (err) => {
    if (err) {
        console.error('Error connecting to database:', err.message);
    } else {
        console.log('Connected to the SQLite database.');
    }
});

// Create the Users table if it doesn't exist
db.run(`
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_id VARCHAR NOT NULL,
        username TEXT NOT NULL,
    )
`, (err) => {
    if (err) {
        console.error('Error creating table:', err.message);
    } else {
        console.log('Users table ready.');

        // Insert preset data
        const presetUsers = [
            { card_id: '53 C7 A8 0E', username: 'Damiano' }
        ];

        const insertQuery = `INSERT INTO Users (username, last_log) VALUES (?, ?)`;

        presetUsers.forEach((user) => {
            db.run(insertQuery, [user.username, user.last_log], (err) => {
                if (err) {
                    console.error('Error inserting data:', err.message);
                } else { 'user: ${user.username}`);
                }
            });
        });
    }
});

// Export the database connection
module.exports = db;
