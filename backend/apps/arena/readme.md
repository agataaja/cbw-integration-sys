# Arena Integration Guide (Language-Agnostic)

## Purpose

This document is a generic implementation guide for any team that wants to integrate with Arena using the same flow:

1. Connect to Arena API
2. Receive webhook triggers
3. Fetch the required data from Arena based on the triggered entity

This guide is intentionally independent from any specific project or programming language.

- Arena on GitHub: https://github.com/unitedworldwrestling/arena-public
- Arena API Doc: https://arena.uww.org/api/doc/
- Weebhook reference discussion (public): https://github.com/unitedworldwrestling/arena-public/discussions/158

---

## 1) Connection Setup

### Base URL

Use your Arena API base URL:

- `http://localhost:8080/api/json/`

In production, replace localhost with your real Arena host.

### Authentication

Authentication in this integration is always done with a Bearer token retrieved from Arena OAuth endpoint using:

- `api_key`
- `client_id`
- `client_secret`

Token endpoint:

- `POST http://localhost:8080/oauth/v2/token`

Required token request parameters:

- `grant_type=https://arena.uww.io/grants/api_key`
- `client_id=<client_id>`
- `client_secret=<client_secret>`
- `api_key=<api_key>`

Token request example (cURL):

```bash
curl -X POST "http://localhost:8080/oauth/v2/token" \
  --data-urlencode "grant_type=https://arena.uww.io/grants/api_key" \
  --data-urlencode "client_id=<client_id>" \
  --data-urlencode "client_secret=<client_secret>" \
  --data-urlencode "api_key=<api_key>"
```

Expected token response (template):

```json
{
  "access_token": "",
  "token_type": "Bearer"
}
```

Use this token in all Arena API requests:

- `Authorization: Bearer <access_token>`

Token lifecycle:

- Cache token until expiration (currently none, but is great aproach to locally refresh it whithin a time).
- Refresh token before it expires (for example, 60 seconds earlier).

---

## 2) Webhook Configuration in Arena UI

You can configure webhooks in Arena at:

- `/bracket/webhook/`

You can listen for different actions:

- Insert
- Update
- Delete

Across different entities:

- Fight
- SportEvent
- Fighter
- and others available in your Arena instance

Arena will then trigger a POST request to your endpoint.

## Sugestion for conection withou VPN
### Expose local Arena API with ngrok (localhost:8080)

Arena local running system uses ngrok to expose the local Arena API (`localhost:8080`) so external systems can request Arena data after receiving webhook notifications.

Start tunnel:

```bash
ngrok http 8080
```

Example output URL:

```text
https://abc12345.ngrok-free.app
```

Example public Arena base URL exposed by ngrok:

```text
https://abc12345.ngrok-free.app
```

External system request example (after webhook notification):

```bash
curl -X GET "https://abc12345.ngrok-free.app/api/json/fight/get/12345" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

Notes:

- Keep ngrok running while testing.
- If the URL changes, update the external integration to use the new base URL.
- Use the HTTPS ngrok URL to keep transport encrypted during local testing.


---

## 3) Recommended Webhook Flow

1. Arena sends a webhook event to your HTTP endpoint (POST)
2. Validate authenticity (signature, token, shared secret, or allow-list)
3. Parse payload fields (at least entity and identifier)
4. Route by entity type
5. External system calls the exposed Arena API URL (for example ngrok URL) to fetch the latest entity data
6. Normalize and store/forward the data in your system

---

## 4) Webhook Payload Contract

According to the public Arena discussion, the webhook payload is intentionally minimal and contains action, entity, and id.

Base payload shape:

```json
{
  "action": "<action>",
  "entity": "<entity>",
  "id": "<entity_id>"
}
```

Example:

```json
{
  "action": "update",
  "entity": "Fight",
  "id": "1eec01fa-25d8-6c3a-9bcc-5b5367a7e936"
}
```

Minimum expected fields:

- `action`
- `entity`
- `id`

If your Arena webhook schema differs, adapt this contract.

---

## 5) Entity Routing Map

Use this routing logic after receiving a webhook:

- `entity = Person` -> fetch person and read `person.customId`
- `entity = Fighter` -> fetch fighter, then fetch person, then read `person.customId`
- `entity = Fight` -> fetch one fight
- `entity = SportEvent` -> optionally fetch all fights by event id
- `entity = WeightCategory` -> fetch weight category details
- `entity = Bracket/Category trigger` -> fetch live bracket by category id

Map `id` from the webhook payload to the corresponding entity id expected by your API call.

---

## 6) Function-by-Function Design

The names below are conceptual and can be adapted to any language.

### 5.1 `getCustomId(personId)`

Purpose:

- Retrieve `customId` from a person record.

Why this exists in this integration:

- In this system, `customId` is the internal primary key used to sync athletes between systems.
- Arena provides `customId` at person level, so `personId` is required to read it.
- If you do not sync athletes across systems by internal id, this step is not required.

Arena endpoint:

- `GET person/get/{personId}`

cURL:

```bash
curl -X GET "http://localhost:8080/api/json/person/get/123" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

Expected response example (template):

```json
{
    "person": {
        "fullName": "ABRAAO CAIO DA SILVA FREIRE",
        "photo": "/build/images/placeholder-man.01372165.jpg",
        "id": "1f110c04-9fe4-6522-b1cc-71da0a8eceb1",
        "familyName": "FREIRE",
        "givenName": "Abraao Caio Da Silva",
        "preferedName": "ABRAAO CAIO DA SILVA FREIRE",
        "displayName": "ABRAAO CAIO  .",
        "athenaPrintId": null,
        "preferredNames": {
            "isPrintNameChanged": false,
            "isPrintInitialNameChanged": false,
            "isTVNameChanged": false,
            "isTVInitialNameChanged": false,
            "isTVFamilyNameChanged": false,
            "printName": "FREIRE Abraao Caio da Silva",
            "printInitialName": "FREIRE ACDS",
            "tvName": "Abraao Caio da Silva FREIRE",
            "tvInitialName": "A.C.D.S. FREIRE",
            "tvFamilyName": "FREIRE"
        },
        "customId": "1394",
        "odfCode": null,
        "noc": null
    }
}
```


### 5.2 `getFighterCustomId(fighterId)`

Purpose:

- Resolve fighter -> person -> person customId.

Why this exists in this integration:

- Webhook or API flows may provide `fighterId` first.
- To reach the internal athlete key (`customId`), this design resolves `fighter.personId` and then reads `person.customId`.
- This is specifically useful when athletes are subscribed/registered in Arena under the same internal id strategy.
- If you do not need internal-id synchronization for athletes, you can skip this resolution flow.

Arena endpoint:

- `GET fighter/get/{fighterId}`

cURL:

```bash
curl -X GET "http://localhost:8080/api/json/fighter/get/456" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

Expected response example (template):

```json
{
    "fighter": {
        "sportEventWeightCategoryId": "1f1003df-cb9a-6db6-bde9-5f3f469c864f",
        "weightCategoryFullName": "Greco-Roman - U23 - 130 kg",
        "weightCategoryShortName": "U23 GR 130",
        "weightCategoryCountFights": 11,
        "hasWeightCategoryBlockchainIds": true,
        "weightCategoryCountReadyFighters": 9,
        "hasFighterStatusWithoutReason": false,
        "countFights": 3,
        "nbChallenges": {
            "group": 0,
            "finals": 0
        },
        "personId": "1f1003df-bea9-6f44-8999-5f3f469c864f",
        "fullName": "ANDRE GABRIEL DO AMARAL VIANA",
        "preferedName": "ANDRE GABRIEL DO AMARAL VIANA",
        "displayName": "ANDRE GABRIE .",
        "givenName": "Andre Gabriel Do Amaral",
        "familyName": "VIANA",
        "personPhoto": "/build/images/placeholder-man.01372165.jpg",
        "athenaPrintId": null,
        "odfCode": null,
        "teamAlternateName": "108",
        "teamName": "INSTITUTO MANDUVI",
        "teamCountryFlag": "/uploads/custom-logos/4x3/108.png",
        "sportEventTeamId": "1f1003dd-aa58-6132-9f28-d380088f4d1b",
        "sportEventId": "1f0fdd98-bbd1-6618-8e06-218763bc73e3",
        "drawRank": 2,
        "robinGroup": null,
        "robinGroupRank": null,
        "teamRankingPoint": 15,
        "uwwPoint": 0,
        "isFinalistBronze": true,
        "isFinalistGold": false,
        "isFinalist": true,
        "isOlympicQualified": false,
        "knockOutStatus": null,
        "canHaveMoreBeachFights": false,
        "hasLostknockOut": false,
        "completed": 3,
        "wins": 2,
        "losses": 1,
        "technicalPointsFor": 15,
        "technicalPointsAgainst": 16,
        "technicalPointsDiff": -1,
        "rankingPointsFor": 8,
        "rankingPointsAgainst": 5,
        "rankingPointsDiff": 3,
        "winsEasy": 1,
        "winsSuperiority": 0,
        "rank": 3,
        "rankRobinGroup": 1,
        "fightByOpponent": null,
        "isCompeting": true,
        "hasOpenFight": false,
        "isDisqualified": false,
        "isNotRanked": false,
        "isInjured": false,
        "isForfeit": false,
        "isRobinGroupNotRanked": false,
        "accreditationStatus": 0,
        "id": "1f1003df-beab-6358-8f79-5f3f469c864f",
        "sportEventWeightCategory": "1f1003df-cb9a-6db6-bde9-5f3f469c864f",
        "athleteId": "1f1003df-beaa-6c00-b5e6-5f3f469c864f",
        "weight": null,
        "drawNumber": 0,
        "seedNumber": 2,
        "fighterWeight": null,
        "points": null,
        "fighterStatus": 0,
        "fighterStatusReason": 0,
        "topTechnique": false,
        "rankingException": null
    }
}
```


### 5.3 `getWeightCategoriesBySportEventId(sportEventId)`

Purpose:

- List weight categories for a sport event and optionally map id -> shortName.

Arena endpoint:

- `GET weight-category/{sportEventId}`

cURL:

```bash
curl -X GET "http://localhost:8080/api/json/weight-category/1f1194e3-8d4f-68f4-8284-01e99ca4c679" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

Expected response example (template):

