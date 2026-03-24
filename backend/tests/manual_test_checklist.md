# Manual Testing Checklist - POLE NL-to-Cypher QA System

> **Purpose**: Comprehensive manual test scenarios to verify system functionality, accuracy, and user experience.

---

## Setup Prerequisites

- [ ] Backend running on `http://localhost:8000`
- [ ] Frontend running on `http://localhost:3000`
- [ ] Neo4j database accessible and populated with POLE data
- [ ] LLM API key configured (Groq/OpenAI/Anthropic/Gemini)
- [ ] Browser DevTools open for debugging (Console + Network tabs)

---

## 1. System Health Checks

### 1.1 Backend Health
- [ ] Visit `http://localhost:8000/api/health`
- [ ] Verify response contains `status: "healthy"`
- [ ] Check Neo4j connection status
- [ ] Check LLM provider status

### 1.2 Schema Introspection
- [ ] Visit `http://localhost:8000/api/schema`
- [ ] Verify all 11 node labels are listed (Person, Crime, Location, Vehicle, Object, Officer, Phone, PhoneCall, Email, PostCode, AREA)
- [ ] Verify all 17 relationship types are present
- [ ] Check that property values are displayed for categorical fields

### 1.3 Few-Shot Examples
- [ ] Visit `http://localhost:8000/api/examples`
- [ ] Verify 24 example question-Cypher pairs are returned
- [ ] Check examples cover all query types (basic, relationships, multi-hop, aggregations)

---

## 2. Basic Query Tests

### 2.1 Simple Count Queries
**Test 1: Total Crime Count**
- [ ] Question: "How many crimes are recorded?"
- [ ] Expected: Returns count > 0
- [ ] Verify: Cypher uses `count(c)`
- [ ] Verify: Answer is in natural language (e.g., "There are X crimes recorded")

**Test 2: Node Type Counts**
- [ ] Question: "How many people are in the database?"
- [ ] Expected: Returns count of Person nodes
- [ ] Verify: Query targets `Person` label

**Test 3: Count with Filter**
- [ ] Question: "How many drug crimes are there?"
- [ ] Expected: Returns count where Crime.type contains 'drug'
- [ ] Verify: Uses `toLower()` and `CONTAINS` for matching

### 2.2 Distinct Value Queries
**Test 4: Crime Types**
- [ ] Question: "What are the different types of crimes?"
- [ ] Expected: Returns list of distinct crime types
- [ ] Verify: Uses `DISTINCT` in Cypher
- [ ] Verify: Results displayed as a list in UI

**Test 5: Officer Ranks**
- [ ] Question: "What ranks do officers have?"
- [ ] Expected: Returns distinct ranks (Constable, Sergeant, Inspector, etc.)

---

## 3. Relationship-Based Queries

### 3.1 Single-Hop Relationships
**Test 6: People Involved in Crimes**
- [ ] Question: "Who are the people involved in crimes?"
- [ ] Expected: Returns Person nodes connected via PARTY_TO to Crime nodes
- [ ] Verify: Shows person names and crime types
- [ ] Verify: Results > 0

**Test 7: Crime Locations**
- [ ] Question: "Where do crimes occur?"
- [ ] Expected: Returns Crime → OCCURRED_AT → Location
- [ ] Verify: Shows addresses/postcodes

**Test 8: Officer Assignments**
- [ ] Question: "Which crimes are investigated by officers?"
- [ ] Expected: Returns Crime → INVESTIGATED_BY → Officer
- [ ] Verify: Shows officer names and ranks

**Test 9: Vehicles in Crimes**
- [ ] Question: "Which vehicles are linked to crimes?"
- [ ] Expected: Returns Vehicle → INVOLVED_IN → Crime
- [ ] Verify: Shows vehicle make, model, registration

### 3.2 Multi-Hop Queries
**Test 10: Person-Crime-Area**
- [ ] Question: "Find people involved in crimes in each area"
- [ ] Expected: Returns Person → PARTY_TO → Crime → OCCURRED_AT → Location → LOCATION_IN_AREA → AREA
- [ ] Verify: Shows person names, crime types, area codes

**Test 11: Filtered Multi-Hop**
- [ ] Question: "Find people involved in drug crimes in area WN"
- [ ] Expected: Filters by crime type AND area code
- [ ] Verify: Uses `toLower()` and `CONTAINS` for both filters
- [ ] Verify: Only returns WN area results

