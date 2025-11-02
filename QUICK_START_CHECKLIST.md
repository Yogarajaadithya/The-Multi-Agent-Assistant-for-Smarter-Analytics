# 🚀 Quick Start Checklist

## Pre-Flight Checks

### 1. Verify Prerequisites
- [ ] LM Studio is installed and running
- [ ] IBM Granite 3.2 8B model is loaded in LM Studio
- [ ] LM Studio API server is running on port 1234
- [ ] PostgreSQL is running
- [ ] Database `hr_data` exists with `employee_attrition` table
- [ ] Python environment is set up for backend
- [ ] Node.js is installed for frontend

---

## Start the System

### 2. Start Backend (Terminal 1)
```powershell
cd d:\Capstone_Prj\The-Multi-Agent-Assistant-for-Smarter-Analytics\backend-repo
uvicorn app.main:app --reload --port 8000
```

**Wait for:**
```
✅ Multi-Agent System initialized successfully!
   - Planner Agent (Question Router)
   - Text-to-SQL + Visualization Agents
   - Hypothesis + Statistical Testing Agents
```

- [ ] Backend started successfully
- [ ] No errors in console
- [ ] Health check works: http://localhost:8000/health

---

### 3. Start Frontend (Terminal 2)
```powershell
cd d:\Capstone_Prj\The-Multi-Agent-Assistant-for-Smarter-Analytics\frontend-repo
npm run dev
```

**Wait for:**
```
➜  Local:   http://localhost:5174/
```

- [ ] Frontend started successfully
- [ ] Can access: http://localhost:5174
- [ ] Page shows "HR Analytics Assistant"

---

## Test the Integration

### 4. Test WHAT Question (Descriptive Analytics)

**In browser at http://localhost:5174:**

1. [ ] Click example prompt: "What is the attrition rate by department?"
2. [ ] Click "Send" button
3. [ ] Wait 3-5 seconds for response

**Verify:**
- [ ] Message shows: "📊 Question Type: WHAT (Descriptive Analytics)"
- [ ] SQL query appears in code block
- [ ] Data table shows 3 rows
- [ ] Bar chart displays correctly
- [ ] No errors in browser console (F12)

**Browser Console Should Show:**
```
Sending analytics query to: http://127.0.0.1:8000/api/analyze
Query: What is the attrition rate by department?
Response status: 200
Question type detected: WHAT
```

---

### 5. Test WHY Question (Causal Analytics)

**In browser:**

1. [ ] Click example prompt: "Why do employees leave the company?"
2. [ ] Click "Send" button
3. [ ] Wait 5-10 seconds for response

**Verify:**
- [ ] Message shows: "📊 Question Type: WHY (Causal Analytics)"
- [ ] 3 hypothesis cards appear
- [ ] 3 statistical test result cards appear
- [ ] Green badges show on significant results (p < 0.05)
- [ ] Effect sizes are displayed (χ², Cohen's d, etc.)
- [ ] Interpretations are shown
- [ ] No errors in browser console

**Browser Console Should Show:**
```
Sending analytics query to: http://127.0.0.1:8000/api/analyze
Query: Why do employees leave the company?
Response status: 200
Question type detected: WHY
```

---

### 6. Run Automated Tests (Terminal 3)

```powershell
cd d:\Capstone_Prj\The-Multi-Agent-Assistant-for-Smarter-Analytics
python test_frontend_backend_sync.py
```

**Verify:**
- [ ] ✅ Backend is healthy
- [ ] ✅ WHAT question processed correctly
- [ ] ✅ WHY question processed correctly
- [ ] ✅ Planner Classification accuracy
- [ ] ✅ Frontend is accessible
- [ ] Results: 5/5 tests passed

---

## Final Verification

### 7. Check All Components

**Backend Console:**
- [ ] No error messages
- [ ] Shows successful query processing logs

**Frontend:**
- [ ] Title: "HR Analytics Assistant"
- [ ] Subtitle: "Ask WHAT questions for insights or WHY questions for causal analysis"
- [ ] 5 example prompts visible
- [ ] Placeholder text: "Ask: What is attrition by dept? or Why do employees leave?"

**Browser Console (F12):**
- [ ] No CORS errors
- [ ] No JavaScript errors
- [ ] Shows "Question type detected" logs

---

## Try Additional Questions

### 8. Test More Examples

**WHAT Questions:**
- [ ] "What is the average monthly income by job role?"
- [ ] "Show me the distribution of years at company"
- [ ] "How many employees are in each department?"

**WHY Questions:**
- [ ] "Why is attrition higher in Sales department?"
- [ ] "What causes employee turnover?"
- [ ] "Explain the relationship between overtime and attrition"

**Custom Questions:**
- [ ] Create your own WHAT question
- [ ] Create your own WHY question

---

## Troubleshooting

### If Backend Won't Start:
- [ ] Check LM Studio is running
- [ ] Check PostgreSQL is accessible
- [ ] Verify environment variables are set
- [ ] Check backend console for specific error
- [ ] Try: `pip install -r backend-repo/requirements.txt`

### If Frontend Won't Start:
- [ ] Check Node.js is installed
- [ ] Try: `cd frontend-repo && npm install`
- [ ] Check for port conflicts on 5174
- [ ] Check frontend console for specific error

### If Questions Fail:
- [ ] Verify backend is running (health check)
- [ ] Check LM Studio API is accessible (http://127.0.0.1:1234)
- [ ] Check PostgreSQL database has data
- [ ] Review browser Network tab (F12) for API errors
- [ ] Check backend console for error details

### If No Visualization:
- [ ] Check response has `visualization.success === true`
- [ ] Verify Plotly is installed: `npm list react-plotly.js`
- [ ] Check browser console for JavaScript errors

---

## Success Indicators

### ✅ Everything is working if:

1. **Backend:**
   - [x] Starts with "Multi-Agent System initialized successfully!"
   - [x] No errors in console
   - [x] Health endpoint responds

2. **Frontend:**
   - [x] Loads at http://localhost:5174
   - [x] Shows updated UI with HR examples
   - [x] Example prompts work

3. **WHAT Questions:**
   - [x] Display SQL queries
   - [x] Show data tables
   - [x] Render charts
   - [x] Message shows "WHAT (Descriptive Analytics)"

4. **WHY Questions:**
   - [x] Display hypothesis cards
   - [x] Show statistical test results
   - [x] Green badges on significant results
   - [x] Message shows "WHY (Causal Analytics)"

5. **Console Logs:**
   - [x] Browser shows "Question type detected"
   - [x] Backend shows query processing logs
   - [x] No CORS or network errors

6. **Tests:**
   - [x] All 5 automated tests pass

---

## Next Steps

Once everything works:

- [ ] Explore different question types
- [ ] Experiment with complex queries
- [ ] Review statistical significance patterns
- [ ] Check visualization rendering
- [ ] Test edge cases and error handling

---

## Documentation Reference

| Document | Purpose |
|----------|---------|
| `SYNC_SUMMARY.md` | This checklist + visual summary |
| `README_INTEGRATION.md` | Complete integration guide |
| `FRONTEND_BACKEND_SYNC.md` | Visual flow diagrams |
| `frontend-repo/INTEGRATION_SUMMARY.md` | Frontend specifics |
| `backend-repo/ARCHITECTURE.md` | System architecture |

---

## Support

**If you encounter issues:**

1. Check the relevant documentation file above
2. Review console logs (backend and browser)
3. Check Network tab (F12) for API details
4. Verify all prerequisites are met
5. Run automated tests for diagnostic info

---

**🎉 You're ready to go! Start from Step 2 and work through the checklist.**
