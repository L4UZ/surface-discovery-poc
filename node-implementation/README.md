# Surface Discovery - Node.js/TypeScript Implementation

In-depth web attack surface discovery service migrated from Python to Node.js with TypeScript, pnpm, and Zod.

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- pnpm (`npm install -g pnpm`)
- External tools: subfinder, httpx, naabu, katana, dnsx

### Installation
```bash
pnpm install
```

### Development
```bash
# Run in development mode
pnpm dev <target-domain>

# Build TypeScript
pnpm build

# Run production build
pnpm start <target-domain>
```

### Code Quality
```bash
# Linting
pnpm lint
pnpm lint:fix

# Formatting
pnpm format
pnpm format:check

# Type checking
pnpm typecheck
```

## 📋 Migration Status

**Current Progress**: ~15% Complete

See [MIGRATION_STATUS.md](./MIGRATION_STATUS.md) for detailed status and implementation guides.

### ✅ Completed (Phase 1)
- Project setup and configuration
- TypeScript strict mode configuration
- ESLint + Prettier setup
- All Zod data models (domain, service, url, auth, discovery)
- Configuration system with depth presets

### 🔄 In Progress (Phase 2+)
- Core infrastructure (utils, tools)
- Discovery pipeline stages
- Playwright crawler
- Orchestration engine
- CLI interface
- Docker configuration

## 🏗️ Project Structure

```
node-implementation/
├── src/
│   ├── models/          # ✅ Zod schemas (COMPLETE)
│   │   ├── domain.ts
│   │   ├── service.ts
│   │   ├── url.ts
│   │   ├── auth.ts
│   │   ├── discovery.ts
│   │   └── index.ts
│   ├── config.ts        # ✅ Configuration (COMPLETE)
│   ├── stages/          # ⏳ TODO - Discovery pipeline stages
│   ├── tools/           # ⏳ TODO - Subprocess wrappers & parsers
│   ├── crawler/         # ⏳ TODO - Playwright deep crawler
│   ├── utils/           # ⏳ TODO - Logger & helpers
│   ├── core.ts          # ⏳ TODO - Main orchestration engine
│   └── cli.ts           # ⏳ TODO - Commander.js CLI
├── package.json
├── tsconfig.json
├── .eslintrc.json
├── .prettierrc
├── MIGRATION_STATUS.md  # 📖 Detailed migration guide
└── README.md            # 📖 This file
```

## 📦 Dependencies

### Production
- **zod** - Runtime validation and TypeScript types
- **commander** - CLI framework
- **chalk** - Terminal colors
- **cli-table3** - Terminal tables
- **ora** - Terminal spinners
- **boxen** - Terminal boxes
- **playwright** - Browser automation
- **winston** - Logging
- **axios** - HTTP client
- **tldts** - Domain parsing
- **date-fns** - Date utilities
- **p-limit** - Concurrency control

### Development
- **typescript** - TypeScript compiler
- **tsx** - TypeScript execution
- **eslint** + **@typescript-eslint** - Linting
- **prettier** - Code formatting
- **typedoc** - API documentation

## 🔧 Key Changes from Python

| Feature | Python | Node.js/TypeScript |
|---------|--------|-------------------|
| Validation | Pydantic | Zod |
| Package Manager | uv | pnpm |
| CLI Framework | Click | Commander.js |
| Terminal Output | Rich | Chalk + cli-table3 + ora |
| Logging | logging module | Winston |
| Async | asyncio | native async/await |
| Subprocess | asyncio subprocess | child_process.spawn() |
| Auth Config | YAML + env vars | JSON only |
| Vulnerability Scan | Nuclei | REMOVED |

## 🐳 Docker Usage (TODO)

```bash
# Build image
docker build -t surface-discovery .

# Run discovery
docker run --rm \
  --cap-add=NET_RAW \
  --cap-add=NET_ADMIN \
  -v $(pwd)/output:/output \
  surface-discovery example.com
```

## 📚 Documentation

- **Migration Guide**: [MIGRATION_STATUS.md](./MIGRATION_STATUS.md)
- **Python Source**: `/Users/lauz/repos/surface-discovery/discovery/`
- **API Docs**: Generate with `npx typedoc --out docs/api src`

## 🛣️ Roadmap

### Phase 2: Core Infrastructure
- [ ] Winston logger
- [ ] Domain/URL helpers
- [ ] Subprocess wrapper
- [ ] Output parsers

### Phase 3: Discovery Stages
- [ ] Passive Discovery (subfinder)
- [ ] Port Discovery (naabu)
- [ ] Active Discovery (httpx)
- [ ] Deep Discovery (katana + playwright)
- [ ] Enrichment (dnsx + whois)
- [ ] Authenticated Discovery

### Phase 4: Integration
- [ ] Playwright crawler
- [ ] URL extractor
- [ ] Discovery engine orchestration
- [ ] CLI interface

### Phase 5: Deployment
- [ ] Docker configuration
- [ ] Documentation
- [ ] Testing (separate phase)

## 📝 Development Notes

### Code Style
- Use strict TypeScript mode
- Prefer functional programming patterns
- Immutable data structures (Object.freeze, readonly)
- Comprehensive error handling (try/catch)

### Testing Strategy
Testing will be implemented in a separate phase after core functionality is complete.

### External Tools
The following Go-based tools must be installed:
- subfinder - Subdomain enumeration
- httpx - HTTP probing
- naabu - Port scanning
- katana - Web crawling
- dnsx - DNS resolution

**Note**: Nuclei has been REMOVED from the migration.

## 🤝 Contributing

This is a migration-in-progress. See MIGRATION_STATUS.md for:
- What's completed
- What needs to be done
- Implementation templates
- Priority order

## 📄 License

MIT

---

For detailed implementation guides and progress tracking, see [MIGRATION_STATUS.md](./MIGRATION_STATUS.md).
