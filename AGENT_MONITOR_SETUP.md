# Agent Monitor Implementation Guide

## Quick Start

This guide helps you implement the enhanced Agent Activity Monitor in your application.

## 📋 Prerequisites

- Frontend: React + TypeScript
- Backend: Python FastAPI
- Node.js and npm installed
- Python 3.8+ installed

## 🚀 Installation Steps

### Step 1: Frontend Updates

The frontend components have already been updated with the new features. No additional installation needed.

#### Updated Files:
- ✅ `frontend-repo/src/components/AgentActivityPopup.tsx`
- ✅ `frontend-repo/src/styles.css` (animations already present)

### Step 2: Backend Setup

#### Install Required Packages

```bash
cd backend-repo
pip install python-dotenv
```

#### Add New Logging Utility

The enhanced logging utility has been created at:
- ✅ `backend-repo/app/utils/logger.py`

### Step 3: Integrate Logging into Existing Agents

#### Option A: Quick Integration (Recommended)

Add logging to your existing agents by importing the logger:

```python
# In any agent file (e.g., planner_agent.py)
from app.utils.logger import get_agent_logger

# At the top of your agent function
logger = get_agent_logger("Planner")  # or "Text-to-SQL", "Visualization", etc.

# Add logging throughout your agent
logger.info("Starting analysis...")
logger.success("Analysis complete", duration=1500)
logger.error("Analysis failed", error=exception)
```

#### Option B: Full Integration (Best Practice)

Replace the `process_question` function in `multi_agent_system.py` with the enhanced version from `logging_integration_example.py`.

### Step 4: Update API Endpoints

Update your FastAPI endpoint to return logs:

```python
# In backend-repo/app/api/routes.py
from app.utils.logger import get_all_logs, system_logger

@router.post("/query")
async def process_query(request: QueryRequest):
    # Clear previous logs
    system_logger.clear_all_logs()
    
    # Process question
    result = await process_question(
        question=request.question,
        # ... other params
    )
    
    # Add logs to response
    result["logs"] = get_all_logs()
    
    return result
```

### Step 5: Test the Integration

1. Start the backend:
```bash
cd backend-repo
uvicorn app.main:app --reload
```

2. Start the frontend:
```bash
cd frontend-repo
npm run dev
```

3. Open the application and submit a query
4. Click the Agent Activity Monitor button
5. Verify logs appear with proper formatting

## 🔧 Configuration Options

### Backend Configuration

#### Customize Log Levels

```python
# In logger.py or your config
import logging

# Set global log level
logging.basicConfig(level=logging.DEBUG)  # Show all logs

# Or per-agent
logger = get_agent_logger("MyAgent")
logger.logger.setLevel(logging.WARNING)  # Only warnings and errors
```

#### Add Custom Log Levels

```python
# In your agent code
logger = get_agent_logger("CustomAgent")

# Use existing levels
logger.info("Information")
logger.success("Success with timing", duration=1000)
logger.warning("Warning message")
logger.error("Error occurred", error=exception)
logger.critical("Critical failure", error=exception)
logger.debug("Debug information")
```

### Frontend Configuration

#### Customize Colors

Edit `frontend-repo/src/components/AgentActivityPopup.tsx`:

```typescript
const getLogColor = (level: string) => {
  switch (level.toLowerCase()) {
    case 'info':
      return 'text-blue-400';  // Change color here
    // ... other cases
  }
};
```

#### Change Default View Settings

```typescript
// In AgentActivityPopup.tsx
const [showStats, setShowStats] = useState(true);  // Stats visible by default
const [groupByAgent, setGroupByAgent] = useState(false);  // Timeline view by default
const [showTimings, setShowTimings] = useState(true);  // Timings visible by default
```

## 📝 Usage Examples

### Example 1: Basic Logging

```python
from app.utils.logger import get_agent_logger

async def my_agent_function(question: str, llm):
    logger = get_agent_logger("MyAgent")
    
    logger.info(f"Processing question: {question}")
    
    try:
        # Your agent logic here
        result = await some_processing(question, llm)
        
        logger.success("Processing complete")
        return result
    
    except Exception as e:
        logger.error("Processing failed", error=e)
        raise
```

### Example 2: Timed Operations

```python
from app.utils.logger import get_agent_logger

logger = get_agent_logger("DatabaseAgent")

# Using decorator
@logger.timed_operation("Database Query")
def query_database(connection, sql):
    cursor = connection.cursor()
    cursor.execute(sql)
    return cursor.fetchall()

# Manual timing
def manual_timing_example():
    logger.start_timer()
    # ... do work ...
    duration = logger.stop_timer()
    logger.success("Operation complete", duration=duration)
```

