/**
 * Tool execution wrapper for external security tools
 * Handles subprocess execution with timeout, error handling, and logging
 */

import { spawn, ChildProcess } from 'child_process';
import { logger, logError } from '../utils/logger.js';
import which from 'which';

/**
 * Custom error for tool not found in PATH
 */
export class ToolNotFoundError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ToolNotFoundError';
  }
}

/**
 * Custom error for tool execution failures
 */
export class ToolExecutionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ToolExecutionError';
  }
}

/**
 * Result from tool execution
 */
export interface ToolResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

/**
 * Execute external security tools via subprocess
 */
export class ToolRunner {
  private timeout: number;
  private requiredTools: Set<string>;

  /**
   * Create a new ToolRunner
   * @param timeout - Default timeout in seconds for tool execution
   */
  constructor(timeout: number = 300) {
    this.timeout = timeout;
    this.requiredTools = new Set(['subfinder', 'httpx', 'katana', 'dnsx', 'naabu']);
  }

  /**
   * Check if tool is installed and in PATH
   * @param toolName - Name of the tool to check
   * @returns True if tool is available
   */
  async checkToolInstalled(toolName: string): Promise<boolean> {
    try {
      await which(toolName);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Check all required tools are installed
   * @returns Map of tool names to availability status
   */
  async checkDependencies(): Promise<Map<string, boolean>> {
    const results = new Map<string, boolean>();

    for (const tool of this.requiredTools) {
      const installed = await this.checkToolInstalled(tool);
      results.set(tool, installed);
    }

    const missing = Array.from(results.entries())
      .filter(([_, available]) => !available)
      .map(([tool, _]) => tool);

    if (missing.length > 0) {
      logger.warn(`Missing tools: ${missing.join(', ')}`);
    }

    return results;
  }

  /**
   * Run external command asynchronously
   * @param command - Command and arguments as array
   * @param timeoutOverride - Optional timeout override in seconds
   * @param check - Raise error if command fails
   * @param stdinData - Optional data to write to stdin
   * @returns Tool execution result
   * @throws ToolNotFoundError if tool not found in PATH
   * @throws ToolExecutionError if command fails and check=true
   * @throws Error if command times out
   */
  async run(
    command: string[],
    timeoutOverride?: number,
    check: boolean = true,
    stdinData?: string
  ): Promise<ToolResult> {
    const toolName = command[0];
    const timeoutSeconds = timeoutOverride ?? this.timeout;
    const timeoutMs = timeoutSeconds * 1000;

    if (!toolName) {
      throw new Error('Command is required');
    }

    // Check tool is available
    const isInstalled = await this.checkToolInstalled(toolName);
    if (!isInstalled) {
      throw new ToolNotFoundError(`Tool not found: ${toolName}`);
    }

    logger.debug(`Running: ${command.join(' ')}`);

    return new Promise((resolve, reject) => {
      const process: ChildProcess = spawn(toolName, command.slice(1), {
        stdio: stdinData ? 'pipe' : ['ignore', 'pipe', 'pipe'],
      });

      let stdout = '';
      let stderr = '';
      let timedOut = false;

      // Setup timeout
      const timer = setTimeout(() => {
        timedOut = true;
        logger.error(`Tool ${toolName} timed out after ${timeoutSeconds}s`);
        process.kill('SIGTERM');

        // Force kill after 5 seconds if still running
        setTimeout(() => {
          if (!process.killed) {
            process.kill('SIGKILL');
          }
        }, 5000);
      }, timeoutMs);

      // Collect stdout
      process.stdout?.on('data', (data: Buffer) => {
        stdout += data.toString('utf-8');
      });

      // Collect stderr
      process.stderr?.on('data', (data: Buffer) => {
        stderr += data.toString('utf-8');
      });

      // Write stdin if provided
      if (stdinData && process.stdin) {
        process.stdin.write(stdinData);
        process.stdin.end();
      }

      // Handle process completion
      process.on('close', (code: number | null) => {
        clearTimeout(timer);

        if (timedOut) {
          reject(new Error(`Tool ${toolName} timed out after ${timeoutSeconds}s`));
          return;
        }

        const exitCode = code ?? 0;

        // Log warnings for non-zero exit codes
        if (exitCode !== 0) {
          logger.warn(`Tool ${toolName} exited with code ${exitCode}: ${stderr.slice(0, 200)}`);
        }

        // Check for errors if requested
        if (check && exitCode !== 0) {
          reject(new ToolExecutionError(`Tool ${toolName} failed: ${stderr.slice(0, 500)}`));
          return;
        }

        resolve({ stdout, stderr, exitCode });
      });

      // Handle process errors
      process.on('error', (error: Error) => {
        clearTimeout(timer);
        logError(`Tool ${toolName} execution error`, error);
        reject(new ToolExecutionError(`Failed to execute ${toolName}: ${error.message}`));
      });
    });
  }

  /**
   * Run subfinder for subdomain enumeration
   * @param domain - Target domain
   * @param timeoutOverride - Optional timeout override
   * @param silent - Silent mode (less output)
   * @returns Raw stdout output
   */
  async runSubfinder(
    domain: string,
    timeoutOverride?: number,
    silent: boolean = true
  ): Promise<string> {
    const command = ['subfinder', '-d', domain];
    if (silent) {
      command.push('-silent');
    }

    const result = await this.run(command, timeoutOverride, false);
    return result.stdout;
  }

  /**
   * Run httpx for HTTP probing and tech detection
   * @param targets - List of domains/URLs to probe
   * @param timeoutOverride - Optional timeout override
   * @param techDetect - Enable technology detection
   * @param followRedirects - Follow HTTP redirects
   * @param jsonOutput - Output in JSON format
   * @returns Raw stdout output
   */
  async runHttpx(
    targets: string[],
    timeoutOverride?: number,
    techDetect: boolean = true,
    followRedirects: boolean = true,
    jsonOutput: boolean = true
  ): Promise<string> {
    const command = ['httpx', '-silent'];

    if (techDetect) {
      command.push('-tech-detect');
    }
    if (followRedirects) {
      command.push('-follow-redirects');
    }
    if (jsonOutput) {
      command.push('-json');
    }

    const targetsInput = targets.join('\n');
    const result = await this.run(command, timeoutOverride, true, targetsInput);
    return result.stdout;
  }

  /**
   * Run dnsx for DNS record retrieval
   * @param domains - List of domains to query
   * @param recordTypes - DNS record types (A, AAAA, MX, TXT, etc.)
   * @param timeoutOverride - Optional timeout override
   * @returns Raw stdout output
   */
  async runDnsx(
    domains: string[],
    recordTypes?: string[],
    timeoutOverride?: number
  ): Promise<string> {
    const command = ['dnsx', '-silent', '-json'];

    if (recordTypes && recordTypes.length > 0) {
      for (const recordType of recordTypes) {
        command.push(`-${recordType.toLowerCase()}`);
      }
    } else {
      // Default: A, AAAA records
      command.push('-a', '-aaaa');
    }

    const domainsInput = domains.join('\n');
    const result = await this.run(command, timeoutOverride, true, domainsInput);
    return result.stdout;
  }

  /**
   * Run katana for web crawling and endpoint discovery
   * @param targets - List of URLs to crawl
   * @param depth - Crawl depth (default: 2)
   * @param jsCrawl - Enable JavaScript crawling (default: true)
   * @param timeoutOverride - Optional timeout override
   * @returns Raw stdout output (JSONL format)
   */
  async runKatana(
    targets: string[],
    depth: number = 2,
    jsCrawl: boolean = true,
    timeoutOverride?: number
  ): Promise<string> {
    const command = ['katana', '-silent', '-jsonl'];

    // Set crawl depth
    command.push('-depth', depth.toString());

    // Enable JavaScript crawling
    if (jsCrawl) {
      command.push('-jc');
    }

    const targetsInput = targets.join('\n');
    const result = await this.run(command, timeoutOverride, true, targetsInput);
    return result.stdout;
  }

  /**
   * Run katana with authentication headers for authenticated crawling
   * @param targets - List of URLs to crawl
   * @param headers - Authentication headers (Authorization, Cookie, custom headers)
   * @param depth - Crawl depth (default: 3 for authenticated surfaces)
   * @param jsCrawl - Enable JavaScript crawling (default: true)
   * @param timeoutOverride - Optional timeout override
   * @returns Raw stdout output (JSONL format)
   */
  async runKatanaAuthenticated(
    targets: string[],
    headers: Record<string, string>,
    depth: number = 3,
    jsCrawl: boolean = true,
    timeoutOverride?: number
  ): Promise<string> {
    const command = ['katana', '-silent', '-jsonl'];

    // Set crawl depth
    command.push('-depth', depth.toString());

    // Enable JavaScript crawling
    if (jsCrawl) {
      command.push('-jc');
    }

    // Add headers
    for (const [key, value] of Object.entries(headers)) {
      command.push('-headers', `${key}: ${value}`);
    }

    const targetsInput = targets.join('\n');
    const result = await this.run(command, timeoutOverride, true, targetsInput);
    return result.stdout;
  }

  /**
   * Run naabu for port scanning
   * @param hosts - List of hosts/IPs to scan
   * @param ports - Port specification (e.g., "80,443,8080" or "1-1000" or "-" for all)
   * @param topPorts - Scan top N ports (100, 1000, or undefined for custom ports)
   * @param rate - Packets per second (default: 1000)
   * @param timeoutOverride - Optional timeout override
   * @returns Raw stdout output (JSONL format)
   */
  async runNaabu(
    hosts: string[],
    ports?: string,
    topPorts?: number,
    rate: number = 1000,
    timeoutOverride?: number
  ): Promise<string> {
    const command = ['naabu', '-silent', '-json'];

    // Port configuration (mutually exclusive)
    if (topPorts) {
      command.push('-top-ports', topPorts.toString());
    } else if (ports) {
      command.push('-p', ports);
    } else {
      // Default to top 100 ports if nothing specified
      command.push('-top-ports', '100');
    }

    // Rate limiting
    command.push('-rate', rate.toString());

    const hostsInput = hosts.join('\n');

    try {
      const result = await this.run(command, timeoutOverride, true, hostsInput);
      return result.stdout;
    } catch (error) {
      // Provide detailed timeout information for debugging
      if (error instanceof Error && error.message.includes('timed out')) {
        const timeoutVal = timeoutOverride ?? this.timeout;
        const portDesc = topPorts ? `top-${topPorts}` : ports ? ports : 'default';

        logger.error(
          `naabu timeout after ${timeoutVal}s: ${hosts.length} hosts, ${portDesc} ports, rate=${rate}pps`
        );

        throw new ToolExecutionError(
          `Port scan timeout after ${timeoutVal}s ` +
            `(${hosts.length} hosts, ${portDesc} ports, rate=${rate}pps). ` +
            `Consider increasing naabu_timeout or reducing port range.`
        );
      }
      throw error;
    }
  }
}
