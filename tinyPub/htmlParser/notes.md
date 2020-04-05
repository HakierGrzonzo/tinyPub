# Style handling:

## Style priority:

1. `style` property on tag
2. linked stylesheet
3. `<style>` tag in the document
4. defaults

## Style dict fetching:

1. Generate global *dict-sheet* for entire document from defaults, `<style>` and linked stylesheet in that order.
2. Fetch style dict from *dict-sheet*; if tag has a valid `style` property, append it to style dict.

# Tag handling:

## Metatypes:

- `<html>`:
  - has nested blocks.
  - has initial width.
  - has *dict-sheet*.
  - has title from `<title>`.
  - has list of tags to ignore.
- in-line:
  - has formatting.
  - has text.
  - can get split by nested in-line.
  - gets converted to 1D array with nested in-lines getting separated and styled.
- block:
  - makes a block of text.
  - formats it.
  - if another block is nested → split parent block and insert it at the same level.
  - margin chars. (can also be used for border drawing)
  - has child in-line element with actual text.
- list-item:
  - extends block
  - has margin and special char for list indent.
  - has child Block element with no margin.
- `<table>`:
  - extends block
  - has nested blocks arranged in grid
