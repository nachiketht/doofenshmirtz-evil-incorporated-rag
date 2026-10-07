"""HR, Learning & Development, Travel."""

HR = "Human Resources"
LD = "Henchperson Training"
TRAVEL = "Travel and Logistics"

REVIEW_V1 = [
    (
        "Purpose",
        "This policy explains how performance is reviewed at Doofenshmirtz Evil "
        "Incorporated, where success is measured in schemes attempted, not schemes "
        "completed, because otherwise nobody would ever get a raise.",
    ),
    (
        "Scope",
        "This policy applies to all employees who have completed their first 90 "
        "days, including robots.",
    ),
    (
        "Review Cycle",
        [
            (
                "Frequency",
                "Performance reviews happen once per year, in December, when the CEO "
                "is in a festive and slightly less evil mood.",
            ),
            (
                "Self-Assessment",
                "Employees write a one-page self-assessment. Self-assessments written as "
                "a monologue are accepted but read aloud at the review.",
            ),
        ],
    ),
    (
        "Rating Scale",
        {
            "intro": "Employees are rated on a five-point scale.",
            "table": [
                ["Rating", "Meaning"],
                ["5", "Diabolical"],
                ["4", "Devious"],
                ["3", "Adequately Evil"],
                ["2", "Mildly Inconvenient"],
                ["1", "Helped the Platypus"],
            ],
            "after": "A rating of 1 requires a follow-up meeting and a long, "
            "disappointed stare.",
        },
    ),
    (
        "Raises",
        "Employees rated 4 or 5 receive a raise of at least 3 percent. Employees rated "
        "5 also get their name on the lobby's Wall of Infamy.",
    ),
    (
        "Acknowledgment",
        "Receiving a review constitutes acknowledgment of this policy.",
    ),
]