### Example 3: Error Handling with Details

```python
from app.utils.logger import get_agent_logger

logger = get_agent_logger("ValidationAgent")

try:
    validate_data(data)
    logger.success("Validation passed")
except ValueError as e:
    logger.error(
        "Validation failed",
        error=e,
        include_trace=True  # Include full stack trace
    )
except Exception as e:
    logger.critical(
        "Unexpected validation error",
        error=e,
        include_trace=True
    )
```

### Example 4: Multi-Step Process Logging

```python
from app.utils.logger import get_agent_logger

async def multi_step_process(question: str):
    logger = get_agent_logger("Orchestrator")
    
    logger.info("Starting multi-step process")
    
    # Step 1
    logger.info("Step 1: Data collection")
    logger.start_timer()
    data = await collect_data()
    duration1 = logger.stop_timer()
    logger.success("Data collected", duration=duration1)
    
    # Step 2
    logger.info("Step 2: Data processing")
    logger.start_timer()
    processed = await process_data(data)
    duration2 = logger.stop_timer()
    logger.success("Data processed", duration=duration2)
    
    # Step 3
    logger.info("Step 3: Result generation")
    logger.start_timer()
    result = await generate_result(processed)
    duration3 = logger.stop_timer()
    logger.success("Result generated", duration=duration3)
    
    total_duration = duration1 + duration2 + duration3
    logger.info(f"Total process time: {total_duration/1000:.2f}s")
    
    return result
```

## 🐛 Troubleshooting

### Issue: Logs not appearing in frontend

**Solution:**
1. Check if backend is returning logs in response:
   ```python
   result["logs"] = get_all_logs()
   ```

2. Verify frontend is receiving logs:
   ```typescript
   console.log("Received logs:", response.logs);
   ```

3. Check API endpoint is being called correctly

### Issue: Timing information not showing

**Solution:**
1. Ensure duration is being passed:
   ```python
   logger.success("Done", duration=duration)
   ```

2. Check `showTimings` state in frontend:
   ```typescript
   const [showTimings, setShowTimings] = useState(true);
   ```

### Issue: Error details not expanding

**Solution:**
1. Verify error has `details` or `stackTrace`:
   ```python
   logger.error("Failed", error=e, include_trace=True)
   ```

2. Check log level is "ERROR" or "CRITICAL"

### Issue: Performance issues with many logs

**Solution:**
1. Clear logs between queries:
   ```python
   system_logger.clear_all_logs()
   ```

2. Limit log retention (configure max logs)

3. Use filters to reduce visible logs

## 📊 Performance Considerations

### Backend Optimization

1. **Clear old logs**: Clear logs between queries to prevent memory buildup
   ```python
   system_logger.clear_all_logs()
   ```

2. **Limit log detail**: Don't include stack traces for non-critical errors
   ```python
   logger.error("Minor error", error=e, include_trace=False)
   ```

3. **Batch logging**: Group related logs together

### Frontend Optimization

1. **Virtual scrolling**: For very large log lists (future enhancement)
2. **Pagination**: Limit visible logs to recent entries
3. **Lazy loading**: Load older logs on demand

## 🔒 Security Considerations

1. **Sanitize sensitive data**: Don't log passwords, API keys, or personal data
   ```python
   # ❌ Bad
   logger.info(f"User logged in with password: {password}")
   
   # ✅ Good
   logger.info(f"User logged in: {username}")
   ```

2. **Limit stack traces in production**: Set `include_trace=False` for production

3. **Validate log data**: Sanitize log messages before display

## 📚 Additional Resources

- [AGENT_MONITOR_IMPROVEMENTS.md](./AGENT_MONITOR_IMPROVEMENTS.md) - Full documentation
- [logging_integration_example.py](./backend-repo/app/utils/logging_integration_example.py) - Integration examples
- [logger.py](./backend-repo/app/utils/logger.py) - Logger implementation

## 🎯 Next Steps

1. ✅ Review this implementation guide
2. ✅ Update your agents with logging
3. ✅ Test the monitor with sample queries
4. ✅ Configure colors and display options
5. ✅ Deploy and monitor in production

## 💡 Tips

- Start with basic logging (`info`, `success`, `error`)
- Add timing for performance-critical operations
- Use `warning` for non-critical issues
- Reserve `critical` for severe failures
- Group related logs under same agent name
- Use descriptive agent names (e.g., "Text-to-SQL" not "SQL")

## 📞 Support

For questions or issues:
1. Check troubleshooting section
2. Review example code
3. Inspect browser console for errors
4. Verify backend logs

---

**Version**: 1.0  
**Last Updated**: December 30, 2025  
**Author**: GitHub Copilot
