"""Finance and Procurement."""

FIN = "Finance"
PROC = "Procurement"

EXPENSE_V1 = [
    (
        "Purpose",
        "This policy explains how employees get reimbursed for money spent on "
        "company business, including evil business. It exists because the CEO once "
        "expensed a volcano and Finance has not emotionally recovered.",
    ),
    (
        "Scope",
        "This policy applies to all employees who spend their own money on behalf of "
        "Doofenshmirtz Evil Incorporated, anywhere in the Tri-State Area or beyond.",
    ),
    (
        "Eligible Expenses",
        [
            (
                "Covered Items",
                "Reimbursable expenses include inator parts, travel, client lunches, "
                "and replacement lab coats damaged by an inator that worked a little "
                "too well.",
            ),
            (
                "Excluded Items",
                "Expenses that are not reimbursable include fedoras, platypus food, "
                "personal revenge projects, and anything purchased primarily to impress "
                "an ex-wife.",
            ),
        ],
    ),
    (
        "Receipts and Deadlines",
        [
            (
                "Submission Deadline",
                "Expense claims must be submitted within 30 days of purchase, with an "
                "itemized receipt. Receipts written on napkins are accepted only if "
                "signed by the vendor.",
            ),
            (
                "Missing Receipts",
                "A missing receipt may be replaced by a sworn statement and a short "
                "interpretive dance performed for Finance, at Finance's discretion.",
            ),
        ],
    ),
    (
        "Approval Limits",
        [
            (
                "Manager Approval",
                "Managers may approve claims up to 500 dollars. Claims above that limit "
                "go to the CFO, who reviews them on Thursdays between naps.",
            ),
            (
                "Inator Purchases",
                "Any single purchase for an inator above 2,000 dollars requires a "
                "written description of what the inator does, in one sentence, with no "
                "backstory.",
            ),
        ],
    ),
    (
        "Reimbursement Timing",
        "Approved claims are paid with the next payroll cycle. Claims paid in "
        "doubloons, gold bars or experimental currency must be converted first.",
    ),
    (
        "Acknowledgment",
        "Submitting an expense claim constitutes acknowledgment of this policy and a "
        "solemn promise that the volcano was a one-time thing.",
    ),
]

