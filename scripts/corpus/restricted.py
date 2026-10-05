"""Top-secret documents. Only retrievable with the six-letter access phrase.

Every file carries the TOP SECRET banner *and* a top-secret manifest entry,
so classification fails closed even if one of the two is lost.
"""

EXEC = "Executive Office"
TS = "top-secret"

COUNTER_V1 = [
    (
        "Purpose",
        "This document sets out the company's official countermeasures against "
        "Perry the Platypus, also known as Agent P of O.W.C.A., our one and only "
        "nemesis. It must never be read aloud during a monologue.",
    ),
    (
        "Scope",
        "This document applies to the CEO and to the three employees cleared for "
        "Nemesis Operations. Everyone else should stop reading and go have some cake.",
    ),
    (
        "Identification",
        [
            (
                "Field Appearance",
                "Agent P is a teal platypus who wears a brown fedora and walks upright "
                "on two legs. Without the fedora he is a mindless pet who just sort of "
                "lies there and does nothing.",
            ),
            (
                "Signature Sound",
                "Agent P announces himself with a low chattering sound. If you hear "
                "the chatter, an inator will be destroyed within the hour.",
            ),
        ],
    ),
    (
        "Trap Specifications",
        [
            (
                "Standard Trap",
                "The standard trap is a reinforced cage that drops from the ceiling "
                "when the nemesis steps on the welcome mat marked 'Welcome, Perry'.",
            ),
            (
                "Trap Load Rating",
                "Every cage must hold at least 400 pounds of determined platypus. "
                "Cages are tested monthly by an intern in a teal costume.",
            ),
            (
                "Trap Code Name",
                "The current trap program is code-named Operation Fedora Drop. The "
                "code name may not be used in emails, chats or elevator monologues.",
            ),
        ],
    ),
    (
        "Monologue Timing",
        "Once Agent P is trapped, the CEO may begin the monologue only after the "
        "inator is fully charged, which takes 4 minutes, so that the escape at "
        "minute eleven is less of a problem.",
    ),
    (
        "Acknowledgment",
        "Reading this document constitutes acknowledgment that you will tell nobody, "
        "especially not anyone wearing a fedora. Curse you, Perry the Platypus.",
    ),
]

