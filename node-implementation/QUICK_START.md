# Quick Start Guide - Continue the Migration

This guide will help you continue the Python → Node.js/TypeScript migration from where it was left off.

## 📊 Current Status

**Foundation**: ✅ **100% Complete**
**Overall Progress**: ~15% Complete

The foundation is solid. You can now build the core functionality on top of these completed components:
- Project setup & configuration
- All data models (Zod schemas)
- Configuration system
- Documentation & guides

## 🚀 Quick Setup

```bash
# Navigate to implementation folder
cd node-implementation

# Install dependencies
pnpm install

# Verify setup
pnpm typecheck
pnpm lint
```

## 📝 What to Do Next

Follow this exact order for best results:

### Step 1: Logger (30 minutes)
**File**: `src/utils/logger.ts`

```bash
# Create the file
touch src/utils/logger.ts
```

Copy this implementation:
```typescript
import winston from 'winston';

export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.printf(({ level, message, timestamp, ...meta }) => {
          const metaStr = Object.keys(meta).length ? `\n${JSON.stringify(meta, null, 2)}` : '';
          return `${timestamp} [${level}]: ${message}${metaStr}`;
        })
      ),
    }),
  ],
});
```

**Test it**:
```typescript
// Add to any file temporarily
import { logger } from './utils/logger.js';

logger.info('Hello from logger');
logger.error('Error test');
```

---

### Step 2: Helpers (1 hour)
**File**: `src/utils/helpers.ts`

```bash
touch src/utils/helpers.ts
```

Implement these 3 critical functions (see MIGRATION_STATUS.md for full template):
1. `extractRootDomain(url: string): string`
2. `isValidDomain(domain: string): boolean`
3. `normalizeUrl(url: string): string`

**Reference**: Python source at `discovery/utils/helpers.py`

---

### Step 3: Tool Runner (3-4 hours) ⚠️ MOST CRITICAL
**File**: `src/tools/runner.ts`

```bash
touch src/tools/runner.ts
```

This is the foundation for everything else. Must implement:

1. **Base `run()` method** - Spawn subprocess with timeout
2. **`runWithStdin()` method** - Pass data to tool via stdin
3. **5 tool-specific methods**:
   - `runSubfinder(domain, timeout)` - Subdomain enum
   - `runHTTPX(targets, techDetect, timeout)` - HTTP probing
   - `runNaabu(hosts, ports, rate, timeout)` - Port scanning
   - `runKatana(targets, depth, timeout)` - Web crawling
   - `runDNSX(domains, queryType, timeout)` - DNS queries

**Full template**: See MIGRATION_STATUS.md → Phase 2 → runner.ts

**Critical Points**:
- Use `child_process.spawn()`
- Implement timeout with `setTimeout()`
- Handle large stdout/stderr streams
- Kill process on timeout
- Propagate errors properly

**Test Each Tool**:
```typescript
import { ToolRunner } from './tools/runner.js';

const runner = new ToolRunner();

// Test subfinder
const output = await runner.runSubfinder('example.com', 60000);
console.log('Subdomains found:', output.split('\n').length);
```

---

### Step 4: Parsers (2-3 hours)
**File**: `src/tools/parsers.ts`

```bash
touch src/tools/parsers.ts
```

Implement 4 parsers (see MIGRATION_STATUS.md for full templates):
1. `SubfinderParser.parse()` - Split lines
2. `HTTPXParser.parse()` - Parse JSONL → Service[]
3. `DNSXParser.parse()` - Parse JSONL → Map<string, DNSRecords>
4. `NaabuParser.parse()` - Parse JSONL → PortScanResult[]

**Critical**: Handle JSONL (JSON Lines) format:
```typescript
output.trim().split('\n').map(line => JSON.parse(line))
```

**Test Parsers**:
```typescript
import { HTTPXParser } from './tools/parsers.js';

const jsonl = `{"url":"https://example.com","status_code":200}
{"url":"https://test.com","status_code":404}`;

const services = HTTPXParser.parse(jsonl);
console.log('Parsed services:', services.length);
```

---

### Step 5: Discovery Stages (6-8 hours)

Create each stage file in order:

```bash
touch src/stages/passive.ts
touch src/stages/portDiscovery.ts
touch src/stages/active.ts
touch src/stages/deep.ts
touch src/stages/enrichment.ts
touch src/stages/authenticated.ts
```

Each follows this pattern:
1. Import runner, parser, logger
2. Create class with `execute()` method
3. Call tool → parse output → return results

