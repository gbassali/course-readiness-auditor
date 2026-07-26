# Assignment 2 — Relational Data Service

**Assessment ID:** `assignment-2`

## Overview

Build a small backend service for managing university course registrations. The service must expose HTTP endpoints for creating courses, enrolling students, dropping registrations, and viewing course rosters.

## Learning Goals

By completing this assignment, students should be able to:

- translate domain requirements into a relational data model;
- apply database normalization principles;
- design clear REST endpoints;
- enforce registration rules in backend domain logic;
- return consistent validation and error responses.

## Functional Requirements

Your service must support:

1. Creating and viewing courses.
2. Creating and viewing students.
3. Enrolling a student in a course.
4. Preventing duplicate registrations.
5. Dropping a student from a course.
6. Rejecting registrations when a course is full.
7. Returning a roster for a selected course.

## Data Requirements

The relational schema must avoid duplicated student and course information. Primary keys, foreign keys, and appropriate uniqueness constraints must be used. Include a short explanation of how the schema follows normalization principles.

## Submission Requirements

Submit:

- the application source code;
- database migration or schema files;
- a README with setup and run instructions;
- example API requests;
- a short design explanation.

## Late Submissions

Late submissions are not accepted. Work submitted after the deadline will receive a grade of zero.

## Evaluation

The submission will be evaluated using the published grading rubric.
