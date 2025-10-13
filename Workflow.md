Vinny AI — Backend Overview
----------------------------

This Flask API connects the frontend chat widget to LM Studio.

Flow:
Frontend (React widget)
   ↓
POST /api/query { message, pagePath, pageHTML }
   ↓
Flask searches loca index for related KB articles
   ↓
Flask builds a prompt + sends to LM Studio via /chat
   ↓
LM generates response → returned to frontend along with KB sources link

Key files:

- KB CSV File
- Screening files (FAQ)

To run FE...

1. cd HackathonFE
2. npm i
3. npm run dev
4. go to link, http://localhost:5173/