**Test 12: Vehicle-Crime-Area**
- [ ] Question: "Find vehicles used in crimes in specific areas"
- [ ] Expected: Returns Vehicle → INVOLVED_IN → Crime → Location → AREA
- [ ] Verify: Shows vehicle details and area codes

---

## 4. Network/Graph Queries

### 4.1 Social Network
**Test 13: Knows Relationships**
- [ ] Question: "Find people who know criminals"
- [ ] Expected: Returns Person → KNOWS → Person → PARTY_TO → Crime
- [ ] Verify: Shows both person names and criminal activities

**Test 14: Family Relationships**
- [ ] Question: "Find family members of people involved in crimes"
- [ ] Expected: Returns Person → FAMILY_REL → Person → PARTY_TO → Crime
- [ ] Verify: Shows relationship type (rel_type property)

**Test 15: Multiple Relationship Types**
- [ ] Question: "Find people connected to criminals via multiple relationships"
- [ ] Expected: Uses `KNOWS|KNOWS_LW|KNOWS_SN` relationship pattern
- [ ] Verify: Returns connections through any of these relationships

### 4.2 Communication Networks
**Test 16: Phone Contacts**
- [ ] Question: "Find phone numbers of people involved in crimes"
- [ ] Expected: Returns Person → HAS_PHONE → Phone where Person → PARTY_TO → Crime
- [ ] Verify: Shows person names and phone numbers

**Test 17: Phone Calls Made**
- [ ] Question: "Find calls made by phones"
- [ ] Expected: Returns PhoneCall → CALLER → Phone
- [ ] Verify: Shows call times and durations

**Test 18: Communication Between Phones**
- [ ] Question: "Find communication between two phones"
- [ ] Expected: Returns PhoneCall with both CALLER and CALLED relationships
- [ ] Verify: Shows caller, receiver, and call metadata

---

## 5. Aggregation Queries

### 5.1 Group By and Count
**Test 19: Area Crime Count**
- [ ] Question: "Which area has the highest number of crimes?"
- [ ] Expected: Groups by area, counts crimes, orders descending, limits to 1
- [ ] Verify: Uses `count()`, `ORDER BY DESC`, `LIMIT 1`
- [ ] Verify: Returns single area with highest count

**Test 20: Officer Workload**
- [ ] Question: "Which officer investigates the most crimes?"
- [ ] Expected: Groups by officer, counts cases, orders descending
- [ ] Verify: Returns officer name and case count

**Test 21: Crime Type Distribution**
- [ ] Question: "How many crimes of each type are there?"
- [ ] Expected: Groups by crime type, counts each
- [ ] Verify: Returns all crime types with counts

### 5.2 Statistical Aggregations
**Test 22: Average Call Duration**
- [ ] Question: "Average duration of phone calls"
- [ ] Expected: Uses `avg(pc.call_duration)`
- [ ] Verify: Returns numeric average

---

## 6. Filtering and Search

### 6.1 String Matching
**Test 23: Partial Match**
- [ ] Question: "Show all crimes related to drugs"
- [ ] Expected: Uses `toLower(c.type) CONTAINS 'drug'`
- [ ] Verify: Returns crimes with 'Drug', 'Drugs', 'drug-related', etc.

**Test 24: Exact Property Match**
- [ ] Question: "Find crimes where no suspect was identified"
- [ ] Expected: Filters by `last_outcome` containing 'no suspect'
- [ ] Verify: Only returns crimes with that outcome

**Test 25: Multiple Filters**
- [ ] Question: "Find burglary crimes investigated by Sergeants"
- [ ] Expected: Filters by crime type AND officer rank
- [ ] Verify: Both conditions applied correctly

### 6.2 Null/Empty Checks
**Test 26: Has Property**
- [ ] Question: "Find crimes that resulted in a charge"
- [ ] Expected: Uses `c.charge IS NOT NULL AND c.charge <> ''`
- [ ] Verify: Only returns crimes with charges

---

## 7. Error Handling and Recovery

### 7.1 Empty Results
**Test 27: No Results Found**
- [ ] Question: "Find people named Zzzzzzzzz" (non-existent name)
- [ ] Expected: System attempts retry (up to 3 times)
- [ ] Verify: `attempts` field shows retry count
- [ ] Verify: Final answer states "No results found" with helpful message

