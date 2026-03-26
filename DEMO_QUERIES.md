# Demo Queries for Investigation Case Studies

This document contains ready-to-use queries for demonstrating the POLE NL-to-Cypher QA System during presentations. Copy and paste these queries into the system to walk through the investigation scenarios.

---

## Case Study 1: Robbery Ring Investigation

### Query 1: Identify All Robberies
```
Show me all robbery crimes in August 2017
```
**Expected Output:** List of robbery-type crimes with dates, locations, and outcomes
**Demo Point:** "Notice how quickly we get a complete picture of all robbery incidents."

---

### Query 2: Find Suspects
```
Who are the people involved in robbery crimes?
```
**Expected Output:** Names of persons connected to robbery incidents
**Demo Point:** "Now we can see exactly who our suspects are—something that would require hours of report cross-referencing."

---

### Query 3: Map Criminal Networks
```
Show me all people who know each other and are involved in robberies
```
**Expected Output:** Graph visualization of connected suspects
**Demo Point:** "This is where it gets powerful—we can see the entire network. Notice the central nodes? Those are our ring leaders."

---

### Query 4: Analyze Communications
```
What phone numbers are associated with people involved in robbery crimes?
```
**Expected Output:** Phone numbers linked to robbery suspects
**Demo Point:** "Communication patterns help us understand coordination. We can now request call records for these specific numbers."

---

### Query 5: Find Locations
```
What are the addresses of people involved in robberies?
```
**Expected Output:** Current addresses of robbery suspects
**Demo Point:** "Geographic clustering tells us where to focus surveillance. See how several suspects live in the same postcode?"

---

### Query 6: Review Investigation Status
```
Which officers are investigating robbery cases?
```
**Expected Output:** Officers assigned to robbery investigations
**Demo Point:** "We can now coordinate teams working on related cases—improving efficiency and information sharing."

---

## Case Study 2: Violence and Public Order Investigation

### Query 1: Assess Crime Volume
```
How many violence and sexual offences occurred in August 2017?
```
**Expected Output:** Count and list of violence crimes
**Demo Point:** "First, we assess the scale. This immediately tells us if we're dealing with a surge or normal patterns."

---

### Query 2: Geographic Analysis
```
Show me locations where violence and sexual offences occurred
```
**Expected Output:** Crime locations with addresses and postcodes
**Demo Point:** "Hotspot analysis reveals where to increase patrols. See the clustering? That's not random."

---

### Query 3: Find Repeat Offenders
```
Who are the people involved in multiple violence crimes?
```
**Expected Output:** Individuals connected to multiple violence incidents
**Demo Point:** "Targeting repeat offenders has the biggest impact. These are our high-priority targets."

---

### Query 4: Expand Social Networks
```
Show me people who know someone involved in violence crimes
```
**Expected Output:** Extended network of associates
**Demo Point:** "We can map the entire social network—identifying potential accomplices and witnesses."

---

### Query 5: Cross-Crime Analysis
```
Show me people involved in both violence crimes and burglary
```
**Expected Output:** Individuals connected to multiple crime types
**Demo Point:** "Cross-crime analysis reveals organized criminal activity. These aren't isolated incidents."

---

### Query 6: Contact Information for Witnesses
```
What are the phone numbers of people involved in violence crimes?
```
**Expected Output:** Phone numbers of involved persons
**Demo Point:** "We can quickly reach out to witnesses and victims for follow-up investigations."

---

### Query 7: Identify Stalled Cases
```
Show me violence crimes where the outcome is unable to prosecute suspect
```
**Expected Output:** Cases with prosecution difficulties
**Demo Point:** "This tells us where we need enhanced evidence gathering or witness protection."

---

## Additional Powerful Queries

### Network Discovery
```
Show me all people who know Todd Hamilton
```
**Expected Output:** Network of associates for a specific person
**Demo Point:** "We can instantly map anyone's social network—invaluable for gang investigations."

---

### Location-Based Investigation
```
Show me all crimes that occurred at locations in the OL11 postcode area
```
**Expected Output:** Crimes in specific geographic area
**Demo Point:** "Focus on specific neighborhoods to identify territorial patterns."

---

### Vehicle Tracking
```
What vehicles are associated with people involved in crimes?
```
**Expected Output:** Vehicles linked to suspects
**Demo Point:** "Vehicle data links suspects to crime scenes—key evidence for prosecution."

---

### Officer Workload Analysis
```
Which officer is investigating the most cases?
```
**Expected Output:** Officer with highest case count
**Demo Point:** "Helps with resource allocation and workload balancing across the team."

---

### Relationship Pattern Analysis
```
Show me people who have family relationships and are both involved in crimes
```
**Expected Output:** Family members involved in criminal activity
**Demo Point:** "Family-based criminal enterprises become immediately visible."

---

### Email Contact Analysis
```
What email addresses are associated with people involved in burglary?
```
**Expected Output:** Email addresses of burglary suspects
**Demo Point:** "Modern investigations need digital contact points—we get them instantly."

---

### Crime Type Distribution
```
How many public order crimes occurred in August 2017?
```
**Expected Output:** Count of public order offenses
**Demo Point:** "Quick statistics help identify crime trends and allocate resources."

---

### Complex Network Query
```
Show me people who know each other, are involved in violence crimes, and live in the same postcode area
```
**Expected Output:** Highly connected suspects in specific geographic area
**Demo Point:** "Complex multi-factor queries that would take days manually—answered in seconds."

---

## Presentation Flow Suggestion

### Opening (Show System Capabilities)
1. Start with simple query: "Show me all robbery crimes"
2. Progress to network query: "Who knows each other and is involved in robberies?"
3. Highlight the graph visualization

### Middle (Demonstrate Investigation Value)
4. Run location query: "What are the addresses of people involved in robberies?"
5. Show cross-reference query: "What phone numbers are associated with people involved in robbery crimes?"
6. Emphasize time saved: "This would have taken days manually"

### Closing (Show Complex Analytics)
7. Run complex query: "People who know each other, involved in violence crimes, in same postcode"
8. Show repeat offender analysis: "People involved in multiple violence crimes"
9. Final message: "Intelligence-driven policing starts with questions. Our system provides answers."

---

## Tips for Effective Demo

1. **Pace Yourself:** Give each query result 10-15 seconds to display before moving on
2. **Highlight Visualization:** When graph appears, zoom and pan to show interactivity
3. **Emphasize Natural Language:** Point out that these are plain English questions, not code
4. **Show Real Impact:** After each query, state how long it would take manually
5. **Interactive Element:** Ask audience for a question and demonstrate live query generation

---

## Backup Queries (If System Issues Occur)

Keep these simpler queries ready:
- "Show me all people named Todd"
- "How many crimes occurred in August 2017?"
- "Show me all locations in the OL11 postcode area"
- "Who are the officers investigating crimes?"

---

## Technical Notes

- All queries return maximum 50 results (system limitation for performance)
- Graph visualization only appears when results include nodes/relationships
- Some queries may return empty results if specific data doesn't exist—that's normal
- If a query fails, the system auto-retries with reformulated query (show this as a feature!)

---

## After the Demo

**Leave Audience With:**
- Case studies document (INVESTIGATION_CASE_STUDIES.md)
- This demo queries file for their reference
- System architecture overview
- Contact information for questions

---

**Demo Success Metrics:**
- ✅ Demonstrated natural language querying
- ✅ Showed graph visualization
- ✅ Proved time-saving value
- ✅ Revealed hidden patterns in data
- ✅ Made complex investigation seem simple

Good luck with your presentation!
