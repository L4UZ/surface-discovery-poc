/**
 * Surface Discovery - Main entry point
 * Exports core functionality for programmatic use
 */

export { DiscoveryEngine } from './core.js';
export { getConfig, type DiscoveryConfig, type DiscoveryDepth } from './config.js';
export * from './models/index.js';
export { logger, setLogLevel, LogLevel } from './utils/logger.js';
export { ToolRunner } from './tools/runner.js';
export * from './stages/index.js';
