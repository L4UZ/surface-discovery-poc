# Surface Discovery: Python → Node.js/TypeScript Migration Status

**Migration Start Date**: 2025-11-07
**Target Stack**: Node.js 20+, TypeScript 5.3, pnpm, Zod
**Exclusions**: Nuclei integration, YAML auth parser, test suite (separate phase)

---

## ✅ Phase 1: Foundation (COMPLETED)

### Project Setup
- ✅ Created `node-implementation/` directory structure
- ✅ Initialized pnpm package manager
- ✅ Configured TypeScript with strict mode (tsconfig.json)
- ✅ Setup ESLint + TypeScript ESLint plugin
- ✅ Setup Prettier code formatting
- ✅ Created .gitignore for Node.js projects
- ✅ Created base directory structure:
  ```
  src/
  ├── models/
  ├── stages/
  ├── tools/
  ├── crawler/
  ├── utils/
  └── types/
  ```

### Data Models Migration (100% Complete)
All Pydantic models successfully migrated to Zod schemas with TypeScript type inference:

1. ✅ **domain.ts** - Domain intelligence models
   - `PortScanResult` - Port scan results
   - `DNSRecords` - DNS record types
   - `WHOISData` - WHOIS registration data
   - `Subdomain` - Discovered subdomain information
   - `DomainInfo` - Complete domain intelligence

2. ✅ **service.ts** - Service and technology detection
   - `SecurityHeaders` - HTTP security headers analysis
   - `TLSInfo` - TLS/SSL certificate information
   - `Technology` - Detected frameworks/technologies
   - `Service` - Live web service information

3. ✅ **url.ts** - URL discovery from crawling
   - `DiscoveredURL` - Individual discovered URL
   - `FormData` - Form metadata from crawling
   - `URLDiscoveryResult` - Crawl results with helper methods

4. ✅ **auth.ts** - Authentication configuration (SIMPLIFIED)
   - `BasicAuth` - Basic authentication credentials
   - `AuthConfig` - Per-URL authentication config
   - `AuthenticationConfig` - Complete auth configuration
   - **Note**: JSON-only format, no YAML parsing or env var substitution

5. ✅ **discovery.ts** - Main discovery results
   - `DiscoveryStage` - Pipeline stage enumeration
   - `TimelineEvent` - Discovery timeline events
   - `DiscoveryMetadata` - Scan execution metadata
   - `Endpoint` - Discovered API endpoints
   - `Recommendation` - Pentest focus recommendations
   - `Statistics` - Discovery statistics summary
   - `DiscoveryResult` - Complete discovery output with helper methods
   - **Removed**: Finding and CVE models (no Nuclei integration)

6. ✅ **index.ts** - Barrel export for all models

### Configuration System
- ✅ **config.ts** - Zod-validated configuration with depth presets
  - Depth presets: shallow, normal, deep
  - Immutable configuration with Object.freeze()
  - No `skipVulnScan` option (Nuclei removed)
  - Complete tool timeout configurations

---

## 🔄 Phase 2: Core Infrastructure (IN PROGRESS)

### Utilities (0% Complete)

#### logger.ts (TODO)
**Purpose**: Winston-based structured logging
**Migration from**: `discovery/utils/logger.py`

**Implementation Guide**:
```typescript
import winston from 'winston';

export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      ),
    }),
  ],
});
```

**Key Features**:
- Structured logging with JSON format
- Configurable log levels
- Colored console output
- Error stack traces

---

#### helpers.ts (TODO)
**Purpose**: Domain/URL parsing and validation utilities
**Migration from**: `discovery/utils/helpers.py`

**Key Functions to Implement**:
```typescript
import { parse } from 'tldts';

/**
 * Extract root domain from URL/hostname
 */
export function extractRootDomain(url: string): string {
  const parsed = parse(url);
  return parsed.domain || url;
}

/**
 * Validate if string is a valid domain
 */
export function isValidDomain(domain: string): boolean {
  const parsed = parse(domain);
  return parsed.isValid && parsed.domain !== null;
}

/**
 * Normalize URL (add protocol, remove trailing slash)
 */
export function normalizeUrl(url: string): string {
  if (!url.match(/^https?:\/\//)) {
    url = `https://${url}`;
  }
  return url.replace(/\/+$/, '');
}
```

---

### Tools Integration (0% Complete)

#### runner.ts (TODO - CRITICAL)
**Purpose**: Subprocess execution wrapper for external tools
**Migration from**: `discovery/tools/runner.py`

**Tools to Support** (5 total, NO nuclei):
- subfinder - Subdomain enumeration
- httpx - HTTP probing
- naabu - Port scanning
- katana - Web crawling
- dnsx - DNS resolution

**Implementation Template**:
```typescript
import { spawn } from 'child_process';

