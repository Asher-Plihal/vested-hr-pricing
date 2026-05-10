# Working Notes

Context and decisions that don't belong in todo.md or updates.md — things that are true right now but may change with further VHR input.



## Authentication & Multi-User Access

Currently there is no authentication, no users table, and no role-gating. The tool runs as a single shared session — anyone with the URL can see and edit any client.

This needs to be designed carefully before the tool goes to production, because the core workflow involves multiple sales agents each managing their own book of clients. Key decisions that need to be made with VHR before building:

- **Data isolation** — can sales agents see each other's clients, or only their own? Is there a manager/admin role that sees everything?
- **Roles** — the requirements mention at least two distinct roles: sales agents (create and edit quotes) and approvers (Justin: pricing, John: WC, Nate: benefits). Are there others?
- **Login method** — username/password, Google SSO, or something else? VHR may have an existing identity provider.
- **Commission visibility** — consultant commission rates are currently visible to anyone. Should sales agents see their own commission but not others', or is this internal-only data?

Auth is deferred to Phase 3. Do not start until VHR answers the above. The full implementation brief will be written at Phase 3 kickoff.

