YC Companies Search, Ranking & Change Intelligence System

# Overview

YC Intelligence is an end-to-end analytics and intelligence platform built on Y Combinator company data.
It performs large-scale scraping, historical change tracking, search & ranking, trend analysis, and AI-assisted insights, exposed via high-performance APIs and visualized through a React-based analytics dashboard.

The system is designed with:

Deterministic data pipelines

Time-series snapshot modeling

Search & scoring engines

Self-hosted LLM integration (no external APIs)

Target data source:

 https://www.ycombinator.com/companies

# System Architecture


 YC Website   
       ↓
 Python Async Scraper       
 - aiohttp / requests       
 - HTML parsing             
 - Retry & resume           
       ↓
 PostgreSQL Database        
 - Versioned snapshots     
 - Change history           
 - Full-text search         
 - Scores & analytics       
       ↓
 API Layer                  
 - FastAPI (core services)  
 - Next.js API routes       
       ↓
 Frontend (Next.js + React) 
 - Explorer                 
 - Analytics dashboards     
 - AI intelligence UI       
       ↓

 Local LLM (Ollama)         
 - phi / phi-3 model        
 - RAG-based prompts        
 - No external data sharing 


# Database Schema

companies

Canonical company records.

Field	        Type
id	             PK
yc_company_id	text
name	        text
domain	        text
founded_year	int
first_seen_at	timestamp
last_seen_at	timestamp
is_active	    boolean
company_snapshots

Stores all meaningful historical states.

Field	           Type
id	               PK
company_id	       FK
batch	           text
stage	           text
description	       text
location	       text
tags	           JSONB
employee_range	   text
scraped_at	       timestamp
snapshot_hash	   SHA256

Rule:
A new snapshot is inserted only if snapshot_hash changes.

company_changes

Derived table (not scraped).

Field	    Type
id	        PK
company_id	FK
change_type	enum
old_value	text
new_value	text
detected_at	timestamp

Change types:

STAGE_CHANGE

LOCATION_CHANGE

TAG_CHANGE

DESCRIPTION_CHANGE

company_scores
Field	           Type
company_id	       FK
momentum_score	   numeric
stability_score	   numeric
last_computed_at   timestamp
scrape_runs

Tracks each scraper execution.

Field	               Type
id	                   PK
started_at	           timestamp
ended_at	           timestamp
total_companies	       int
new_companies	       int
updated_companies	   int
unchanged_companies	   int
failed_companies	   int
avg_time_per_company_ms	numeric

# Change Detection Logic

On every scrape:

Fetch latest company data

Generate snapshot_hash

Compare with previous snapshot

If different:

Insert new snapshot

Detect changes field-by-field

Insert records into company_changes

This guarantees:

No duplicate snapshots

Deterministic change history

Time-series correctness

# Scoring & Ranking Logic

Momentum Score

Calculated from:

Number of changes in last 6 months

Stage progression (e.g., Active → Public)

Tag growth

Recency of activity

Stability Score

Calculated from:

Time since last change

Description consistency

Location stability

Scores are computed programmatically during analytics jobs.

# Search System

Implemented using PostgreSQL Full-Text Search (tsvector) on:

Company name

Description

Tags

Features:

Keyword ranking

Partial matches

Pagination

Sorting by relevance or momentum score

# Performance Measurement

For each company scrape:

Index page fetch time

Detail page fetch time

HTML parsing time

DB write time

Change detection time

Score computation time

After scraping:

Total companies processed

Total changes detected

Average time per company

Total runtime

Logs are saved to scraper.log.

# API Endpoints

Search

GET /api/search

Filters:

batch

stage

location

score range
Sorting:

relevance

momentum score

Company Details

GET /api/companies/:id

Returns:

Company profile

Snapshot history

Change history

Scores & trends

Trends

GET /api/trends

Returns:

Fastest growing tags

Locations with highest new company count

Stage transition trends over time

Leaderboard

GET /api/leaderboard

# LLM Usage (Self-Hosted)

Model

Ollama

phi / phi-3 (lightweight, local, low-RAM)

Why Ollama?

Fully self-hosted

No external API calls

No data leaves the system

Approved by TL constraints

LLM Integration Pattern (RAG)

We use Retrieval-Augmented Generation (RAG):

Fetch company data from PostgreSQL

Inject data into structured prompt

Query local LLM via Ollama HTTP API

Return human-readable insights

Use Cases

Company insight generation

Change explanation

Score interpretation

Trend explanation

LLM Safety Rules

LLM output never overwrites raw data

System works even if LLM is disabled

LLM responses are computed at request time

No scraped data is sent externally

# Frontend Pages

Company Explorer

Full-text search

Multi-filter UI

Pagination

Score-based sorting

Analytics Dashboard

Batch distribution

Location distribution

Stage analytics

Trends Dashboard

Tag growth

Location trends

Stage transitions

AI Intelligence Page

Ask natural language questions

Context-aware answers

Powered by local LLM

# Deployment

Backend: FastAPI

Frontend: Next.js

Database: PostgreSQL

LLM Runtime: Ollama (local)

# Submission Info

GitHub Repo: [https://github.com/Abhinand8286/yc-intelligence-ai]


# Final Notes

This system demonstrates:

Advanced scraping

Deterministic data modeling

Search & ranking engines

Analytics pipelines

High-performance APIs

Self-hosted LLM intelligence

No external APIs are used for AI inference.


