import { describe, expect, it } from 'vitest';
import { groupTimezones } from './groupTimezones';

describe('groupTimezones', () => {
  it('unions UTC in even when the engine list omits it', () => {
    const groups = groupTimezones(['Europe/Warsaw'], 'Europe/Warsaw');
    const other = groups.find((g) => g.label === 'Inne');
    expect(other?.zones).toContain('UTC');
  });

  it('does not duplicate UTC when the engine list already includes it', () => {
    const groups = groupTimezones(['UTC', 'Europe/Warsaw'], 'Europe/Warsaw');
    const other = groups.find((g) => g.label === 'Inne');
    expect(other?.zones.filter((z) => z === 'UTC')).toHaveLength(1);
  });

  it('surfaces a stored legacy alias missing from the engine list as a leading group', () => {
    const groups = groupTimezones(['Europe/Warsaw', 'America/New_York'], 'US/Eastern');
    expect(groups[0]).toEqual({ label: 'US/Eastern', zones: ['US/Eastern'] });
  });

  it('does not add a leading group when the stored value is already in the list', () => {
    const groups = groupTimezones(['Europe/Warsaw'], 'Europe/Warsaw');
    expect(groups.some((g) => g.label === 'Europe/Warsaw')).toBe(false);
  });

  it('groups by region prefix and sorts zones within a group', () => {
    const groups = groupTimezones(['Europe/Warsaw', 'Europe/Berlin'], 'Europe/Warsaw');
    const europe = groups.find((g) => g.label === 'Europe');
    expect(europe?.zones).toEqual(['Europe/Berlin', 'Europe/Warsaw']);
  });

  it('puts slashless zones into "Inne" and sorts groups alphabetically with "Inne" last', () => {
    const groups = groupTimezones(['Europe/Warsaw', 'America/New_York', 'CET'], 'Europe/Warsaw');
    expect(groups.map((g) => g.label)).toEqual(['America', 'Europe', 'Inne']);
    const other = groups.find((g) => g.label === 'Inne');
    expect(other?.zones).toEqual(['CET', 'UTC']);
  });
});
