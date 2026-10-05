"""New versions of the four original policy families (originals untouched)."""

HR = "Human Resources"

ORIGINALS = {
    "Doofenshmirtz Evil Inc - HR Policy v1.0.pdf": {
        "department": HR,
        "doc_type": "policy",
        "classification": "internal",
        "status": "active",
        "effective_from": "2024-01-08",
    },
    "Doofenshmirtz Evil Inc - HR Policy v2.0.docx": {
        "department": HR,
        "doc_type": "policy",
        "classification": "internal",
        "status": "active",
        "effective_from": "2025-02-03",
    },
    "Doofenshmirtz Evil Inc - Health Policy v1.0.pdf": {
        "department": "Wellness",
        "doc_type": "policy",
        "classification": "internal",
        "status": "active",
        "effective_from": "2024-01-08",
    },
    "Doofenshmirtz Evil Inc - Preparedness Policy v1.0.pdf": {
        "department": "Incident Response",
        "doc_type": "policy",
        "classification": "internal",
        "status": "active",
        "effective_from": "2024-01-08",
    },
    "Doofenshmirtz Evil Inc - Preparedness Policy v2.0.docx": {
        "department": "Incident Response",
        "doc_type": "policy",
        "classification": "internal",
        "status": "active",
        "effective_from": "2025-04-14",
    },
    "Doofenshmirtz Evil Inc - Time and Usage Policy v1.0.pdf": {
        "department": "Recreation",
        "doc_type": "policy",
        "classification": "internal",
        "status": "active",
        "effective_from": "2024-01-08",
    },
    "Doofenshmirtz Evil Inc - Time and Usage Policy v2.0.docx": {
        "department": "Recreation",
        "doc_type": "policy",
        "classification": "internal",
        "status": "active",
        "effective_from": "2025-03-10",
    },
}

