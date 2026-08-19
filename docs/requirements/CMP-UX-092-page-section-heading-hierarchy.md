# CMP-UX-092 — Page / Section Heading Hierarchy

## Problem
In the Premium UI experiment, Streamlit page headers and subheaders were visually inverted: section titles such as “New todo” could appear more prominent than the page title.

## Requirement
Main-content page headers shall be visually dominant over section subheaders while retaining the restrained Premium UI hierarchy.

## Acceptance criteria
- `st.header` is approximately 30 px in main content.
- `st.subheader` is approximately 20 px in main content.
- Sidebar branding is unaffected by main-content heading rules.

## Status
Verification
