"""Incident reports, org charts, FAQs, meeting minutes and other documents."""


def doc(name, department, doc_type, date, fmt, sections):
    return {
        "name": name,
        "department": department,
        "doc_type": doc_type,
        "versions": [
            {"version": "1.0", "date": date, "format": fmt, "sections": sections}
        ],
    }


def incident(number, title, date, fmt, summary, timeline, cause, actions):
    return doc(
        f"Incident Report IR-{number} {title}",
        "Incident Response",
        "incident_report",
        date,
        fmt,
        [
            ("Summary", summary),
            ("Timeline", {"bullets": timeline}),
            ("Root Cause", cause),
            ("Corrective Actions", actions),
            (
                "Sign-Off",
                "Reviewed by the Incident Commander and filed with Incident "
                "Response. A joke was included in the cover email, per HR Policy.",
            ),
        ],
    )


INCIDENTS = [
    incident(
        "0042",
        "Rogue Shrink-inator in the Break Room",
        "2024-03-07",
        "md",
        "At 3:04 p.m. the Shrink-inator was accidentally fired in the break room, "
        "shrinking the coffee machine, two chairs and the deputy head of Finance to "
        "roughly the size of a teacup. The inator was meant for a scheme "
        "against the tallest building in the Tri-State Area. Severity was set to Sev 3.",
        [
            "3:04 p.m. Shrink-inator fired while being carried past the microwave",
            "3:06 p.m. Deputy head of Finance reported the incident by shouting very quietly",
            "3:40 p.m. Reverse setting located in the manual, on page 112",
            "4:15 p.m. Everyone and everything restored except one chair",
        ],
        "The Shrink-inator was carried with its safety cap off. The trigger was "
        "pressed by an elbow while the carrier reached for a donut.",
        [
            ("Safety Caps", "Inators must be carried with the safety cap on, always."),
            (
                "Break Room Ban",
                "Inators are banned from the break room. The small chair is kept "
                "on the CEO's desk as a reminder.",
            ),
        ],
    ),
    incident(
        "0057",
        "Sentient Ooze Union Drive",
        "2024-08-19",
        "pdf",
        "The basement ooze became self-aware and attempted to unionize the "
        "cleaning robots. Severity was set to Sev 2 because the ooze had a "
        "surprisingly good list of demands.",
        [
            "9:00 a.m. Ooze found holding a meeting with three cleaning robots",
            "9:30 a.m. Ooze requested dental coverage and a window",
            "11:00 a.m. HR agreed to a window",
        ],
        "The ooze was exposed to the Intelligence-inator during a nearby test and "
        "was never placed in a sealed container.",
        [
            (
                "Containment",
                "All goo is now stored in sealed containers and counted weekly.",
            ),
            (
                "Ooze Relations",
                "The ooze now has a small window and a seat on the Wellness Committee.",
            ),
        ],
    ),
    incident(
        "0063",
        "Foosball Table Heist",
        "2025-01-23",
        "docx",
        "The company foosball table disappeared overnight. It was found two days "
        "later on the roof, rearranged so that every player was a goalie.",
        [
            "Monday 8:00 a.m. Foosball table reported missing",
            "Monday 8:05 a.m. Token transfers frozen by the Chief Token Officer",
            "Wednesday 10:00 a.m. Table found on the roof next to blimp slot two",
        ],
        "A night-shift minion moved the table to practice in private before the "
        "quarterly Foosball Leaderboard reset. Security footage had been deleted "
        "after 90 days, so the first theft attempt was never noticed.",
        [
            (
                "Footage Retention",
                "Camera footage retention was extended, see Data Retention Policy 2.0.",
            ),
            ("Table Anchoring", "The foosball table is now bolted to the floor."),
        ],
    ),
    incident(
        "0071",
        "Elevator Monologue Overrun",
        "2025-06-12",
        "md",
        "The CEO began a monologue about his childhood in Gimmelshtump in the main "
        "elevator and refused to let the doors open until he had finished. Nine "
        "employees were trapped for 47 minutes.",
        [
            "12:01 p.m. Monologue begins between floors three and four",
            "12:30 p.m. Employees begin sharing snacks",
            "12:48 p.m. Monologue ends with the words 'and that is why I hate lawn gnomes'",
        ],
        "There was no rule limiting monologues in shared spaces.",
        [
            (
                "Elevator Rule",
                "The Elevator Monologue Rule was added to HR Policy 3.0.",
            ),
            ("Snack Kit", "A snack kit is now stored in every elevator."),
        ],
    ),
    incident(
        "0088",
        "Self-Destruct Button Leaned On",
        "2025-09-02",
        "pdf",
        "A visiting vendor leaned on the self-destruct button of the "
        "Weather-Control-inator during a sales pitch. The inator was destroyed and "
        "it rained indoors for 20 minutes.",
        [
            "2:10 p.m. Vendor leans on the button while describing a discount",
            "2:11 p.m. Inator destroyed, indoor rain begins",
            "2:31 p.m. Rain stops, vendor offers a bigger discount",
        ],
        "The self-destruct button had no confirmation step and was placed exactly at "
        "leaning height.",
        [
            (
                "Confirmation Prompt",
                "A confirmation prompt was added in Self-Destruct Button Policy 3.0.",
            ),
            ("Vendor Escort", "Vendors are now escorted away from all inators."),
        ],
    ),
    incident(
        "0094",
        "Blimp Docking Collision",
        "2025-11-14",
        "docx",
        "A visiting villain's blimp overstayed its docking slot and was struck by "
        "the company blimp returning from Gimmelshtump. Both blimps lost "
        "approximately one third of their dignity.",
        [
            "4:00 p.m. Guest blimp exceeds its docking time by 3 hours",
            "4:20 p.m. Company blimp attempts to dock in slot one, slot one is occupied",
            "4:21 p.m. Gentle collision, loud squeaking noise",
        ],
        "Guest blimps were not tracked against the docking time limit.",
        [
            (
                "Third Slot",
                "A third docking slot was added in Parking and Blimp Docking Policy 3.0.",
            ),
            ("Docking Timers", "Each slot now has a large countdown timer."),
        ],
    ),
    incident(
        "0101",
        "Smart Fridge Botnet",
        "2025-04-03",
        "md",
        "The break room smart fridge joined a botnet and ordered 300 jars of pickles "
        "to the lobby. The pickles were donated to the minion cafeteria.",
        [
            "Monday Pickle delivery number one arrives",
            "Tuesday Pickle deliveries two through nine arrive",
            "Wednesday IT Security disconnects the fridge",
        ],
        "The smart fridge was connected to the main Inator Network with its "
        "default password.",
        [
            (
                "Smart Device Rule",
                "Smart devices now live on an isolated subnet, see Acceptable Use of "
                "Inator Network Policy 2.0.",
            ),
            ("Pickle Budget", "No pickle budget was approved."),
        ],
    ),
    incident(
        "0112",
        "Intern Turned Into Houseplant",
        "2024-12-05",
        "pdf",
        "An intern was accidentally turned into a ficus by the "
        "Plant-Everything-inator and spent an afternoon in the lab before anyone "
        "noticed. No platypus was involved, for once. The intern reported "
        "the experience as 'very relaxing'.",
        [
            "1:00 p.m. Intern working alone in Lab 4",
            "1:05 p.m. Inator misfires, intern becomes a ficus",
            "5:30 p.m. Night guard waters the ficus, ficus says thank you",
        ],
        "The intern was working alone with no lab buddy and no check-in schedule.",
        [
            (
                "Buddy System",
                "A lab buddy system was added in Laboratory Safety Policy 2.0.",
            ),
            (
                "Watering",
                "The intern received a full day of paid leave and fertilizer.",
            ),
        ],
    ),
]