export class ToolRunner {
  /**
   * Execute command with timeout and error handling
   */
  async run(
    command: string[],
    timeout: number,
    check: boolean = true
  ): Promise<{ stdout: string; stderr: string; exitCode: number }> {
    return new Promise((resolve, reject) => {
      const proc = spawn(command[0], command.slice(1));
      let stdout = '';
      let stderr = '';

      const timer = setTimeout(() => {
        proc.kill();
        reject(new Error(`Command timed out after ${timeout}ms`));
      }, timeout);

      proc.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      proc.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      proc.on('close', (code) => {
        clearTimeout(timer);
        if (check && code !== 0) {
          reject(new Error(`Command failed with exit code ${code}: ${stderr}`));
        } else {
          resolve({ stdout, stderr, exitCode: code || 0 });
        }
      });

      proc.on('error', (err) => {
        clearTimeout(timer);
        reject(err);
      });
    });
  }

  /**
   * Run subfinder for subdomain enumeration
   */
  async runSubfinder(domain: string, timeout: number): Promise<string> {
    const command = ['subfinder', '-d', domain, '-silent'];
    const { stdout } = await this.run(command, timeout, false);
    return stdout;
  }

  /**
   * Run httpx for HTTP probing
   */
  async runHTTPX(
    targets: string[],
    techDetect: boolean,
    timeout: number
  ): Promise<string> {
    const command = ['httpx', '-silent', '-json'];
    if (techDetect) command.push('-tech-detect');

    return this.runWithStdin(command, targets.join('\n'), timeout);
  }

  /**
   * Run naabu for port scanning
   */
  async runNaabu(
    hosts: string[],
    ports: string,
    rate: number,
    timeout: number
  ): Promise<string> {
    const command = [
      'naabu',
      '-silent',
      '-json',
      '-p', ports,
      '-rate', rate.toString(),
    ];

    return this.runWithStdin(command, hosts.join('\n'), timeout);
  }

  /**
   * Run katana for web crawling
   */
  async runKatana(
    targets: string[],
    depth: number,
    timeout: number
  ): Promise<string> {
    const command = [
      'katana',
      '-silent',
      '-json',
      '-d', depth.toString(),
    ];

    return this.runWithStdin(command, targets.join('\n'), timeout);
  }

  /**
   * Run dnsx for DNS resolution
   */
  async runDNSX(
    domains: string[],
    queryType: string,
    timeout: number
  ): Promise<string> {
    const command = [
      'dnsx',
      '-silent',
      '-json',
      '-' + queryType,
    ];

    return this.runWithStdin(command, domains.join('\n'), timeout);
  }

  /**
   * Run command with stdin input
   */
  private async runWithStdin(
    command: string[],
    stdin: string,
    timeout: number
  ): Promise<string> {
    return new Promise((resolve, reject) => {
      const proc = spawn(command[0], command.slice(1));
      let stdout = '';
      let stderr = '';

      const timer = setTimeout(() => {
        proc.kill();
        reject(new Error(`Command timed out after ${timeout}ms`));
      }, timeout);

      proc.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      proc.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      proc.on('close', (code) => {
        clearTimeout(timer);
        if (code !== 0) {
          reject(new Error(`Command failed: ${stderr}`));
        } else {
          resolve(stdout);
        }
      });

      proc.on('error', (err) => {
        clearTimeout(timer);
        reject(err);
      });

      // Write stdin and close
      proc.stdin.write(stdin);
      proc.stdin.end();
    });
  }
}
```

**Critical Notes**:
- MUST handle JSONL (JSON Lines) output format
- MUST implement timeout with AbortController or setTimeout
- MUST handle tool not found errors gracefully
- MUST parse output line-by-line for large datasets

---

#### parsers.ts (TODO - CRITICAL)
**Purpose**: Parse tool output into Zod-validated models
**Migration from**: `discovery/tools/parsers.py`

**Parsers to Implement** (4 total, NO NucleiParser):

```typescript
import { z } from 'zod';
import { serviceSchema } from '../models/service.js';
import { dnsRecordsSchema } from '../models/domain.js';
import { portScanResultSchema } from '../models/domain.js';

export class SubfinderParser {
  /**
   * Parse subfinder line-separated output
   */
  static parse(output: string): string[] {
    return output
      .trim()
      .split('\n')
      .filter((line) => line.trim().length > 0);
  }
}