**Test 28: Invalid Filter Values**
- [ ] Question: "Find crimes in year 9999"
- [ ] Expected: Returns empty results gracefully
- [ ] Verify: Suggests rephrasing the question

### 7.2 Ambiguous Questions
**Test 29: Unclear Intent**
- [ ] Question: "Show me stuff"
- [ ] Expected: System generates best-effort query
- [ ] Verify: Returns some results OR asks for clarification

**Test 30: Multiple Interpretations**
- [ ] Question: "Find John"
- [ ] Expected: Searches Person nodes for name 'John'
- [ ] Verify: Returns multiple Johns if present

### 7.3 Syntax Error Recovery
**Test 31: Self-Correction**
- [ ] Monitor backend logs for "attempt 2" or "attempt 3"
- [ ] Verify: System logs show error context being fed back to LLM
- [ ] Verify: Final query executes successfully

---

## 8. Performance Tests

### 8.1 Response Times
**Test 32: Simple Query Speed**
- [ ] Question: "How many crimes?"
- [ ] Expected: Response time < 2 seconds
- [ ] Verify: `execution_time_ms` in response

**Test 33: Complex Query Speed**
- [ ] Question: "Find people connected to drug crimes in area WN through family members"
- [ ] Expected: Response time < 5 seconds
- [ ] Verify: Multi-hop query completes within timeout

### 8.2 Concurrent Requests
**Test 34: Multiple Questions in Parallel**
- [ ] Open multiple browser tabs
- [ ] Submit different questions simultaneously
- [ ] Verify: All requests complete successfully
- [ ] Verify: No timeout or connection errors

---

## 9. Graph Visualization (Frontend)

### 9.1 Graph Display
**Test 35: Graph Rendering**
- [ ] Question: "Find people involved in crimes"
- [ ] Expected: Graph visualization appears
- [ ] Verify: Nodes colored by type (Person, Crime, etc.)
- [ ] Verify: Edges show relationship types

**Test 36: Interactive Graph**
- [ ] Click on a node
- [ ] Verify: Node highlights or shows details
- [ ] Try zoom in/out
- [ ] Try panning the graph

**Test 37: Empty Graph Handling**
- [ ] Submit query that returns no graph data
- [ ] Verify: Graph panel shows "No graph data" message

---

## 10. User Experience

### 10.1 UI Responsiveness
**Test 38: Loading States**
- [ ] Submit a question
- [ ] Verify: Loading spinner or indicator appears
- [ ] Verify: Submit button is disabled during processing

**Test 39: Error Display**
- [ ] Stop backend server
- [ ] Submit a question
- [ ] Verify: Error message displayed clearly
- [ ] Verify: Error suggests checking connection

### 10.2 Results Presentation
**Test 40: Answer Formatting**
- [ ] Verify: Natural language answer appears prominently
- [ ] Verify: Cypher query is collapsible/expandable
- [ ] Verify: Results table is readable and formatted

**Test 41: Example Questions**
- [ ] Click on an example question
- [ ] Verify: Question populates input field
- [ ] Verify: Can edit before submitting

**Test 42: Copy Cypher Button**
- [ ] Submit a question
- [ ] Click "Copy Cypher" button
- [ ] Verify: Query copied to clipboard
- [ ] Verify: Confirmation feedback shown

---

## 11. Cross-Browser Testing

### 11.1 Browser Compatibility
- [ ] Test in Chrome/Edge
- [ ] Test in Firefox
- [ ] Test in Safari (if available)
- [ ] Verify: UI renders correctly in all browsers
- [ ] Verify: All features work consistently

### 11.2 Responsive Design
- [ ] Test on desktop (1920x1080)
- [ ] Test on laptop (1366x768)
- [ ] Test on tablet view (768px width)
- [ ] Test on mobile view (375px width)
- [ ] Verify: Layout adapts appropriately

---

## 12. API Endpoint Testing (Direct)

### 12.1 POST /api/ask
**Test 43: Valid Request**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How many crimes?"}'
```
- [ ] Verify: Returns JSON with answer, cypher, results, attempts

**Test 44: Invalid Request**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{}'
```
- [ ] Verify: Returns 422 validation error

### 12.2 GET Endpoints
**Test 45: Schema Endpoint**
```bash
curl http://localhost:8000/api/schema
```
- [ ] Verify: Returns schema text

**Test 46: Examples Endpoint**
```bash
curl http://localhost:8000/api/examples
```
- [ ] Verify: Returns array of examples

