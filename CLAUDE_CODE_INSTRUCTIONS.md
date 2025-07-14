# Claude Code Startup Instructions

## Objective
Build a universal workflow automation platform that can eliminate backlogs for any organization using Claude agent swarms.

## First Implementation Target
Lackawanna County property tax appeals - process their 8-month backlog before selling to them.

## What Claude Code Should Build

### 1. Data Collection System
- Web scraper using Puppeteer/Playwright
- Scrape Lackawanna County assessment database
- Collect appeals information and schedules
- Auto-adapt to different government website structures

### 2. Claude Flow Swarm Processing
- Data collector agent (web scraping)
- Pattern analyzer agent (identify appeal patterns)
- Processor swarm (8 agents processing appeals in parallel)  
- Validator consensus (3 agents validating results)
- Report generator agent (create deliverables)

### 3. Delivery Strategy
- Partial report: Sample processed appeals + statistics (free teaser)
- Complete report: All appeals processed with recommendations (paid)
- "Done deal" approach: deliver value before payment

### 4. Universal Adaptation
- System should work for any organization's workflows
- Counties, law firms, healthcare, manufacturing, etc.
- Self-configuring primitives for different domains

## Development Priority
1. Get Lackawanna data collection working
2. Process first 10 appeals as proof of concept
3. Generate sample partial report
4. Build complete processing pipeline
5. Create universal adaptation framework

## Expected Outcome
Working demo that processes Lackawanna County's appeals backlog and generates compelling reports showing value delivered.

## Data Sources Available
- Lackawanna County Assessment Database: https://lcao.lackawannacounty.org
- Appeals information and schedules available online
- Property assessment data publicly accessible
- Can demonstrate with real data before selling

## Key Features
- Web scraping with Playwright/Puppeteer
- Claude Flow swarm coordination
- Partial/complete report generation
- "Done deal" sales model
- Universal primitive architecture
