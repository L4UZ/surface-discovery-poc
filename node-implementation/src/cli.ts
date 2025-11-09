#!/usr/bin/env node
/**
 * CLI interface for Surface Discovery
 */

import { Command } from 'commander';
import { readFileSync, writeFileSync } from 'fs';
import { resolve } from 'path';
import chalk from 'chalk';
import ora from 'ora';
import Table from 'cli-table3';
import boxen from 'boxen';
import { DiscoveryEngine } from './core.js';
import { getConfig, type DiscoveryDepth } from './config.js';
import { setLogLevel, LogLevel } from './utils/logger.js';
import { sanitizeFilename } from './utils/helpers.js';
import { ToolRunner } from './tools/runner.js';
import type { AuthenticationConfig } from './models/auth.js';
import { authenticationConfigSchema } from './models/auth.js';

/**
 * Display banner with application info
 */
function displayBanner(): void {
  const banner = boxen(
    chalk.bold.cyan('Surface Discovery') +
      '\n\n' +
      chalk.gray('In-depth web attack surface discovery') +
      '\n' +
      chalk.gray('Node.js/TypeScript Edition'),
    {
      padding: 1,
      margin: 1,
      borderStyle: 'round',
      borderColor: 'cyan',
    }
  );
  console.log(banner);
}

/**
 * Check if all required tools are installed
 */
async function checkDependencies(): Promise<void> {
  const spinner = ora('Checking tool dependencies...').start();

  const runner = new ToolRunner();
  const results = await runner.checkDependencies();

  spinner.stop();

  // Create table
  const table = new Table({
    head: [chalk.cyan('Tool'), chalk.cyan('Status')],
    colWidths: [20, 15],
  });

  for (const [tool, installed] of results.entries()) {
    table.push([
      tool,
      installed
        ? chalk.green('✓ Installed')
        : chalk.red('✗ Not Found'),
    ]);
  }

  console.log('\n' + table.toString() + '\n');

  const missing = Array.from(results.entries())
    .filter(([_, installed]) => !installed)
    .map(([tool, _]) => tool);

  if (missing.length > 0) {
    console.log(chalk.red.bold('Missing tools:'), missing.join(', '));
    console.log(
      chalk.yellow('\nInstall missing tools before running discovery.')
    );
    process.exit(1);
  } else {
    console.log(chalk.green.bold('✓ All required tools are installed!\n'));
  }
}

/**
 * Display summary table of results
 */
function displayResults(result: any): void {
  const table = new Table({
    head: [chalk.cyan('Metric'), chalk.cyan('Value')],
    colWidths: [30, 20],
  });

  table.push(
    ['Subdomains Discovered', result.statistics.totalSubdomains.toString()],
    ['Live Services', result.statistics.liveServices.toString()],
    ['Total Endpoints', result.statistics.totalEndpoints.toString()],
    ['Open Ports', result.statistics.totalOpenPorts.toString()],
    [
      'Technologies Detected',
      (result.technologies?.length ?? 0).toString(),
    ],
    [
      'Duration',
      `${result.metadata.duration?.toFixed(2) ?? 0}s`,
    ]
  );

  console.log('\n' + chalk.bold.green('Discovery Results:'));
  console.log(table.toString() + '\n');
}

/**
 * Main CLI program
 */
async function main() {
  const program = new Command();

  program
    .name('surface-discovery')
    .description('In-depth web attack surface discovery service')
    .version('2.0.0')
    .option(
      '--url <url>',
      'Target URL or domain to discover (e.g., https://example.com or example.com)'
    )
    .option(
      '--output <path>',
      'Output file path (default: discovery_<domain>.json)'
    )
    .option(
      '--depth <level>',
      'Discovery depth level (shallow|normal|deep)',
      'normal'
    )
    .option(
      '--timeout <seconds>',
      'Maximum execution time in seconds',
      (value) => parseInt(value, 10)
    )
    .option(
      '--parallel <count>',
      'Maximum parallel tasks',
      (value) => parseInt(value, 10)
    )
    .option('--verbose', 'Enable verbose logging')
    .option('--check-tools', 'Check if required tools are installed and exit')
    .option(
      '--auth-config <path>',
      'Path to JSON authentication configuration file'
    )
    .parse(process.argv);

  const options = program.opts();

  // Setup logger
  if (options.verbose) {
    setLogLevel(LogLevel.DEBUG);
  }

  // Check tools mode
  if (options.checkTools) {
    await checkDependencies();
    return;
  }

  // Validate URL is provided for normal operation
  if (!options.url) {
    console.error(
      chalk.red.bold('Error:') + ' --url is required (unless using --check-tools)'
    );
    process.exit(1);
  }

  // Display banner
  displayBanner();

  try {
    // Build config
    const depth = (options.depth as DiscoveryDepth) ?? 'normal';
    const config = getConfig(depth, {
      parallel: options.parallel,
      verbose: options.verbose ?? false,
    });

    // Parse auth config if provided
    let authConfig: AuthenticationConfig | undefined;
    if (options.authConfig) {
      try {
        const authData = JSON.parse(
          readFileSync(resolve(options.authConfig), 'utf-8')
        );
        authConfig = authenticationConfigSchema.parse(authData);
        console.log(
          chalk.cyan('✓ Loaded authentication configuration\n')
        );
      } catch (error) {
        console.error(
          chalk.red.bold('Error:') + ` Failed to parse auth config: ${error}`
        );
        process.exit(1);
      }
    }

    // Display discovery info
    console.log(chalk.bold.cyan('Target:'), options.url);
    console.log(chalk.bold.cyan('Depth:'), depth);
    console.log(chalk.bold.cyan('Starting discovery...\n'));

    // Create discovery engine
    const engine = new DiscoveryEngine(config);

    // Run discovery with spinner
    const spinner = ora('Running discovery pipeline...').start();

    const result = await engine.discover(options.url, authConfig);

    spinner.succeed('Discovery completed!');

    // Generate output filename if not provided
    let outputPath = options.output;
    if (!outputPath) {
      const domain = result.metadata.target;
      const safeDomain = sanitizeFilename(domain);
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      outputPath = `discovery_${safeDomain}_${timestamp}.json`;
    }

    // Write results to file
    const outputData = JSON.stringify(result, null, 2);
    writeFileSync(resolve(outputPath), outputData, 'utf-8');

    console.log(
      chalk.green.bold('\n✓ Results saved to:'),
      chalk.underline(outputPath)
    );

    // Display summary
    displayResults(result);

    // Success
    process.exit(0);
  } catch (error) {
    console.error(chalk.red.bold('\n✗ Discovery failed:'), error);
    process.exit(1);
  }
}

// Run CLI
main().catch((error) => {
  console.error(chalk.red.bold('Fatal error:'), error);
  process.exit(1);
});