**Test 47: Health Endpoint**
```bash
curl http://localhost:8000/api/health
```
- [ ] Verify: Returns health status

---

## 13. Edge Cases

### 13.1 Special Characters
**Test 48: Quotes in Question**
- [ ] Question: "Find crimes with 'drugs' in description"
- [ ] Verify: Handles single quotes correctly

**Test 49: Unicode Characters**
- [ ] Question: "Find person named François"
- [ ] Verify: Handles accented characters

### 13.2 Very Long Questions
**Test 50: Long Question**
- [ ] Question: (300+ word question about finding complex patterns)
- [ ] Verify: System processes without truncation errors

### 13.3 Rapid Repeated Queries
**Test 51: Same Question Repeated**
- [ ] Submit same question 5 times rapidly
- [ ] Verify: All requests complete successfully
- [ ] Verify: Results are consistent

---

## 14. LLM Provider Testing

### 14.1 Multiple Provider Support
**Test 52: Groq (LLaMA 3.3)**
- [ ] Set `GROQ_API_KEY` in .env
- [ ] Remove other API keys
- [ ] Submit test questions
- [ ] Verify: System uses Groq

**Test 53: OpenAI (GPT-4o)**
- [ ] Set `OPENAI_API_KEY` in .env
- [ ] Submit test questions
- [ ] Verify: System uses OpenAI

**Test 54: Anthropic (Claude)**
- [ ] Set `ANTHROPIC_API_KEY` in .env
- [ ] Submit test questions
- [ ] Verify: System uses Claude

**Test 55: Google (Gemini)**
- [ ] Set `GOOGLE_API_KEY` in .env
- [ ] Submit test questions
- [ ] Verify: System uses Gemini

---

## 15. Data Consistency

### 15.1 Result Verification
**Test 56: Cross-Check Results**
- [ ] Question: "How many crimes are recorded?"
- [ ] Note the count
- [ ] Run equivalent raw Cypher in Neo4j Browser: `MATCH (c:Crime) RETURN count(c)`
- [ ] Verify: Counts match

**Test 57: Relationship Verification**
- [ ] Question: "Who is John Smith party to?"
- [ ] Run raw Cypher: `MATCH (p:Person {name: 'John', surname: 'Smith'})-[:PARTY_TO]->(c:Crime) RETURN c`
- [ ] Verify: Results match

---

## Success Criteria Summary

### Must Pass (Critical)
- [ ] All 24 few-shot example questions return correct results (Tests vary)
- [ ] Retry mechanism works on syntax errors (Test 31)
- [ ] Empty results handled gracefully (Tests 27-28)
- [ ] Multi-hop queries execute correctly (Tests 10-12)
- [ ] Graph visualization displays (Tests 35-37)
- [ ] API endpoints respond correctly (Tests 43-47)

### Should Pass (Important)
- [ ] At least 90% of manual test cases pass
- [ ] Response times meet targets (Tests 32-33)
- [ ] Cross-browser compatibility verified (Test 11.1)
- [ ] Error messages are user-friendly
- [ ] UI is intuitive and responsive

### Nice to Have (Enhancements)
- [ ] All edge cases handled gracefully
- [ ] All LLM providers tested and working
- [ ] Mobile experience is smooth
- [ ] Performance under load is acceptable

---

## Testing Workflow

1. **Start System**: Backend → Frontend → Neo4j
2. **Health Check**: Run section 1 tests
3. **Core Functionality**: Run sections 2-6 tests
4. **Error Handling**: Run section 7 tests
5. **UI/UX**: Run sections 9-10 tests
6. **Advanced**: Run sections 11-15 tests
7. **Document Issues**: Note any failures or unexpected behavior
8. **Retest Fixes**: Re-run failed tests after fixes

---

## Issue Template

When you find a bug, document it:

```
**Test Number**: Test X
**Question**: "..."
**Expected**: ...
**Actual**: ...
**Cypher Generated**: ...
**Error Message**: ...
**Attempts**: X
**Screenshots**: (if applicable)
**Reproducible**: Yes/No
**Severity**: Critical/High/Medium/Low
```

---

## Notes
- Test with a populated database (at least 100 nodes across different types)
- Clear browser cache if experiencing issues
- Check backend logs for detailed error messages
- Some tests may need adjustments based on actual data in your Neo4j database
- Document any questions that consistently fail for LLM prompt refinement
