# Design Document

## Overview

This design document outlines the approach to fix UI aesthetics and translation issues in the ComputePulse application. The primary focus is on ensuring complete language support for the verification button and calculation modal, improving visual consistency, and maintaining smooth language transitions.

The application currently has a translation system in place using the `TRANSLATIONS` object, but there are gaps in implementation where some UI elements don't properly respond to language changes or display incorrect translations.

## Architecture

The ComputePulse application follows a React-based component architecture with:

1. **Translation System**: Centralized `TRANSLATIONS` object in `translations.ts` containing all UI strings for EN and CN languages
2. **Language State Management**: Language state managed at the App level and passed down to components via props
3. **Reactive UI Updates**: Components receive language prop and use it to select appropriate translations from the TRANSLATIONS object

### Current Issues

1. The verification button in `App.tsx` uses a hardcoded fallback text instead of properly accessing the translation object
2. The `CalculationModal` component properly implements translations but may have missing translation keys
3. Language switching may not trigger re-renders in all components due to prop passing issues

## Components and Interfaces

### Modified Components

#### 1. App.tsx
- **Current Issue**: Verification button uses `{t.verifyData || "Verify Data"}` which suggests the translation key might be missing or incorrectly accessed
- **Fix**: Ensure `verifyData` key exists in both EN and CN translations and remove the fallback

#### 2. CalculationModal.tsx
- **Current State**: Already implements proper translation usage with `const t = TRANSLATIONS[language]`
- **Verification Needed**: Ensure all text content uses translation keys, including:
  - Table headers
  - Unit labels (hr vs 小时)
  - Formula descriptions
  - Tab labels

#### 3. translations.ts
- **Current State**: Contains most translation keys
- **Fix**: Verify all keys used in components exist in both EN and CN objects

### Translation Interface

```typescript
interface TranslationKeys {
  // Existing keys...
  verifyData: string;
  calcTitle: string;
  calcDesc: string;
  gpuPricing: string;
  tokenSvi: string;
  // ... all other keys
}

type Translations = {
  EN: TranslationKeys;
  CN: TranslationKeys;
}
```

## Data Models

### Language State
```typescript
type Language = 'EN' | 'CN';
```

### Currency Configuration
```typescript
interface CurrencyConfig {
  code: CurrencyCode;
  symbol: string;
  rate: number;
}
```