FAMILIES = [
    {
        "name": "Remote Work and Tri-State Commute Policy",
        "department": HR,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-03-25",
                "format": "docx",
                "sections": [
                    (
                        "Purpose",
                        "This policy explains when employees may work remotely and how "
                        "the company supports commuting across the Tri-State Area, where "
                        "traffic is often caused by giant robots.",
                    ),
                    (
                        "Scope",
                        "This policy applies to all employees whose job does not require "
                        "physically guarding an inator.",
                    ),
                    (
                        "Remote Work",
                        [
                            (
                                "Remote Days",
                                "Eligible employees may work remotely up to 2 days per "
                                "week, agreed with their manager.",
                            ),
                            (
                                "Home Lairs",
                                "Employees working from home may not build inators larger "
                                "than a microwave in their kitchen.",
                            ),
                        ],
                    ),
                    (
                        "Commuting",
                        [
                            (
                                "Commute Stipend",
                                "Employees receive a commute stipend of 100 dollars per "
                                "month for transit, bikes or blimp fuel.",
                            ),
                            (
                                "Robot Traffic",
                                "Employees delayed by a giant robot, rampaging monster or "
                                "rival villain's scheme are not marked late.",
                            ),
                        ],
                    ),
                    (
                        "Equipment",
                        "Remote employees receive a laptop and one evil-looking desk lamp.",
                    ),
                    (
                        "Acknowledgment",
                        "Working from anywhere constitutes acknowledgment of this policy.",
                    ),
                ],
            },
            {
                "version": "2.0",
                "date": "2025-08-18",
                "format": "pdf",
                "base": "1.0",
                "purpose": "Version 2.0 increases remote days and the commute stipend "
                "after employees proved they scheme just as well in pajamas.",
                "replace": {
                    "Remote Work": (
                        "Remote Work",
                        [
                            (
                                "Remote Days",
                                "Eligible employees may now work remotely up to 3 days "
                                "per week, up from 2 days.",
                            ),
                            (
                                "Home Lairs",
                                "Home inators are now limited to the size of a toaster, "
                                "after a home Freeze-inator froze an entire apartment "
                                "block.",
                            ),
                        ],
                    ),
                    "Commuting": (
                        "Commuting",
                        [
                            (
                                "Commute Stipend",
                                "The commute stipend rises to 150 dollars per month.",
                            ),
                            (
                                "Robot Traffic",
                                "Delays caused by giant robots still do not count as "
                                "late, unless the robot belongs to the employee.",
                            ),
                        ],
                    ),
                },
            },
        ],
    },
    {
        "name": "Performance Review Policy",
        "department": HR,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-04-08",
                "format": "pdf",
                "sections": REVIEW_V1,
            },
            {
                "version": "2.0",
                "date": "2025-04-28",
                "format": "md",
                "base": "1.0",
                "purpose": "Version 2.0 adds a mid-year check-in, because a full year "
                "was too long to wait to find out you had helped the platypus.",
                "replace": {
                    "Review Cycle": (
                        "Review Cycle",
                        [
                            (
                                "Frequency",
                                "Performance reviews now happen twice per year, in June "
                                "and December.",
                            ),
                            (
                                "Self-Assessment",
                                "Self-assessments are limited to one page. Monologue-style "
                                "self-assessments are now limited to 2 minutes when read "
                                "aloud.",
                            ),
                        ],
                    )
                },
            },
            {
                "version": "3.0",
                "date": "2026-05-04",
                "format": "docx",
                "base": "2.0",
                "purpose": "Version 3.0 raises the minimum raise and adds peer feedback, "
                "so that reviews are no longer based entirely on the CEO's memory.",
                "replace": {
                    "Raises": (
                        "Raises",
                        "Employees rated 4 or 5 now receive a raise of at least 5 percent. "
                        "Employees rated 5 still get their name on the Wall of Infamy.",
                    )
                },
                "add": [
                    (
                        "Peer Feedback",
                        "Each review includes feedback from three peers. Feedback from "
                        "Norm is included automatically and is always positive.",
                    )
                ],
            },
        ],
    },
    {
        "name": "Training and Onboarding Policy",
        "department": LD,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-05-20",
                "format": "md",
                "sections": [
                    (
                        "Purpose",
                        "This policy explains how new henchpeople, scientists and interns "
                        "are trained, so that nobody presses the wrong button on their "
                        "first day.",
                    ),
                    (
                        "Scope",
                        "This policy applies to every new hire and every employee changing "
                        "roles.",
                    ),
                    (
                        "Onboarding",
                        [
                            (
                                "First Week",
                                "New hires spend their first week shadowing a senior "
                                "employee and learning where all the trap doors are.",
                            ),
                            (
                                "Required Courses",
                                "Required courses are Lab Safety Basics, Evil Laughing for "
                                "Beginners, and Recognizing a Platypus in Disguise.",
                            ),
                        ],
                    ),
                    (
                        "Ongoing Training",
                        "Every employee completes at least 10 hours of training per year. "
                        "Watching the CEO's old home videos counts for 1 hour, maximum.",
                    ),
                    (
                        "Certificates",
                        "Completed courses earn a certificate signed by the CEO with a "
                        "purple pen.",
                    ),
                    (
                        "Acknowledgment",
                        "Attending any training constitutes acknowledgment of this policy.",
                    ),
                ],
            },
            {
                "version": "2.0",
                "date": "2025-09-15",
                "format": "docx",
                "base": "1.0",
                "purpose": "Version 2.0 doubles annual training hours and adds a course "
                "on inator ethics, which leadership describes as 'mostly optional'.",
                "replace": {
                    "Ongoing Training": (
                        "Ongoing Training",
                        "Every employee now completes at least 20 hours of training per "
                        "year, up from 10 hours. Inator Ethics is required for anyone "
                        "with a soldering iron.",
                    )
                },
            },
        ],
    },
    {
        "name": "Travel Policy",
        "department": TRAVEL,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-06-10",
                "format": "pdf",
                "sections": [
                    (
                        "Purpose",
                        "This policy governs business travel, including conferences, "
                        "villain summits, and the CEO's frequent trips to Gimmelshtump to "
                        "visit old grudges.",
                    ),
                    (
                        "Scope",
                        "This policy applies to all travel paid for by the company.",
                    ),
                    (
                        "Booking",
                        [
                            (
                                "Advance Booking",
                                "Flights must be booked at least 14 days in advance. "
                                "Travel by company blimp requires 3 days of notice.",
                            ),
                            (
                                "Class of Travel",
                                "Employees fly economy. The CEO may fly business class, "
                                "or by blimp, or by a rocket of his own design, at his own "
                                "risk.",
                            ),
                        ],
                    ),
                    (
                        "Lodging",
                        "Hotels are booked through the travel desk. Hotels shaped like a "
                        "volcano are preferred but not required.",
                    ),
                    (
                        "Villain Summits",
                        "Attendance at villain summits requires manager approval and a "
                        "promise not to sign up for any joint scheme without Legal.",
                    ),
                    (
                        "Acknowledgment",
                        "Booking any trip constitutes acknowledgment of this policy.",
                    ),
                ],
            },
            {
                "version": "2.0",
                "date": "2025-10-06",
                "format": "md",
                "base": "1.0",
                "purpose": "Version 2.0 shortens the booking window and adds rules for "
                "travel through portals, which are cheaper but harder to expense.",
                "replace": {
                    "Booking": (
                        "Booking",
                        [
                            (
                                "Advance Booking",
                                "Flights must now be booked at least 21 days in advance, "
                                "up from 14 days. Blimp travel still needs 3 days of "
                                "notice.",
                            ),
                            (
                                "Class of Travel",
                                "Employees fly economy, and the CEO may still fly by "
                                "rocket at his own risk.",
                            ),
                        ],
                    )
                },
                "add": [
                    (
                        "Portal Travel",
                        "Travel by portal is allowed only to destinations in this "
                        "dimension. Receipts from other dimensions are not accepted.",
                    )
                ],
            },
        ],
    },
]