FAMILIES = [
    {
        "name": "Perry the Platypus Countermeasures Protocol",
        "department": EXEC,
        "doc_type": "policy",
        "classification": TS,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-06-24",
                "format": "pdf",
                "sections": COUNTER_V1,
            },
            {
                "version": "2.0",
                "date": "2025-07-21",
                "format": "md",
                "base": "1.0",
                "purpose": "Version 2.0 upgrades every trap after Agent P escaped "
                "Operation Fedora Drop forty-three times in a row, a statistic the CEO "
                "has asked us to stop mentioning.",
                "replace": {
                    "Trap Specifications": (
                        "Trap Specifications",
                        [
                            (
                                "Standard Trap",
                                "The standard trap is now a self-sealing bubble of "
                                "industrial-grade bubblegum that inflates around the "
                                "nemesis when he lands on the balcony.",
                            ),
                            (
                                "Trap Load Rating",
                                "Every trap must now hold at least 900 pounds of "
                                "determined platypus, up from 400 pounds.",
                            ),
                            (
                                "Trap Code Name",
                                "The trap program is now code-named Operation Bubblegum "
                                "Bowler. Operation Fedora Drop is retired.",
                            ),
                        ],
                    )
                },
                "add": [
                    (
                        "Decoy Program",
                        "Three decoy inators are placed on lower floors on every scheme "
                        "day. The real inator is always on the top floor, behind the "
                        "purple curtain, because Agent P never checks the curtain.",
                    )
                ],
            },
        ],
    },
    {
        "name": "Agent P Sighting Reports",
        "department": EXEC,
        "doc_type": "incident_report",
        "classification": TS,
        "versions": [
            {
                "version": "1.0",
                "date": "2025-12-15",
                "format": "docx",
                "sections": [
                    (
                        "Summary",
                        "This log collects confirmed sightings of Perry the Platypus "
                        "near company property in 2025. It is updated by the Nemesis "
                        "Operations team every Friday.",
                    ),
                    (
                        "Confirmed Sightings",
                        {
                            "table": [
                                ["Date", "Location", "Outcome"],
                                [
                                    "2025-03-04",
                                    "Rooftop blimp slot two",
                                    "Freeze-inator destroyed",
                                ],
                                [
                                    "2025-06-12",
                                    "Main elevator shaft",
                                    "Monologue cut short",
                                ],
                                [
                                    "2025-09-02",
                                    "Lab 4 air vent",
                                    "Weather-Control-inator destroyed",
                                ],
                                [
                                    "2025-11-14",
                                    "Inside the company blimp",
                                    "Blimp deflated",
                                ],
                            ],
                            "after": "Every sighting ended with the CEO shouting 'Curse "
                            "you, Perry the Platypus!' within 90 seconds.",
                        },
                    ),
                    (
                        "Entry Points",
                        [
                            (
                                "Most Used Entry",
                                "Agent P most often enters through the rooftop air vent "
                                "next to blimp slot two, used in 7 of 12 sightings.",
                            ),
                            (
                                "Arrival Time",
                                "Agent P usually arrives between 2:00 and 3:00 p.m., "
                                "shortly after the inator is announced.",
                            ),
                        ],
                    ),
                    (
                        "Recommendations",
                        "Weld the rooftop vent shut, move scheme announcements to 4 p.m., "
                        "and stop announcing schemes on the company blog.",
                    ),
                ],
            }
        ],
    },
    {
        "name": "Executive Escape Blimp Protocol",
        "department": EXEC,
        "doc_type": "policy",
        "classification": TS,
        "versions": [
            {
                "version": "1.0",
                "date": "2025-02-10",
                "format": "md",
                "sections": [
                    (
                        "Purpose",
                        "This protocol explains how the CEO escapes when a scheme is "
                        "foiled by Perry the Platypus, which happens every time.",
                    ),
                    (
                        "Scope",
                        "This protocol applies to the CEO and to Norm, who pilots the "
                        "blimp when the CEO is too busy shaking his fist.",
                    ),
                    (
                        "Escape Blimp",
                        [
                            (
                                "Location",
                                "The escape blimp is hidden behind the giant neon 'D' on "
                                "the roof, folded into a box labeled 'Holiday "
                                "Decorations'.",
                            ),
                            (
                                "Launch Phrase",
                                "The blimp inflates when the CEO shouts 'Curse you, "
                                "Perry the Platypus!' within 3 feet of the box.",
                            ),
                        ],
                    ),
                    (
                        "Destinations",
                        "The blimp flies to the backup lair in the abandoned miniature "
                        "golf course, then circles until the nemesis goes home for "
                        "dinner.",
                    ),
                    (
                        "Acknowledgment",
                        "Knowing this protocol constitutes acknowledgment that you will "
                        "never, ever store real holiday decorations in that box.",
                    ),
                ],
            }
        ],
    },
    {
        "name": "Inator Master Plan Ledger",
        "department": EXEC,
        "doc_type": "policy",
        "classification": TS,
        "versions": [
            {
                "version": "1.0",
                "date": "2026-01-05",
                "format": "pdf",
                "sections": [
                    (
                        "Purpose",
                        "This ledger lists the CEO's master plan for taking over the "
                        "entire Tri-State Area in 2026, one inator at a time, while "
                        "keeping Agent P too busy to stop all of them.",
                    ),
                    (
                        "Scope",
                        "This ledger is readable only by the CEO and the Inator Review "
                        "Board.",
                    ),
                    (
                        "Planned Inators",
                        {
                            "table": [
                                ["Quarter", "Inator", "Target"],
                                [
                                    "Q1",
                                    "Sock-Stealer-inator",
                                    "Every left sock in the Tri-State Area",
                                ],
                                [
                                    "Q2",
                                    "Daylight-Savings-inator",
                                    "Make every Monday 3 hours longer",
                                ],
                                [
                                    "Q3",
                                    "Obey-My-Jingle-inator",
                                    "Get the company jingle stuck in every head",
                                ],
                                [
                                    "Q4",
                                    "Platypus-Repellent-inator",
                                    "Keep Agent P out of the building",
                                ],
                            ],
                            "after": "The Q4 inator is the most important, because it "
                            "protects the other three.",
                        },
                    ),
                    (
                        "Funding",
                        "The master plan is funded from the Platypus Countermeasures "
                        "budget line, which is 10 percent of the evil budget.",
                    ),
                    (
                        "Acknowledgment",
                        "Reading this ledger constitutes acknowledgment that you will "
                        "not mention the Sock-Stealer-inator before the first quarter.",
                    ),
                ],
            }
        ],
    },
]
