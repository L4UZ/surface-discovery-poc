# Technical Decisions: Node.js Migration - Surface Discovery

## Architectural Patterns

### 1. Data Validation Strategy
**Decision**: Use Zod for all data validation and type inference
**Rationale**:
- Runtime validation + compile-time types from single source
- Better DX than separate validation + TypeScript types
- Composable schemas with transforms and refinements
- User explicitly requested Zod over alternatives

**Implementation**:
```typescript
// Schema definition
export const schema = z.object({...}).strict().readonly();

// Type extraction
export type Type = z.infer<typeof schema>;

// Validation
const validated = schema.parse(data); // throws on error
const result = schema.safeParse(data); // returns Result<T>
```

### 2. Immutability Approach
**Decision**: Dual-layer immutability (compile-time + runtime)
**Rationale**:
- TypeScript `readonly` provides compile-time safety
- `Object.freeze()` provides runtime immutability
- Zod `.readonly()` enforces immutability in schemas
- Prevents accidental mutations in long-running processes

**Implementation**:
- Configuration: `Object.freeze()` + Zod `.readonly()`
- Results: Functional transformations (return new objects)
- No in-place modifications anywhere in codebase

### 3. Helper Functions vs Methods
**Decision**: Static helper classes over instance methods
**Rationale**:
- Functional programming patterns (input → output)
- No hidden state or side effects
- Easier to test and reason about
- More aligned with TypeScript/JavaScript ecosystem

**Pattern**:
```typescript
// Instead of:
result.addUrl(url);  // mutation

// Use:
const newResult = ResultHelper.addUrl(result, url); // new object
```

### 4. Error Handling Strategy
**Decision**: Try/catch with logging, propagate to caller
**Rationale**:
- Node.js doesn't have asyncio exception patterns
- Caller decides how to handle errors
- Log errors at source for debugging
- Don't swallow errors silently

**Pattern**:
```typescript
try {
  const result = await operation();
  return result;
} catch (error) {
  logger.error(`Operation failed: ${error}`);
  throw error; // propagate to caller
}
```

## Technology Selections

### 1. Package Manager: pnpm
**Decision**: Use pnpm instead of npm/yarn
**Rationale**:
- User preference for disk efficiency
- Similar to Python's uv philosophy
- Fast installation and linking
- Better for monorepos (future consideration)

### 2. Testing: Vitest (Deferred)
**Decision**: Use Vitest but defer to post-migration
**Rationale**:
- User explicitly requested post-migration testing
- Focus on core functionality first
- Vitest has better TypeScript integration than Jest
- Native ESM support

### 3. CLI Framework: Commander.js
**Decision**: Commander.js over alternatives
**Rationale**:
- Most popular and mature Node.js CLI framework
- Direct Python Click equivalent
- Clean API and good TypeScript support
- Extensive documentation

### 4. Logging: Winston
**Decision**: Winston over alternatives (pino, bunyan)
**Rationale**:
- Most established and feature-complete
- Excellent TypeScript support
- Structured logging with JSON format
- Multiple transport options
- Similar to Python logging module

### 5. Terminal UI: Chalk + cli-table3 + ora + boxen
**Decision**: Multiple libraries instead of single framework
**Rationale**:
- Python Rich doesn't have direct Node.js equivalent
- Best-in-class for each feature:
  - Chalk: colors (most popular)
  - cli-table3: tables (actively maintained)
  - ora: spinners (excellent API)
  - boxen: boxes (simple and effective)

## Removed Features

### 1. Nuclei Integration
**Decision**: Remove completely from migration
**Rationale**:
- User explicitly requested removal
- Simplifies pipeline to 5 stages
- Reduces dependencies and complexity
- No need for Finding/CVE models

**Impact**:
- Removed 1 tool integration
- Removed 2 data models
- Removed 1 parser
- Removed 1 discovery stage

