# Multi-user seats (not “log into owner”)

## Mental model

| Role | Who | How they sign in |
|------|-----|------------------|
| **Owner** | You (operator) | `ACCESS.txt` / admin user — **your** machine host |
| **Member** | Invited user | **Their** username + password they chose at register |

Register **never** puts someone on the owner account.  
A seat invite key only proves “owner allowed a new seat.” The new person picks identity + password.

## Seat invite keys (cryptographic)

- Format: `pk_seat_<random>`
- Server stores **SHA-256(key)** only — not the raw key after mint
- Minted by owner: `POST /v1/admin/invites` `{ "label": "alice", "max_uses": 1 }`
- Response includes **invite_key once** — give that string to Alice
- Alice opens **Create my seat**, pastes key, chooses username/password
- Key uses increment; when exhausted, key is dead

List (admin): `GET /v1/admin/invites` — prefixes only, never raw secrets.

## Owner stays logged in

- Minting invites does **not** revoke owner sessions
- Members get separate tokens
- Owner password lives in ACCESS / users.json admin row (`is_owner: true`)

## Ship paths for members

1. Owner mints seat key  
2. Member opens cloud desk **or** Electron / Edge against the product  
3. **Create my seat** with key  
4. Later: sign in with **their** user/pass only  

Invite is not “here’s my password.”