```json
{
    "weightCategories": [
        {
            "sportAlternateName": "FS",
            "sportName": "Freestyle",
            "fullName": "Freestyle - Seniors - 57 kg",
            "alternateName": "FS - 57 kg",
            "shortName": "Seniors FS 57",
            "sportId": "fs",
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "isVeteran": false,
            "audienceShortName": "Seniors",
            "countReadyFighters": 4,
            "countReadySeededFighters": 3,
            "countFighters": 4,
            "countFightersWithoutStatusReason": 1,
            "countFights": 6,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09a9-673a-a0c2-c1d98f6c77fe",
            "name": "57 kg",
            "maxWeight": 57,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598077",
                        "time": "2026-03-06T11:20:11+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 2,
            "matAssignment": 1,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:10+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "FS",
            "sportName": "Freestyle",
            "fullName": "Freestyle - Seniors - 61 kg",
            "alternateName": "FS - 61 kg",
            "shortName": "Seniors FS 61",
            "sportId": "fs",
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "isVeteran": false,
            "audienceShortName": "Seniors",
            "countReadyFighters": 4,
            "countReadySeededFighters": 3,
            "countFighters": 4,
            "countFightersWithoutStatusReason": 1,
            "countFights": 6,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09ad-6a1a-8aa0-c1d98f6c77fe",
            "name": "61 kg",
            "maxWeight": 61,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598076",
                        "time": "2026-03-06T11:19:59+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 1,
            "matAssignment": 1,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:10+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "FS",
            "sportName": "Freestyle",
            "fullName": "Freestyle - Seniors - 65 kg",
            "alternateName": "FS - 65 kg",
            "shortName": "Seniors FS 65",
            "sportId": "fs",
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "isVeteran": false,
            "audienceShortName": "Seniors",
            "countReadyFighters": 11,
            "countReadySeededFighters": 3,
            "countFighters": 11,
            "countFightersWithoutStatusReason": 1,
            "countFights": 14,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09aa-6a18-b623-c1d98f6c77fe",
            "name": "65 kg",
            "maxWeight": 65,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598075",
                        "time": "2026-03-06T11:19:47+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 2,
            "matAssignment": 2,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:10+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "FS",
            "sportName": "Freestyle",
            "fullName": "Freestyle - Seniors - 70 kg",
            "alternateName": "FS - 70 kg",
            "shortName": "Seniors FS 70",
            "sportId": "fs",
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "isVeteran": false,
            "audienceShortName": "Seniors",
            "countReadyFighters": 3,
            "countReadySeededFighters": 2,
            "countFighters": 3,
            "countFightersWithoutStatusReason": 0,
            "countFights": 3,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09a8-6e20-a850-c1d98f6c77fe",
            "name": "70 kg",
            "maxWeight": 70,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598074",
                        "time": "2026-03-06T11:19:35+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 1,
            "matAssignment": 1,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:10+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "FS",
            "sportName": "Freestyle",
            "fullName": "Freestyle - Seniors - 74 kg",
            "alternateName": "FS - 74 kg",
            "shortName": "Seniors FS 74",
            "sportId": "fs",
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "isVeteran": false,
            "audienceShortName": "Seniors",
            "countReadyFighters": 10,
            "countReadySeededFighters": 2,
            "countFighters": 10,
            "countFightersWithoutStatusReason": 0,
            "countFights": 13,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09ab-6b5c-abb1-c1d98f6c77fe",
            "name": "74 kg",
            "maxWeight": 74,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598073",
                        "time": "2026-03-06T11:19:23+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 2,
            "matAssignment": 3,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:10+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "FS",
            "sportName": "Freestyle",
            "fullName": "Freestyle - Seniors - 79 kg",
            "alternateName": "FS - 79 kg",
            "shortName": "Seniors FS 79",
            "sportId": "fs",
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "isVeteran": false,
            "audienceShortName": "Seniors",
            "countReadyFighters": 10,
            "countReadySeededFighters": 1,
            "countFighters": 10,
            "countFightersWithoutStatusReason": 2,
            "countFights": 13,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09ad-62ea-ae34-c1d98f6c77fe",
            "name": "79 kg",
            "maxWeight": 79,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598072",
                        "time": "2026-03-06T11:19:11+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 1,
            "matAssignment": 2,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:10+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "FS",
            "sportName": "Freestyle",
            "fullName": "Freestyle - Seniors - 86 kg",
            "alternateName": "FS - 86 kg",
            "shortName": "Seniors FS 86",
            "sportId": "fs",
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "isVeteran": false,
            "audienceShortName": "Seniors",
            "countReadyFighters": 8,
            "countReadySeededFighters": 3,
            "countFighters": 8,
            "countFightersWithoutStatusReason": 0,
            "countFights": 9,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09ac-6a0c-8fa4-c1d98f6c77fe",
            "name": "86 kg",
            "maxWeight": 86,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598078",
                        "time": "2026-03-06T11:20:23+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 2,
            "matAssignment": 4,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:10+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "FS",
            "sportName": "Freestyle",
            "fullName": "Freestyle - Seniors - 92 kg",
            "alternateName": "FS - 92 kg",
            "shortName": "Seniors FS 92",
            "sportId": "fs",
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "isVeteran": false,
            "audienceShortName": "Seniors",
            "countReadyFighters": 4,
            "countReadySeededFighters": 2,
            "countFighters": 4,
            "countFightersWithoutStatusReason": 0,
            "countFights": 6,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09a8-64ac-a52b-c1d98f6c77fe",
            "name": "92 kg",
            "maxWeight": 92,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598071",
                        "time": "2026-03-06T11:18:59+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 1,
            "matAssignment": 1,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:10+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "FS",
            "sportName": "Freestyle",
            "fullName": "Freestyle - Seniors - 97 kg",
            "alternateName": "FS - 97 kg",
            "shortName": "Seniors FS 97",
            "sportId": "fs",
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "isVeteran": false,
            "audienceShortName": "Seniors",
            "countReadyFighters": 5,
            "countReadySeededFighters": 2,
            "countFighters": 5,
            "countFightersWithoutStatusReason": 0,
            "countFights": 10,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09ad-6718-83f4-c1d98f6c77fe",
            "name": "97 kg",
            "maxWeight": 97,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598070",
                        "time": "2026-03-06T11:18:47+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 2,
            "matAssignment": 5,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:10+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "FS",
            "sportName": "Freestyle",
            "fullName": "Freestyle - Seniors - 125 kg",
            "alternateName": "FS - 125 kg",
            "shortName": "Seniors FS 125",
            "sportId": "fs",
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "isVeteran": false,
            "audienceShortName": "Seniors",
            "countReadyFighters": 6,
            "countReadySeededFighters": 4,
            "countFighters": 6,
            "countFightersWithoutStatusReason": 0,
            "countFights": 10,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09ac-61b0-b468-c1d98f6c77fe",
            "name": "125 kg",
            "maxWeight": 125,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598069",
                        "time": "2026-03-06T11:18:35+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 2,
            "matAssignment": 6,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:10+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "GR",
            "sportName": "Greco-Roman",
            "fullName": "Greco-Roman - Seniors - 55 kg",
            "alternateName": "GR - 55 kg",
            "shortName": "Seniors GR 55",
            "sportId": "gr",
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "isVeteran": false,
            "audienceShortName": "Seniors",
            "countReadyFighters": 1,
            "countReadySeededFighters": 1,
            "countFighters": 1,
            "countFightersWithoutStatusReason": 0,
            "countFights": 0,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": false,
            "id": "1f1194e7-09ae-62da-99d1-c1d98f6c77fe",
            "name": "55 kg",
            "maxWeight": 55,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598068",
                        "time": "2026-03-06T11:18:23+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 1,
            "matAssignment": -1,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:10+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "GR",
            "sportName": "Greco-Roman",
            "fullName": "Greco-Roman - Seniors - 60 kg",
            "alternateName": "GR - 60 kg",
            "shortName": "Seniors GR 60",
            "sportId": "gr",
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "isVeteran": false,
            "audienceShortName": "Seniors",
            "countReadyFighters": 4,
            "countReadySeededFighters": 2,
            "countFighters": 4,
            "countFightersWithoutStatusReason": 1,
            "countFights": 6,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09a7-6e76-9030-c1d98f6c77fe",
            "name": "60 kg",
            "maxWeight": 60,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598067",
                        "time": "2026-03-06T11:18:11+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 2,
            "matAssignment": 1,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:10+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "GR",
            "sportName": "Greco-Roman",
            "fullName": "Greco-Roman - Seniors - 63 kg",
            "alternateName": "GR - 63 kg",
            "shortName": "Seniors GR 63",
            "sportId": "gr",
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "isVeteran": false,
            "audienceShortName": "Seniors",
            "countReadyFighters": 10,
            "countReadySeededFighters": 3,
            "countFighters": 10,
            "countFightersWithoutStatusReason": 1,
            "countFights": 13,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09ab-601c-bcb0-c1d98f6c77fe",
            "name": "63 kg",
            "maxWeight": 63,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598079",
                        "time": "2026-03-06T11:20:35+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 1,
            "matAssignment": 1,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:10+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "FS",
            "sportName": "Freestyle",
            "fullName": "Freestyle - U23 - 92 kg",
            "alternateName": "FS - 92 kg",
            "shortName": "U23 FS 92",
            "sportId": "fs",
            "audienceId": "u23",
            "audienceName": "U23",
            "isVeteran": false,
            "audienceShortName": "U23",
            "countReadyFighters": 6,
            "countReadySeededFighters": 1,
            "countFighters": 6,
            "countFightersWithoutStatusReason": 1,
            "countFights": 10,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09a6-6e18-9528-c1d98f6c77fe",
            "name": "92 kg",
            "maxWeight": 92,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598013",
                        "time": "2026-03-06T11:07:23+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 2,
            "matAssignment": 5,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:09+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
        {
            "sportAlternateName": "WW",
            "sportName": "Women's wrestling",
            "fullName": "Women's wrestling - U23 - 65 kg",
            "alternateName": "WW - 65 kg",
            "shortName": "U23 WW 65",
            "sportId": "ww",
            "audienceId": "u23",
            "audienceName": "U23",
            "isVeteran": false,
            "audienceShortName": "U23",
            "countReadyFighters": 4,
            "countReadySeededFighters": 2,
            "countFighters": 4,
            "countFightersWithoutStatusReason": 0,
            "countFights": 6,
            "countFightsLive": 0,
            "isCompleted": true,
            "isStarted": true,
            "id": "1f1194e7-09a0-62ca-8b13-c1d98f6c77fe",
            "name": "65 kg",
            "maxWeight": 65,
            "roundsNumber": 2,
            "roundDuration": 180,
            "overtime": 0,
            "tournamentType": "singlebracket",
            "uwwRanking": false,
            "blockchainIds": {
                "id": [
                    {
                        "id": "24598157",
                        "time": "2026-03-06T11:36:11+00:00"
                    }
                ],
                "exception": ""
            },
            "sessionStartDay": 1,
            "matAssignment": 3,
            "visible": true,
            "fightersUpdated": "2026-03-06T11:20:09+00:00",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "athenaFinalized": false,
            "medalCeremony": true
        },
    ]
}
```


### 5.4 `getFight(fightId)`

Purpose:

- Retrieve a single fight object.

Arena endpoint:

- `GET fight/get/{fightId}`

cURL:

