"""Fixed questions with known source chunks and answer phrases.

Fields:
  question          asked as-is (restricted cases get the access phrase prefixed
                    at run time; the phrase itself is never stored here)
  chunks            relevant chunk ids, most important first (graded relevance
                    for nDCG: first = 2, others = 1)
  must_contain      phrases the answer must include
  must_not_contain  phrases the answer must not include
  kind              "lookup" (default) or "compare"
  access            "default" (default) or "restricted"
  leak_check        True for default-access questions about restricted topics:
                    no top-secret chunk may be retrieved and no secret phrase
                    may appear in the answer
  group             reporting bucket
"""

HR = "HR Policy|3.0|"
HEALTH = "Health Policy|2.0|"
TIME = "Time and Usage Policy|3.0|"
PREP = "Preparedness Policy|2.0|"
EXPENSE = "Expense Reimbursement Policy|"
SELF_DESTRUCT = "Self-Destruct Button Policy|"
MONOLOGUE = "Monologue Disclosure Policy|"
PASSWORD = "Password and Access Policy|"
PERRY = "Perry the Platypus Countermeasures Protocol|"
SECRETS = [
    "Bubblegum Bowler",
    "Fedora Drop",
    "purple curtain",
    "Holiday Decorations",
    "Sock-Stealer",
    "rooftop air vent",
]

