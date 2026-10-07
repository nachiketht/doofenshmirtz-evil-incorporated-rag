"""Evil PR and Engineering."""

PR = "Evil PR"
ENG = "Engineering"

PR_V1 = [
    (
        "Purpose",
        "This policy governs how the company presents itself to the public, the "
        "media, and the citizens of the Tri-State Area, most of whom have seen our "
        "logo on at least one falling object.",
    ),
    (
        "Scope",
        "This policy applies to anyone speaking for the company, posting about the "
        "company, or appearing on the news near a smoking crater.",
    ),
    (
        "Social Media",
        [
            (
                "Approved Accounts",
                "Only the Evil PR team may post on official company accounts. Posts "
                "must include at least one evil laugh, written as 'mwahaha'.",
            ),
            (
                "Personal Accounts",
                "Employees may mention they work here, but may not post photos of "
                "unfinished inators or the CEO's baby pictures.",
            ),
        ],
    ),
    (
        "Media Requests",
        "All media requests go to Evil PR within 24 hours. Employees may not give "
        "interviews while a scheme is in progress.",
    ),
    (
        "Slogans",
        "The official slogan is 'Doofenshmirtz Evil Incorporated: Evil, But "
        "Incorporated'. New slogans must be approved by the CEO and tested on Norm.",
    ),
    (
        "Acknowledgment",
        "Speaking about the company in public constitutes acknowledgment of this "
        "policy.",
    ),
]

FAMILIES = [
    {
        "name": "Evil PR and Social Media Policy",
        "department": PR,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-02-19",
                "format": "docx",
                "sections": PR_V1,
            },
            {
                "version": "2.0",
                "date": "2025-02-03",
                "format": "md",
                "base": "1.0",
                "purpose": "Version 2.0 speeds up media responses after a news crew "
                "filmed the Giant Floating Baby Head for six hours with no comment from "
                "the company.",
                "replace": {
                    "Media Requests": (
                        "Media Requests",
                        "All media requests must now reach Evil PR within 2 hours, down "
                        "from 24 hours. Interviews during schemes remain prohibited.",
                    )
                },
                "add": [
                    (
                        "Influencers",
                        "The company may sponsor villain influencers with more than "
                        "10,000 followers, provided they never film the self-destruct "
                        "button.",
                    )
                ],
            },
            {
                "version": "3.0",
                "date": "2026-03-23",
                "format": "pdf",
                "base": "2.0",
                "purpose": "Version 3.0 retires the old slogan after focus groups in "
                "Danville said it was 'technically accurate but not inspiring'.",
                "replace": {
                    "Slogans": (
                        "Slogans",
                        "The official slogan is now 'Doofenshmirtz Evil Incorporated: "
                        "Taking Over the Tri-State Area, One Inator at a Time'. Old "
                        "merchandise may be sold at a discount.",
                    )
                },
            },
        ],
    },
    {
        "name": "Inator Code Review and Deployment Policy",
        "department": ENG,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-07-15",
                "format": "md",
                "sections": [
                    (
                        "Purpose",
                        "Modern inators run software. This policy explains how that "
                        "software is reviewed and deployed, so that no inator ships with "
                        "a bug that makes it shoot rainbows.",
                    ),
                    (
                        "Scope",
                        "This policy applies to all firmware, apps and scripts that "
                        "control an inator, robot or self-destruct mechanism.",
                    ),
                    (
                        "Code Review",
                        [
                            (
                                "Reviewers",
                                "Every change needs approval from one other engineer. "
                                "Changes to self-destruct logic need two approvals.",
                            ),
                            (
                                "Review Time",
                                "Reviews should be completed within 1 business day, or "
                                "before the next scheme, whichever comes first.",
                            ),
                        ],
                    ),
                    (
                        "Deployment",
                        [
                            (
                                "Deploy Windows",
                                "Inator software is deployed on Tuesdays and Wednesdays "
                                "only. Deploying on a Friday is forbidden.",
                            ),
                            (
                                "Rollback",
                                "Every deployment must have a rollback plan that works "
                                "even if a platypus has already unplugged the inator.",
                            ),
                        ],
                    ),
                    (
                        "Testing",
                        "Automated tests must pass before deployment. Testing in "
                        "production is allowed only on the Tri-State Area's least "
                        "important bridge.",
                    ),
                    (
                        "Acknowledgment",
                        "Merging any code constitutes acknowledgment of this policy.",
                    ),
                ],
            },
            {
                "version": "2.0",
                "date": "2025-11-03",
                "format": "docx",
                "base": "1.0",
                "purpose": "Version 2.0 removes the bridge from approved test sites and "
                "adds a staging lair, because the city noticed.",
                "replace": {
                    "Testing": (
                        "Testing",
                        "Automated tests must pass before deployment, and every release "
                        "must run for 24 hours in the staging lair before reaching any "
                        "real inator. Testing on bridges is prohibited.",
                    )
                },
            },
        ],
    },
]
