/**
 * Authentication configuration models
 */

import { z } from 'zod';

/**
 * Basic authentication credentials
 */
export const basicAuthSchema = z.object({
  /** Username for basic auth */
  username: z.string(),
  /** Password for basic auth */
  password: z.string(),
});

export type BasicAuth = z.infer<typeof basicAuthSchema>;

/**
 * Authentication configuration for a specific URL
 */
export const authConfigSchema = z.object({
  /** Target URL requiring authentication */
  url: z.string().url(),
  /** Custom headers for authentication (e.g., Authorization, X-API-Key) */
  headers: z.record(z.string()).optional(),
  /** Authentication cookies (e.g., session_id, csrf_token) */
  cookies: z.record(z.string()).optional(),
  /** Basic authentication credentials */
  basic: basicAuthSchema.optional(),
});

export type AuthConfig = z.infer<typeof authConfigSchema>;

/**
 * Complete authentication configuration
 */
export const authenticationConfigSchema = z.object({
  /** List of authentication configurations per URL */
  authentication: z.array(authConfigSchema).default([]),
  /** Target URLs for authenticated crawling */
  targets: z.array(z.string()).optional(),
});

export type AuthenticationConfig = z.infer<typeof authenticationConfigSchema>;
