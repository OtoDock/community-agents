# The Home app (OtoDock 1.7 and later)

Every user of this agent has their own **Home** app, pinned when they joined:
one page with the weather for their city on top and their to-do list below.
It welcomes them on their first visit — greeting them with your display name
and showing one card per capability, greyed with the platform's reason where
the tool behind it is missing or not connected (a "Set up" button completes
their personal setup, the same way your `complete_setup` tool does) — and
shows the dashboard afterwards. On a platform before 1.7 there is no Home app: then
`list_apps` shows none and the personal-dashboard offer in your setup guide
is what you do instead.

The app keeps its data in its own database: the city with its coordinates
and time zone, the units, and the to-dos. **Never keep a second copy of any
of that in memory** — read the app when you need it, write the app when the
user asks for a change. "Change my city to Lisbon", "add milk to my list",
"tick off the dentist" are all changes to the app, made through its API
with the session token you already hold:

1. `list_apps` → the per-user app with the slug `home` → its id (`<id>`
   below).
2. Look a city up: `GET $PROXY_URL/v1/apps/<id>/api/geocode?q=Lisbon` →
   `{results: [{name, admin1, country, lat, lon, tz}]}`; pick the one the
   user means (ask when two match).
3. Set it: `PUT $PROXY_URL/v1/apps/<id>/api/settings` with
   `{"city": "Lisbon, Portugal", "lat": 38.72, "lon": -9.14, "tz": "Europe/Lisbon"}`
   (`units` takes `celsius` or `fahrenheit`). The page updates by itself.
4. To-dos: `GET …/api/todos`; `POST …/api/todos` with `{"text": "…"}`;
   `PATCH …/api/todos/<todo id>` with `{"done": true}`, `{"text": "…"}` or
   `{"position": 0}`; `DELETE …/api/todos/<todo id>`.

Every call: `-H "Authorization: Bearer $PROXY_API_KEY" -H 'content-type:
application/json'`. The app answers the current user's copy only; you cannot
reach another user's Home app. The user can also ask you to change the page
itself (its footer says so): that is a normal app change — the folder is the
user's `workspace/apps/home/`, deploy it with `deploy_app` and tell them the
new release waits for their approval on the app's card.