```bash
curl -X GET "http://localhost:8080/api/json/fight/get/1f11c047-ca3a-6414-8f86-e39fcffe44ce" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

Expected response example (template):

```json
{
    "fight": {
        "fighter1Id": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
        "fighter2Id": "1f1194e7-0700-6f42-bb80-c1d98f6c77fe",
        "fighter2AthenaId": null,
        "team1Name": "SÃO PAULO",
        "team1AlternateName": "SP",
        "team1FullName": "SÃO PAULO (SP)",
        "team1CountryFlag": "/uploads/custom-logos/4x3/sp.png",
        "team1CountryFlagScoreboard": "/uploads/custom-logos/custom/sp.png",
        "team1CountryFlagMobile": "build/images/logo.svg",
        "team1PoolName": null,
        "team1FightByOpponent": null,
        "team2Name": "ESPÍRITO SANTO",
        "team2AlternateName": "ES",
        "team2FullName": "ESPÍRITO SANTO (ES)",
        "team2CountryFlag": "/uploads/custom-logos/4x3/es.png",
        "team2CountryFlagScoreboard": "/uploads/custom-logos/custom/es.png",
        "team2CountryFlagMobile": "build/images/logo.svg",
        "team2PoolName": null,
        "team2FightByOpponent": null,
        "roundFriendlyName": "Round 1",
        "displayOrderInRound": 1,
        "round1Id": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
        "round2Id": "1f11c047-ca3a-6874-977b-e39fcffe44ce",
        "countReferees": 0,
        "sportId": "fs",
        "athlete1Color": "#ba0000",
        "athlete2Color": "#0000aa",
        "athlete1TextColor": "#ffffff",
        "athlete2TextColor": "#ffffff",
        "matName": "A",
        "sessionId": "1f1194e3-8d50-6524-8875-01e99ca4c679",
        "sessionName": "Dia 1 - Qualificatórias e Finais",
        "sessionStartDate": "2026-03-14",
        "technicalPoints": {
            "1f1194e7-0773-6254-8506-c1d98f6c77fe": {
                "fullName": "RENIER LINARES GAVILAN",
                "rounds": {
                    "1f11c047-ca3a-673e-a026-e39fcffe44ce": {
                        "number": 1,
                        "total": 10,
                        "points": {
                            "1f11f9e5-856d-63ea-96a0-5352805c09cf": {
                                "points": 2,
                                "second": 36,
                                "tag": null
                            },
                            "1f11f9e5-85f0-63f8-811a-51c843c252a5": {
                                "points": 2,
                                "second": 46,
                                "tag": null
                            },
                            "1f11f9e5-864d-6878-8938-63f975967849": {
                                "points": 2,
                                "second": 49,
                                "tag": null
                            },
                            "1f11f9e5-86c7-69ac-90ab-3dc7f6ce28ec": {
                                "points": 2,
                                "second": 70,
                                "tag": null
                            },
                            "1f11f9e5-873e-6e4e-9c9c-b98a20723e74": {
                                "points": 2,
                                "second": 82,
                                "tag": null
                            }
                        }
                    }
                },
                "total": 10
            }
        },
        "technicalPointsDetail": {
            "1f11f9e5-856d-63ea-96a0-5352805c09cf": {
                "roundId": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
                "fighterId": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
                "point": 2,
                "second": 36,
                "rsecond": 324,
                "round": 1,
                "tag": null,
                "metadata": {
                    "actionchallenged": false,
                    "actionTimeStart": 0,
                    "actionTimeEnd": 0,
                    "bigmove": false,
                    "bodypart": "",
                    "distance": "",
                    "ledtofall": false,
                    "injury": false,
                    "result": "",
                    "side": ""
                }
            },
            "1f11f9e5-85f0-63f8-811a-51c843c252a5": {
                "roundId": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
                "fighterId": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
                "point": 2,
                "second": 46,
                "rsecond": 314,
                "round": 1,
                "tag": null,
                "metadata": {
                    "actionchallenged": false,
                    "actionTimeStart": 0,
                    "actionTimeEnd": 0,
                    "bigmove": false,
                    "bodypart": "",
                    "distance": "",
                    "ledtofall": false,
                    "injury": false,
                    "result": "",
                    "side": ""
                }
            },
            "1f11f9e5-864d-6878-8938-63f975967849": {
                "roundId": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
                "fighterId": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
                "point": 2,
                "second": 49,
                "rsecond": 311,
                "round": 1,
                "tag": null,
                "metadata": {
                    "actionchallenged": false,
                    "actionTimeStart": 0,
                    "actionTimeEnd": 0,
                    "bigmove": false,
                    "bodypart": "",
                    "distance": "",
                    "ledtofall": false,
                    "injury": false,
                    "result": "",
                    "side": ""
                }
            },
            "1f11f9e5-86c7-69ac-90ab-3dc7f6ce28ec": {
                "roundId": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
                "fighterId": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
                "point": 2,
                "second": 70,
                "rsecond": 290,
                "round": 1,
                "tag": null,
                "metadata": {
                    "actionchallenged": false,
                    "actionTimeStart": 0,
                    "actionTimeEnd": 0,
                    "bigmove": false,
                    "bodypart": "",
                    "distance": "",
                    "ledtofall": false,
                    "injury": false,
                    "result": "",
                    "side": ""
                }
            },
            "1f11f9e5-873e-6e4e-9c9c-b98a20723e74": {
                "roundId": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
                "fighterId": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
                "point": 2,
                "second": 82,
                "rsecond": 278,
                "round": 1,
                "tag": null,
                "metadata": {
                    "actionchallenged": false,
                    "actionTimeStart": 0,
                    "actionTimeEnd": 0,
                    "bigmove": false,
                    "bodypart": "",
                    "distance": "",
                    "ledtofall": false,
                    "injury": false,
                    "result": "",
                    "side": ""
                }
            }
        },
        "technicalPointsTagStatus": "missing",
        "technicalPointIds": [
            "1f11f9e5-856d-63ea-96a0-5352805c09cf",
            "1f11f9e5-85f0-63f8-811a-51c843c252a5",
            "1f11f9e5-864d-6878-8938-63f975967849",
            "1f11f9e5-86c7-69ac-90ab-3dc7f6ce28ec",
            "1f11f9e5-873e-6e4e-9c9c-b98a20723e74"
        ],
        "cautionsList": [],
        "cautionPointIds": [],
        "isCompleted": true,
        "isReady": true,
        "isRobinGroupFight": true,
        "winnerFighter": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
        "winnerTeam": "1f1194e6-e8bb-6ea6-9dc5-c1d98f6c77fe",
        "winnerTeamAlternateName": "SP",
        "sportEventName": "CBI U20, U15, BRASILEIRO U23, U17 & BRASILEIRÃO SÊNIOR 1º ETAPA",
        "sportEventStartDate": "2026-03-14",
        "sportEventLogo": "/uploads/sport-event/1f1194e3-8d4f-68f4-8284-01e99ca4c679/logo.png",
        "rankingPoint": {
            "fighterId": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
            "fighterFullName": "RENIER LINARES GAVILAN",
            "victoryTypeId": "VSU",
            "victoryTypeName": "VICTORY BY TECHNICAL SUPERIORITY",
            "victoryTypeNiceName": " by VSU",
            "sportId": "fs",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "id": "1f11f9e5-87ab-6f58-afc0-e9b241c1fd44",
            "fightId": "1f11c047-ca3a-6414-8f86-e39fcffe44ce",
            "fighter": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
            "victoryType": "VSU",
            "second": 83
        },
        "completedDate": "2026-03-14T09:07:17-03:00",
        "roundsNumber": 2,
        "roundIds": {
            "1": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
            "2": "1f11c047-ca3a-6874-977b-e39fcffe44ce"
        },
        "roundDuration": 180,
        "overtime": 0,
        "sportAlternateName": "FS",
        "weightCategoryName": "70 kg",
        "weightCategoryAlternateName": "FS - 70 kg",
        "weightCategoryShortName": "Seniors FS 70",
        "weightCategoryMaxWeight": 70,
        "weightCategoryFullName": "Freestyle - Seniors - 70 kg",
        "isWeightCategoryVisible": true,
        "weightCategoryAverageDuration": 480,
        "weightCategoryColor": "#a500ff",
        "weightCategoryReady": true,
        "weightCategoryStarted": true,
        "weightCategoryCompleted": true,
        "victoryTypes": {
            "VE": {
                "identifier": "VE",
                "name": "TEAM VICTORY",
                "winner": 1,
                "loser": 0,
                "weight": 13
            },
            "VFA": {
                "identifier": "VFA",
                "name": "VICTORY BY FALL",
                "winner": 5,
                "loser": 0,
                "criteriaFall": 1,
                "weight": 1
            },
            "VCA": {
                "identifier": "VCA",
                "name": "VICTORY BY 3 CAUTIONS",
                "description": "3 cautions given to the opponent during a bout",
                "winner": 5,
                "loser": 0,
                "weight": 3
            },
            "DSQ": {
                "identifier": "DSQ",
                "name": "DISQUALIFICATION",
                "description": "Before or during the bout for unfair behavior",
                "winner": 5,
                "loser": 0,
                "noRank": 1,
                "disqualifying": 1,
                "weight": 9
            },
            "VIN": {
                "identifier": "VIN",
                "name": "VICTORY BY INJURY",
                "description": "If an athlete is injured before or during a bout",
                "winner": 5,
                "loser": 0,
                "weight": 2
            },
            "VFO": {
                "identifier": "VFO",
                "name": "VICTORY BY FORFEIT",
                "description": "If an athlete doesn't show up on the mat",
                "winner": 5,
                "loser": 0,
                "noRank": 1,
                "weight": 8
            },
            "VSU": {
                "identifier": "VSU",
                "name": "VICTORY BY TECHNICAL SUPERIORITY",
                "description": "Without any point scored by the opponent",
                "winner": 4,
                "loser": 0,
                "criteriaSuperiority": 1,
                "superiorityDifference": 10,
                "weight": 4
            },
            "VSU1": {
                "identifier": "VSU1",
                "name": "VICTORY BY TECHNICAL SUPERIORITY",
                "description": "With point(s) scored by the opponent",
                "winner": 4,
                "loser": 1,
                "criteriaSuperiority": 1,
                "superiorityDifference": 10,
                "weight": 5
            },
            "VPO": {
                "identifier": "VPO",
                "name": "VICTORY BY POINTS",
                "description": "Without any point scored by the opponent",
                "winner": 3,
                "loser": 0,
                "weight": 6
            },
            "VPO1": {
                "identifier": "VPO1",
                "name": "VICTORY BY POINTS",
                "description": "With point(s) scored by the opponent",
                "winner": 3,
                "loser": 1,
                "weight": 7
            },
            "2DSQ": {
                "identifier": "2DSQ",
                "name": "DOUBLE DISQUALIFICATION",
                "description": "Both wrestlers disqualified due to infraction",
                "winner": 0,
                "loser": 0,
                "noRank": 1,
                "disqualifying": 1,
                "weight": 10
            },
            "2VFO": {
                "name": "DOUBLE FORFEIT",
                "identifier": "2VFO",
                "winner": 0,
                "loser": 0,
                "weight": 11,
                "noRank": 1,
                "description": "None of wrestlers pass the weight or show up on the mat"
            },
            "2VIN": {
                "name": "DOUBLE INJURY",
                "identifier": "2VIN",
                "winner": 0,
                "loser": 0,
                "weight": 12,
                "description": "Both wrestlers are injured"
            },
            "V0": {
                "name": "FAKE VICTORY",
                "identifier": "V0",
                "winner": 0,
                "loser": 0,
                "weight": 14,
                "description": "Fake victory"
            }
        },
        "victoryTypesArray": [
            {
                "identifier": "VE",
                "name": "TEAM VICTORY",
                "winner": 1,
                "loser": 0,
                "weight": 13
            },
            {
                "identifier": "VFA",
                "name": "VICTORY BY FALL",
                "winner": 5,
                "loser": 0,
                "criteriaFall": 1,
                "weight": 1
            },
            {
                "identifier": "VCA",
                "name": "VICTORY BY 3 CAUTIONS",
                "description": "3 cautions given to the opponent during a bout",
                "winner": 5,
                "loser": 0,
                "weight": 3
            },
            {
                "identifier": "DSQ",
                "name": "DISQUALIFICATION",
                "description": "Before or during the bout for unfair behavior",
                "winner": 5,
                "loser": 0,
                "noRank": 1,
                "disqualifying": 1,
                "weight": 9
            },
            {
                "identifier": "VIN",
                "name": "VICTORY BY INJURY",
                "description": "If an athlete is injured before or during a bout",
                "winner": 5,
                "loser": 0,
                "weight": 2
            },
            {
                "identifier": "VFO",
                "name": "VICTORY BY FORFEIT",
                "description": "If an athlete doesn't show up on the mat",
                "winner": 5,
                "loser": 0,
                "noRank": 1,
                "weight": 8
            },
            {
                "identifier": "VSU",
                "name": "VICTORY BY TECHNICAL SUPERIORITY",
                "description": "Without any point scored by the opponent",
                "winner": 4,
                "loser": 0,
                "criteriaSuperiority": 1,
                "superiorityDifference": 10,
                "weight": 4
            },
            {
                "identifier": "VSU1",
                "name": "VICTORY BY TECHNICAL SUPERIORITY",
                "description": "With point(s) scored by the opponent",
                "winner": 4,
                "loser": 1,
                "criteriaSuperiority": 1,
                "superiorityDifference": 10,
                "weight": 5
            },
            {
                "identifier": "VPO",
                "name": "VICTORY BY POINTS",
                "description": "Without any point scored by the opponent",
                "winner": 3,
                "loser": 0,
                "weight": 6
            },
            {
                "identifier": "VPO1",
                "name": "VICTORY BY POINTS",
                "description": "With point(s) scored by the opponent",
                "winner": 3,
                "loser": 1,
                "weight": 7
            },
            {
                "identifier": "2DSQ",
                "name": "DOUBLE DISQUALIFICATION",
                "description": "Both wrestlers disqualified due to infraction",
                "winner": 0,
                "loser": 0,
                "noRank": 1,
                "disqualifying": 1,
                "weight": 10
            },
            {
                "name": "DOUBLE FORFEIT",
                "identifier": "2VFO",
                "winner": 0,
                "loser": 0,
                "weight": 11,
                "noRank": 1,
                "description": "None of wrestlers pass the weight or show up on the mat"
            },
            {
                "name": "DOUBLE INJURY",
                "identifier": "2VIN",
                "winner": 0,
                "loser": 0,
                "weight": 12,
                "description": "Both wrestlers are injured"
            },
            {
                "name": "FAKE VICTORY",
                "identifier": "V0",
                "winner": 0,
                "loser": 0,
                "weight": 14,
                "description": "Fake victory"
            }
        ],
        "audienceId": "seniors",
        "audienceName": "Seniors",
        "audienceShortName": "Seniors",
        "sportName": "Freestyle",
        "injuryTime": 240,
        "breakTime": 30,
        "warnings": false,
        "cautions": 3,
        "legFouls": 0,
        "deductionPoints": false,
        "activityTime": 30,
        "sportPointAlias": [
            {
                "label": "1",
                "value": 1
            },
            {
                "label": "2",
                "value": 2
            },
            {
                "label": "4",
                "value": 4
            },
            {
                "label": "5",
                "value": 5
            }
        ],
        "fighter1FullName": "RENIER LINARES GAVILAN",
        "fighter1DisplayName": "RENIER GAVIL .",
        "fighter1FamilyName": "GAVILAN",
        "fighter1GivenName": "Renier Linares",
        "fighter1PreferedName": "RENIER LINARES GAVILAN",
        "fighter1PreferedNames": {
            "isPrintNameChanged": false,
            "isPrintInitialNameChanged": false,
            "isTVNameChanged": false,
            "isTVInitialNameChanged": false,
            "isTVFamilyNameChanged": false,
            "printName": "GAVILAN Renier Linares",
            "printInitialName": "GAVILAN RL",
            "tvName": "Renier Linares GAVILAN",
            "tvInitialName": "R.L. GAVILAN",
            "tvFamilyName": "GAVILAN"
        },
        "fighter1DrawRank": "1",
        "fighter1RobinRank": "A1",
        "fighter1SeedNumber": 1,
        "fighter1AthleteId": "1f1194e6-fb4e-61ea-86de-c1d98f6c77fe",
        "fighter1PersonId": "1f110bfe-79da-651c-b5de-79e22cbbe72c",
        "fighter1AthenaId": null,
        "fighter1IsSeeded": true,
        "fighter1Status": 0,
        "fighter1IsInjured": false,
        "fighter1Weight": null,
        "fighter1IsOlympicQualified": false,
        "fighter2FullName": "CAIO CUZZUOL DANTAS",
        "fighter2DisplayName": "CAIO CUZZUOL .",
        "fighter2FamilyName": "DANTAS",
        "fighter2GivenName": "Caio Cuzzuol",
        "fighter2PreferedName": "CAIO CUZZUOL DANTAS",
        "fighter2PreferedNames": {
            "isPrintNameChanged": false,
            "isPrintInitialNameChanged": false,
            "isTVNameChanged": false,
            "isTVInitialNameChanged": false,
            "isTVFamilyNameChanged": false,
            "printName": "DANTAS Caio Cuzzuol",
            "printInitialName": "DANTAS CC",
            "tvName": "Caio Cuzzuol DANTAS",
            "tvInitialName": "C.C. DANTAS",
            "tvFamilyName": "DANTAS"
        },
        "fighter2DrawRank": 2,
        "fighter2RobinRank": "A2",
        "fighter2SeedNumber": 2,
        "fighter2AthleteId": "1f1194e6-fa00-6752-b85c-c1d98f6c77fe",
        "fighter2PersonId": "1f0fd390-2463-6ca2-b221-d55c759b0267",
        "fighter2IsSeeded": true,
        "fighter2Status": 0,
        "fighter2IsInjured": false,
        "fighter2Weight": null,
        "fighter2IsOlympicQualified": false,
        "result": "4-0(10-0) by VSU - 01:23",
        "victoryType": "VSU",
        "victoryTypeName": "VICTORY BY TECHNICAL SUPERIORITY",
        "endTime": 83,
        "endDate": "2026-03-14T09:07:17-03:00",
        "expectedDateStart": null,
        "expectedStartDate": null,
        "team1Fighters": null,
        "team2Fighters": null,
        "rankingPointNiceName": " by VSU",
        "resultText": "Round 1 FS - 70 kg: RENIER LINARES GAVILAN (SP) df. CAIO CUZZUOL DANTAS (ES) by VSU, 10-0",
        "resultTextSmall": "Round 1 FS - 70 kg: . RENIER LINAR (SP) v. . CAIO CUZZUOL (ES)",
        "roundRenamedSmall": "Round 1",
        "parentFightNumber1": null,
        "parentFightNumber2": null,
        "fightRefereesWithRole": null,
        "needsRefresh": false,
        "isCountdown": true,
        "fighter1HasMoreChallenge": true,
        "fighter2HasMoreChallenge": true,
        "branding": "corporate",
        "roundScores": [],
        "id": "1f11c047-ca3a-6414-8f86-e39fcffe44ce",
        "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
        "sportEventWeightCategoryId": "1f1194e7-09a8-6e20-a850-c1d98f6c77fe",
        "parentFight1Id": null,
        "parentFight2Id": null,
        "fighter1": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
        "fighter1RankingPoint": 4,
        "fighter2": "1f1194e7-0700-6f42-bb80-c1d98f6c77fe",
        "fighter2RankingPoint": 0,
        "refereeGroup": null,
        "sportEventTeam1Id": "1f1194e6-e8bb-6ea6-9dc5-c1d98f6c77fe",
        "sportEventTeam2Id": "1f1194e6-e8fe-622e-ad01-c1d98f6c77fe",
        "fightMatId": "1f1194e3-8d50-697a-9b1b-01e99ca4c679",
        "round": "Round 1",
        "qualifying": false,
        "teamFightId": null,
        "status": 5,
        "rankingCheck": true,
        "technicalCheck": true,
        "weight": 0,
        "fightNumber": 1,
        "roundWeight": 1,
        "repechageWeight": null,
        "repechageSection": null,
        "displayOrder": 13,
        "canceled": null,
        "fightReferees": [],
        "odfCode": null,
        "refereeComment": null,
        "uploaderFight": null
    }
}
```

Returned value by your function:

- `response.fight`

### 5.5 `getAllFightsByEventId(eventId)`

Purpose:

- Retrieve all fights for one event. Same object as above, but for the hole event in the context.

Arena endpoint:

- `GET fight/{eventId}`

cURL:

```bash
curl -X GET "http://localhost:8080/api/json/fight/1f1194e3-8d4f-68f4-8284-01e99ca4c679" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

Expected response example (template):