ORG_CHARTS = [
    doc(
        "Executive Org Chart",
        "Executive Office",
        "org_chart",
        "2026-01-05",
        "md",
        [
            (
                "Overview",
                "This chart lists the executive team of Doofenshmirtz Evil "
                "Incorporated as of January 2026.",
            ),
            (
                "Executive Team",
                {
                    "table": [
                        ["Role", "Name", "Reports To"],
                        [
                            "Chief Executive Officer",
                            "Dr. Heinz Doofenshmirtz",
                            "Nobody",
                        ],
                        ["Chief Token Officer", "Classified", "Nobody, by charter"],
                        ["Chief Financial Officer", "Gretchen Moneybags", "CEO"],
                        ["Head of Inator R&D", "Dr. Ilsa Coilwhip", "CEO"],
                        ["Head of Lab Safety", "Marvin Goggleson", "CEO"],
                        ["Head of Minion Operations", "Big Lou", "CEO"],
                        ["Robot Butler and Tie-Breaker", "Norm", "CEO"],
                    ],
                    "after": "The CEO's daughter Vanessa is not an employee and has "
                    "asked to be removed from all company materials.",
                },
            ),
            (
                "Succession",
                "If the CEO is trapped, shrunk or turned into a houseplant, the CFO "
                "acts as CEO until he is restored.",
            ),
        ],
    ),
    doc(
        "Inator R&D Org Chart",
        "Inator R&D",
        "org_chart",
        "2026-01-05",
        "md",
        [
            (
                "Overview",
                "This chart lists the teams in Inator R&D and what each one builds.",
            ),
            (
                "Teams",
                {
                    "table": [
                        ["Team", "Lead", "Focus"],
                        [
                            "Rays and Beams",
                            "Dr. Ilsa Coilwhip",
                            "Shrink, grow and freeze rays",
                        ],
                        ["Weather", "Stormy Petrel", "Weather-Control-inators"],
                        ["Robotics", "Norm", "Norm-bots and giant robots"],
                        [
                            "Self-Destruct Engineering",
                            "Gary Redbutton",
                            "Buttons and prompts",
                        ],
                        ["Portals", "Dr. Elsewhere", "Portals to other dimensions"],
                    ],
                    "after": "The Portals team sits on the fourth floor, or sometimes "
                    "in another dimension.",
                },
            ),
            (
                "Review Board",
                "Inator R&D sends every deployment to the Inator Review Board.",
            ),
        ],
    ),
    doc(
        "Minion Operations Org Chart",
        "Minion Operations",
        "org_chart",
        "2026-01-05",
        "docx",
        [
            (
                "Overview",
                "This chart lists the crews in Minion Operations and their shifts.",
            ),
            (
                "Crews",
                {
                    "table": [
                        ["Crew", "Crew Chief", "Shift"],
                        ["Lair Guard", "Big Lou", "Day"],
                        ["Night Watch", "Sleepy Sal", "Night"],
                        ["Snack Logistics", "Crunch", "Day"],
                        ["Chase Squad", "Speedy Pete", "Scheme days"],
                    ],
                    "after": "The Chase Squad holds the company record for longest "
                    "platypus chase, at 3 hours and 12 minutes.",
                },
            ),
            (
                "Union",
                "Minions are represented by the Minion Union, which meets on the "
                "first Monday of each month.",
            ),
        ],
    ),
]


