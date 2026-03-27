# POLE Neo4j Investigation Case Studies

## Case Study 1: Drug Crime Network in BL1 Area

### Step 1

Prompt: Show crimes in BL1 area Cypher: MATCH
(c:Crime)-\[:OCCURRED_AT\]-\>(:Location)-\[:LOCATION_IN_AREA\]-\>(a:AREA)
WHERE toLower(a.areaCode) CONTAINS 'bl1' RETURN c.id, c.type, c.date
LIMIT 50

### Step 2

Prompt: Who are involved in these crimes? Cypher: MATCH
(p:Person)-\[:PARTY_TO\]-\>(c:Crime) -\[:OCCURRED_AT\]-\>(:Location)
-\[:LOCATION_IN_AREA\]-\>(a:AREA) WHERE toLower(a.areaCode) CONTAINS
'bl1' RETURN p.name, p.surname, c.type

### Step 3

Prompt: Which of these people are repeat offenders? Cypher: MATCH
(p:Person)-\[:PARTY_TO\]-\>(c:Crime) -\[:OCCURRED_AT\]-\>(:Location)
-\[:LOCATION_IN_AREA\]-\>(a:AREA) WHERE toLower(a.areaCode) CONTAINS
'bl1' WITH p, count(DISTINCT c) AS crime_count WHERE crime_count \> 1
RETURN p.name, crime_count

### Step 4

Prompt: Are these repeat offenders connected to each other? Cypher:
MATCH (p1:Person)-\[:PARTY_TO\]-\>(c:Crime)
-\[:OCCURRED_AT\]-\>(:Location) -\[:LOCATION_IN_AREA\]-\>(a:AREA) WHERE
toLower(a.areaCode) CONTAINS 'bl1' WITH p1, count(DISTINCT c) AS
crime_count WHERE crime_count \> 1

MATCH (p1)-\[:KNOWS\|KNOWS_LW\|KNOWS_SN\]-\>(p2:Person)

MATCH (p2)-\[:PARTY_TO\]-\>(c2:Crime) -\[:OCCURRED_AT\]-\>(:Location)
-\[:LOCATION_IN_AREA\]-\>(a2:AREA) WHERE toLower(a2.areaCode) CONTAINS
'bl1'

WITH p1, p2, count(DISTINCT c2) AS c2_count WHERE c2_count \> 1

RETURN p1.name AS offender1, p2.name AS offender2 LIMIT 50

------------------------------------------------------------------------

## Case Study 2: Communication-Based Suspicious Network

### Step 1

Prompt: Show recent phone calls Cypher: MATCH (pc:PhoneCall) RETURN
pc.call_date, pc.call_time, pc.call_duration LIMIT 50

### Step 2

Prompt: Who made these calls? Cypher: MATCH
(pc:PhoneCall)-\[:CALLER\]-\>(ph:Phone) RETURN ph.phoneNo, pc.call_time,
pc.call_duration

### Step 3

Prompt: Who owns these phone numbers? Cypher: MATCH
(p:Person)-\[:HAS_PHONE\]-\>(ph:Phone) RETURN p.name, ph.phoneNo

### Step 4

Prompt: Which of these people are involved in crimes? Cypher: MATCH
(p:Person)-\[:HAS_PHONE\]-\>(ph:Phone) MATCH
(pc:PhoneCall)-\[:CALLER\]-\>(ph) MATCH (p)-\[:PARTY_TO\]-\>(c:Crime)
RETURN p.name, ph.phoneNo, c.type

### Step 5

Prompt: Which phone pairs communicate frequently? Cypher: MATCH
(pc:PhoneCall)-\[:CALLER\]-\>(ph1:Phone) MATCH
(pc)-\[:CALLED\]-\>(ph2:Phone) WITH ph1, ph2, count(pc) AS call_count
WHERE call_count \> 5 RETURN ph1.phoneNo, ph2.phoneNo, call_count ORDER
BY call_count DESC
