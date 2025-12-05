import { describe, it, expect } from 'vitest';
import { TRANSLATIONS } from './translations';

describe('Translation Completeness', () => {
  it('should have all EN keys in CN translations', () => {
    const enKeys = Object.keys(TRANSLATIONS.EN).sort();
    const cnKeys = Object.keys(TRANSLATIONS.CN).sort();
    
    const missingInCN = enKeys.filter(key => !cnKeys.includes(key));
    
    expect(missingInCN).toEqual([]);
  });

  it('should have all CN keys in EN translations', () => {
    const enKeys = Object.keys(TRANSLATIONS.EN).sort();
    const cnKeys = Object.keys(TRANSLATIONS.CN).sort();
    
    const missingInEN = cnKeys.filter(key => !enKeys.includes(key));
    
    expect(missingInEN).toEqual([]);
  });

  it('should have the same number of keys in both languages', () => {
    const enKeyCount = Object.keys(TRANSLATIONS.EN).length;
    const cnKeyCount = Object.keys(TRANSLATIONS.CN).length;
    
    expect(enKeyCount).toBe(cnKeyCount);
  });

  it('should not have empty translation values in EN', () => {
    const enEntries = Object.entries(TRANSLATIONS.EN);
    const emptyKeys = enEntries
      .filter(([_, value]) => !value || value.trim() === '')
      .map(([key]) => key);
    
    expect(emptyKeys).toEqual([]);
  });

  it('should not have empty translation values in CN', () => {
    const cnEntries = Object.entries(TRANSLATIONS.CN);
    const emptyKeys = cnEntries
      .filter(([_, value]) => !value || value.trim() === '')
      .map(([key]) => key);
    
    expect(emptyKeys).toEqual([]);
  });
});
