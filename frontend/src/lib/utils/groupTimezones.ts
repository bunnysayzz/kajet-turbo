export interface TimezoneGroup {
  label: string;
  zones: string[];
}

const OTHER_GROUP = 'Inne';

/**
 * Groups IANA timezone identifiers by region prefix for a <select>/<optgroup> UI.
 *
 * Guards against three engine-dependent gaps in `Intl.supportedValuesOf('timeZone')`:
 * 'UTC' is unioned in explicitly (Firefox/Safari omit it, Chrome doesn't), and
 * `currentValue` is unioned in too and surfaced as a standalone leading group when it
 * isn't part of `availableZones` — it may be a legacy alias (`US/Eastern`,
 * `Asia/Calcutta`) that Python's zoneinfo accepts but the browser's ICU doesn't list,
 * and it must never be silently dropped from the option set (a <select> with nothing
 * selected would overwrite the stored value on the next save).
 */
export function groupTimezones(availableZones: string[], currentValue: string): TimezoneGroup[] {
  const known = new Set(availableZones);
  known.add('UTC');

  const groups: TimezoneGroup[] = [];
  if (!known.has(currentValue)) {
    groups.push({ label: currentValue, zones: [currentValue] });
  }

  const byRegion = new Map<string, string[]>();
  for (const zone of known) {
    const slash = zone.indexOf('/');
    const region = slash === -1 ? OTHER_GROUP : zone.slice(0, slash);
    (byRegion.get(region) ?? byRegion.set(region, []).get(region)!).push(zone);
  }

  const regionGroups = [...byRegion.entries()]
    .sort(([a], [b]) => (a === OTHER_GROUP ? 1 : b === OTHER_GROUP ? -1 : a.localeCompare(b)))
    .map(([label, zones]) => ({ label, zones: zones.sort((x, y) => x.localeCompare(y)) }));

  return [...groups, ...regionGroups];
}
