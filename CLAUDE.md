# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Python Environment
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run main demo
python demos/lackawanna-demo.py
```

### Node.js Environment  
```bash
# Install Node.js dependencies
npm install

# Run automation demo
npm start
```

### Run Tests
```bash
# Python tests
python -m pytest tests/ -v

# JavaScript tests
npm test
```

### Run Demo Workflow
```bash
# Run complete workflow demonstration
python demo_workflow.py
```

### No Linting/Type Checking
No linting or type checking is currently configured. Consider adding these tools for code quality.

## Architecture Overview

This is a **Universal Workflow Automation Platform** that uses Claude agent swarms to process organizational backlogs. The system follows a primitive-based architecture where domain-specific workflows can be plugged in.

### Core Components

**Claude Flow Swarm (`/claude-flow/swarm-config.yml`)**
- Mesh topology with up to 15 specialized agents
- Data Collector → Pattern Analyzer → Processor Swarm (8 agents) → Validator Consensus (3 agents) → Report Generator
- Consensus-based coordination with human handoff for high-uncertainty cases

**Data Collection (`/data-collectors/`)**
- Web scraping with anti-detection measures (2-5 second delays, user agent rotation)
- Session limits (max 50 requests) for responsible scraping
- Async processing with Playwright

**Primitives (`/primitives/`)**
- Domain-specific processing logic
- Current implementation: Lackawanna County property tax appeals
- Designed for universal adaptation to different organization types

### Data Flow Architecture

1. **Data Collector Agent**: Gathers workflow data via web scraping, APIs, or file processing
2. **Pattern Analyzer Agent**: Identifies workflow patterns and bottlenecks  
3. **Processor Swarm**: 8 agents process backlog items in parallel
4. **Validator Consensus**: 3 agents validate results through cross-checking
5. **Report Generator**: Creates partial reports (free samples) and complete reports (paid)

### Business Model Integration

The platform implements a "Done Deal" approach:
- Process backlogs before payment
- Generate partial reports as teasers with samples and statistics
- Deliver complete reports with full recommendations upon payment

## Key Files and Their Purpose

- `claude-flow/swarm-config.yml` - Agent swarm orchestration configuration
- `data-collectors/web-scraper.py` - Safe web scraping with anti-detection
- `primitives/lackawanna-appeals/primitive.py` - Domain-specific processing logic
- `demos/lackawanna-demo.py` - Demonstration workflow for property tax appeals
- `requirements.txt` - Python dependencies (Playwright, Pandas, Requests, BeautifulSoup4, Pydantic)
- `package.json` - Node.js dependencies (Playwright, Puppeteer)

## Development Notes

### Current Status
- Framework structure is in place but components need full implementation
- Demo scripts are placeholders requiring completion
- No integration between Python and Node.js components yet

### Next Implementation Priorities
1. Complete Lackawanna data collection implementation
2. Process first 10 appeals as proof of concept
3. Generate sample partial report
4. Build complete processing pipeline
5. Create universal adaptation framework

### Code Patterns
- Use async/await for all I/O operations
- Implement conservative rate limiting for web scraping (2-5 second delays)
- Follow consensus-based validation patterns for critical decisions
- Structure code as pluggable primitives for different domains