def faq(name, department, date, fmt, intro, topics):
    sections = [("About This FAQ", intro)]
    for title, entries in topics:
        sections.append(
            (
                title,
                [
                    (sub, f"Q: {question} A: {answer}")
                    for sub, question, answer in entries
                ],
            )
        )
    return doc(name, department, "faq", date, fmt, sections)


FAQS = [
    faq(
        "Token Economy FAQ",
        "Recreation",
        "2026-03-02",
        "md",
        "Answers to the questions employees ask most about Focus Tokens under the "
        "Time & Usage Policy.",
        [
            (
                "Earning Tokens",
                [
                    (
                        "Base Allocation",
                        "How many tokens do I get?",
                        "Under Time & Usage Policy 3.0 you get 750,000 tokens per "
                        "six-hour cycle.",
                    ),
                    (
                        "Foosball Bonus",
                        "Do I still win tokens at foosball?",
                        "Yes, but only a flat 10,000-token bonus. You no longer take "
                        "the loser's tokens.",
                    ),
                ],
            ),
            (
                "Spending Tokens",
                [
                    (
                        "Gifting Tokens",
                        "Can I give tokens to a friend?",
                        "No. Gifting, pooling and borrowing tokens are still "
                        "prohibited, and losing at foosball on purpose is detected by "
                        "the monitoring AI.",
                    ),
                    (
                        "Running Out",
                        "What happens if I run out?",
                        "Ask the Chief Token Officer, and if he says no, enjoy some "
                        "skincare.",
                    ),
                ],
            ),
        ],
    ),
    faq(
        "New Hire FAQ",
        "Henchperson Training",
        "2025-09-15",
        "pdf",
        "Questions new hires ask in their first week at Doofenshmirtz Evil "
        "Incorporated.",
        [
            (
                "First Day",
                [
                    (
                        "Where To Go",
                        "Where do I go on my first day?",
                        "Go to the lobby of the tall purple building with the giant "
                        "neon sign and ask for Norm.",
                    ),
                    (
                        "What To Wear",
                        "What should I wear?",
                        "Anything comfortable. Do not wear a suit, a tie or a fedora.",
                    ),
                ],
            ),
            (
                "Common Worries",
                [
                    (
                        "Trap Doors",
                        "Will I fall through a trap door?",
                        "Probably not. Trap doors in public hallways now have a small "
                        "sign reading 'Probably Fine'.",
                    ),
                    (
                        "The Platypus",
                        "What if I see a platypus?",
                        "Do not approach it. Report it to Facilities and tell the CEO, "
                        "who will be thrilled.",
                    ),
                ],
            ),
        ],
    ),
    faq(
        "Inator Lab FAQ",
        "Lab Safety",
        "2026-01-26",
        "docx",
        "Practical questions about working in the inator labs.",
        [
            (
                "Safety",
                [
                    (
                        "Goggles",
                        "Can I wear swim goggles?",
                        "No. Swim goggles are not safety goggles, no matter how tight "
                        "they are.",
                    ),
                    (
                        "Working Alone",
                        "Can I work alone in the lab late at night?",
                        "No. You need a lab buddy who checks on you every 20 minutes.",
                    ),
                ],
            ),
            (
                "Testing",
                [
                    (
                        "Watermelons",
                        "Why are there so many watermelons?",
                        "Watermelons are the approved test target for every inator "
                        "prototype review, because they never wear fedoras.",
                    ),
                    (
                        "Portals",
                        "How many portals can be open?",
                        "One portal per lab, closed before lunch.",
                    ),
                ],
            ),
        ],
    ),
    faq(
        "Expense FAQ",
        "Finance",
        "2026-01-12",
        "md",
        "Quick answers about expenses under Expense Reimbursement Policy 3.0.",
        [
            (
                "Claims",
                [
                    (
                        "Deadline",
                        "How long do I have to submit a claim?",
                        "14 days from the purchase, with an itemized receipt.",
                    ),
                    (
                        "Fedoras",
                        "Can I expense a fedora?",
                        "No. Fedoras are never reimbursable, for reasons the CEO "
                        "describes as personal.",
                    ),
                ],
            ),
            (
                "Expense Card",
                [
                    (
                        "Card Shape",
                        "Why is the expense card shaped like a button?",
                        "Branding. It is shaped like a self-destruct button, but pressing it "
                        "does not destroy anything.",
                    ),
                ],
            ),
        ],
    ),
    faq(
        "Pet Leave FAQ",
        "Human Resources",
        "2026-02-02",
        "pdf",
        "Answers about pet adoption leave under HR Policy 3.0.",
        [
            (
                "Leave Length",
                [
                    (
                        "Platypus Leave",
                        "How much leave do I get for adopting a platypus?",
                        "10 days of paid leave, the most of any pet, as long as the "
                        "platypus is not wearing a hat.",
                    ),
                    (
                        "Fish",
                        "Does a goldfish count?",
                        "Yes, a goldfish counts as a pet and gets the standard 5 days. "
                        "It may not be used to test any inator.",
                    ),
                ],
            ),
        ],
    ),
]


