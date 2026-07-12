```bash
nvm use 24
node --version # should show v24.x
pnpm install
pnpm dev
```

## Supabase (cross-platform)

CLI is a **devDependency** (`supabase`) so Mac / Windows / Linux all use the same install path via pnpm — no Homebrew required. Local stack needs [Docker Desktop](https://docs.docker.com/get-docker/) running.

### One-time setup

```bash
nvm use 24
pnpm install

# one-time: create supabase/ at repo root
pnpm supabase init

# one-time: auth + link remote project
pnpm supabase login
pnpm supabase link --project-ref ihwgjwjlugadehhcbehk
```

### Day-to-day

| Command                             | Purpose                                                 |
| ----------------------------------- | ------------------------------------------------------- |
| `pnpm db:migration:new <name>`      | Create a new migration SQL file                         |
| `pnpm db:start`                     | Start local Docker stack                                |
| `pnpm db:stop`                      | Stop local Docker stack                                 |
| `pnpm db:reset`                     | Wipe local DB, replay all migrations + seed             |
| `pnpm db:push`                      | Apply pending migrations to remote                      |
| `pnpm exec supabase migration up`   | Apply pending migrations locally (no wipe)              |
| `pnpm exec supabase migration list` | Compare local vs remote migration status                |
| `pnpm exec supabase db pull`        | Pull remote schema into a migration (avoid if possible) |

Notes:

```bash
export SUPABASE_DB_PASSWORD='your-new-or-existing-db-password'
pnpm db:push # this comment blocked by NUS WiFi
# or

pnpm exec supabase db push --password 'your-db-password'


# load password from backend/.env without putting it on the command line
set -a && source backend/.env && set +a

pnpm exec supabase db push --db-url \
  "postgresql://postgres.ihwgjwjlugadehhcbehk:${SUPABASE_DB_PASSWORD}@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres"
```

Command When

```bash
supabase migration new <name> # Every schema/data change
supabase db reset # Local: wipe + replay all migrations + seed
supabase migration up # Local: apply pending only
supabase db push # Remote: apply pending to linked project
supabase db pull # Capture remote schema into a migration (if you changed UI first — avoid when possible)
supabase migration list # See local vs remote status
```

You can also run any CLI command with `pnpm exec supabase <command>`.