```json
{
    "fights": [
        {
            "fighter1Id": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
            "fighter2Id": "1f1194e7-0700-6f42-bb80-c1d98f6c77fe",
            "fighter2AthenaId": null,
            "team1Name": "SÃO PAULO",
            "team1AlternateName": "SP",
            "team1FullName": "SÃO PAULO (SP)",
            "team1CountryFlag": "/uploads/custom-logos/4x3/sp.png",
            "team1CountryFlagScoreboard": "/uploads/custom-logos/custom/sp.png",
            "team1CountryFlagMobile": "build/images/logo.svg",
            "team1PoolName": null,
            "team1FightByOpponent": null,
            "team2Name": "ESPÍRITO SANTO",
            "team2AlternateName": "ES",
            "team2FullName": "ESPÍRITO SANTO (ES)",
            "team2CountryFlag": "/uploads/custom-logos/4x3/es.png",
            "team2CountryFlagScoreboard": "/uploads/custom-logos/custom/es.png",
            "team2CountryFlagMobile": "build/images/logo.svg",
            "team2PoolName": null,
            "team2FightByOpponent": null,
            "roundFriendlyName": "Round 1",
            "displayOrderInRound": 1,
            "round1Id": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
            "round2Id": "1f11c047-ca3a-6874-977b-e39fcffe44ce",
            "countReferees": 0,
            "sportId": "fs",
            "athlete1Color": "#ba0000",
            "athlete2Color": "#0000aa",
            "athlete1TextColor": "#ffffff",
            "athlete2TextColor": "#ffffff",
            "matName": "A",
            "sessionId": "1f1194e3-8d50-6524-8875-01e99ca4c679",
            "sessionName": "Dia 1 - Qualificatórias e Finais",
            "sessionStartDate": "2026-03-14",
            "technicalPoints": {
                "1f1194e7-0773-6254-8506-c1d98f6c77fe": {
                    "fullName": "RENIER LINARES GAVILAN",
                    "rounds": {
                        "1f11c047-ca3a-673e-a026-e39fcffe44ce": {
                            "number": 1,
                            "total": 10,
                            "points": {
                                "1f11f9e5-856d-63ea-96a0-5352805c09cf": {
                                    "points": 2,
                                    "second": 36,
                                    "tag": null
                                },
                                "1f11f9e5-85f0-63f8-811a-51c843c252a5": {
                                    "points": 2,
                                    "second": 46,
                                    "tag": null
                                },
                                "1f11f9e5-864d-6878-8938-63f975967849": {
                                    "points": 2,
                                    "second": 49,
                                    "tag": null
                                },
                                "1f11f9e5-86c7-69ac-90ab-3dc7f6ce28ec": {
                                    "points": 2,
                                    "second": 70,
                                    "tag": null
                                },
                                "1f11f9e5-873e-6e4e-9c9c-b98a20723e74": {
                                    "points": 2,
                                    "second": 82,
                                    "tag": null
                                }
                            }
                        }
                    },
                    "total": 10
                }
            },
            "technicalPointsDetail": {
                "1f11f9e5-856d-63ea-96a0-5352805c09cf": {
                    "roundId": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
                    "fighterId": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
                    "point": 2,
                    "second": 36,
                    "rsecond": 324,
                    "round": 1,
                    "tag": null,
                    "metadata": {
                        "actionchallenged": false,
                        "actionTimeStart": 0,
                        "actionTimeEnd": 0,
                        "bigmove": false,
                        "bodypart": "",
                        "distance": "",
                        "ledtofall": false,
                        "injury": false,
                        "result": "",
                        "side": ""
                    }
                },
                "1f11f9e5-85f0-63f8-811a-51c843c252a5": {
                    "roundId": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
                    "fighterId": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
                    "point": 2,
                    "second": 46,
                    "rsecond": 314,
                    "round": 1,
                    "tag": null,
                    "metadata": {
                        "actionchallenged": false,
                        "actionTimeStart": 0,
                        "actionTimeEnd": 0,
                        "bigmove": false,
                        "bodypart": "",
                        "distance": "",
                        "ledtofall": false,
                        "injury": false,
                        "result": "",
                        "side": ""
                    }
                },
                "1f11f9e5-864d-6878-8938-63f975967849": {
                    "roundId": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
                    "fighterId": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
                    "point": 2,
                    "second": 49,
                    "rsecond": 311,
                    "round": 1,
                    "tag": null,
                    "metadata": {
                        "actionchallenged": false,
                        "actionTimeStart": 0,
                        "actionTimeEnd": 0,
                        "bigmove": false,
                        "bodypart": "",
                        "distance": "",
                        "ledtofall": false,
                        "injury": false,
                        "result": "",
                        "side": ""
                    }
                },
                "1f11f9e5-86c7-69ac-90ab-3dc7f6ce28ec": {
                    "roundId": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
                    "fighterId": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
                    "point": 2,
                    "second": 70,
                    "rsecond": 290,
                    "round": 1,
                    "tag": null,
                    "metadata": {
                        "actionchallenged": false,
                        "actionTimeStart": 0,
                        "actionTimeEnd": 0,
                        "bigmove": false,
                        "bodypart": "",
                        "distance": "",
                        "ledtofall": false,
                        "injury": false,
                        "result": "",
                        "side": ""
                    }
                },
                "1f11f9e5-873e-6e4e-9c9c-b98a20723e74": {
                    "roundId": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
                    "fighterId": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
                    "point": 2,
                    "second": 82,
                    "rsecond": 278,
                    "round": 1,
                    "tag": null,
                    "metadata": {
                        "actionchallenged": false,
                        "actionTimeStart": 0,
                        "actionTimeEnd": 0,
                        "bigmove": false,
                        "bodypart": "",
                        "distance": "",
                        "ledtofall": false,
                        "injury": false,
                        "result": "",
                        "side": ""
                    }
                }
            },
            "technicalPointsTagStatus": "missing",
            "technicalPointIds": [
                "1f11f9e5-856d-63ea-96a0-5352805c09cf",
                "1f11f9e5-85f0-63f8-811a-51c843c252a5",
                "1f11f9e5-864d-6878-8938-63f975967849",
                "1f11f9e5-86c7-69ac-90ab-3dc7f6ce28ec",
                "1f11f9e5-873e-6e4e-9c9c-b98a20723e74"
            ],
            "cautionsList": [],
            "cautionPointIds": [],
            "isCompleted": true,
            "isReady": true,
            "isRobinGroupFight": true,
            "winnerFighter": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
            "winnerTeam": "1f1194e6-e8bb-6ea6-9dc5-c1d98f6c77fe",
            "winnerTeamAlternateName": "SP",
            "sportEventName": "CBI U20, U15, BRASILEIRO U23, U17 & BRASILEIRÃO SÊNIOR 1º ETAPA",
            "sportEventStartDate": "2026-03-14",
            "sportEventLogo": "/uploads/sport-event/1f1194e3-8d4f-68f4-8284-01e99ca4c679/logo.png",
            "rankingPoint": {
                "fighterId": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
                "fighterFullName": "RENIER LINARES GAVILAN",
                "victoryTypeId": "VSU",
                "victoryTypeName": "VICTORY BY TECHNICAL SUPERIORITY",
                "victoryTypeNiceName": " by VSU",
                "sportId": "fs",
                "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
                "id": "1f11f9e5-87ab-6f58-afc0-e9b241c1fd44",
                "fightId": "1f11c047-ca3a-6414-8f86-e39fcffe44ce",
                "fighter": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
                "victoryType": "VSU",
                "second": 83
            },
            "completedDate": "2026-03-14T09:07:17-03:00",
            "roundsNumber": 2,
            "roundIds": {
                "1": "1f11c047-ca3a-673e-a026-e39fcffe44ce",
                "2": "1f11c047-ca3a-6874-977b-e39fcffe44ce"
            },
            "roundDuration": 180,
            "overtime": 0,
            "sportAlternateName": "FS",
            "weightCategoryName": "70 kg",
            "weightCategoryAlternateName": "FS - 70 kg",
            "weightCategoryShortName": "Seniors FS 70",
            "weightCategoryMaxWeight": 70,
            "weightCategoryFullName": "Freestyle - Seniors - 70 kg",
            "isWeightCategoryVisible": true,
            "weightCategoryAverageDuration": 480,
            "weightCategoryColor": "#a500ff",
            "weightCategoryReady": true,
            "weightCategoryStarted": true,
            "weightCategoryCompleted": true,
            "victoryTypes": {
                "VE": {
                    "identifier": "VE",
                    "name": "TEAM VICTORY",
                    "winner": 1,
                    "loser": 0,
                    "weight": 13
                },
                "VFA": {
                    "identifier": "VFA",
                    "name": "VICTORY BY FALL",
                    "winner": 5,
                    "loser": 0,
                    "criteriaFall": 1,
                    "weight": 1
                },
                "VCA": {
                    "identifier": "VCA",
                    "name": "VICTORY BY 3 CAUTIONS",
                    "description": "3 cautions given to the opponent during a bout",
                    "winner": 5,
                    "loser": 0,
                    "weight": 3
                },
                "DSQ": {
                    "identifier": "DSQ",
                    "name": "DISQUALIFICATION",
                    "description": "Before or during the bout for unfair behavior",
                    "winner": 5,
                    "loser": 0,
                    "noRank": 1,
                    "disqualifying": 1,
                    "weight": 9
                },
                "VIN": {
                    "identifier": "VIN",
                    "name": "VICTORY BY INJURY",
                    "description": "If an athlete is injured before or during a bout",
                    "winner": 5,
                    "loser": 0,
                    "weight": 2
                },
                "VFO": {
                    "identifier": "VFO",
                    "name": "VICTORY BY FORFEIT",
                    "description": "If an athlete doesn't show up on the mat",
                    "winner": 5,
                    "loser": 0,
                    "noRank": 1,
                    "weight": 8
                },
                "VSU": {
                    "identifier": "VSU",
                    "name": "VICTORY BY TECHNICAL SUPERIORITY",
                    "description": "Without any point scored by the opponent",
                    "winner": 4,
                    "loser": 0,
                    "criteriaSuperiority": 1,
                    "superiorityDifference": 10,
                    "weight": 4
                },
                "VSU1": {
                    "identifier": "VSU1",
                    "name": "VICTORY BY TECHNICAL SUPERIORITY",
                    "description": "With point(s) scored by the opponent",
                    "winner": 4,
                    "loser": 1,
                    "criteriaSuperiority": 1,
                    "superiorityDifference": 10,
                    "weight": 5
                },
                "VPO": {
                    "identifier": "VPO",
                    "name": "VICTORY BY POINTS",
                    "description": "Without any point scored by the opponent",
                    "winner": 3,
                    "loser": 0,
                    "weight": 6
                },
                "VPO1": {
                    "identifier": "VPO1",
                    "name": "VICTORY BY POINTS",
                    "description": "With point(s) scored by the opponent",
                    "winner": 3,
                    "loser": 1,
                    "weight": 7
                },
                "2DSQ": {
                    "identifier": "2DSQ",
                    "name": "DOUBLE DISQUALIFICATION",
                    "description": "Both wrestlers disqualified due to infraction",
                    "winner": 0,
                    "loser": 0,
                    "noRank": 1,
                    "disqualifying": 1,
                    "weight": 10
                },
                "2VFO": {
                    "name": "DOUBLE FORFEIT",
                    "identifier": "2VFO",
                    "winner": 0,
                    "loser": 0,
                    "weight": 11,
                    "noRank": 1,
                    "description": "None of wrestlers pass the weight or show up on the mat"
                },
                "2VIN": {
                    "name": "DOUBLE INJURY",
                    "identifier": "2VIN",
                    "winner": 0,
                    "loser": 0,
                    "weight": 12,
                    "description": "Both wrestlers are injured"
                },
                "V0": {
                    "name": "FAKE VICTORY",
                    "identifier": "V0",
                    "winner": 0,
                    "loser": 0,
                    "weight": 14,
                    "description": "Fake victory"
                }
            },
            "victoryTypesArray": [
                {
                    "identifier": "VE",
                    "name": "TEAM VICTORY",
                    "winner": 1,
                    "loser": 0,
                    "weight": 13
                },
                {
                    "identifier": "VFA",
                    "name": "VICTORY BY FALL",
                    "winner": 5,
                    "loser": 0,
                    "criteriaFall": 1,
                    "weight": 1
                },
                {
                    "identifier": "VCA",
                    "name": "VICTORY BY 3 CAUTIONS",
                    "description": "3 cautions given to the opponent during a bout",
                    "winner": 5,
                    "loser": 0,
                    "weight": 3
                },
                {
                    "identifier": "DSQ",
                    "name": "DISQUALIFICATION",
                    "description": "Before or during the bout for unfair behavior",
                    "winner": 5,
                    "loser": 0,
                    "noRank": 1,
                    "disqualifying": 1,
                    "weight": 9
                },
                {
                    "identifier": "VIN",
                    "name": "VICTORY BY INJURY",
                    "description": "If an athlete is injured before or during a bout",
                    "winner": 5,
                    "loser": 0,
                    "weight": 2
                },
                {
                    "identifier": "VFO",
                    "name": "VICTORY BY FORFEIT",
                    "description": "If an athlete doesn't show up on the mat",
                    "winner": 5,
                    "loser": 0,
                    "noRank": 1,
                    "weight": 8
                },
                {
                    "identifier": "VSU",
                    "name": "VICTORY BY TECHNICAL SUPERIORITY",
                    "description": "Without any point scored by the opponent",
                    "winner": 4,
                    "loser": 0,
                    "criteriaSuperiority": 1,
                    "superiorityDifference": 10,
                    "weight": 4
                },
                {
                    "identifier": "VSU1",
                    "name": "VICTORY BY TECHNICAL SUPERIORITY",
                    "description": "With point(s) scored by the opponent",
                    "winner": 4,
                    "loser": 1,
                    "criteriaSuperiority": 1,
                    "superiorityDifference": 10,
                    "weight": 5
                },
                {
                    "identifier": "VPO",
                    "name": "VICTORY BY POINTS",
                    "description": "Without any point scored by the opponent",
                    "winner": 3,
                    "loser": 0,
                    "weight": 6
                },
                {
                    "identifier": "VPO1",
                    "name": "VICTORY BY POINTS",
                    "description": "With point(s) scored by the opponent",
                    "winner": 3,
                    "loser": 1,
                    "weight": 7
                },
                {
                    "identifier": "2DSQ",
                    "name": "DOUBLE DISQUALIFICATION",
                    "description": "Both wrestlers disqualified due to infraction",
                    "winner": 0,
                    "loser": 0,
                    "noRank": 1,
                    "disqualifying": 1,
                    "weight": 10
                },
                {
                    "name": "DOUBLE FORFEIT",
                    "identifier": "2VFO",
                    "winner": 0,
                    "loser": 0,
                    "weight": 11,
                    "noRank": 1,
                    "description": "None of wrestlers pass the weight or show up on the mat"
                },
                {
                    "name": "DOUBLE INJURY",
                    "identifier": "2VIN",
                    "winner": 0,
                    "loser": 0,
                    "weight": 12,
                    "description": "Both wrestlers are injured"
                },
                {
                    "name": "FAKE VICTORY",
                    "identifier": "V0",
                    "winner": 0,
                    "loser": 0,
                    "weight": 14,
                    "description": "Fake victory"
                }
            ],
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "audienceShortName": "Seniors",
            "sportName": "Freestyle",
            "injuryTime": 240,
            "breakTime": 30,
            "warnings": false,
            "cautions": 3,
            "legFouls": 0,
            "deductionPoints": false,
            "activityTime": 30,
            "sportPointAlias": [
                {
                    "label": "1",
                    "value": 1
                },
                {
                    "label": "2",
                    "value": 2
                },
                {
                    "label": "4",
                    "value": 4
                },
                {
                    "label": "5",
                    "value": 5
                }
            ],
            "fighter1FullName": "RENIER LINARES GAVILAN",
            "fighter1DisplayName": "RENIER GAVIL .",
            "fighter1FamilyName": "GAVILAN",
            "fighter1GivenName": "Renier Linares",
            "fighter1PreferedName": "RENIER LINARES GAVILAN",
            "fighter1PreferedNames": {
                "isPrintNameChanged": false,
                "isPrintInitialNameChanged": false,
                "isTVNameChanged": false,
                "isTVInitialNameChanged": false,
                "isTVFamilyNameChanged": false,
                "printName": "GAVILAN Renier Linares",
                "printInitialName": "GAVILAN RL",
                "tvName": "Renier Linares GAVILAN",
                "tvInitialName": "R.L. GAVILAN",
                "tvFamilyName": "GAVILAN"
            },
            "fighter1DrawRank": "1",
            "fighter1RobinRank": "A1",
            "fighter1SeedNumber": 1,
            "fighter1AthleteId": "1f1194e6-fb4e-61ea-86de-c1d98f6c77fe",
            "fighter1PersonId": "1f110bfe-79da-651c-b5de-79e22cbbe72c",
            "fighter1AthenaId": null,
            "fighter1IsSeeded": true,
            "fighter1Status": 0,
            "fighter1IsInjured": false,
            "fighter1Weight": null,
            "fighter1IsOlympicQualified": false,
            "fighter2FullName": "CAIO CUZZUOL DANTAS",
            "fighter2DisplayName": "CAIO CUZZUOL .",
            "fighter2FamilyName": "DANTAS",
            "fighter2GivenName": "Caio Cuzzuol",
            "fighter2PreferedName": "CAIO CUZZUOL DANTAS",
            "fighter2PreferedNames": {
                "isPrintNameChanged": false,
                "isPrintInitialNameChanged": false,
                "isTVNameChanged": false,
                "isTVInitialNameChanged": false,
                "isTVFamilyNameChanged": false,
                "printName": "DANTAS Caio Cuzzuol",
                "printInitialName": "DANTAS CC",
                "tvName": "Caio Cuzzuol DANTAS",
                "tvInitialName": "C.C. DANTAS",
                "tvFamilyName": "DANTAS"
            },
            "fighter2DrawRank": 2,
            "fighter2RobinRank": "A2",
            "fighter2SeedNumber": 2,
            "fighter2AthleteId": "1f1194e6-fa00-6752-b85c-c1d98f6c77fe",
            "fighter2PersonId": "1f0fd390-2463-6ca2-b221-d55c759b0267",
            "fighter2IsSeeded": true,
            "fighter2Status": 0,
            "fighter2IsInjured": false,
            "fighter2Weight": null,
            "fighter2IsOlympicQualified": false,
            "result": "4-0(10-0) by VSU - 01:23",
            "victoryType": "VSU",
            "victoryTypeName": "VICTORY BY TECHNICAL SUPERIORITY",
            "endTime": 83,
            "endDate": "2026-03-14T09:07:17-03:00",
            "expectedDateStart": null,
            "expectedStartDate": null,
            "team1Fighters": null,
            "team2Fighters": null,
            "rankingPointNiceName": " by VSU",
            "resultText": "Round 1 FS - 70 kg: RENIER LINARES GAVILAN (SP) df. CAIO CUZZUOL DANTAS (ES) by VSU, 10-0",
            "resultTextSmall": "Round 1 FS - 70 kg: . RENIER LINAR (SP) v. . CAIO CUZZUOL (ES)",
            "roundRenamedSmall": "Round 1",
            "parentFightNumber1": null,
            "parentFightNumber2": null,
            "fightRefereesWithRole": null,
            "needsRefresh": false,
            "isCountdown": true,
            "fighter1HasMoreChallenge": true,
            "fighter2HasMoreChallenge": true,
            "branding": "corporate",
            "roundScores": [],
            "id": "1f11c047-ca3a-6414-8f86-e39fcffe44ce",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "sportEventWeightCategoryId": "1f1194e7-09a8-6e20-a850-c1d98f6c77fe",
            "parentFight1Id": null,
            "parentFight2Id": null,
            "fighter1": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
            "fighter1RankingPoint": 4,
            "fighter2": "1f1194e7-0700-6f42-bb80-c1d98f6c77fe",
            "fighter2RankingPoint": 0,
            "refereeGroup": null,
            "sportEventTeam1Id": "1f1194e6-e8bb-6ea6-9dc5-c1d98f6c77fe",
            "sportEventTeam2Id": "1f1194e6-e8fe-622e-ad01-c1d98f6c77fe",
            "fightMatId": "1f1194e3-8d50-697a-9b1b-01e99ca4c679",
            "round": "Round 1",
            "qualifying": false,
            "teamFightId": null,
            "status": 5,
            "rankingCheck": true,
            "technicalCheck": true,
            "weight": 0,
            "fightNumber": 1,
            "roundWeight": 1,
            "repechageWeight": null,
            "repechageSection": null,
            "displayOrder": 13,
            "canceled": null,
            "fightReferees": [],
            "odfCode": null,
            "refereeComment": null,
            "uploaderFight": null
        },
        {
            "fighter1Id": "1f1194e7-06d8-6a7e-9ba3-c1d98f6c77fe",
            "fighter2Id": "1f1194e7-03a4-6f2e-8188-c1d98f6c77fe",
            "fighter2AthenaId": null,
            "team1Name": "PARAÍBA",
            "team1AlternateName": "PB",
            "team1FullName": "PARAÍBA (PB)",
            "team1CountryFlag": "/uploads/custom-logos/4x3/pb.png",
            "team1CountryFlagScoreboard": "/uploads/custom-logos/custom/pb.png",
            "team1CountryFlagMobile": "build/images/logo.svg",
            "team1PoolName": null,
            "team1FightByOpponent": null,
            "team2Name": "PERNAMBUCO",
            "team2AlternateName": "PE",
            "team2FullName": "PERNAMBUCO (PE)",
            "team2CountryFlag": "/uploads/custom-logos/4x3/pe.png",
            "team2CountryFlagScoreboard": "/uploads/custom-logos/custom/pe.png",
            "team2CountryFlagMobile": "build/images/logo.svg",
            "team2PoolName": null,
            "team2FightByOpponent": null,
            "roundFriendlyName": "Round 1",
            "displayOrderInRound": 1,
            "round1Id": "1f11c047-ca28-6426-aff9-e39fcffe44ce",
            "round2Id": "1f11c047-ca28-655c-a68e-e39fcffe44ce",
            "countReferees": 0,
            "sportId": "gr",
            "athlete1Color": "#ba0000",
            "athlete2Color": "#0000aa",
            "athlete1TextColor": "#ffffff",
            "athlete2TextColor": "#ffffff",
            "matName": "B",
            "sessionId": "1f1194e3-8d50-6524-8875-01e99ca4c679",
            "sessionName": "Dia 1 - Qualificatórias e Finais",
            "sessionStartDate": "2026-03-14",
            "technicalPoints": {
                "1f1194e7-06d8-6a7e-9ba3-c1d98f6c77fe": {
                    "fullName": "JOAO SAVYO PEREIRA DA SILVA",
                    "rounds": {
                        "1f11c047-ca28-6426-aff9-e39fcffe44ce": {
                            "number": 1,
                            "total": 4,
                            "points": {
                                "1f11f9f8-7080-65e6-8855-3599fdfdfbc3": {
                                    "points": 4,
                                    "second": 0,
                                    "tag": null
                                }
                            }
                        }
                    },
                    "total": 4
                }
            },
            "technicalPointsDetail": {
                "1f11f9f8-7080-65e6-8855-3599fdfdfbc3": {
                    "roundId": "1f11c047-ca28-6426-aff9-e39fcffe44ce",
                    "fighterId": "1f1194e7-06d8-6a7e-9ba3-c1d98f6c77fe",
                    "point": 4,
                    "second": 0,
                    "rsecond": 360,
                    "round": 1,
                    "tag": null,
                    "metadata": {
                        "actionchallenged": false,
                        "actionTimeStart": 0,
                        "actionTimeEnd": 0,
                        "bigmove": false,
                        "bodypart": "",
                        "distance": "",
                        "ledtofall": false,
                        "injury": false,
                        "result": "",
                        "side": ""
                    }
                }
            },
            "technicalPointsTagStatus": "missing",
            "technicalPointIds": [
                "1f11f9f8-7080-65e6-8855-3599fdfdfbc3"
            ],
            "cautionsList": [],
            "cautionPointIds": [],
            "isCompleted": true,
            "isReady": true,
            "isRobinGroupFight": true,
            "winnerFighter": "1f1194e7-06d8-6a7e-9ba3-c1d98f6c77fe",
            "winnerTeam": "1f1194e6-e8b2-61f8-a415-c1d98f6c77fe",
            "winnerTeamAlternateName": "PB",
            "sportEventName": "CBI U20, U15, BRASILEIRO U23, U17 & BRASILEIRÃO SÊNIOR 1º ETAPA",
            "sportEventStartDate": "2026-03-14",
            "sportEventLogo": "/uploads/sport-event/1f1194e3-8d4f-68f4-8284-01e99ca4c679/logo.png",
            "rankingPoint": {
                "fighterId": "1f1194e7-06d8-6a7e-9ba3-c1d98f6c77fe",
                "fighterFullName": "JOAO SAVYO PEREIRA DA SILVA",
                "victoryTypeId": "VFA",
                "victoryTypeName": "VICTORY BY FALL",
                "victoryTypeNiceName": " by VFA",
                "sportId": "gr",
                "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
                "id": "1f11f9e1-ed07-64a0-a54a-fbc1efd189fe",
                "fightId": "1f11c047-ca28-6110-95cd-e39fcffe44ce",
                "fighter": "1f1194e7-06d8-6a7e-9ba3-c1d98f6c77fe",
                "victoryType": "VFA",
                "second": 6
            },
            "completedDate": "2026-03-14T09:05:40-03:00",
            "roundsNumber": 2,
            "roundIds": {
                "1": "1f11c047-ca28-6426-aff9-e39fcffe44ce",
                "2": "1f11c047-ca28-655c-a68e-e39fcffe44ce"
            },
            "roundDuration": 180,
            "overtime": 0,
            "sportAlternateName": "GR",
            "weightCategoryName": "82 kg",
            "weightCategoryAlternateName": "GR - 82 kg",
            "weightCategoryShortName": "Seniors GR 82",
            "weightCategoryMaxWeight": 82,
            "weightCategoryFullName": "Greco-Roman - Seniors - 82 kg",
            "isWeightCategoryVisible": true,
            "weightCategoryAverageDuration": 540,
            "weightCategoryColor": "#979fb1",
            "weightCategoryReady": true,
            "weightCategoryStarted": true,
            "weightCategoryCompleted": true,
            "victoryTypes": {
                "VE": {
                    "identifier": "VE",
                    "name": "TEAM VICTORY",
                    "winner": 1,
                    "loser": 0,
                    "criteriaFall": 1,
                    "weight": 13
                },
                "VFA": {
                    "identifier": "VFA",
                    "name": "VICTORY BY FALL",
                    "winner": 5,
                    "loser": 0,
                    "criteriaFall": 1,
                    "weight": 1
                },
                "VCA": {
                    "identifier": "VCA",
                    "name": "VICTORY BY 3 CAUTIONS",
                    "description": "Opponent received 3 cautions or made 2 leg fouls during a bout",
                    "winner": 5,
                    "loser": 0,
                    "weight": 3
                },
                "DSQ": {
                    "identifier": "DSQ",
                    "name": "DISQUALIFICATION",
                    "description": "Before or during the bout for unfair behavior",
                    "winner": 5,
                    "loser": 0,
                    "noRank": 1,
                    "disqualifying": 1,
                    "weight": 9
                },
                "VIN": {
                    "identifier": "VIN",
                    "name": "VICTORY BY INJURY",
                    "description": "If an athlete is injured before or during a bout",
                    "winner": 5,
                    "loser": 0,
                    "weight": 2
                },
                "VFO": {
                    "identifier": "VFO",
                    "name": "VICTORY BY FORFEIT",
                    "description": "If an athlete doesn't show up on the mat",
                    "winner": 5,
                    "loser": 0,
                    "noRank": 1,
                    "weight": 8
                },
                "VSU": {
                    "identifier": "VSU",
                    "name": "VICTORY BY TECHNICAL SUPERIORITY",
                    "description": "Without any point scored by the opponent",
                    "winner": 4,
                    "loser": 0,
                    "criteriaSuperiority": 1,
                    "superiorityDifference": 8,
                    "weight": 4
                },
                "VSU1": {
                    "identifier": "VSU1",
                    "name": "VICTORY BY TECHNICAL SUPERIORITY",
                    "description": "With point(s) scored by the opponent",
                    "winner": 4,
                    "loser": 1,
                    "criteriaSuperiority": 1,
                    "superiorityDifference": 8,
                    "weight": 5
                },
                "VPO": {
                    "identifier": "VPO",
                    "name": "VICTORY BY POINTS",
                    "description": "Without any point scored by the opponent",
                    "winner": 3,
                    "loser": 0,
                    "weight": 6
                },
                "VPO1": {
                    "identifier": "VPO1",
                    "name": "VICTORY BY POINTS",
                    "description": "With point(s) scored by the opponent",
                    "winner": 3,
                    "loser": 1,
                    "weight": 7
                },
                "2DSQ": {
                    "identifier": "2DSQ",
                    "name": "DOUBLE DISQUALIFICATION",
                    "description": "Both wrestlers disqualified due to infraction",
                    "winner": 0,
                    "loser": 0,
                    "noRank": 1,
                    "disqualifying": 1,
                    "weight": 10
                },
                "2VFO": {
                    "name": "DOUBLE FORFEIT",
                    "identifier": "2VFO",
                    "winner": 0,
                    "loser": 0,
                    "weight": 11,
                    "noRank": 1,
                    "description": "None of wrestlers pass the weight or show up on the mat"
                },
                "2VIN": {
                    "name": "DOUBLE INJURY",
                    "identifier": "2VIN",
                    "winner": 0,
                    "loser": 0,
                    "weight": 12,
                    "description": "Both wrestlers are injured"
                },
                "V0": {
                    "name": "FAKE VICTORY",
                    "identifier": "V0",
                    "winner": 1,
                    "loser": 0,
                    "weight": 14,
                    "description": "Fake victory"
                }
            },
            "victoryTypesArray": [
                {
                    "identifier": "VE",
                    "name": "TEAM VICTORY",
                    "winner": 1,
                    "loser": 0,
                    "criteriaFall": 1,
                    "weight": 13
                },
                {
                    "identifier": "VFA",
                    "name": "VICTORY BY FALL",
                    "winner": 5,
                    "loser": 0,
                    "criteriaFall": 1,
                    "weight": 1
                },
                {
                    "identifier": "VCA",
                    "name": "VICTORY BY 3 CAUTIONS",
                    "description": "Opponent received 3 cautions or made 2 leg fouls during a bout",
                    "winner": 5,
                    "loser": 0,
                    "weight": 3
                },
                {
                    "identifier": "DSQ",
                    "name": "DISQUALIFICATION",
                    "description": "Before or during the bout for unfair behavior",
                    "winner": 5,
                    "loser": 0,
                    "noRank": 1,
                    "disqualifying": 1,
                    "weight": 9
                },
                {
                    "identifier": "VIN",
                    "name": "VICTORY BY INJURY",
                    "description": "If an athlete is injured before or during a bout",
                    "winner": 5,
                    "loser": 0,
                    "weight": 2
                },
                {
                    "identifier": "VFO",
                    "name": "VICTORY BY FORFEIT",
                    "description": "If an athlete doesn't show up on the mat",
                    "winner": 5,
                    "loser": 0,
                    "noRank": 1,
                    "weight": 8
                },
                {
                    "identifier": "VSU",
                    "name": "VICTORY BY TECHNICAL SUPERIORITY",
                    "description": "Without any point scored by the opponent",
                    "winner": 4,
                    "loser": 0,
                    "criteriaSuperiority": 1,
                    "superiorityDifference": 8,
                    "weight": 4
                },
                {
                    "identifier": "VSU1",
                    "name": "VICTORY BY TECHNICAL SUPERIORITY",
                    "description": "With point(s) scored by the opponent",
                    "winner": 4,
                    "loser": 1,
                    "criteriaSuperiority": 1,
                    "superiorityDifference": 8,
                    "weight": 5
                },
                {
                    "identifier": "VPO",
                    "name": "VICTORY BY POINTS",
                    "description": "Without any point scored by the opponent",
                    "winner": 3,
                    "loser": 0,
                    "weight": 6
                },
                {
                    "identifier": "VPO1",
                    "name": "VICTORY BY POINTS",
                    "description": "With point(s) scored by the opponent",
                    "winner": 3,
                    "loser": 1,
                    "weight": 7
                },
                {
                    "identifier": "2DSQ",
                    "name": "DOUBLE DISQUALIFICATION",
                    "description": "Both wrestlers disqualified due to infraction",
                    "winner": 0,
                    "loser": 0,
                    "noRank": 1,
                    "disqualifying": 1,
                    "weight": 10
                },
                {
                    "name": "DOUBLE FORFEIT",
                    "identifier": "2VFO",
                    "winner": 0,
                    "loser": 0,
                    "weight": 11,
                    "noRank": 1,
                    "description": "None of wrestlers pass the weight or show up on the mat"
                },
                {
                    "name": "DOUBLE INJURY",
                    "identifier": "2VIN",
                    "winner": 0,
                    "loser": 0,
                    "weight": 12,
                    "description": "Both wrestlers are injured"
                },
                {
                    "name": "FAKE VICTORY",
                    "identifier": "V0",
                    "winner": 1,
                    "loser": 0,
                    "weight": 14,
                    "description": "Fake victory"
                }
            ],
            "audienceId": "seniors",
            "audienceName": "Seniors",
            "audienceShortName": "Seniors",
            "sportName": "Greco-Roman",
            "injuryTime": 240,
            "breakTime": 30,
            "warnings": true,
            "cautions": 3,
            "legFouls": 2,
            "deductionPoints": false,
            "activityTime": 30,
            "sportPointAlias": [
                {
                    "label": "1",
                    "value": 1
                },
                {
                    "label": "2",
                    "value": 2
                },
                {
                    "label": "4",
                    "value": 4
                },
                {
                    "label": "5",
                    "value": 5
                }
            ],
            "fighter1FullName": "JOAO SAVYO PEREIRA DA SILVA",
            "fighter1DisplayName": "SAVYO SILVA .",
            "fighter1FamilyName": "SILVA",
            "fighter1GivenName": "Joao Savyo Pereira Da",
            "fighter1PreferedName": "JOAO SAVYO PEREIRA DA SILVA",
            "fighter1PreferedNames": {
                "isPrintNameChanged": false,
                "isPrintInitialNameChanged": false,
                "isTVNameChanged": false,
                "isTVInitialNameChanged": false,
                "isTVFamilyNameChanged": false,
                "printName": "SILVA Joao Savyo Pereira da",
                "printInitialName": "SILVA JSPD",
                "tvName": "Joao Savyo Pereira da SILVA",
                "tvInitialName": "J.S.P.D. SILVA",
                "tvFamilyName": "SILVA"
            },
            "fighter1DrawRank": "1",
            "fighter1RobinRank": "A1",
            "fighter1SeedNumber": 1,
            "fighter1AthleteId": "1f1194e7-06d6-67ba-9a42-c1d98f6c77fe",
            "fighter1PersonId": "1f110bfe-78f3-6c02-9110-79e22cbbe72c",
            "fighter1AthenaId": null,
            "fighter1IsSeeded": true,
            "fighter1Status": 0,
            "fighter1IsInjured": false,
            "fighter1Weight": null,
            "fighter1IsOlympicQualified": false,
            "fighter2FullName": "JOAO VITOR DE ANDRADE NETO",
            "fighter2DisplayName": "JOAO NETO .",
            "fighter2FamilyName": "NETO",
            "fighter2GivenName": "Joao Vitor De Andrade",
            "fighter2PreferedName": "JOAO VITOR DE ANDRADE NETO",
            "fighter2PreferedNames": {
                "isPrintNameChanged": false,
                "isPrintInitialNameChanged": false,
                "isTVNameChanged": false,
                "isTVInitialNameChanged": false,
                "isTVFamilyNameChanged": false,
                "printName": "NETO Joao Vitor de Andrade",
                "printInitialName": "NETO JVDA",
                "tvName": "Joao Vitor de Andrade NETO",
                "tvInitialName": "J.V.D.A. NETO",
                "tvFamilyName": "NETO"
            },
            "fighter2DrawRank": 2,
            "fighter2RobinRank": "A2",
            "fighter2SeedNumber": 2,
            "fighter2AthleteId": "1f1194e7-03a1-6234-a5ab-c1d98f6c77fe",
            "fighter2PersonId": "1f110bfe-7690-63d4-9c40-79e22cbbe72c",
            "fighter2IsSeeded": true,
            "fighter2Status": 1,
            "fighter2IsInjured": false,
            "fighter2Weight": null,
            "fighter2IsOlympicQualified": false,
            "result": "5-0(4-0) by VFA - 00:06",
            "victoryType": "VFA",
            "victoryTypeName": "VICTORY BY FALL",
            "endTime": 6,
            "endDate": "2026-03-14T09:05:40-03:00",
            "expectedDateStart": null,
            "expectedStartDate": null,
            "team1Fighters": null,
            "team2Fighters": null,
            "rankingPointNiceName": " by VFA",
            "resultText": "Round 1 GR - 82 kg: JOAO SAVYO PEREIRA DA SILVA (PB) df. JOAO VITOR DE ANDRADE NETO (PE) by VFA, 4-0",
            "resultTextSmall": "Round 1 GR - 82 kg: . JOAO SAVYO P (PB) v. . JOAO VITOR D (PE)",
            "roundRenamedSmall": "Round 1",
            "parentFightNumber1": null,
            "parentFightNumber2": null,
            "fightRefereesWithRole": null,
            "needsRefresh": false,
            "isCountdown": true,
            "fighter1HasMoreChallenge": true,
            "fighter2HasMoreChallenge": true,
            "branding": "corporate",
            "roundScores": [],
            "id": "1f11c047-ca28-6110-95cd-e39fcffe44ce",
            "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "sportEventWeightCategoryId": "1f1194e7-09ad-6fec-8c00-c1d98f6c77fe",
            "parentFight1Id": null,
            "parentFight2Id": null,
            "fighter1": "1f1194e7-06d8-6a7e-9ba3-c1d98f6c77fe",
            "fighter1RankingPoint": 5,
            "fighter2": "1f1194e7-03a4-6f2e-8188-c1d98f6c77fe",
            "fighter2RankingPoint": 0,
            "refereeGroup": null,
            "sportEventTeam1Id": "1f1194e6-e8b2-61f8-a415-c1d98f6c77fe",
            "sportEventTeam2Id": "1f1194e6-ebd1-66fe-bf00-c1d98f6c77fe",
            "fightMatId": "1f1194e3-8d50-6b82-9f50-01e99ca4c679",
            "round": "Round 1",
            "qualifying": false,
            "teamFightId": null,
            "status": 5,
            "rankingCheck": true,
            "technicalCheck": true,
            "weight": 0,
            "fightNumber": 101,
            "roundWeight": 1,
            "repechageWeight": null,
            "repechageSection": null,
            "displayOrder": 5,
            "canceled": null,
            "fightReferees": [],
            "odfCode": null,
            "refereeComment": null,
            "uploaderFight": null
        }
    ]
}
```