### 2. YAML Auth Config
**Decision**: JSON-only authentication configuration
**Rationale**:
- User explicitly requested simplification
- Removes dependency on js-yaml
- No env var substitution needed
- Simpler implementation and testing

**Impact**:
- Auth configs must be pre-processed
- No runtime env var substitution
- Direct JSON.parse() + Zod validation
- Reduced complexity in auth parser

### 3. Python Output Compatibility
**Decision**: Modernize output format, no backward compatibility
**Rationale**:
- User explicitly accepted breaking changes
- Allows for improved JSON structure
- Can use camelCase consistently
- Leverage Zod transformations

**Impact**:
- Output JSON differs from Python version
- Consumers need to update parsers
- Better alignment with JavaScript conventions
- Cleaner data structures

## Subprocess Integration

### 1. Tool Execution Pattern
**Decision**: `child_process.spawn()` over `exec()` or `execFile()`
**Rationale**:
- Stream-based output handling (better for large outputs)
- No shell interpretation (security)
- Better control over stdin/stdout/stderr
- Similar to Python asyncio.create_subprocess_exec

**Critical Implementation Details**:
- Timeout with `setTimeout()` + `process.kill()`
- Accumulate stdout/stderr in chunks
- Handle 'close' event, not 'exit'
- Clean up timer on completion

### 2. JSONL Parsing Strategy
**Decision**: Line-by-line parsing with error tolerance
**Rationale**:
- External tools output JSON Lines format
- Some lines may be malformed (tool errors)
- Need to handle large outputs efficiently
- Filter empty lines before parsing

**Pattern**:
```typescript
output.trim()
  .split('\n')
  .filter(line => line.trim())
  .map(line => {
    try {
      return JSON.parse(line);
    } catch {
      logger.warn(`Failed to parse line: ${line}`);
      return null;
    }
  })
  .filter(Boolean)
```

## Playwright Integration

### 1. API Compatibility
**Decision**: Direct migration, minimal changes
**Rationale**:
- Playwright API is nearly identical in Python and Node.js
- Same methods, similar async patterns
- Good TypeScript types built-in
- Extensive documentation

**Key Differences**:
- `async with` → `try/finally` with manual cleanup
- Context manager pattern → explicit open/close
- Page methods use camelCase instead of snake_case

### 2. Browser Selection
**Decision**: Chromium only (same as Python)
**Rationale**:
- Consistency with Python implementation
- Smallest installation size
- Best headless performance
- Sufficient for discovery use case

## Configuration Management

### 1. Depth Presets
**Decision**: Three presets (shallow, normal, deep)
**Rationale**:
- Same as Python implementation
- Covers common use cases
- Easy to override specific values
- Clear semantics for users

**Design**:
- Immutable preset objects
- `getConfig()` function for overrides
- Zod validation on merged config
- Type-safe with TypeScript

### 2. Tool Timeout Configuration
**Decision**: Separate timeout for each tool
**Rationale**:
- Tools have different performance characteristics
- Some tools (naabu) can take much longer
- Allows fine-tuned control per depth
- Matches Python implementation

## File Organization

### 1. Directory Structure
**Decision**: Flat structure under src/ with category folders
**Rationale**:
- Clear separation of concerns
- Easy to navigate
- Scalable for future growth
- Standard Node.js pattern

**Structure**:
```
src/
├── models/    - Data schemas
├── stages/    - Discovery pipeline
├── tools/     - External tool integration
├── crawler/   - Playwright automation
├── utils/     - Shared utilities
└── types/     - Global TypeScript types
```

### 2. Barrel Exports
**Decision**: Use index.ts barrel exports for models
**Rationale**:
- Clean imports throughout codebase
- Single source of truth for exports
- Easy to add/remove exports
- Standard TypeScript pattern

**Usage**:
```typescript
// Instead of:
import { Subdomain } from './models/domain.js';
import { Service } from './models/service.js';

// Use:
import { Subdomain, Service } from './models/index.js';
```

## Development Workflow