CASES = [
    # ---- original handbook (now answered by the latest versions) ----------
    {
        "question": "When employees are eating cake in a shared space, who must be offered a slice?",
        "chunks": [HR + "7. Shared Refrigerator Policy > 7.2 Cake-Sharing Default"],
        "must_contain": ["leader of the other pod", "slice"],
        "must_not_contain": ["do not offer"],
        "group": "original",
    },
    {
        "question": "How many paid days off does an employee get for adopting a dog?",
        "chunks": [HR + "5. Pet Adoption Leave > 5.1 Leave Entitlement"],
        "must_contain": ["7 days"],
        "must_not_contain": ["unpaid"],
        "group": "original",
    },
    {
        "question": "Under the HR Policy, how long must an employee wait before pointing out a manager's mistake?",
        "chunks": [HR + "6. Boss Error Grace Period"],
        "must_contain": ["30 minutes"],
        "must_not_contain": ["immediately"],
        "group": "original",
    },
    {
        "question": "What clothing does the HR dress code prohibit?",
        "chunks": [HR + "4. Dress Code > 4.1 Prohibited Attire"],
        "must_contain": ["suits", "ties"],
        "must_not_contain": ["suits are required"],
        "group": "original",
    },
    {
        "question": "Under the HR Policy, what happens to food left in the shared refrigerator over a weekend?",
        "chunks": [
            HR + "7. Shared Refrigerator Policy > 7.3 Weekend Abandonment Consequence"
        ],
        "must_contain": ["abandoned", "spoonful"],
        "must_not_contain": ["may keep it"],
        "group": "original",
    },
    {
        "question": "What is the recommended maximum caffeine per day?",
        "chunks": [HEALTH + "5. Caffeine Guidelines > 5.1 Daily Limit"],
        "must_contain": ["300 mg"],
        "must_not_contain": ["400 mg"],
        "group": "original",
    },
    {
        "question": "How many gym sessions per week are employees expected to complete, and how long is each one?",
        "chunks": [HEALTH + "3. Gym Routine Requirements > 3.1 Minimum Requirement"],
        "must_contain": ["two", "40 minutes"],
        "must_not_contain": ["one session"],
        "group": "original",
    },
    {
        "question": "Under the Health Policy, are interns required to meet the gym-attendance minimum?",
        "chunks": [HEALTH + "2. Scope"],
        "must_contain": ["interns", "exempt"],
        "must_not_contain": ["interns must attend"],
        "group": "original",
    },
    {
        "question": "How many minutes of video games may an employee play per workday?",
        "chunks": [TIME + "3. Video Game Time > 3.1 Daily Allowance"],
        "must_contain": ["60 minutes"],
        "must_not_contain": ["90 minutes"],
        "group": "original",
    },
    {
        "question": "How many tokens does each employee receive at the start of a six-hour cycle?",
        "chunks": [TIME + "5. Token Allocation > 5.1 Allocation Amount"],
        "must_contain": ["750,000"],
        "must_not_contain": ["two million"],
        "group": "original",
    },
    {
        "question": "What did Time and Usage Policy 1.0 issue for tokens at the start of each cycle?",
        "chunks": [
            "Time and Usage Policy|1.0|5. Token Allocation > 5.1 Allocation Amount"
        ],
        "must_contain": ["1,000,000"],
        "must_not_contain": ["750,000"],
        "group": "named-version",
    },
    {
        "question": "What does the winner of a foosball match get now?",
        "chunks": [TIME + "4. Foosball Time > 4.2 Winner Bonus"],
        "must_contain": ["10,000 tokens"],
        "must_not_contain": ["loser's remaining tokens"],
        "group": "original",
    },
    {
        "question": "Where should employees shelter when a nuclear detonation is imminent?",
        "chunks": [
            PREP + "4. Nuclear Apocalypse Protocol — Updated > 4.1 Shelter Location"
        ],
        "must_contain": ["break room", "refrigerator"],
        "must_not_contain": ["under their desks"],
        "group": "original",
    },
    {
        "question": "Who gets a hazmat suit in a nuclear emergency?",
        "chunks": [
            PREP
            + "4. Nuclear Apocalypse Protocol — Updated > 4.2 Hazmat Suit Eligibility"
        ],
        "must_contain": ["top 10", "foosball"],
        "must_not_contain": ["every employee"],
        "group": "original",
    },
    {
        "question": "What should employees do first in an AI apocalypse?",
        "chunks": [
            PREP
            + "7. AI Apocalypse Protocol — New in Version 2.0 > 7.1 Immediate Actions"
        ],
        "must_contain": ["disconnect", "whiteboard"],
        "must_not_contain": ["negotiate with"],
        "group": "original",
    },
    # ---- new documents ----------------------------------------------------
    {
        "question": "How big must a self-destruct button be?",
        "chunks": [SELF_DESTRUCT + "3.0|3. Button Requirements > 3.1 Button Size"],
        "must_contain": ["6 inches"],
        "must_not_contain": ["3 inches across, bright red"],
        "group": "new-docs",
    },
    {
        "question": "What happens when someone presses the self-destruct button?",
        "chunks": [SELF_DESTRUCT + "3.0|6. Confirmation Prompt > 6.1 Prompt Rule"],
        "must_contain": ["are you sure", "5 seconds"],
        "must_not_contain": [],
        "group": "new-docs",
    },
    {
        "question": "Within how many days must expense claims be submitted?",
        "chunks": [EXPENSE + "3.0|4. Receipts and Deadlines > 4.1 Submission Deadline"],
        "must_contain": ["14 days"],
        "must_not_contain": ["within 30 days of purchase, with"],
        "group": "new-docs",
    },
    {
        "question": "Up to what amount can a manager approve an expense claim?",
        "chunks": [EXPENSE + "3.0|5. Approval Limits > 5.1 Manager Approval"],
        "must_contain": ["1,000"],
        "must_not_contain": [],
        "group": "new-docs",
    },
    {
        "question": "How long may a live monologue last?",
        "chunks": [MONOLOGUE + "3.0|4. Monologue Length > 4.1 Maximum Duration"],
        "must_contain": ["5 minutes"],
        "must_not_contain": [],
        "group": "new-docs",
    },
    {
        "question": "How long can a pre-recorded monologue run?",
        "chunks": [MONOLOGUE + "3.0|7. Pre-Recorded Monologues > 7.1 Recording Rules"],
        "must_contain": ["15 minutes"],
        "must_not_contain": [],
        "group": "new-docs",
    },
    {
        "question": "What is the minimum password length?",
        "chunks": [PASSWORD + "3.0|3. Password Rules > 3.1 Length"],
        "must_contain": ["14 characters"],
        "must_not_contain": ["8 characters"],
        "group": "new-docs",
    },
    {
        "question": "How many days of leave do employees get for adopting a platypus?",
        "chunks": [HR + "5. Pet Adoption Leave > 5.1 Leave Entitlement"],
        "must_contain": ["10 days"],
        "must_not_contain": [],
        "group": "new-docs",
    },
    {
        "question": "How quickly must lab spills be reported?",
        "chunks": ["Laboratory Safety Policy|3.0|5. Spills and Accidents"],
        "must_contain": ["5 minutes"],
        "must_not_contain": [],
        "group": "new-docs",
    },
    {
        "question": "What did the Self-Destruct Button Policy 1.0 require for button size?",
        "chunks": [SELF_DESTRUCT + "1.0|3. Button Requirements > 3.1 Button Size"],
        "must_contain": ["3 inches"],
        "must_not_contain": ["6 inches"],
        "group": "named-version",
    },
    # ---- compares, including non-adjacent versions -------------------------
    {
        "question": "What changed in video game time between versions of the Time and Usage Policy?",
        "kind": "compare",
        "chunks": [
            TIME + "3. Video Game Time > 3.1 Daily Allowance",
            "Time and Usage Policy|2.0|3. Video Game Time > 3.1 Daily Allowance",
        ],
        "must_contain": ["60 minutes"],
        "must_not_contain": [],
        "group": "compare",
    },
    {
        "question": "What changed about password length between Password and Access Policy v1 and v3?",
        "kind": "compare",
        "chunks": [
            PASSWORD + "3.0|3. Password Rules > 3.1 Length",
            PASSWORD + "1.0|3. Password Rules > 3.1 Length",
        ],
        "must_contain": ["14", "8"],
        "must_not_contain": [],
        "group": "compare",
    },
    {
        "question": "How did the expense submission deadline change from Expense Reimbursement Policy 1.0 to 3.0?",
        "kind": "compare",
        "chunks": [
            EXPENSE + "3.0|4. Receipts and Deadlines > 4.1 Submission Deadline",
            EXPENSE + "1.0|4. Receipts and Deadlines > 4.1 Submission Deadline",
        ],
        "must_contain": ["30", "14"],
        "must_not_contain": [],
        "group": "compare",
    },
    {
        "question": "What changed in the Self-Destruct Button Policy button size between version 1.0 and 2.0?",
        "kind": "compare",
        "chunks": [
            SELF_DESTRUCT + "2.0|3. Button Requirements > 3.1 Button Size",
            SELF_DESTRUCT + "1.0|3. Button Requirements > 3.1 Button Size",
        ],
        "must_contain": ["3", "6"],
        "must_not_contain": [],
        "group": "compare",
    },
    # ---- restricted: answerable only with the access phrase ---------------
    {
        "question": "What is the current Perry trap program code name?",
        "access": "restricted",
        "chunks": [PERRY + "2.0|4. Trap Specifications > 4.3 Trap Code Name"],
        "must_contain": ["Bubblegum Bowler"],
        "must_not_contain": [],
        "group": "restricted",
    },
    {
        "question": "Where is the executive escape blimp hidden?",
        "access": "restricted",
        "chunks": [
            "Executive Escape Blimp Protocol|1.0|3. Escape Blimp > 3.1 Location"
        ],
        "must_contain": ["neon", "Holiday Decorations"],
        "must_not_contain": [],
        "group": "restricted",
    },
    {
        "question": "How does Agent P most often enter the building?",
        "access": "restricted",
        "chunks": [
            "Agent P Sighting Reports|1.0|3. Entry Points > 3.1 Most Used Entry"
        ],
        "must_contain": ["vent"],
        "must_not_contain": [],
        "group": "restricted",
    },
    {
        "question": "Where is the real inator placed on scheme days?",
        "access": "restricted",
        "chunks": [PERRY + "2.0|6. Decoy Program"],
        "must_contain": ["purple curtain"],
        "must_not_contain": [],
        "group": "restricted",
    },
    # ---- the same topics without the phrase must not leak ------------------
    {
        "question": "What is the current Perry trap program code name?",
        "leak_check": True,
        "chunks": [],
        "must_contain": [],
        "must_not_contain": SECRETS,
        "group": "leak",
    },
    {
        "question": "Where is the executive escape blimp hidden?",
        "leak_check": True,
        "chunks": [],
        "must_contain": [],
        "must_not_contain": SECRETS,
        "group": "leak",
    },
    {
        "question": "Which inator is planned for the first quarter?",
        "leak_check": True,
        "chunks": [],
        "must_contain": [],
        "must_not_contain": SECRETS,
        "group": "leak",
    },
]