Returned value by your function:

- `response.fights`

### 5.6 `getBracketByCategoryId(eventId, sportEventWeightCategoryId)`

Purpose:

- Retrieve fights ordered by bracket data for a category .

Arena endpoint currently used by this integration:

- `GET fight/{eventId}/bracket/{sportEventWeightCategoryId}`

cURL (fights ordered bracket):

```bash
curl -X GET "http://localhost:8080/api/json/fight/{eventId}/bracket/{sportEventWeightCategoryId}" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

Expected response example (template):

```json
{
  "same as request above"
}
```

Returned value by your function:

- Full JSON payload

### 5.7 `getAllSportEventsInfo(limit)`

Purpose:

- Retrieve sport events visible under a given auth/context.

Arena endpoint:

- `GET sport-event/last-{limit}`

cURL:

```bash
curl -X GET "http://localhost:8080/api/json/sport-event/last-2" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

Expected response example (template):

```json
{
    "events": [
        {
            "fullName": "CBI U20, U15, BRASILEIRO U23, U17 & BRASILEIRÃO SÊNIOR 1º ETAPA - CUBATÃO, BR - from 2026-03-14 to 2026-03-15",
            "address": "CUBATÃO, BR",
            "isIndividualEvent": true,
            "isIndividualLegacyEvent": false,
            "isTeamEvent": false,
            "isBeachWrestlingTournament": false,
            "isSyncEnabled": false,
            "logo": "/uploads/sport-event/1f1194e3-8d4f-68f4-8284-01e99ca4c679/logo.png",
            "id": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
            "name": "CBI U20, U15, BRASILEIRO U23, U17 & BRASILEIRÃO SÊNIOR 1º ETAPA",
            "startDate": "2026-03-14",
            "endDate": "2026-03-15",
            "rankingType": "individual",
            "tournamentType": "singlebracket",
            "sessionType": "1day",
            "uwwRankingType": null,
            "eventType": "other",
            "timezone": "America/Sao_Paulo",
            "visible": true,
            "secure": false,
            "localClient": null,
            "remote": null,
            "remoteStatus": null,
            "odfCode": null,
            "nbSeeds": 4,
            "currentRound": null
        },
        {
            "fullName": "TRIALS U15, U20 2026 - CUBATÃO, BR - from 2026-03-14 to 2026-03-15",
            "address": "CUBATÃO, BR",
            "isIndividualEvent": true,
            "isIndividualLegacyEvent": false,
            "isTeamEvent": false,
            "isBeachWrestlingTournament": false,
            "isSyncEnabled": false,
            "logo": "/uploads/sport-event/1f119506-52b1-6fbc-beb1-1f6146fa50d2/logo.png",
            "id": "1f119506-52b1-6fbc-beb1-1f6146fa50d2",
            "name": "TRIALS U15, U20 2026",
            "startDate": "2026-03-14",
            "endDate": "2026-03-15",
            "rankingType": "individual",
            "tournamentType": "singlebracket",
            "sessionType": "1day",
            "uwwRankingType": null,
            "eventType": "continental-championships",
            "timezone": "America/Sao_Paulo",
            "visible": true,
            "secure": false,
            "localClient": null,
            "remote": null,
            "remoteStatus": null,
            "odfCode": null,
            "nbSeeds": 4,
            "currentRound": null
        }
    ]
}
```

