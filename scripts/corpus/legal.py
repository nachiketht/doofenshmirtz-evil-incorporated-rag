"""Legal and Compliance."""

LEGAL = "Legal"
COMP = "Compliance"

MONOLOGUE_V1 = [
    (
        "Purpose",
        "Legal has determined that most of the company's schemes fail because the "
        "scheme is fully explained, out loud, to a trapped platypus. This policy "
        "limits what may be disclosed during an evil monologue.",
    ),
    (
        "Scope",
        "This policy applies to anyone delivering a monologue on company time, "
        "especially the CEO.",
    ),
    (
        "Disclosure Limits",
        [
            (
                "Permitted Content",
                "A monologue may include a tragic childhood backstory, the name of the "
                "inator, and a general sense of menace.",
            ),
            (
                "Prohibited Content",
                "A monologue may not disclose the location of the self-destruct button, "
                "the inator's weakness, or the exact time the scheme begins.",
            ),
        ],
    ),
    (
        "Monologue Length",
        [
            (
                "Maximum Duration",
                "Monologues are limited to 10 minutes. Legal notes that a trapped "
                "nemesis typically escapes at minute eleven.",
            ),
            (
                "Backstory Allowance",
                "Backstories about Gimmelshtump may run an extra 2 minutes, because they "
                "are always relevant, according to the CEO.",
            ),
        ],
    ),
    (
        "Audience",
        "Monologues may be delivered only to a captured nemesis, a mirror, or Norm. "
        "Monologuing to vendors during price negotiations is prohibited.",
    ),
    (
        "Acknowledgment",
        "Anyone who has ever said 'and now, I will tell you my plan' acknowledges this "
        "policy.",
    ),
]

