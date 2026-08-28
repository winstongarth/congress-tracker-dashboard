import { useEffect, useState } from "react";

// Delays reflecting `value` until it's stopped changing for `delayMs` --
// used so typing into a filter field doesn't fire a GraphQL request per
// keystroke.
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timeout = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timeout);
  }, [value, delayMs]);

  return debounced;
}