export class HTTPXParser {
  /**
   * Parse httpx JSON lines output
   */
  static parse(output: string): Service[] {
    return output
      .trim()
      .split('\n')
      .filter((line) => line.trim())
      .map((line) => {
        const data = JSON.parse(line);
        return this.parseService(data);
      });
  }

  private static parseService(data: any): Service {
    return serviceSchema.parse({
      url: data.url,
      statusCode: data.status_code || data['status-code'],
      contentLength: data.content_length || data['content-length'],
      title: data.title,
      server: data.server,
      technologies: this.parseTechnologies(data.tech || data.technologies || []),
      securityHeaders: this.parseSecurityHeaders(data),
      tlsInfo: this.parseTLSInfo(data.tls),
      responseTime: data.response_time || data.time,
      redirectsTo: data.final_url || data.chain?.[data.chain.length - 1],
      discoveredAt: new Date(),
    });
  }

  // Implement parseTechnologies, parseSecurityHeaders, parseTLSInfo...
}

export class DNSXParser {
  /**
   * Parse dnsx JSON lines output
   */
  static parse(output: string): Map<string, DNSRecords> {
    const records = new Map<string, DNSRecords>();

    output
      .trim()
      .split('\n')
      .filter((line) => line.trim())
      .forEach((line) => {
        const data = JSON.parse(line);
        const hostname = data.host;

        if (!records.has(hostname)) {
          records.set(hostname, {
            a: [],
            aaaa: [],
            mx: [],
            txt: [],
            ns: [],
            cname: undefined,
          });
        }

        const record = records.get(hostname)!;

        if (data.a) record.a.push(...data.a);
        if (data.aaaa) record.aaaa.push(...data.aaaa);
        if (data.mx) record.mx.push(...data.mx);
        if (data.txt) record.txt.push(...data.txt);
        if (data.ns) record.ns.push(...data.ns);
        if (data.cname) record.cname = data.cname[0];
      });

    return records;
  }
}

export class NaabuParser {
  /**
   * Parse naabu JSON lines output
   */
  static parse(output: string): PortScanResult[] {
    return output
      .trim()
      .split('\n')
      .filter((line) => line.trim())
      .map((line) => {
        const data = JSON.parse(line);
        return portScanResultSchema.parse({
          port: data.port,
          protocol: data.protocol || 'tcp',
          state: 'open',
          service: data.service,
          version: data.version,
          discoveredAt: new Date(),
        });
      });
  }
}
```

---

## 📝 Phase 3: Discovery Stages (0% Complete)

All stages need to be created from scratch. Each stage follows a similar pattern:

### Stage Template Pattern
```typescript
import { DiscoveryConfig } from '../config.js';
import { ToolRunner } from '../tools/runner.js';
import { SubfinderParser } from '../tools/parsers.js';
import { logger } from '../utils/logger.js';

export class PassiveDiscoveryStage {
  private runner: ToolRunner;
  private config: DiscoveryConfig;

  constructor(config: DiscoveryConfig) {
    this.config = config;
    this.runner = new ToolRunner();
  }

  async execute(target: string): Promise<SomeResult> {
    logger.info(`Starting passive discovery for ${target}`);

    try {
      // 1. Run tool
      const output = await this.runner.runSubfinder(
        target,
        this.config.subfinderTimeout * 1000
      );

      // 2. Parse output
      const subdomains = SubfinderParser.parse(output);

      // 3. Apply limits if configured
      const limited = this.config.maxSubdomains
        ? subdomains.slice(0, this.config.maxSubdomains)
        : subdomains;

      logger.info(`Discovered ${limited.length} subdomains`);
      return { subdomains: limited };
    } catch (error) {
      logger.error(`Passive discovery failed: ${error}`);
      throw error;
    }
  }
}
```

### Stages to Implement

1. **stages/passive.ts** - Subfinder subdomain enumeration
2. **stages/portDiscovery.ts** - Naabu port scanning
3. **stages/active.ts** - HTTPx HTTP probing + tech detection
4. **stages/deep.ts** - Katana + Playwright deep crawling
5. **stages/enrichment.ts** - DNSx + WHOIS (NO nuclei)
6. **stages/authenticated.ts** - Authenticated discovery with JSON auth config

---

## 🕷️ Phase 4: Playwright Crawler (0% Complete)

### crawler/deepCrawler.ts (TODO)
**Migration from**: `discovery/crawler/deep_crawler.py`

**Key Features**:
- Recursive depth-limited crawling
- Same-domain filtering
- Authentication context support (cookies, headers)
- JavaScript execution
- Form discovery

### crawler/urlExtractor.ts (TODO)
**Migration from**: `discovery/crawler/url_extractor.py`

**Key Features**:
- Extract URLs from: links, forms, onclick handlers, iframes, meta refresh
- URL deduplication
- Parameter extraction

---

## ⚙️ Phase 5: Core Orchestration (0% Complete)

### core.ts - DiscoveryEngine (TODO - CRITICAL)
**Migration from**: `discovery/core.py`

**Architecture**: Sequential 5-stage pipeline orchestration

**Stages**:
1. Passive Discovery (Subfinder)
2. Port Discovery (Naabu)
3. Active Discovery (HTTPx)
4. Deep Discovery (Katana + Playwright)
5. Enrichment (DNSx + WHOIS)

**Implementation Pattern**:
```typescript
export class DiscoveryEngine {
  private config: DiscoveryConfig;
  private result: DiscoveryResult;