### Component Props
```typescript
interface CalculationModalProps {
  isOpen: boolean;
  onClose: () => void;
  computeData: ComputeProvider[];
  tokenData: TokenProvider[];
  currency: CurrencyConfig;
  language: Language; // Critical for translation
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing the acceptance criteria, several properties can be consolidated:
- Properties 1.1 and 1.2 (button text for specific languages) are examples of the same underlying property
- Property 1.4 (no fallback English) is an edge case of 1.1
- Property 2.1 and 2.5 (all text in selected language) can be combined into one comprehensive property
- Properties about styling (3.1, 3.3, 3.4) are not programmatically testable
- Property 4.1 (timing) is not reliably testable

### Testable Properties

Property 1: Language switching updates all UI text
*For any* language setting (EN or CN), when the language is changed, all visible UI text elements should update to display the corresponding translation from the TRANSLATIONS object
**Validates: Requirements 1.3, 2.2**

Property 2: Modal content matches selected language
*For any* language setting, when the calculation modal is opened, all text content within the modal (headers, labels, units, descriptions) should match the selected language
**Validates: Requirements 2.1, 2.3, 2.4**

Property 3: View state persists across language changes
*For any* view state (active tab, view mode, modal open/closed), switching languages should preserve the current state without resetting or changing the user's position
**Validates: Requirements 4.2, 4.3**

Property 4: Currency symbols update with language-triggered currency changes
*For any* language change that triggers a currency change (CN→CNY, EN→USD), all displayed currency symbols should update to match the new currency
**Validates: Requirements 4.5**

### Example Tests

Example 1: Verification button displays correct text for CN
When language is set to CN, the verification button should display "验证数据"
**Validates: Requirements 1.1**

Example 2: Verification button displays correct text for EN
When language is set to EN, the verification button should display "Verify Data"
**Validates: Requirements 1.2**

Example 3: Hover state provides visual feedback
When the user hovers over the verification button, CSS classes or styles should change to provide visual feedback
**Validates: Requirements 3.2**

Example 4: Button visible on mobile viewports
When viewport width is set to mobile size (e.g., 375px), the verification button should be rendered and visible
**Validates: Requirements 3.5**

## Error Handling

### Missing Translation Keys
- **Issue**: If a translation key is missing from the TRANSLATIONS object, the component may display `undefined` or fallback text
- **Solution**: 
  1. Add TypeScript interface for translation keys to ensure compile-time checking
  2. Implement a translation helper function that logs warnings for missing keys in development
  3. Provide sensible fallbacks only in production

### Language State Synchronization
- **Issue**: Language state changes may not propagate to all components if props aren't properly passed
- **Solution**: Ensure language prop is passed to all components that display text, or consider using React Context for global language state

### Currency-Language Coupling
- **Issue**: The app currently couples language changes with currency changes (CN→CNY, EN→USD)
- **Solution**: This is intentional behavior but should be clearly documented. Users should be able to override if needed.

## Testing Strategy

### Unit Testing

Unit tests will cover:
1. **Translation Key Completeness**: Verify all keys exist in both EN and CN translation objects
2. **Component Rendering**: Test that components render correct text for each language setting
3. **Button Click Handlers**: Verify language toggle buttons update state correctly
4. **Currency Symbol Display**: Test that currency symbols match the selected currency

### Property-Based Testing

We will use **React Testing Library** with **fast-check** for property-based testing in TypeScript/React.

Property-based tests will:
1. Generate random language settings and verify all UI text updates accordingly
2. Generate random view states and verify they persist across language changes
3. Generate random currency configurations and verify symbols display correctly

**Configuration**: Each property-based test should run a minimum of 100 iterations.

**Tagging**: Each property-based test must include a comment tag in this format:
```typescript
// **Feature: ui-translation-fixes, Property 1: Language switching updates all UI text**
```

### Integration Testing

Integration tests will verify:
1. End-to-end language switching flow from button click to UI update
2. Modal opening with different language settings
3. Tab switching within modal while changing languages

### Manual Testing Checklist

Since some requirements involve visual aesthetics that are difficult to test programmatically:
1. Visual inspection of button styling consistency
2. Verification of proper spacing and alignment
3. Testing on actual mobile devices for responsive behavior
4. Checking for text flicker during language transitions

## Implementation Plan

### Phase 1: Fix Translation Keys
1. Audit all translation keys used in components
2. Ensure `verifyData` key exists in translations.ts
3. Remove fallback strings from components (e.g., `|| "Verify Data"`)
4. Add any missing translation keys

### Phase 2: Improve Button Styling
1. Review button styling in App.tsx
2. Ensure consistent styling with other header buttons
3. Add proper hover states
4. Test responsive behavior

### Phase 3: Verify Modal Translations
1. Audit CalculationModal for any hardcoded strings
2. Ensure all table headers use translation keys
3. Verify unit labels (hr vs 小时) are properly translated
4. Test tab switching with language changes

### Phase 4: Testing
1. Write unit tests for translation completeness
2. Write property-based tests for language switching
3. Write integration tests for modal behavior
4. Perform manual testing for visual aspects

## Dependencies

- React 18+
- TypeScript
- React Testing Library (for testing)
- fast-check (for property-based testing)
- Existing translation system in translations.ts

## Performance Considerations

- Language switching should be instantaneous (< 100ms) since it only involves updating state and re-rendering with different strings
- No network requests are involved in language switching
- Translation object is loaded at build time, not runtime

## Accessibility Considerations

- Ensure `lang` attribute on HTML element updates with language changes
- Verify screen readers announce content in the correct language
- Maintain keyboard navigation functionality across language switches

## Future Enhancements


2. Implement lazy loading of translation files for better performance
3. Add user preference persistence (localStorage)
4. Implement translation management system for easier updates
