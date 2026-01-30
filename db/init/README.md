# Database Initialization Scripts

This directory contains database initialization scripts that are automatically executed when Docker containers are first created.

## Directory Structure

```
db/init/
├── postgres/
│   └── 01-init.sql      # PostgreSQL initialization script
└── neo4j/
    └── init.cypher      # Neo4j initialization script
```

## PostgreSQL Initialization

**Location**: `postgres/01-init.sql`

**Execution**: Automatically run by PostgreSQL container on first startup via `/docker-entrypoint-initdb.d/`

**Contents**:
- PostgreSQL extensions (uuid-ossp, pg_trgm, btree_gin, btree_gist, pgcrypto)
- Asset tables (organization, domain, ip, netblock, certificate, service, client_application, credential)
- Auxiliary tables (import_logs, operation_logs, tags, asset_tags)
- Indexes (B-Tree, GIN, GiST, Trigram)
- Default tags (High/Medium/Low Risk, Production/Development/Testing, Cloud/On-Premise)

**Note**: This script only runs once when the PostgreSQL volume is first created. To re-run:
```bash
docker-compose down -v  # Warning: This deletes all data!
docker-compose up -d
```

## Neo4j Initialization

**Location**: `neo4j/init.cypher`

**Execution**: Automatically applied by `scripts/bootstrap.sh` on first run

**Contents**:
- Unique constraints on `external_id` for 7 node types
- 24 property indexes for high-frequency queries
- 4 composite indexes for combined queries

**Automatic execution via bootstrap**:
```bash
./scripts/bootstrap.sh  # Automatically applies Neo4j initialization
```

**Manual execution** (if needed):
```bash
# Option 1: Using cypher-shell
docker exec -i externalhound-neo4j \
  cypher-shell -u neo4j -p externalhound_neo4j_pass \
  < db/init/neo4j/init.cypher

# Option 2: Using Neo4j Browser
# 1. Visit http://localhost:7474
# 2. Login with neo4j / externalhound_neo4j_pass
# 3. Copy and paste the contents of init.cypher
```

**Note**: The bootstrap script checks if Neo4j is already initialized and only applies the script if constraints don't exist.

## Modifying Initialization Scripts

### Adding New Tables/Indexes (PostgreSQL)

1. Edit `db/init/postgres/01-init.sql`
2. Add your SQL statements
3. Recreate the database:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### Adding New Constraints/Indexes (Neo4j)

1. Edit `db/init/neo4j/init.cypher`
2. Re-run the Neo4j initialization:
   ```bash
   docker exec -i externalhound-neo4j \
     cypher-shell -u neo4j -p externalhound_neo4j_pass \
     < db/init/neo4j/init.cypher
   ```

## Production Considerations

- **PostgreSQL**: Use Alembic migrations for schema changes instead of modifying init scripts
- **Neo4j**: Use migration scripts or API calls to manage schema changes
- **Backup**: Always backup data before modifying initialization scripts
- **Testing**: Test initialization scripts in a development environment first

## Related Files

- `docker-compose.yml`: Mounts these scripts into containers
- `scripts/bootstrap.sh`: Automated initialization and verification
- `backend/alembic/`: PostgreSQL schema migrations (for production)

## Troubleshooting

**PostgreSQL initialization failed**:
```bash
# Check logs
docker-compose logs postgres

# Verify script syntax
docker exec -i externalhound-postgres \
  psql -U postgres -d externalhound -f /docker-entrypoint-initdb.d/01-init.sql
```

**Neo4j initialization failed**:
```bash
# Check logs
docker-compose logs neo4j

# Verify Cypher syntax
docker exec -i externalhound-neo4j \
  cypher-shell -u neo4j -p externalhound_neo4j_pass \
  < db/init/neo4j/init.cypher
```
