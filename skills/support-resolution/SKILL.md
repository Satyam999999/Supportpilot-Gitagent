---
name: support-resolution
description: Resolve support FAQ queries with grounded responses and citations.
license: MIT
metadata:
  author: satyamghosh
  version: "1.0.0"
  category: support
---

# Skill: Support Resolution

## Purpose
Answer common support queries accurately from the knowledge base.

## Inputs
- user_query
- retrieved_context

## Outputs
- answer
- citations
- category

## Strategy
1. Identify user intent category.
2. Retrieve top relevant entries.
3. Generate concise answer tied to retrieved facts.
4. Include at least one source reference.

## Failure Mode
If relevant context is weak, request clarification or route to escalation skill.
