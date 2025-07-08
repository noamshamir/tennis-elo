# Tennis ELO API

A simple REST API for tracking tennis players and their ELO ratings based on matches.

## Setup

1. Clone this repository
2. Install dependencies
    ```
    npm install
    ```
3. Create a `.env` file in the root directory with the following variables:
    ```
    PORT=3000
    ```

## Running the Server

### Development mode

```
npm run dev
```

### Production mode

```
npm start
```

## API Endpoints

### Base URL

```
http://localhost:3000/api
```

### Players

-   `GET /api/players` - Get all players
-   `GET /api/players/:id` - Get a specific player
-   `POST /api/players` - Create a new player
    -   Required body: `{ "name": "Player Name" }`
-   `PUT /api/players/:id` - Update a player
    -   Required body: `{ "name": "Updated Name" }`

### Matches

-   `GET /api/matches` - Get all matches
-   `GET /api/matches/:id` - Get a specific match
-   `POST /api/matches` - Record a new match
    -   Required body: `{ "player1Id": "1", "player2Id": "2", "winnerId": "1" }`

## ELO Rating System

This API implements the ELO rating system for chess, adapted for tennis. When a match is recorded, both players' ELO ratings are updated based on the outcome of the match.

New players start with an ELO rating of 1500.