def minutes(name, department, date, fmt, attendees, items, actions):
    return doc(
        name,
        department,
        "meeting_minutes",
        date,
        fmt,
        [
            ("Attendees", attendees),
            ("Discussion", items),
            ("Action Items", {"bullets": actions}),
            ("Next Meeting", "The next meeting will be scheduled by Norm."),
        ],
    )


MINUTES = [
    minutes(
        "Leadership Meeting Minutes 2025 Q1",
        "Executive Office",
        "2025-03-31",
        "md",
        "CEO, CFO, Head of Inator R&D, Head of Minion Operations, Norm (taking notes).",
        [
            (
                "Budget Rebalance",
                "The CFO reported that Inator R&D spent its entire annual budget by "
                "February. Leadership agreed to release R&D funding quarterly.",
            ),
            (
                "Nemesis Update",
                "The CEO reported that the nemesis foiled 11 schemes this quarter, a "
                "new record. The CEO described this as 'actually kind of impressive'.",
            ),
        ],
        [
            "CFO to publish Evil Budget Allocation Policy 2.0",
            "Head of Inator R&D to stop buying volcano-grade lava",
        ],
    ),
    minutes(
        "Inator Review Board Minutes 2026 March",
        "Inator R&D",
        "2026-03-30",
        "docx",
        "CEO, Head of Lab Safety, Norm (tie-breaking vote).",
        [
            (
                "Freeze-inator Review",
                "The Freeze-inator passed review after freezing two watermelons. Lab "
                "Safety voted no, the CEO voted yes, and Norm broke the tie with a "
                "yes.",
            ),
            (
                "Portal Request",
                "A request to open a second portal in Lab 2 was denied, because only "
                "one portal may be open per lab.",
            ),
        ],
        [
            "Freeze-inator scheduled for deployment next Tuesday",
            "Portals team to close the portal before lunch, every day",
        ],
    ),
    minutes(
        "Minion Union Meeting Minutes 2025 June",
        "Minion Operations",
        "2025-06-02",
        "pdf",
        "Union representatives, Head of Minion Operations, the basement ooze "
        "(observer).",
        [
            (
                "Shift Length",
                "The union requested shorter shifts, noting that being chased by a "
                "platypus is exhausting. Management agreed to 7-hour shifts.",
            ),
            (
                "Night Bonus",
                "The union requested a higher night-shift bonus. Management agreed to "
                "20 percent and a nicer nightlight.",
            ),
        ],
        [
            "Head of Minion Operations to publish Minion Scheduling Policy 2.0",
            "Ooze to be given a vote at the next meeting",
        ],
    ),
    minutes(
        "Wellness Committee Minutes 2025 August",
        "Wellness",
        "2025-08-25",
        "md",
        "Wellness lead, on-site nutritionist, three employees, the basement ooze.",
        [
            (
                "Caffeine",
                "The committee recommended lowering the caffeine limit to 300 mg after "
                "an analyst vibrated through a wall.",
            ),
            (
                "Sleep",
                "The committee proposed a sleep section recommending at least 7 hours "
                "per night.",
            ),
        ],
        [
            "Wellness lead to publish Health & Wellness Policy 2.0",
            "Nutritionist to remove the triple espresso from the cafeteria menu",
        ],
    ),
    minutes(
        "Evil PR Crisis Meeting Minutes 2025 January",
        "Evil PR",
        "2025-01-30",
        "docx",
        "Head of Evil PR, CEO, two social media interns.",
        [
            (
                "Floating Baby Head",
                "The Giant Floating Baby Head-inator was on the news for six hours with no "
                "comment from the company. PR agreed to respond to media within 2 "
                "hours from now on.",
            ),
            (
                "Slogan",
                "Focus groups found the slogan 'Evil, But Incorporated' accurate but "
                "not inspiring. A new slogan will be tested on Norm.",
            ),
        ],
        [
            "Head of Evil PR to publish Evil PR and Social Media Policy 2.0",
            "Interns to stop posting the CEO's baby pictures",
        ],
    ),
]