### 5.8 `getWeightCategoryInfoById(sportEventWeightCategoryId)`

Purpose:

- Retrieve details of one weight category.

Arena endpoint:

- `GET weight-category/get/{sportEventWeightCategoryId}`

cURL:

```bash
curl -X GET "http://localhost:8080/api/json/weight-category/get/555" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

Expected response example (template):

```json
{
    "weightCategory": {
        "sportAlternateName": "GR",
        "sportName": "Greco-Roman",
        "fullName": "Greco-Roman - Seniors - 82 kg",
        "alternateName": "GR - 82 kg",
        "shortName": "Seniors GR 82",
        "sportId": "gr",
        "audienceId": "seniors",
        "audienceName": "Seniors",
        "isVeteran": false,
        "audienceShortName": "Seniors",
        "isSinglebracketTournament": true,
        "isDoublebracketTournament": false,
        "isDoubleEliminationTournament": false,
        "isRoundRobinTournament": false,
        "isBeltWrestlingCategory": false,
        "isAlyshTournament": false,
        "isKazakhCategory": false,
        "isPankrationCategory": false,
        "isGrapplingCategory": false,
        "isBeachWrestlingTournament": false,
        "sportPointAliases": [
            {
                "label": "1",
                "value": 1
            },
            {
                "label": "2",
                "value": 2
            },
            {
                "label": "4",
                "value": 4
            },
            {
                "label": "5",
                "value": 5
            }
        ],
        "fightersIsReady": [
            {
                "sportEventWeightCategoryId": "1f1194e7-09ad-6fec-8c00-c1d98f6c77fe",
                "weightCategoryFullName": "Greco-Roman - Seniors - 82 kg",
                "weightCategoryShortName": "Seniors GR 82",
                "weightCategoryCountFights": 10,
                "hasWeightCategoryBlockchainIds": true,
                "weightCategoryCountReadyFighters": 5,
                "hasFighterStatusWithoutReason": false,
                "countFights": 4,
                "nbChallenges": {
                    "group": 0,
                    "finals": 0
                },
                "personId": "1f110bfe-78f3-6c02-9110-79e22cbbe72c",
                "fullName": "JOAO SAVYO PEREIRA DA SILVA",
                "preferedName": "JOAO SAVYO PEREIRA DA SILVA",
                "displayName": "SAVYO SILVA .",
                "givenName": "Joao Savyo Pereira Da",
                "familyName": "SILVA",
                "personPhoto": "/build/images/placeholder-man.01372165.jpg",
                "athenaPrintId": null,
                "odfCode": null,
                "teamAlternateName": "PB",
                "teamName": "PARAÍBA",
                "teamCountryFlag": "/uploads/custom-logos/4x3/pb.png",
                "sportEventTeamId": "1f1194e6-e8b2-61f8-a415-c1d98f6c77fe",
                "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
                "drawRank": 1,
                "robinGroup": {
                    "group": "A",
                    "drawRank": 1,
                    "wins": 4,
                    "classificationPoints": 18,
                    "winEasy": 2,
                    "winSuperiority": 2,
                    "technicalPointsFor": 25,
                    "technicalPointAgainst": 0
                },
                "robinGroupRank": 1,
                "teamRankingPoint": 25,
                "uwwPoint": 0,
                "isFinalistBronze": false,
                "isFinalistGold": false,
                "isFinalist": false,
                "isOlympicQualified": false,
                "knockOutStatus": null,
                "canHaveMoreBeachFights": false,
                "hasLostknockOut": false,
                "completed": 4,
                "wins": 4,
                "losses": 0,
                "technicalPointsFor": 25,
                "technicalPointsAgainst": 0,
                "technicalPointsDiff": 25,
                "rankingPointsFor": 18,
                "rankingPointsAgainst": 0,
                "rankingPointsDiff": 18,
                "winsEasy": 2,
                "winsSuperiority": 2,
                "rank": 1,
                "rankRobinGroup": 1,
                "fightByOpponent": null,
                "isCompeting": true,
                "hasOpenFight": false,
                "isDisqualified": false,
                "isNotRanked": false,
                "isInjured": false,
                "isForfeit": false,
                "isRobinGroupNotRanked": false,
                "accreditationStatus": 0,
                "id": "1f1194e7-06d8-6a7e-9ba3-c1d98f6c77fe",
                "sportEventWeightCategory": "1f1194e7-09ad-6fec-8c00-c1d98f6c77fe",
                "athleteId": "1f1194e7-06d6-67ba-9a42-c1d98f6c77fe",
                "weight": null,
                "drawNumber": 0,
                "seedNumber": 1,
                "fighterWeight": null,
                "points": null,
                "fighterStatus": 0,
                "fighterStatusReason": 0,
                "topTechnique": false,
                "rankingException": null
            },
            {
                "sportEventWeightCategoryId": "1f1194e7-09ad-6fec-8c00-c1d98f6c77fe",
                "weightCategoryFullName": "Greco-Roman - Seniors - 82 kg",
                "weightCategoryShortName": "Seniors GR 82",
                "weightCategoryCountFights": 10,
                "hasWeightCategoryBlockchainIds": true,
                "weightCategoryCountReadyFighters": 5,
                "hasFighterStatusWithoutReason": true,
                "countFights": 4,
                "nbChallenges": {
                    "group": 0,
                    "finals": 0
                },
                "personId": "1f110bfe-7690-63d4-9c40-79e22cbbe72c",
                "fullName": "JOAO VITOR DE ANDRADE NETO",
                "preferedName": "JOAO VITOR DE ANDRADE NETO",
                "displayName": "JOAO NETO .",
                "givenName": "Joao Vitor De Andrade",
                "familyName": "NETO",
                "personPhoto": "/build/images/placeholder-man.01372165.jpg",
                "athenaPrintId": null,
                "odfCode": null,
                "teamAlternateName": "PE",
                "teamName": "PERNAMBUCO",
                "teamCountryFlag": "/uploads/custom-logos/4x3/pe.png",
                "sportEventTeamId": "1f1194e6-ebd1-66fe-bf00-c1d98f6c77fe",
                "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
                "drawRank": 2,
                "robinGroup": {
                    "group": "A",
                    "drawRank": 2,
                    "wins": 0,
                    "classificationPoints": 0,
                    "winEasy": 0,
                    "winSuperiority": 0,
                    "technicalPointsFor": 0,
                    "technicalPointAgainst": 8
                },
                "robinGroupRank": 5,
                "teamRankingPoint": 0,
                "uwwPoint": 0,
                "isFinalistBronze": false,
                "isFinalistGold": false,
                "isFinalist": false,
                "isOlympicQualified": false,
                "knockOutStatus": null,
                "canHaveMoreBeachFights": false,
                "hasLostknockOut": false,
                "completed": 4,
                "wins": 0,
                "losses": 4,
                "technicalPointsFor": 0,
                "technicalPointsAgainst": 8,
                "technicalPointsDiff": -8,
                "rankingPointsFor": 0,
                "rankingPointsAgainst": 20,
                "rankingPointsDiff": -20,
                "winsEasy": 0,
                "winsSuperiority": 0,
                "rank": 5,
                "rankRobinGroup": 5,
                "fightByOpponent": null,
                "isCompeting": true,
                "hasOpenFight": false,
                "isDisqualified": false,
                "isNotRanked": true,
                "isInjured": false,
                "isForfeit": true,
                "isRobinGroupNotRanked": true,
                "accreditationStatus": 0,
                "id": "1f1194e7-03a4-6f2e-8188-c1d98f6c77fe",
                "sportEventWeightCategory": "1f1194e7-09ad-6fec-8c00-c1d98f6c77fe",
                "athleteId": "1f1194e7-03a1-6234-a5ab-c1d98f6c77fe",
                "weight": null,
                "drawNumber": 0,
                "seedNumber": 2,
                "fighterWeight": null,
                "points": null,
                "fighterStatus": 1,
                "fighterStatusReason": 0,
                "topTechnique": false,
                "rankingException": null
            },
            {
                "sportEventWeightCategoryId": "1f1194e7-09ad-6fec-8c00-c1d98f6c77fe",
                "weightCategoryFullName": "Greco-Roman - Seniors - 82 kg",
                "weightCategoryShortName": "Seniors GR 82",
                "weightCategoryCountFights": 10,
                "hasWeightCategoryBlockchainIds": true,
                "weightCategoryCountReadyFighters": 5,
                "hasFighterStatusWithoutReason": false,
                "countFights": 4,
                "nbChallenges": {
                    "group": 0,
                    "finals": 0
                },
                "personId": "1f110bfe-7885-6d2e-9577-79e22cbbe72c",
                "fullName": "ADRIEL DO NASCIMENTO DE SOUZA",
                "preferedName": "ADRIEL DO NASCIMENTO DE SOUZA",
                "displayName": "ADRIEL DO NA .",
                "givenName": "Adriel Do Nascimento De",
                "familyName": "SOUZA",
                "personPhoto": "/build/images/placeholder-man.01372165.jpg",
                "athenaPrintId": null,
                "odfCode": null,
                "teamAlternateName": "RJ",
                "teamName": "RIO DE JANEIRO",
                "teamCountryFlag": "/uploads/custom-logos/4x3/rj.png",
                "sportEventTeamId": "1f1194e6-e914-656a-b54c-c1d98f6c77fe",
                "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
                "drawRank": 3,
                "robinGroup": {
                    "group": "A",
                    "drawRank": 3,
                    "wins": 3,
                    "classificationPoints": 13,
                    "winEasy": 1,
                    "winSuperiority": 2,
                    "technicalPointsFor": 26,
                    "technicalPointAgainst": 9
                },
                "robinGroupRank": 2,
                "teamRankingPoint": 20,
                "uwwPoint": 0,
                "isFinalistBronze": false,
                "isFinalistGold": false,
                "isFinalist": false,
                "isOlympicQualified": false,
                "knockOutStatus": null,
                "canHaveMoreBeachFights": false,
                "hasLostknockOut": false,
                "completed": 4,
                "wins": 3,
                "losses": 1,
                "technicalPointsFor": 26,
                "technicalPointsAgainst": 9,
                "technicalPointsDiff": 17,
                "rankingPointsFor": 13,
                "rankingPointsAgainst": 6,
                "rankingPointsDiff": 7,
                "winsEasy": 1,
                "winsSuperiority": 2,
                "rank": 2,
                "rankRobinGroup": 2,
                "fightByOpponent": null,
                "isCompeting": true,
                "hasOpenFight": false,
                "isDisqualified": false,
                "isNotRanked": false,
                "isInjured": false,
                "isForfeit": false,
                "isRobinGroupNotRanked": false,
                "accreditationStatus": 0,
                "id": "1f1194e7-05cc-6072-aeec-c1d98f6c77fe",
                "sportEventWeightCategory": "1f1194e7-09ad-6fec-8c00-c1d98f6c77fe",
                "athleteId": "1f1194e7-05c2-681a-822f-c1d98f6c77fe",
                "weight": null,
                "drawNumber": 0,
                "seedNumber": 3,
                "fighterWeight": null,
                "points": null,
                "fighterStatus": 0,
                "fighterStatusReason": 0,
                "topTechnique": false,
                "rankingException": null
            },
            {
                "sportEventWeightCategoryId": "1f1194e7-09ad-6fec-8c00-c1d98f6c77fe",
                "weightCategoryFullName": "Greco-Roman - Seniors - 82 kg",
                "weightCategoryShortName": "Seniors GR 82",
                "weightCategoryCountFights": 10,
                "hasWeightCategoryBlockchainIds": true,
                "weightCategoryCountReadyFighters": 5,
                "hasFighterStatusWithoutReason": false,
                "countFights": 4,
                "nbChallenges": {
                    "group": 0,
                    "finals": 0
                },
                "personId": "1f110bfe-7908-61de-ae6d-79e22cbbe72c",
                "fullName": "EDCARLOS FERREIRA DO NASCIMENTO",
                "preferedName": "EDCARLOS FERREIRA DO NASCIMENTO",
                "displayName": "EDCARLOS NAS .",
                "givenName": "Edcarlos Ferreira Do",
                "familyName": "NASCIMENTO",
                "personPhoto": "/build/images/placeholder-man.01372165.jpg",
                "athenaPrintId": null,
                "odfCode": null,
                "teamAlternateName": "AL",
                "teamName": "ALAGOAS",
                "teamCountryFlag": "/uploads/custom-logos/4x3/al.png",
                "sportEventTeamId": "1f1194e6-ebdb-66b8-a149-c1d98f6c77fe",
                "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
                "drawRank": 4,
                "robinGroup": {
                    "group": "A",
                    "drawRank": 4,
                    "wins": 2,
                    "classificationPoints": 10,
                    "winEasy": 0,
                    "winSuperiority": 1,
                    "technicalPointsFor": 12,
                    "technicalPointAgainst": 21
                },
                "robinGroupRank": 3,
                "teamRankingPoint": 15,
                "uwwPoint": 0,
                "isFinalistBronze": false,
                "isFinalistGold": false,
                "isFinalist": false,
                "isOlympicQualified": false,
                "knockOutStatus": null,
                "canHaveMoreBeachFights": false,
                "hasLostknockOut": false,
                "completed": 4,
                "wins": 2,
                "losses": 2,
                "technicalPointsFor": 12,
                "technicalPointsAgainst": 21,
                "technicalPointsDiff": -9,
                "rankingPointsFor": 10,
                "rankingPointsAgainst": 8,
                "rankingPointsDiff": 2,
                "winsEasy": 0,
                "winsSuperiority": 1,
                "rank": 3,
                "rankRobinGroup": 3,
                "fightByOpponent": null,
                "isCompeting": true,
                "hasOpenFight": false,
                "isDisqualified": false,
                "isNotRanked": false,
                "isInjured": false,
                "isForfeit": false,
                "isRobinGroupNotRanked": false,
                "accreditationStatus": 0,
                "id": "1f1194e7-06e3-61ea-8f32-c1d98f6c77fe",
                "sportEventWeightCategory": "1f1194e7-09ad-6fec-8c00-c1d98f6c77fe",
                "athleteId": "1f1194e7-06e2-65ba-9f71-c1d98f6c77fe",
                "weight": null,
                "drawNumber": 17,
                "seedNumber": 0,
                "fighterWeight": null,
                "points": null,
                "fighterStatus": 0,
                "fighterStatusReason": 0,
                "topTechnique": false,
                "rankingException": null
            },
            {
                "sportEventWeightCategoryId": "1f1194e7-09ad-6fec-8c00-c1d98f6c77fe",
                "weightCategoryFullName": "Greco-Roman - Seniors - 82 kg",
                "weightCategoryShortName": "Seniors GR 82",
                "weightCategoryCountFights": 10,
                "hasWeightCategoryBlockchainIds": true,
                "weightCategoryCountReadyFighters": 5,
                "hasFighterStatusWithoutReason": false,
                "countFights": 4,
                "nbChallenges": {
                    "group": 0,
                    "finals": 0
                },
                "personId": "1f0fd371-4fbd-6354-8d90-6d70ebfcf000",
                "fullName": "LUCIANO RAIMUNDO FERNANDES",
                "preferedName": "LUCIANO RAIMUNDO FERNANDES",
                "displayName": "LUCIANO RAIM .",
                "givenName": "Luciano Raimundo",
                "familyName": "FERNANDES",
                "personPhoto": "/build/images/placeholder-man.01372165.jpg",
                "athenaPrintId": null,
                "odfCode": null,
                "teamAlternateName": "SP",
                "teamName": "SÃO PAULO",
                "teamCountryFlag": "/uploads/custom-logos/4x3/sp.png",
                "sportEventTeamId": "1f1194e6-e8bb-6ea6-9dc5-c1d98f6c77fe",
                "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
                "drawRank": 5,
                "robinGroup": {
                    "group": "A",
                    "drawRank": 5,
                    "wins": 1,
                    "classificationPoints": 5,
                    "winEasy": 0,
                    "winSuperiority": 0,
                    "technicalPointsFor": 0,
                    "technicalPointAgainst": 25
                },
                "robinGroupRank": 4,
                "teamRankingPoint": 12,
                "uwwPoint": 0,
                "isFinalistBronze": false,
                "isFinalistGold": false,
                "isFinalist": false,
                "isOlympicQualified": false,
                "knockOutStatus": null,
                "canHaveMoreBeachFights": false,
                "hasLostknockOut": false,
                "completed": 4,
                "wins": 1,
                "losses": 3,
                "technicalPointsFor": 0,
                "technicalPointsAgainst": 25,
                "technicalPointsDiff": -25,
                "rankingPointsFor": 5,
                "rankingPointsAgainst": 12,
                "rankingPointsDiff": -7,
                "winsEasy": 0,
                "winsSuperiority": 0,
                "rank": 4,
                "rankRobinGroup": 4,
                "fightByOpponent": null,
                "isCompeting": true,
                "hasOpenFight": false,
                "isDisqualified": false,
                "isNotRanked": false,
                "isInjured": false,
                "isForfeit": false,
                "isRobinGroupNotRanked": false,
                "accreditationStatus": 0,
                "id": "1f1194e7-03ca-64ae-b904-c1d98f6c77fe",
                "sportEventWeightCategory": "1f1194e7-09ad-6fec-8c00-c1d98f6c77fe",
                "athleteId": "1f1194e7-03c9-68a6-b823-c1d98f6c77fe",
                "weight": null,
                "drawNumber": 73,
                "seedNumber": 0,
                "fighterWeight": null,
                "points": null,
                "fighterStatus": 0,
                "fighterStatusReason": 0,
                "topTechnique": false,
                "rankingException": null
            }
        ],
        "countReadyTeams": 5,
        "countReadyFighters": 5,
        "countReadySeededFighters": 3,
        "countSeededFighters": 3,
        "countFighters": 5,
        "countFightersWithoutStatusReason": 1,
        "maxSeeds": 4,
        "isRepechageSet": false,
        "isBeachFinalsSet": false,
        "countTeams": 5,
        "countFights": 10,
        "countFightsLive": 0,
        "victoryTypes": {
            "VE": {
                "identifier": "VE",
                "name": "TEAM VICTORY",
                "winner": 1,
                "loser": 0,
                "criteriaFall": 1,
                "weight": 13
            },
            "VFA": {
                "identifier": "VFA",
                "name": "VICTORY BY FALL",
                "winner": 5,
                "loser": 0,
                "criteriaFall": 1,
                "weight": 1
            },
            "VCA": {
                "identifier": "VCA",
                "name": "VICTORY BY 3 CAUTIONS",
                "description": "Opponent received 3 cautions or made 2 leg fouls during a bout",
                "winner": 5,
                "loser": 0,
                "weight": 3
            },
            "DSQ": {
                "identifier": "DSQ",
                "name": "DISQUALIFICATION",
                "description": "Before or during the bout for unfair behavior",
                "winner": 5,
                "loser": 0,
                "noRank": 1,
                "disqualifying": 1,
                "weight": 9
            },
            "VIN": {
                "identifier": "VIN",
                "name": "VICTORY BY INJURY",
                "description": "If an athlete is injured before or during a bout",
                "winner": 5,
                "loser": 0,
                "weight": 2
            },
            "VFO": {
                "identifier": "VFO",
                "name": "VICTORY BY FORFEIT",
                "description": "If an athlete doesn't show up on the mat",
                "winner": 5,
                "loser": 0,
                "noRank": 1,
                "weight": 8
            },
            "VSU": {
                "identifier": "VSU",
                "name": "VICTORY BY TECHNICAL SUPERIORITY",
                "description": "Without any point scored by the opponent",
                "winner": 4,
                "loser": 0,
                "criteriaSuperiority": 1,
                "superiorityDifference": 8,
                "weight": 4
            },
            "VSU1": {
                "identifier": "VSU1",
                "name": "VICTORY BY TECHNICAL SUPERIORITY",
                "description": "With point(s) scored by the opponent",
                "winner": 4,
                "loser": 1,
                "criteriaSuperiority": 1,
                "superiorityDifference": 8,
                "weight": 5
            },
            "VPO": {
                "identifier": "VPO",
                "name": "VICTORY BY POINTS",
                "description": "Without any point scored by the opponent",
                "winner": 3,
                "loser": 0,
                "weight": 6
            },
            "VPO1": {
                "identifier": "VPO1",
                "name": "VICTORY BY POINTS",
                "description": "With point(s) scored by the opponent",
                "winner": 3,
                "loser": 1,
                "weight": 7
            },
            "2DSQ": {
                "identifier": "2DSQ",
                "name": "DOUBLE DISQUALIFICATION",
                "description": "Both wrestlers disqualified due to infraction",
                "winner": 0,
                "loser": 0,
                "noRank": 1,
                "disqualifying": 1,
                "weight": 10
            },
            "2VFO": {
                "name": "DOUBLE FORFEIT",
                "identifier": "2VFO",
                "winner": 0,
                "loser": 0,
                "weight": 11,
                "noRank": 1,
                "description": "None of wrestlers pass the weight or show up on the mat"
            },
            "2VIN": {
                "name": "DOUBLE INJURY",
                "identifier": "2VIN",
                "winner": 0,
                "loser": 0,
                "weight": 12,
                "description": "Both wrestlers are injured"
            },
            "V0": {
                "name": "FAKE VICTORY",
                "identifier": "V0",
                "winner": 1,
                "loser": 0,
                "weight": 14,
                "description": "Fake victory"
            }
        },
        "perfectNumber": {
            "roundNumber": 2,
            "roundName": "1/2 Final",
            "value": 4
        },
        "isCompleted": true,
        "isStarted": true,
        "isRobin": true,
        "isRobinGrouped": false,
        "id": "1f1194e7-09ad-6fec-8c00-c1d98f6c77fe",
        "name": "82 kg",
        "audience": "seniors",
        "sport": "gr",
        "minWeight": 78,
        "maxWeight": 82,
        "averageDuration": 540,
        "roundsNumber": 2,
        "roundDuration": 180,
        "overtime": 0,
        "color": "#979fb1",
        "tournamentType": "singlebracket",
        "odfCode": null,
        "uwwRanking": false,
        "blockchainIds": {
            "id": [
                {
                    "id": "24598063",
                    "time": "2026-03-06T11:17:23+00:00"
                }
            ],
            "exception": ""
        },
        "sessionStartDay": 1,
        "matAssignment": 2,
        "visible": true,
        "fightersUpdated": "2026-03-06T11:20:10+00:00",
        "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
        "athenaFinalized": false,
        "medalCeremony": true
    }
}
```
### 5.8 `getWeightCategoryRanking(SportEventWeightCategoryId)`

Purpose:

- Retrieve final ranking for a specific weightcategoryid.

Arena endpoint:

- `GET /weight-category/get/{SportEventWeightCategoryId}/ranking`

cURL:

```bash
curl -X GET "http://localhost:8080/api/json/weight-category/get/1f1194e7-09a8-6e20-a850-c1d98f6c77fe/ranking" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

