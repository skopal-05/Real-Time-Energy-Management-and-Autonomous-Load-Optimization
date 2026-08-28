import type { ReactNode } from "react";
import type { Resource } from "@/hooks/useResource";
import { ErrorState, LoadingState } from "./States";

interface ResourceBoundaryProps<T> {
  resource: Resource<T>;
  children: (data: T) => ReactNode;
  /** Height/shape of the skeleton shown on first load. */
  loading?: ReactNode;
  /** Rendered when the request succeeded but returned nothing usable. */
  empty?: ReactNode;
  isEmpty?: (data: T) => boolean;
}

/**
 * Renders loading / error / empty / ready for one resource, so every page
 * handles these states identically instead of re-implementing them.
 */
export function ResourceBoundary<T>({
  resource,
  children,
  loading,
  empty,
  isEmpty,
}: ResourceBoundaryProps<T>) {
  if (resource.error) {
    return <ErrorState message={resource.error} onRetry={resource.reload} />;
  }
  if (resource.data === null) {
    return <>{loading ?? <LoadingState />}</>;
  }
  if (isEmpty?.(resource.data)) {
    return <>{empty ?? null}</>;
  }
  return <>{children(resource.data)}</>;
}
