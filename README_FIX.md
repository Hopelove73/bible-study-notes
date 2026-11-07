# Bible Notes Fix Summary

## Completed
- **ezk-15 A04**: Fixed - moved verse 2 from body to scripture div
- **ezk-08 A20**: Fixed verses 8, 9 (A20 errors resolved)

## Pending
- **ezk-13 A20**: 12 verses [1,2,7-9,11-16,18] need scripture block rewriting
- **ezk-14 A04**: 13 missing verses need adding to scripture divs
- **ezk-14 A20**: Verses [7,8,10,11] need text fixes vs verses JSON
- **ezk-08 A20**: Verses [12,13] still have mismatches vs verses JSON

## Source of Truth
All verses must match `verses/<id>.json` exactly after normalization. JSON files unmodified.

## Key Pattern
Verse numbers 1→n must appear exactly once in `<div class="scripture">` blocks with text normalizing identically to the JSON source.