FAMILIES = [
    {
        "name": "Monologue Disclosure Policy",
        "department": LEGAL,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-02-19",
                "format": "pdf",
                "sections": MONOLOGUE_V1,
            },
            {
                "version": "2.0",
                "date": "2025-02-24",
                "format": "docx",
                "base": "1.0",
                "purpose": "Version 2.0 shortens monologues after an internal study showed "
                "that every scheme longer than one monologue page was foiled.",
                "replace": {
                    "Monologue Length": (
                        "Monologue Length",
                        [
                            (
                                "Maximum Duration",
                                "Monologues are now limited to 5 minutes, down from 10 "
                                "minutes. A timer will be installed in every trap room.",
                            ),
                            (
                                "Backstory Allowance",
                                "The Gimmelshtump backstory allowance is reduced to 1 "
                                "extra minute and must include at least one fact that is "
                                "actually true.",
                            ),
                        ],
                    )
                },
                "add": [
                    (
                        "Legal Review",
                        "Monologues delivered to an audience of more than one platypus "
                        "require advance review by Legal.",
                    )
                ],
            },
            {
                "version": "3.0",
                "date": "2026-03-16",
                "format": "md",
                "base": "2.0",
                "purpose": "Version 3.0 introduces the pre-recorded monologue, so the CEO "
                "can express himself fully without standing next to the nemesis.",
                "replace": {
                    "Monologue Length": (
                        "Monologue Length",
                        [
                            (
                                "Maximum Duration",
                                "A live monologue is now limited to 5 minutes, down from "
                                "10 minutes. A timer will be installed in every trap room.",
                            ),
                            (
                                "Backstory Allowance",
                                "The Gimmelshtump backstory allowance is reduced to 1 "
                                "extra minute and must include at least one fact that is "
                                "actually true.",
                            ),
                        ],
                    )
                },
                "add": [
                    (
                        "Pre-Recorded Monologues",
                        [
                            (
                                "Recording Rules",
                                "Monologues may be pre-recorded and played on a loop. A "
                                "recorded monologue may run 15 minutes because the "
                                "speaker is not physically present to be kicked.",
                            ),
                            (
                                "Storage",
                                "Recordings must be stored on the Inator Network and "
                                "deleted after 30 days, to limit leaks to O.W.C.A.",
                            ),
                        ],
                    )
                ],
            },
        ],
    },
    {
        "name": "Intellectual Property and Inator Patent Policy",
        "department": LEGAL,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-06-03",
                "format": "md",
                "sections": [
                    (
                        "Purpose",
                        "This policy explains who owns the inators, schemes and slogans "
                        "invented at the company, and how to file a patent before a rival "
                        "villain steals the idea.",
                    ),
                    (
                        "Scope",
                        "This policy covers every invention made on company time or with "
                        "company lasers.",
                    ),
                    (
                        "Ownership",
                        [
                            (
                                "Company Ownership",
                                "Every inator invented by an employee belongs to the company. "
                                "The inventor keeps naming rights, provided the name ends in "
                                "'-inator'.",
                            ),
                            (
                                "Naming Disputes",
                                "If two employees claim the same inator name, the name goes "
                                "to whoever built the working prototype first.",
                            ),
                        ],
                    ),
                    (
                        "Patent Filing",
                        [
                            (
                                "Filing Deadline",
                                "Inventors must submit an invention disclosure to Legal "
                                "within 60 days of a working prototype.",
                            ),
                            (
                                "Inventor Bonus",
                                "Each granted patent earns the inventor a bonus of 1,000 "
                                "dollars and a framed photo with the CEO.",
                            ),
                        ],
                    ),
                    (
                        "Trade Secrets",
                        "Self-destruct button placement is treated as a trade secret and "
                        "may not be described in any patent application.",
                    ),
                    (
                        "Acknowledgment",
                        "Inventing anything constitutes acknowledgment of this policy.",
                    ),
                ],
            },
            {
                "version": "2.0",
                "date": "2025-07-07",
                "format": "pdf",
                "base": "1.0",
                "purpose": "Version 2.0 shortens the filing deadline after a rival "
                "villain patented the Turn-Everything-Into-Cheese-inator eleven days "
                "before we did.",
                "replace": {
                    "Patent Filing": (
                        "Patent Filing",
                        [
                            (
                                "Filing Deadline",
                                "Inventors must now submit an invention disclosure within "
                                "21 days of a working prototype, down from 60 days.",
                            ),
                            (
                                "Inventor Bonus",
                                "Each granted patent now earns a bonus of 2,500 dollars, "
                                "and the framed photo with the CEO is optional.",
                            ),
                        ],
                    )
                },
            },
        ],
    },
    {
        "name": "Data Retention Policy",
        "department": COMP,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-07-01",
                "format": "docx",
                "sections": [
                    (
                        "Purpose",
                        "This policy sets how long the company keeps records, so that the "
                        "basement stops filling up with boxes labeled 'SCHEMES MISC'.",
                    ),
                    (
                        "Scope",
                        "This policy covers paper records, digital files, inator logs and "
                        "security camera footage.",
                    ),
                    (
                        "Retention Periods",
                        {
                            "intro": "Records are kept for the following periods.",
                            "table": [
                                ["Record Type", "Retention Period"],
                                ["Financial records", "7 years"],
                                ["Inator test logs", "3 years"],
                                ["Security camera footage", "90 days"],
                                ["Monologue recordings", "30 days"],
                                ["Meeting minutes", "5 years"],
                            ],
                            "after": "Footage that shows a platypus is kept for 1 year "
                            "for pattern analysis.",
                        },
                    ),
                    (
                        "Destruction",
                        "Records past their retention period are shredded. Shredding by "
                        "Destroy-Paper-inator is permitted only outdoors.",
                    ),
                    (
                        "Legal Holds",
                        "Records under a legal hold may not be destroyed, even if they "
                        "are very embarrassing.",
                    ),
                    (
                        "Acknowledgment",
                        "Creating any record constitutes acknowledgment of this policy.",
                    ),
                ],
            },
            {
                "version": "2.0",
                "date": "2025-08-04",
                "format": "md",
                "base": "1.0",
                "purpose": "Version 2.0 extends camera footage retention after the company "
                "repeatedly deleted the only evidence of who keeps stealing the "
                "foosball.",
                "replace": {
                    "Retention Periods": (
                        "Retention Periods",
                        {
                            "intro": "Records are now kept for the following periods.",
                            "table": [
                                ["Record Type", "Retention Period"],
                                ["Financial records", "7 years"],
                                ["Inator test logs", "5 years"],
                                ["Security camera footage", "180 days"],
                                ["Monologue recordings", "30 days"],
                                ["Meeting minutes", "5 years"],
                                ["Feedback on chatbot answers", "1 year"],
                            ],
                            "after": "Footage that shows a platypus is now kept for 3 "
                            "years.",
                        },
                    )
                },
            },
        ],
    },
]