  constructor(target: string, config: DiscoveryConfig) {
    this.config = config;
    this.result = this.initializeResult(target);
  }

  async discover(): Promise<DiscoveryResult> {
    try {
      await this.runPassiveDiscovery();
      await this.runPortDiscovery();
      await this.runActiveDiscovery();
      await this.runDeepDiscovery();
      await this.runEnrichment();
      await this.finalize();

      return this.result;
    } catch (error) {
      this.result.metadata.status = DiscoveryStage.FAILED;
      this.result.metadata.error = String(error);
      throw error;
    }
  }

  private async runPassiveDiscovery(): Promise<void> {
    // Implementation
  }

  // ... other stages
}
```

---

## 🖥️ Phase 6: CLI Interface (0% Complete)

### cli.ts (TODO)
**Migration from**: `discovery/cli.py`

**Framework**: Commander.js (replaces Click)
**Output**: Chalk + cli-table3 + ora (replaces Rich)

**Implementation Template**:
```typescript
#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import Table from 'cli-table3';
import { DiscoveryEngine } from './core.js';
import { getConfig } from './config.js';

const program = new Command();

program
  .name('surface-discovery')
  .description('In-depth web attack surface discovery service')
  .version('0.1.0')
  .argument('<target>', 'Target domain to scan')
  .option('-d, --depth <level>', 'Discovery depth (shallow|normal|deep)', 'normal')
  .option('-t, --timeout <seconds>', 'Max execution time', '600')
  .option('-p, --parallel <count>', 'Max parallel tasks', '10')
  .option('-o, --output <file>', 'Output JSON file')
  .option('-v, --verbose', 'Verbose logging')
  .action(async (target, options) => {
    const spinner = ora('Initializing discovery...').start();

    try {
      const config = getConfig(options.depth as any, {
        timeout: parseInt(options.timeout),
        parallel: parseInt(options.parallel),
        verbose: options.verbose,
      });

      const engine = new DiscoveryEngine(target, config);
      const result = await engine.discover();

      spinner.succeed('Discovery completed!');

      // Display results with chalk + cli-table3
      const table = new Table({
        head: ['Metric', 'Value'],
        style: { head: ['cyan'] },
      });

      table.push(
        ['Subdomains', result.statistics.totalSubdomains],
        ['Live Services', result.statistics.liveServices],
        ['Technologies', result.statistics.technologiesDetected],
        ['Endpoints', result.statistics.endpointsDiscovered]
      );

      console.log(table.toString());

      if (options.output) {
        await fs.promises.writeFile(
          options.output,
          JSON.stringify(result, null, 2)
        );
        console.log(chalk.green(`✓ Results saved to ${options.output}`));
      }
    } catch (error) {
      spinner.fail('Discovery failed');
      console.error(chalk.red(error));
      process.exit(1);
    }
  });

program.parse();
```

---

## 🐳 Phase 7: Docker Configuration (0% Complete)

### Dockerfile (TODO)
**Migration from**: `Dockerfile`

**Key Changes**:
- Base image: `FROM node:20-slim` (instead of Python)
- Go tools stage: UNCHANGED (subfinder, httpx, naabu, katana, dnsx)
- NO nuclei installation
- Playwright: `npx playwright install chromium --with-deps`
- Entrypoint: `node dist/cli.js`

**Template**:
```dockerfile
# Stage 1: Go tools builder (NO CHANGES except remove nuclei)
FROM golang:1.24-bookworm AS go-builder

RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest && \
    go install -v github.com/projectdiscovery/katana/cmd/katana@latest && \
    go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest

