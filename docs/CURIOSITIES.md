# Curiosities — features you didn't order

Open **`/curiosities`** (also `/lab`, `/weird`).

## 1. Dream Mode
Idle Subcortex consolidates wiki + world model + serendipity into a dream journal.  
Not chat spam — REM for the host.

`POST /v1/dreams/now` · desk mode `dream`

## 2. Agent Duels
FORGE / AESTHETE / SENTINEL each propose a plan; ARCHON judges; winner saved + receipt.

`POST /v1/duels` `{"challenge":"…"}` · desk mode `duel`

## 3. Time Capsules
Future-you messages fire on timer, file change, idle, or keyword in sessions.

`POST /v1/capsules` · desk mode `capsule` · e.g. `in 120s: check the deploy`

## 4. Serendipity
Unexpected links across wiki nodes, facts, dreams, builds.

`GET /v1/serendipity`

## 5. Proof Chain
Local hash-linked receipts for dreams, duels, ships, capsules.

`GET /v1/proofs` · `GET /v1/proofs/verify` · desk mode `proof`
