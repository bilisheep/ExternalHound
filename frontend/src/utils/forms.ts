export const cleanPayload = <T extends Record<string, unknown>>(payload: T): T => {
  const cleaned: Record<string, unknown> = {};

  Object.entries(payload).forEach(([key, value]) => {
    if (value === undefined || value === null) {
      return;
    }
    if (typeof value === 'string' && value.trim() === '') {
      return;
    }
    cleaned[key] = value;
  });

  return cleaned as T;
};