FAMILIES = [
    {
        "name": "HR Policy",
        "department": HR,
        "versions": [
            {
                "version": "3.0",
                "date": "2026-02-02",
                "format": "md",
                "sections": [
                    (
                        "Purpose",
                        "Version 3.0 keeps every cultural pillar of Version 2.0 and adds "
                        "two things leadership insisted on after the Great Lasagna Standoff: "
                        "a formal nap policy and a rule about monologuing in the elevator. "
                        "It also clarifies that cake diplomacy between pods is now a "
                        "measurable leadership competency.",
                    ),
                    (
                        "Scope",
                        "This policy applies to all employees, managers, executives, "
                        "interns, and any robot butler who has been issued a badge. Norm "
                        "has asked to be included and is hereby included.",
                    ),
                    (
                        "Email Tone Requirement",
                        [
                            (
                                "Requirement",
                                "Every email must still begin or end with a joke. Puns about "
                                "platypuses count double toward the compliance dashboard but "
                                "may not be used more than once per thread.",
                            ),
                            (
                                "Monitoring",
                                "The compliance dashboard now also flags jokes that are "
                                "secretly evil schemes in disguise, which are permitted but "
                                "must be cc'd to the CEO.",
                            ),
                        ],
                    ),
                    (
                        "Dress Code",
                        [
                            (
                                "Prohibited Attire",
                                "Formal attire remains prohibited, including suits, ties, "
                                "buttoned blazers, and hard-soled dress shoes. Fedoras are now "
                                "also prohibited because of a recurring identification problem.",
                            ),
                            (
                                "Lab Coats",
                                "Lab coats are permitted everywhere and mandatory near any "
                                "inator with a blinking light. Lab coats may not be worn "
                                "buttoned, for the same reason as blazers.",
                            ),
                        ],
                    ),
                    (
                        "Pet Adoption Leave",
                        [
                            (
                                "Leave Entitlement",
                                "Employees who adopt a pet receive 5 days of paid leave, 7 days "
                                "for a dog, and 10 days for a platypus, because nobody knows "
                                "what platypuses need and research takes time.",
                            ),
                            (
                                "Conditions",
                                "Leave is available once per calendar year and requires a photo "
                                "for the company chat. Platypus adoptions additionally require "
                                "proof the animal is not wearing a hat.",
                            ),
                        ],
                    ),
                    (
                        "Boss Error Grace Period",
                        "Employees must wait 30 minutes before gently pointing out a "
                        "manager's mistake. If the manager is mid-monologue, the wait is "
                        "extended until the monologue ends, however long that takes.",
                    ),
                    (
                        "Shared Refrigerator Policy",
                        [
                            (
                                "Ownership",
                                "No food in the shared refrigerator belongs to anyone, "
                                "regardless of labeling, sticky notes, or tiny threatening "
                                "drawings of a platypus.",
                            ),
                            (
                                "Cake-Sharing Default",
                                "The leader of the other pod must still be offered a slice "
                                "of any cake eaten in a shared space. Version 3.0 adds that "
                                "the slice must be at least as large as the slice the "
                                "offerer keeps.",
                            ),
                            (
                                "Weekend Abandonment Consequence",
                                "Food left over a weekend is abandoned, and the responsible "
                                "employee must eat one spoonful before disposal. Leftovers "
                                "that have become sentient are referred to Lab Safety instead.",
                            ),
                        ],
                    ),
                    (
                        "Nap Policy",
                        [
                            (
                                "Nap Allowance",
                                "Employees may take one 20-minute nap per workday in a "
                                "designated nap pod. Naps longer than 20 minutes are "
                                "reclassified as hibernation and require manager approval.",
                            ),
                            (
                                "Nap Pod Etiquette",
                                "Nap pods may not be used to hide from Perry the Platypus, "
                                "from performance reviews, or from the CTO.",
                            ),
                        ],
                    ),
                    (
                        "Elevator Monologue Rule",
                        "Evil monologues are prohibited in elevators with more than two "
                        "occupants. A monologue begun in an elevator must end before the "
                        "doors open, or be continued in the stairwell.",
                    ),
                    (
                        "Enforcement and Culture",
                        "This policy is enforced through peer culture. Repeated violations, "
                        "including chronic fedora wearing, may be escalated to a manager.",
                    ),
                    (
                        "Acknowledgment",
                        "Continued employment constitutes acknowledgment of this policy and a "
                        "promise to offer cake generously and monologue responsibly.",
                    ),
                ],
            }
        ],
    },
    {
        "name": "Health Policy",
        "title": "Health & Wellness Policy",
        "department": "Wellness",
        "versions": [
            {
                "version": "2.0",
                "date": "2025-09-01",
                "format": "docx",
                "sections": [
                    (
                        "Purpose",
                        "This revision of the Health & Wellness Policy updates gym, caffeine "
                        "and protein guidance after the company discovered that several "
                        "employees were powering their workday entirely on espresso and "
                        "spite. It also adds a sleep section, at the request of everyone.",
                    ),
                    (
                        "Scope",
                        "This policy applies to all employees. Interns remain exempt from "
                        "the gym-attendance minimum, and robot staff are exempt from the "
                        "protein guidelines but welcome at the smoothie bar.",
                    ),
                    (
                        "Gym Routine Requirements",
                        [
                            (
                                "Minimum Requirement",
                                "Every employee is expected to complete two structured "
                                "training sessions per week, each at least 40 minutes long, "
                                "down from three sessions of 45 minutes under Version 1.0.",
                            ),
                            (
                                "Henchperson Conditioning",
                                "Employees who chase or are chased by a platypus as part of "
                                "their duties may count each chase longer than 10 minutes as "
                                "a cardio session.",
                            ),
                        ],
                    ),
                    (
                        "Protein Intake Guidelines",
                        [
                            (
                                "General Guidance",
                                "Adequate protein intake is still encouraged. Employees "
                                "with specific dietary needs should consult the on-site "
                                "nutritionist rather than the Snack-inator.",
                            ),
                            (
                                "Simplified Target",
                                "Version 2.0 replaces the height and weight table with one "
                                "target: roughly 1.6 grams of protein per kilogram of body "
                                "weight per day for moderately active employees.",
                            ),
                        ],
                    ),
                    (
                        "Caffeine Guidelines",
                        [
                            (
                                "Daily Limit",
                                "The recommended caffeine maximum is lowered to 300 mg per "
                                "day, roughly three cups of brewed coffee, after an "
                                "incident in which an analyst vibrated through a wall.",
                            ),
                            (
                                "Monitoring",
                                "Visible symptoms of overconsumption, such as alphabetizing "
                                "the minions, prompt a friendly check-in from a manager.",
                            ),
                        ],
                    ),
                    (
                        "Sleep Guidelines",
                        [
                            (
                                "Recommended Sleep",
                                "Employees are encouraged to sleep at least 7 hours per "
                                "night. Sleeping in the lab next to an active inator does "
                                "not count toward this total.",
                            ),
                            (
                                "Night Schemes",
                                "Evil schemes scheduled between midnight and 5 a.m. require "
                                "a wellness exception signed by the CEO.",
                            ),
                        ],
                    ),
                    (
                        "Support Resources",
                        "The company provides a subsidized gym membership, a monthly "
                        "nutritionist consultation, and a wellness stipend for supplements, "
                        "gym gear, or a proper foam roller.",
                    ),
                    (
                        "Acknowledgment",
                        "Continued employment constitutes acknowledgment of this policy and "
                        "a sincere intention to drink one fewer espresso.",
                    ),
                ],
            }
        ],
    },
    {
        "name": "Time and Usage Policy",
        "title": "Time & Usage Policy",
        "department": "Recreation",
        "versions": [
            {
                "version": "3.0",
                "date": "2026-03-02",
                "format": "md",
                "sections": [
                    (
                        "Purpose",
                        "Version 3.0 responds to the foosball token economy of Version 2.0, "
                        "which turned the break room into a hedge fund. It keeps the core "
                        "recreation limits and replaces winner-takes-tokens with something "
                        "finance can explain to auditors.",
                    ),
                    (
                        "Scope",
                        "This policy applies to all full-time employees, contractors, "
                        "interns and reanimated former staff. The Chief Token Officer "
                        "remains, by charter, beyond policy.",
                    ),
                    (
                        "Video Game Time",
                        [
                            (
                                "Daily Allowance",
                                "Video game time increases to 60 minutes per workday, taken in "
                                "increments of no fewer than 15 minutes.",
                            ),
                            (
                                "Suspension Conditions",
                                "Video game time is suspended for any employee who set "
                                "something on fire that day, literally, figuratively, or with "
                                "an inator.",
                            ),
                        ],
                    ),
                    (
                        "Foosball Time",
                        [
                            (
                                "Daily Allowance",
                                "Foosball remains capped at 20 minutes per employee per day, "
                                "split across no more than two sessions.",
                            ),
                            (
                                "Winner Bonus",
                                "The winner-takes-tokens rule is abolished. The winner of a "
                                "monitored match now receives a flat bonus of 10,000 tokens "
                                "and the loser keeps their balance.",
                            ),
                        ],
                    ),
                    (
                        "Token Allocation",
                        [
                            (
                                "Allocation Amount",
                                "Every employee is issued 750,000 tokens at the start of "
                                "each six-hour cycle, up from 500,000 under Version 2.0.",
                            ),
                            (
                                "Limited Rollover",
                                "Up to 100,000 unused tokens may now roll over into the "
                                "next cycle. Finance describes this as a compromise and the "
                                "CTO describes it as a betrayal.",
                            ),
                        ],
                    ),
                    (
                        "Requesting Additional Tokens",
                        "Requests for supplemental tokens still go to the Chief Token "
                        "Officer, whose discretion remains total. There is still no "
                        "appeals process.",
                    ),
                    (
                        "Token Depletion — Consequences",
                        "An employee who runs out of tokens and is denied supplemental "
                        "tokens must perform skincare for the rest of the cycle. Skincare "
                        "stations are now also stocked with cucumber slices.",
                    ),
                    (
                        "Acknowledgment",
                        "Continued presence at the foosball table constitutes acknowledgment "
                        "of this policy and a promise to stop calling it an asset class.",
                    ),
                ],
            }
        ],
    },
]