# Stage 2: Node.js runtime
FROM node:20-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy Go tools
COPY --from=go-builder /go/bin/* /usr/local/bin/

# Create non-root user
RUN useradd -m -u 1000 discovery

WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install pnpm and dependencies
RUN npm install -g pnpm && \
    pnpm install --frozen-lockfile --prod

# Install Playwright Chromium
RUN npx playwright install chromium --with-deps

# Copy application
COPY dist/ ./dist/

# Set ownership
RUN chown -R discovery:discovery /app

USER discovery

# Grant network capabilities for naabu (requires --cap-add at runtime)
# docker run --cap-add=NET_RAW --cap-add=NET_ADMIN ...

VOLUME ["/output"]

ENTRYPOINT ["node", "dist/cli.js"]
```

### docker-compose.yml (TODO)
Update service configuration for Node.js runtime

### docker-entrypoint.sh (TODO)
Update shebang and Node.js invocation

---

## 📚 Phase 8: Documentation (0% Complete)

### README.md (TODO)
Update with:
- Node.js/pnpm installation instructions
- Build process: `pnpm install && pnpm build`
- Run commands: `pnpm start -- <target>`
- Docker usage (updated)
- Removed features: Nuclei integration, YAML auth parsing

### API Documentation (TODO)
Generate with TypeDoc:
```bash
pnpm add -D typedoc
npx typedoc --out docs/api src
```

---

## 📊 Overall Progress

| Phase | Status | Files | Progress |
|-------|--------|-------|----------|
| 1. Foundation | ✅ COMPLETE | 10/10 | 100% |
| 2. Core Infrastructure | 🔄 IN PROGRESS | 1/4 | 25% |
| 3. Discovery Stages | ⏳ TODO | 0/6 | 0% |
| 4. Playwright Crawler | ⏳ TODO | 0/2 | 0% |
| 5. Core Orchestration | ⏳ TODO | 0/1 | 0% |
| 6. CLI Interface | ⏳ TODO | 0/1 | 0% |
| 7. Docker Configuration | ⏳ TODO | 0/3 | 0% |
| 8. Documentation | ⏳ TODO | 0/2 | 0% |

**Total Progress**: ~15% complete

---

## 🚀 Next Steps (Priority Order)

1. **CRITICAL**: Implement `tools/runner.ts` (subprocess wrapper)
2. **CRITICAL**: Implement `tools/parsers.ts` (output parsing)
3. **CRITICAL**: Implement `utils/logger.ts` (logging system)
4. **HIGH**: Implement `utils/helpers.ts` (domain/URL utilities)
5. **HIGH**: Implement all 6 discovery stages
6. **HIGH**: Implement Playwright crawler + URL extractor
7. **MEDIUM**: Implement `core.ts` orchestration engine
8. **MEDIUM**: Implement `cli.ts` Commander.js interface
9. **MEDIUM**: Update Docker configuration
10. **LOW**: Update documentation

---

## 🛠️ Development Workflow

### Setup
```bash
cd node-implementation
pnpm install
```

### Development
```bash
# Run in dev mode with tsx
pnpm dev <target>

# Build TypeScript
pnpm build

# Run production build
pnpm start <target>
```

### Linting & Formatting
```bash
# Lint
pnpm lint
pnpm lint:fix

# Format
pnpm format
pnpm format:check

# Type check
pnpm typecheck
```

---

## ⚠️ Key Migration Differences

1. **No Nuclei**: Removed vulnerability scanning completely
2. **Auth Config**: JSON-only format (no YAML parsing, no env var substitution)
3. **Immutability**: Zod `.readonly()` + `Object.freeze()` instead of Pydantic `frozen=True`
4. **Date Handling**: Native `Date` objects instead of datetime
5. **Async**: Native `async`/`await` instead of `asyncio`
6. **Subprocess**: `child_process.spawn()` instead of `asyncio.create_subprocess_exec`
7. **Logging**: Winston instead of Python `logging` module
8. **CLI**: Commander.js instead of Click
9. **Terminal Output**: Chalk + cli-table3 + ora instead of Rich

---

## 📝 Notes

- All Zod schemas provide runtime validation and TypeScript type inference
- Helper classes (`URLDiscoveryResultHelper`, `DiscoveryResultHelper`) replace Python methods
- Configuration is immutable by design (functional programming approach)
- Error handling uses try/catch instead of Python exception patterns
- JSON serialization: `JSON.stringify()` replaces `model_dump(mode='json')`

---

## 📞 Support

For issues or questions about this migration:
- Check Python source code: `/Users/lauz/repos/surface-discovery/discovery/`
- Reference this document for completed vs TODO items
- Follow implementation templates provided above

**Estimated Remaining Time**: 3-4 weeks (1 developer full-time)