### 1. Development vs Production
**Decision**: tsx for development, tsc for production
**Rationale**:
- tsx allows direct TypeScript execution
- Fast iteration during development
- tsc produces optimized JavaScript for production
- Clear separation of concerns

### 2. Code Quality Tools
**Decision**: ESLint + Prettier + TypeScript strict mode
**Rationale**:
- ESLint catches logic errors and bad patterns
- Prettier enforces consistent formatting
- TypeScript strict mode catches type errors
- Industry standard combination

**Configuration**:
- ESLint: TypeScript plugin, recommended rules
- Prettier: 100 char width, single quotes
- TypeScript: all strict flags enabled

## Docker Strategy

### 1. Multi-Stage Build
**Decision**: Two-stage build (Go tools + Node.js runtime)
**Rationale**:
- Go tools built in separate stage
- Smaller final image (no Go toolchain)
- Cleaner separation of concerns
- Matches Python Dockerfile pattern

**Stages**:
1. Go builder: Install 5 ProjectDiscovery tools
2. Node.js runtime: Install pnpm, deps, Playwright

### 2. Base Image Selection
**Decision**: node:20-slim for runtime
**Rationale**:
- Official Node.js image
- Slim variant reduces size
- Node 20 LTS with long support
- Good security practices

### 3. Playwright Installation
**Decision**: Install in Docker build, not at runtime
**Rationale**:
- Faster container startup
- Predictable image size
- No network calls at runtime
- Matches Python approach

## Documentation Strategy

### 1. Multi-Level Documentation
**Decision**: README, MIGRATION_STATUS, QUICK_START, SUMMARY
**Rationale**:
- Different audiences need different details
- README: general overview
- MIGRATION_STATUS: implementation templates
- QUICK_START: continuation guide
- SUMMARY: executive overview

### 2. Code Documentation
**Decision**: JSDoc comments for all public APIs
**Rationale**:
- Good IDE integration
- Can generate TypeDoc documentation
- Self-documenting code
- TypeScript type hints + descriptions

**Pattern**:
```typescript
/**
 * Description of function
 * @param param - Parameter description
 * @returns Return value description
 */
export function example(param: string): number {
  // implementation
}
```

## Migration Philosophy

### 1. Foundation First
**Decision**: Complete models and config before implementation
**Rationale**:
- Solid foundation prevents rework
- Type-safe contracts established early
- Clear interfaces for all components
- Can implement stages independently

### 2. Incremental Implementation
**Decision**: Build and test each component individually
**Rationale**:
- Easier to debug issues
- Faster feedback loops
- Can verify each piece works
- Reduces integration problems

### 3. Template-Driven Development
**Decision**: Provide complete templates for all remaining work
**Rationale**:
- Faster implementation
- Consistent patterns
- Reduces decision fatigue
- Clear examples to follow

## Future Considerations

### 1. Testing Strategy (Post-Migration)
- Unit tests for all modules
- Integration tests for discovery pipeline
- Mocking strategy for external tools
- >80% code coverage target

### 2. Performance Optimization
- Benchmark against Python version
- Identify bottlenecks
- Optimize hot paths
- Consider caching strategies

### 3. Error Recovery
- Implement retry logic for transient failures
- Save partial results on timeout
- Resume capability for long scans
- Graceful degradation

### 4. Monitoring & Observability
- Structured logging with correlation IDs
- Metrics collection (Prometheus?)
- Distributed tracing
- Performance profiling

## Summary

These technical decisions establish a solid foundation for the Node.js migration. Key principles:

1. **Type Safety**: TypeScript strict mode + Zod validation
2. **Immutability**: Functional patterns, no mutations
3. **Simplicity**: Remove unnecessary complexity (Nuclei, YAML)
4. **Standards**: Use established Node.js patterns and tools
5. **Documentation**: Comprehensive guides for all remaining work

The migration is 15% complete with a clear path forward. All architectural decisions are made, and templates are provided for the remaining 85% of work.
