# 029 — Design a Real-Time Game Leaderboard

Design leaderboards for a popular mobile game: players see their rank and the top players, updated in real time as matches finish.

## Functional requirements

- Update a player's score when a match ends.
- Show the global top 100 players.
- Show any player's own rank and the players just above and below them.
- Separate leaderboards per season (resets monthly), per region, and among friends.
- Break ties deterministically (earlier achiever ranks higher).

## Constraints to assume

- 100 million players in the current season; 20 million daily active.
- 5,000 score updates per second at peak (match completions), bursting to 20,000 during events.
- 50,000 leaderboard reads per second; p99 under 100 ms.
- A player must see their new rank within a few seconds of finishing a match.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope estimates: memory for scores, update and read load.
3. <abbr title="Application Programming Interface">API</abbr> contract for updates and reads.
4. Baseline design for a single leaderboard and why it works.
5. Scaling to 100 million players: sharding, global rank, and approximate vs exact rank.
6. Ties, seasons, friend leaderboards, durability, and cheating.
7. One explicit trade-off you would revisit for exact rank of every player at any moment.

Do not open the solution until you have made and explained your own design.
