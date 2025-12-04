# Implementation Plan

- [x] 1. Audit and fix translation keys

  - Review all translation keys used in App.tsx and CalculationModal.tsx
  - Verify `verifyData` key exists in both EN and CN translations
  - Remove fallback strings from components (e.g., `|| "Verify Data"`)
  - Ensure all translation keys are properly typed
  - _Requirements: 1.1, 1.2, 1.4_

- [x] 2. Fix verification button translation
  - Remove the fallback `|| "Verify Data"` from the verification button in App.tsx
  - Ensure the button uses `t.verifyData` directly
  - Verify the button text updates when language changes
  - _Requirements: 1.1, 1.2, 1.3_

- [ ]* 2.1 Write property test for language switching
  - **Property 1: Language switching updates all UI text**
  - **Validates: Requirements 1.3, 2.2**

- [x] 3. Fix hardcoded "Formula:" string in CalculationModal









  - Replace hardcoded "Formula:" with `t.formula` in the GPU pricing tab
  - Replace hardcoded formula description with `t.formulaDesc`
  - Verify the formula text updates when language changes
  - _Requirements: 2.1, 2.3, 2.4, 2.5_

- [x] 4. Add missing CN translation keys





  - Add `formula` key to CN translations ("公式:")
  - Add `formulaDesc` key to CN translations with Chinese formula description
  - Verify all EN keys now exist in CN translations
  - _Requirements: 2.1, 2.4_

- [ ]* 4.1 Write property test for modal content language
  - **Property 2: Modal content matches selected language**
  - **Validates: Requirements 2.1, 2.3, 2.4**

- [x] 5. Improve verification button styling



  - Review button styling for consistency with other header buttons
  - Ensure hover states provide visual feedback
  - Verify icon and text alignment
  - Test button spacing with adjacent elements
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ]* 5.1 Write example test for hover state
  - **Example 3: Hover state provides visual feedback**
  - **Validates: Requirements 3.2**

- [x] 6. Test responsive behavior


  - Verify button is visible on mobile viewports
  - Test button accessibility on small screens
  - Ensure proper touch target size
  - _Requirements: 3.5_

- [ ]* 6.1 Write example test for mobile visibility
  - **Example 4: Button visible on mobile viewports**
  - **Validates: Requirements 3.5**

- [x] 7. Implement view state persistence


  - Ensure active tab persists when switching languages
  - Verify view mode (COMPUTE/TOKENS/GRID_LOAD) persists
  - Test modal open/closed state persistence
  - _Requirements: 4.2, 4.3_

- [ ]* 7.1 Write property test for view state persistence
  - **Property 3: View state persists across language changes**
  - **Validates: Requirements 4.2, 4.3**

- [x] 8. Verify currency symbol updates


  - Test that currency symbols update when language triggers currency change
  - Verify CN→CNY and EN→USD transitions
  - Ensure all currency displays are updated
  - _Requirements: 4.5_

- [ ]* 8.1 Write property test for currency symbol updates
  - **Property 4: Currency symbols update with language-triggered currency changes**
  - **Validates: Requirements 4.5**

- [x] 9. Add translation key completeness tests


  - Write unit test to verify all EN keys exist in CN
  - Write unit test to verify all CN keys exist in EN
  - Ensure no missing translation keys
  - _Requirements: 1.1, 1.2, 2.1_

- [x] 10. Final checkpoint - Ensure all tests pass



  - Ensure all tests pass, ask the user if questions arise.