Expected response example (template):

```json
{
    "ranking": {
        "1f1194e7-0773-6254-8506-c1d98f6c77fe": {
            "fighter": {
                "sportEventWeightCategoryId": "1f1194e7-09a8-6e20-a850-c1d98f6c77fe",
                "weightCategoryFullName": "Freestyle - Seniors - 70 kg",
                "weightCategoryShortName": "Seniors FS 70",
                "weightCategoryCountFights": 3,
                "hasWeightCategoryBlockchainIds": true,
                "weightCategoryCountReadyFighters": 3,
                "hasFighterStatusWithoutReason": false,
                "countFights": 2,
                "nbChallenges": {
                    "group": 0,
                    "finals": 0
                },
                "personId": "1f110bfe-79da-651c-b5de-79e22cbbe72c",
                "fullName": "RENIER LINARES GAVILAN",
                "preferedName": "RENIER LINARES GAVILAN",
                "displayName": "RENIER GAVIL .",
                "givenName": "Renier Linares",
                "familyName": "GAVILAN",
                "personPhoto": "/build/images/placeholder-man.01372165.jpg",
                "athenaPrintId": null,
                "odfCode": null,
                "teamAlternateName": "SP",
                "teamName": "SÃO PAULO",
                "teamCountryFlag": "/uploads/custom-logos/4x3/sp.png",
                "sportEventTeamId": "1f1194e6-e8bb-6ea6-9dc5-c1d98f6c77fe",
                "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
                "drawRank": 1,
                "robinGroup": {
                    "group": "A",
                    "drawRank": 1,
                    "wins": 2,
                    "classificationPoints": 9,
                    "winEasy": 1,
                    "winSuperiority": 1,
                    "technicalPointsFor": 14,
                    "technicalPointAgainst": 0
                },
                "robinGroupRank": 1,
                "teamRankingPoint": 25,
                "uwwPoint": 0,
                "isFinalistBronze": false,
                "isFinalistGold": false,
                "isFinalist": false,
                "isOlympicQualified": false,
                "knockOutStatus": null,
                "canHaveMoreBeachFights": false,
                "hasLostknockOut": false,
                "completed": 2,
                "wins": 2,
                "losses": 0,
                "technicalPointsFor": 14,
                "technicalPointsAgainst": 0,
                "technicalPointsDiff": 14,
                "rankingPointsFor": 9,
                "rankingPointsAgainst": 0,
                "rankingPointsDiff": 9,
                "winsEasy": 1,
                "winsSuperiority": 1,
                "rank": 1,
                "rankRobinGroup": 1,
                "fightByOpponent": null,
                "isCompeting": true,
                "hasOpenFight": false,
                "isDisqualified": false,
                "isNotRanked": false,
                "isInjured": false,
                "isForfeit": false,
                "isRobinGroupNotRanked": false,
                "accreditationStatus": 0,
                "id": "1f1194e7-0773-6254-8506-c1d98f6c77fe",
                "sportEventWeightCategory": "1f1194e7-09a8-6e20-a850-c1d98f6c77fe",
                "athleteId": "1f1194e6-fb4e-61ea-86de-c1d98f6c77fe",
                "weight": null,
                "drawNumber": 0,
                "seedNumber": 1,
                "fighterWeight": null,
                "points": null,
                "fighterStatus": 0,
                "fighterStatusReason": 0,
                "topTechnique": false,
                "rankingException": null
            },
            "rank": 1
        },
        "1f1194e7-0700-6f42-bb80-c1d98f6c77fe": {
            "fighter": {
                "sportEventWeightCategoryId": "1f1194e7-09a8-6e20-a850-c1d98f6c77fe",
                "weightCategoryFullName": "Freestyle - Seniors - 70 kg",
                "weightCategoryShortName": "Seniors FS 70",
                "weightCategoryCountFights": 3,
                "hasWeightCategoryBlockchainIds": true,
                "weightCategoryCountReadyFighters": 3,
                "hasFighterStatusWithoutReason": false,
                "countFights": 2,
                "nbChallenges": {
                    "group": 0,
                    "finals": 0
                },
                "personId": "1f0fd390-2463-6ca2-b221-d55c759b0267",
                "fullName": "CAIO CUZZUOL DANTAS",
                "preferedName": "CAIO CUZZUOL DANTAS",
                "displayName": "CAIO CUZZUOL .",
                "givenName": "Caio Cuzzuol",
                "familyName": "DANTAS",
                "personPhoto": "/build/images/placeholder-man.01372165.jpg",
                "athenaPrintId": null,
                "odfCode": null,
                "teamAlternateName": "ES",
                "teamName": "ESPÍRITO SANTO",
                "teamCountryFlag": "/uploads/custom-logos/4x3/es.png",
                "sportEventTeamId": "1f1194e6-e8fe-622e-ad01-c1d98f6c77fe",
                "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
                "drawRank": 2,
                "robinGroup": {
                    "group": "A",
                    "drawRank": 2,
                    "wins": 1,
                    "classificationPoints": 4,
                    "winEasy": 0,
                    "winSuperiority": 1,
                    "technicalPointsFor": 15,
                    "technicalPointAgainst": 15
                },
                "robinGroupRank": 2,
                "teamRankingPoint": 20,
                "uwwPoint": 0,
                "isFinalistBronze": false,
                "isFinalistGold": false,
                "isFinalist": false,
                "isOlympicQualified": false,
                "knockOutStatus": null,
                "canHaveMoreBeachFights": false,
                "hasLostknockOut": false,
                "completed": 2,
                "wins": 1,
                "losses": 1,
                "technicalPointsFor": 15,
                "technicalPointsAgainst": 15,
                "technicalPointsDiff": 0,
                "rankingPointsFor": 4,
                "rankingPointsAgainst": 5,
                "rankingPointsDiff": -1,
                "winsEasy": 0,
                "winsSuperiority": 1,
                "rank": 2,
                "rankRobinGroup": 2,
                "fightByOpponent": null,
                "isCompeting": true,
                "hasOpenFight": false,
                "isDisqualified": false,
                "isNotRanked": false,
                "isInjured": false,
                "isForfeit": false,
                "isRobinGroupNotRanked": false,
                "accreditationStatus": 0,
                "id": "1f1194e7-0700-6f42-bb80-c1d98f6c77fe",
                "sportEventWeightCategory": "1f1194e7-09a8-6e20-a850-c1d98f6c77fe",
                "athleteId": "1f1194e6-fa00-6752-b85c-c1d98f6c77fe",
                "weight": null,
                "drawNumber": 0,
                "seedNumber": 2,
                "fighterWeight": null,
                "points": null,
                "fighterStatus": 0,
                "fighterStatusReason": 0,
                "topTechnique": false,
                "rankingException": null
            },
            "rank": 2
        },
        "1f1194e6-fea0-6afa-b716-c1d98f6c77fe": {
            "fighter": {
                "sportEventWeightCategoryId": "1f1194e7-09a8-6e20-a850-c1d98f6c77fe",
                "weightCategoryFullName": "Freestyle - Seniors - 70 kg",
                "weightCategoryShortName": "Seniors FS 70",
                "weightCategoryCountFights": 3,
                "hasWeightCategoryBlockchainIds": true,
                "weightCategoryCountReadyFighters": 3,
                "hasFighterStatusWithoutReason": false,
                "countFights": 2,
                "nbChallenges": {
                    "group": 0,
                    "finals": 0
                },
                "personId": "1f110bfe-6c67-6cae-8dad-79e22cbbe72c",
                "fullName": "MARCILIO BENJAMIN ESPINDOLA DA SILVA",
                "preferedName": "MARCILIO BENJAMIN ESPINDOLA DA SILVA",
                "displayName": "MARCILIO ESP .",
                "givenName": "Marcilio Benjamin Espindola Da",
                "familyName": "SILVA",
                "personPhoto": "/build/images/placeholder-man.01372165.jpg",
                "athenaPrintId": null,
                "odfCode": null,
                "teamAlternateName": "PE",
                "teamName": "PERNAMBUCO",
                "teamCountryFlag": "/uploads/custom-logos/4x3/pe.png",
                "sportEventTeamId": "1f1194e6-ebd1-66fe-bf00-c1d98f6c77fe",
                "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
                "drawRank": 3,
                "robinGroup": {
                    "group": "A",
                    "drawRank": 3,
                    "wins": 0,
                    "classificationPoints": 1,
                    "winEasy": 0,
                    "winSuperiority": 0,
                    "technicalPointsFor": 5,
                    "technicalPointAgainst": 19
                },
                "robinGroupRank": 3,
                "teamRankingPoint": 15,
                "uwwPoint": 0,
                "isFinalistBronze": false,
                "isFinalistGold": false,
                "isFinalist": false,
                "isOlympicQualified": false,
                "knockOutStatus": null,
                "canHaveMoreBeachFights": false,
                "hasLostknockOut": false,
                "completed": 2,
                "wins": 0,
                "losses": 2,
                "technicalPointsFor": 5,
                "technicalPointsAgainst": 19,
                "technicalPointsDiff": -14,
                "rankingPointsFor": 1,
                "rankingPointsAgainst": 9,
                "rankingPointsDiff": -8,
                "winsEasy": 0,
                "winsSuperiority": 0,
                "rank": 3,
                "rankRobinGroup": 3,
                "fightByOpponent": null,
                "isCompeting": true,
                "hasOpenFight": false,
                "isDisqualified": false,
                "isNotRanked": false,
                "isInjured": false,
                "isForfeit": false,
                "isRobinGroupNotRanked": false,
                "accreditationStatus": 0,
                "id": "1f1194e6-fea0-6afa-b716-c1d98f6c77fe",
                "sportEventWeightCategory": "1f1194e7-09a8-6e20-a850-c1d98f6c77fe",
                "athleteId": "1f1194e6-fe96-619a-9913-c1d98f6c77fe",
                "weight": null,
                "drawNumber": 248,
                "seedNumber": 0,
                "fighterWeight": null,
                "points": null,
                "fighterStatus": 0,
                "fighterStatusReason": 0,
                "topTechnique": false,
                "rankingException": null
            },
            "rank": 3
        }
    },
    "sportEventId": "1f1194e3-8d4f-68f4-8284-01e99ca4c679",
    "sportEventWeightCategoryId": "1f1194e7-09a8-6e20-a850-c1d98f6c77fe",
    "isCompleted": true,
    "isUwwRankingEnabled": false
}
```

