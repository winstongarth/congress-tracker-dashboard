const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
});

export function formatAmountRange(min: number, max: number): string {
  return `${currencyFormatter.format(min)} - ${currencyFormatter.format(max)}`;
}

export function formatDisclosureDate(isoDate: string): string {
  // Dates come back as "YYYY-MM-DD" with no time component; parsing that
  // directly with `new Date(...)` treats it as UTC midnight, which can
  // roll back a day in negative-UTC-offset timezones. Split it instead.
  const [year, month, day] = isoDate.split("-").map(Number);
  return dateFormatter.format(new Date(year, month - 1, day));
}