OTHER = [
    doc(
        "Company Glossary",
        "Executive Office",
        "glossary",
        "2025-10-01",
        "md",
        [
            (
                "About This Glossary",
                "Terms used across Doofenshmirtz Evil Incorporated documents.",
            ),
            (
                "Terms",
                [
                    (
                        "Inator",
                        "Any device built to do something evil. The name must end in "
                        "'-inator'.",
                    ),
                    (
                        "Tri-State Area",
                        "The region the company is trying to take over, one inator at "
                        "a time.",
                    ),
                    (
                        "Gimmelshtump",
                        "The CEO's home village, source of most backstories and an "
                        "extra per diem.",
                    ),
                    (
                        "Focus Token",
                        "The internal currency spent on tasks, deliverables and deep "
                        "thoughts.",
                    ),
                    (
                        "The Nemesis",
                        "The company's one and only nemesis. Further details are "
                        "classified.",
                    ),
                ],
            ),
        ],
    ),
    doc(
        "Onboarding Welcome Memo",
        "Human Resources",
        "memo",
        "2025-09-15",
        "docx",
        [
            (
                "Welcome",
                "Welcome to Doofenshmirtz Evil Incorporated! We are thrilled you have "
                "joined us in our mission to take over the entire Tri-State Area.",
            ),
            (
                "Your First Week",
                "You will shadow a senior employee, learn where the trap doors are, "
                "and take Evil Laughing for Beginners.",
            ),
            (
                "A Note From The CEO",
                "Please do not touch any button labeled 'SELF-DESTRUCT' during your "
                "first week. Or ever. Unless it is really dramatic.",
            ),
        ],
    ),
]

FAMILIES = [*INCIDENTS, *ORG_CHARTS, *FAQS, *MINUTES, *OTHER]