**Start with passive.ts** (simplest):
```typescript
import { ToolRunner } from '../tools/runner.js';
import { SubfinderParser } from '../tools/parsers.js';
import { DiscoveryConfig } from '../config.js';
import { logger } from '../utils/logger.js';

export class PassiveDiscoveryStage {
  private runner: ToolRunner;
  private config: DiscoveryConfig;

  constructor(config: DiscoveryConfig) {
    this.config = config;
    this.runner = new ToolRunner();
  }

  async execute(target: string): Promise<string[]> {
    logger.info(`Starting passive discovery for ${target}`);

    const output = await this.runner.runSubfinder(
      target,
      this.config.subfinderTimeout * 1000
    );

    const subdomains = SubfinderParser.parse(output);

    // Apply max subdomains limit if configured
    const limited = this.config.maxSubdomains
      ? subdomains.slice(0, this.config.maxSubdomains)
      : subdomains;

    logger.info(`Discovered ${limited.length} subdomains`);
    return limited;
  }
}
```

Repeat this pattern for other stages (see MIGRATION_STATUS.md for details).

---

### Step 6: Playwright Crawler (4-5 hours)

```bash
touch src/crawler/deepCrawler.ts
touch src/crawler/urlExtractor.ts
```

**Reference**:
- Python: `discovery/crawler/deep_crawler.py`
- Python: `discovery/crawler/url_extractor.py`

The Playwright API is nearly identical in Node.js vs Python!

---

### Step 7: Core Engine (3-4 hours)

```bash
touch src/core.ts
```

Orchestrate all stages sequentially:
```typescript
export class DiscoveryEngine {
  async discover(): Promise<DiscoveryResult> {
    await this.runPassiveDiscovery();    // Stage 1
    await this.runPortDiscovery();       // Stage 1.5
    await this.runActiveDiscovery();     // Stage 2
    await this.runDeepDiscovery();       // Stage 3
    await this.runEnrichment();          // Stage 4
    await this.runAuthenticatedDiscovery(); // Stage 5 (if auth config)

    return this.result;
  }
}
```

---

### Step 8: CLI (2-3 hours)

```bash
touch src/cli.ts
```

Add shebang at top:
```typescript
#!/usr/bin/env node
```

Use Commander.js (see template in MIGRATION_STATUS.md).

**Make executable**:
```bash
chmod +x src/cli.ts
```

---

### Step 9: Docker (2-3 hours)

Create/update 3 files:
1. `Dockerfile` - Multi-stage build
2. `docker-compose.yml` - Service config
3. `docker-entrypoint.sh` - Container entrypoint

**Templates**: See MIGRATION_STATUS.md → Phase 7

---

## 🧪 Testing Strategy

Test incrementally as you build:

### Test Each Component
```typescript
// In a test file or temporarily in the component
import { ToolRunner } from './tools/runner.js';

async function test() {
  const runner = new ToolRunner();
  const result = await runner.runSubfinder('example.com', 60000);
  console.log(result);
}

test().catch(console.error);
```

### Test End-to-End
Once CLI is done:
```bash
# Build
pnpm build

# Run
node dist/cli.js example.com --depth shallow --verbose
```

---

## 📚 Key Resources

### Documentation
- **MIGRATION_STATUS.md** - Detailed templates for every file
- **README.md** - Project overview
- **docs/MIGRATION_SUMMARY.md** - What's done, what's left

### Python Reference
- **Location**: `/Users/lauz/repos/surface-discovery/discovery/`
- Study the Python code when implementing each stage

### External Docs
- Zod: https://zod.dev
- Commander.js: https://github.com/tj/commander.js
- Winston: https://github.com/winstonjs/winston
- Playwright: https://playwright.dev

---

## ⚡ Pro Tips

1. **Work Incrementally**: Complete one file, test it, move to next
2. **Reference Python**: Keep Python code open for comparison
3. **Test Early**: Don't wait to test until everything is done
4. **Use TypeScript**: Let the compiler catch errors
5. **Follow Templates**: MIGRATION_STATUS.md has complete examples
6. **Commit Often**: Git commit after each completed component

---

## 🆘 Common Issues

### Issue: Tool not found
```
Error: spawn subfinder ENOENT
```
**Solution**: Install ProjectDiscovery tools:
```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
# etc...
```

### Issue: Timeout not working
**Solution**: Ensure you're using `setTimeout()` correctly:
```typescript
const timer = setTimeout(() => {
  proc.kill();
  reject(new Error('Timeout'));
}, timeout);

// Clear timeout when done
clearTimeout(timer);
```

### Issue: JSONL parsing fails
**Solution**: Filter empty lines before parsing:
```typescript
output.trim().split('\n').filter(line => line.trim()).map(JSON.parse)
```

---

## 🎯 Success Metrics

You'll know you're done when:
- ✅ All tools execute successfully
- ✅ All stages run sequentially
- ✅ CLI displays formatted results
- ✅ Docker image builds and runs
- ✅ Output matches Python version structure

---

## 📞 Need Help?

1. Check **MIGRATION_STATUS.md** for detailed templates
2. Reference Python code in `/Users/lauz/repos/surface-discovery/discovery/`
3. Search for specific implementation details in this document

---

**Start Here**: `src/utils/logger.ts` → Then follow the steps above in order.

Good luck! 🚀
