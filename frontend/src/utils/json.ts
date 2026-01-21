export const formatJson = (value: unknown): string => {
  if (value === undefined || value === null) {
    return '';
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch (error) {
    return '';
  }
};

export const safeParseJson = (
  value?: string
): { value?: Record<string, unknown>; error?: string } => {
  if (!value || value.trim() === '') {
    return { value: undefined };
  }

  try {
    const parsed = JSON.parse(value) as Record<string, unknown>;
    return { value: parsed };
  } catch (error) {
    return { error: 'Invalid JSON' };
  }
};