FAMILIES = [
    {
        "name": "Expense Reimbursement Policy",
        "department": FIN,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-02-05",
                "format": "pdf",
                "sections": EXPENSE_V1,
            },
            {
                "version": "2.0",
                "date": "2025-01-13",
                "format": "docx",
                "base": "1.0",
                "purpose": "Version 2.0 shortens the receipt deadline and adds per-diem "
                "rules after an audit found a single business trip to Gimmelshtump that "
                "somehow included forty-one goat-cheese tastings.",
                "replace": {
                    "Receipts and Deadlines": (
                        "Receipts and Deadlines",
                        [
                            (
                                "Submission Deadline",
                                "Expense claims must now be submitted within 14 days of "
                                "purchase, down from 30 days, with an itemized receipt.",
                            ),
                            (
                                "Missing Receipts",
                                "The interpretive dance option is retired. A missing "
                                "receipt now requires a sworn statement countersigned by "
                                "a manager.",
                            ),
                        ],
                    )
                },
                "add": [
                    (
                        "Per Diem",
                        [
                            (
                                "Daily Meal Allowance",
                                "Employees traveling on company business receive a meal "
                                "per diem of 75 dollars per day, regardless of how many "
                                "goat-cheese tastings are available locally.",
                            ),
                            (
                                "Gimmelshtump Exception",
                                "Trips to Gimmelshtump receive an additional 10 dollars "
                                "per day for emotional support pastries.",
                            ),
                        ],
                    )
                ],
            },
            {
                "version": "3.0",
                "date": "2026-01-12",
                "format": "md",
                "base": "2.0",
                "purpose": "Version 3.0 introduces the company expense card and raises "
                "the manager approval limit, because managers were spending more time "
                "approving lunches than scheming.",
                "replace": {
                    "Approval Limits": (
                        "Approval Limits",
                        [
                            (
                                "Manager Approval",
                                "Managers may now approve claims up to 1,000 dollars, "
                                "doubled from the 500 dollars allowed under earlier "
                                "versions.",
                            ),
                            (
                                "Inator Purchases",
                                "Inator purchases above 2,000 dollars still require a one "
                                "sentence description. The sentence may no longer end "
                                "with an evil laugh.",
                            ),
                        ],
                    )
                },
                "add": [
                    (
                        "Company Expense Card",
                        [
                            (
                                "Eligibility",
                                "Employees with more than six months of service may "
                                "request a company expense card, which is purple and "
                                "shaped like a tiny self-destruct button.",
                            ),
                            (
                                "Card Limit",
                                "Each card has a monthly limit of 3,000 dollars. Pressing "
                                "the card like a button does not destroy anything, "
                                "despite repeated attempts.",
                            ),
                        ],
                    )
                ],
            },
        ],
    },
    {
        "name": "Evil Budget Allocation Policy",
        "department": FIN,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-03-04",
                "format": "pdf",
                "sections": [
                    (
                        "Purpose",
                        "This policy explains how the annual evil budget is divided "
                        "between departments, so that no single scheme can consume the "
                        "entire company's money again.",
                    ),
                    (
                        "Scope",
                        "This policy covers every department with a budget line, "
                        "including the departments the CEO forgot he created.",
                    ),
                    (
                        "Budget Split",
                        {
                            "intro": "The annual evil budget is split as follows.",
                            "table": [
                                ["Department", "Share of Budget"],
                                ["Inator R&D", "45 percent"],
                                ["Minion Operations", "20 percent"],
                                ["Facilities and Lair Upkeep", "15 percent"],
                                ["Evil PR", "10 percent"],
                                ["Everything Else", "10 percent"],
                            ],
                            "after": "Unspent budget returns to the general evil fund at "
                            "the end of the fiscal year.",
                        },
                    ),
                    (
                        "Mid-Year Requests",
                        [
                            (
                                "Request Window",
                                "Departments may request a mid-year budget increase once, "
                                "in June, by submitting a form and a convincing villain "
                                "backstory.",
                            ),
                            (
                                "Backstory Review",
                                "Backstories are scored by the CFO for emotional impact. "
                                "Backstories involving a childhood in Gimmelshtump score "
                                "automatically high, which Finance acknowledges is unfair.",
                            ),
                        ],
                    ),
                    (
                        "Overspend Consequences",
                        "A department that overspends its share loses its snack budget "
                        "for the following quarter.",
                    ),
                    (
                        "Acknowledgment",
                        "Department heads acknowledge this policy by spending responsibly, "
                        "or at least creatively.",
                    ),
                ],
            },
            {
                "version": "2.0",
                "date": "2025-03-03",
                "format": "docx",
                "base": "1.0",
                "purpose": "Version 2.0 rebalances the budget after Inator R&D spent its "
                "entire share by February on a single Make-Everything-Evil-inator that "
                "was destroyed by a platypus within the hour.",
                "replace": {
                    "Budget Split": (
                        "Budget Split",
                        {
                            "intro": "The annual evil budget is now split as follows.",
                            "table": [
                                ["Department", "Share of Budget"],
                                ["Inator R&D", "35 percent"],
                                ["Minion Operations", "20 percent"],
                                ["Facilities and Lair Upkeep", "15 percent"],
                                ["Evil PR", "10 percent"],
                                ["Platypus Countermeasures", "10 percent"],
                                ["Everything Else", "10 percent"],
                            ],
                            "after": "Inator R&D funding is released quarterly instead "
                            "of all at once.",
                        },
                    ),
                    "Overspend Consequences": (
                        "Overspend Consequences",
                        "A department that overspends loses its snack budget for two "
                        "quarters and must present a lessons-learned slideshow with no "
                        "evil laughing.",
                    ),
                },
            },
        ],
    },
    {
        "name": "Vendor and Procurement Policy",
        "department": PROC,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-04-01",
                "format": "md",
                "sections": [
                    (
                        "Purpose",
                        "This policy governs how the company buys things from other "
                        "companies, including the many questionable suppliers of the "
                        "Tri-State Area evil-supply market.",
                    ),
                    (
                        "Scope",
                        "This policy applies to every purchase made with company money, "
                        "from staplers to shrink rays.",
                    ),
                    (
                        "Approved Vendors",
                        [
                            (
                                "Vendor List",
                                "Purchases should be made from the approved vendor list, "
                                "which includes Evil Supplies Depot, Lasers R Us, and "
                                "Gary's Discount Self-Destruct Buttons.",
                            ),
                            (
                                "New Vendors",
                                "A new vendor must pass a background check and confirm in "
                                "writing that it is not a front for O.W.C.A.",
                            ),
                        ],
                    ),
                    (
                        "Quotes",
                        [
                            (
                                "Three-Quote Rule",
                                "Purchases above 5,000 dollars require three written quotes. "
                                "A quote from a vendor who laughs maniacally during the call "
                                "counts as half a quote.",
                            ),
                            (
                                "Sole Source",
                                "Single-vendor purchases are allowed only when the part is "
                                "unique, such as a replacement crystal for a de-love-inator.",
                            ),
                        ],
                    ),
                    (
                        "Payment Terms",
                        "Vendors are paid within 45 days of invoice. Vendors demanding "
                        "payment in the form of a captured platypus are removed from the "
                        "list.",
                    ),
                    (
                        "Acknowledgment",
                        "Anyone who buys anything acknowledges this policy, especially "
                        "the person who bought forty rubber chickens last spring.",
                    ),
                ],
            },
            {
                "version": "2.0",
                "date": "2025-05-05",
                "format": "pdf",
                "base": "1.0",
                "purpose": "Version 2.0 lowers the three-quote threshold and adds a "
                "sustainability rule, after Procurement discovered that 70 percent of "
                "inator parts were being bought from a single cousin.",
                "replace": {
                    "Quotes": (
                        "Quotes",
                        [
                            (
                                "Three-Quote Rule",
                                "Purchases above 2,500 dollars now require three written "
                                "quotes, down from 5,000 dollars. Quotes from relatives of "
                                "the buyer do not count.",
                            ),
                            (
                                "Sole Source",
                                "Single-vendor purchases require written approval from "
                                "Procurement and a one-paragraph explanation of why nobody "
                                "else sells that crystal.",
                            ),
                        ],
                    ),
                    "Payment Terms": (
                        "Payment Terms",
                        "Vendors are now paid within 30 days of invoice. Payment in "
                        "captured platypuses remains prohibited.",
                    ),
                },
                "add": [
                    (
                        "Sustainable Evil",
                        "At least one in five inator parts must be recycled or refurbished. "
                        "Parts salvaged from inators destroyed by Perry the Platypus count "
                        "toward this target.",
                    )
                ],
            },
        ],
    },
]
