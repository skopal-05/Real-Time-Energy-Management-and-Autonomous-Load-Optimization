import { apiConfig, isLiveMode } from "./config";
import type { DataSource } from "./dataSource";
import { httpDataSource } from "./httpDataSource";
import { mockDataSource } from "./mockDataSource";

/**
 * Resolves the active data source.
 *
 * Components call `getDataSource()` — they never import an adapter directly, so
 * the whole application switches between demo and live data from configuration.
 */
export function getDataSource(): DataSource {
  return isLiveMode ? httpDataSource : mockDataSource;
}

export { apiConfig, isLiveMode };
export { DataSourceError } from "./dataSource";
export type { DataSource } from "./dataSource";
export { subscribe } from "./realtime";
export { getAuthService } from "./authService";
export type { AuthService } from "./authService";