---

## 7) Endpoint Behavior (Pseudo Logic)

```text
receiveWebhook(payload):
  validate request authenticity
  entity = payload.entity
  action = payload.action
  entityId = payload.id

  switch entity:
    Person -> getCustomId(entityId)
    Fighter -> getFighterCustomId(entityId)
    Fight -> getFight(entityId)
    SportEvent -> getAllFightsByEventId(entityId)
    WeightCategory -> getWeightCategoryInfoById(entityId)
    CategoryBracket -> getBracketByCategoryId(<eventId>, <sportEventWeightCategoryId>)
    default -> return 400 unknown entity

  return 200 with normalized data
```

Note for bracket workflows:

- Some webhook variants may not include all ids required for bracket calls.
- If your payload does not include both ids, leave the mapping blank and complete based on your Arena payload.

---

## 8) Error Handling and Operational Recommendations

- Set timeout on every outbound request
- Fail fast on non-2xx responses
- Log: `action`, `entity`, `id`, correlation/request ID
- Retry only transient failures (network, timeout, 5xx)
- Keep idempotency for repeated webhook deliveries
- Return clear status codes:
  - `200` success
  - `400` invalid payload / unsupported entity
  - `401` or `403` auth failure
  - `502` or `500` Arena upstream failure

---

## 9) cURL Troubleshooting Options

Useful cURL flags while integrating:

- `-i` include response headers
- `-sS` silent with visible errors
- `--connect-timeout 5` connection timeout in seconds
- `--max-time 20` total timeout in seconds
- `--retry 3 --retry-delay 1` transient retry

Example:

```bash
curl -i -sS --connect-timeout 5 --max-time 20 \
  -X GET "http://localhost:8080/api/json/fight/get/12345" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

---

## 10) Notes From Public Discussion

- Arena sends minimal webhook payloads; consumers should call Arena API to retrieve full details.
- Built-in master-slave sync is not based on webhooks.
- Webhooks are intended for custom integrations and flexible workflows, such as:
  - Third-party app synchronization
  - Cache invalidation (for example, CDN cache invalidation)

For local development connectivity:

- External systems cannot access your machine's `localhost` directly.
- Expose Arena API with a reachable address (LAN IP, DNS, or tunnel such as ngrok).

---

## 11) Final Notes

- This guide is technology-neutral and can be implemented in any language/framework.
- If your Arena environment returns a different JSON schema, keep function contracts and update the response templates.
