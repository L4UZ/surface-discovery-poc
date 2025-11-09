/**
 * Logging utility using Winston
 * Provides structured logging with multiple transports and levels
 */

import winston from 'winston';

/**
 * Log levels in order of severity
 */
export enum LogLevel {
  ERROR = 'error',
  WARN = 'warn',
  INFO = 'info',
  DEBUG = 'debug',
}

/**
 * Custom format for console output with colors and timestamps
 */
const consoleFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.colorize({ all: true }),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    let log = `${timestamp} [${level}] ${message}`;
    if (Object.keys(meta).length > 0) {
      log += ` ${JSON.stringify(meta)}`;
    }
    return log;
  }),
);

/**
 * Format for file output (JSON structured logging)
 */
const fileFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.json(),
);

/**
 * Create logger instance with configurable level
 */
export function createLogger(level: LogLevel = LogLevel.INFO): winston.Logger {
  const logger = winston.createLogger({
    level,
    transports: [
      // Console transport for human-readable output
      new winston.transports.Console({
        format: consoleFormat,
      }),
    ],
    // Don't exit on uncaught exceptions
    exitOnError: false,
  });

  return logger;
}

/**
 * Add file transport to existing logger
 * @param logger - Logger instance to configure
 * @param filename - Path to log file
 * @param level - Minimum log level for file output
 */
export function addFileTransport(
  logger: winston.Logger,
  filename: string,
  level: LogLevel = LogLevel.DEBUG,
): void {
  logger.add(
    new winston.transports.File({
      filename,
      level,
      format: fileFormat,
    }),
  );
}

/**
 * Default logger instance for the application
 * Can be configured by calling setLogLevel()
 */
export const logger = createLogger();

/**
 * Update log level for the default logger
 * @param level - New log level
 */
export function setLogLevel(level: LogLevel): void {
  logger.level = level;
}

/**
 * Helper function to log errors with stack traces
 * @param message - Error message
 * @param error - Error object
 */
export function logError(message: string, error: unknown): void {
  if (error instanceof Error) {
    logger.error(message, {
      error: error.message,
      stack: error.stack,
    });
  } else {
    logger.error(message, { error: String(error) });
  }
}

/**
 * Helper function to log stage execution
 * @param stage - Discovery stage name
 * @param action - Action being performed
 * @param details - Additional details
 */
export function logStage(
  stage: string,
  action: 'start' | 'complete' | 'error',
  details?: Record<string, unknown>,
): void {
  const message = `${stage} - ${action}`;
  if (action === 'error') {
    logger.error(message, details);
  } else {
    logger.info(message, details);
  }
}
