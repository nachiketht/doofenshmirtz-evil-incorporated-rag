"""Lab Safety and Inator R&D."""

LAB = "Lab Safety"
RND = "Inator R&D"

LAB_V1 = [
    (
        "Purpose",
        "This policy keeps employees safe in the laboratories, where most of the "
        "company's inators are built, tested, and occasionally pointed at the wrong "
        "wall.",
    ),
    (
        "Scope",
        "This policy applies to anyone entering a laboratory, including visitors, "
        "interns, and robots on cleaning duty.",
    ),
    (
        "Protective Equipment",
        [
            (
                "Required Gear",
                "Safety goggles and a lab coat are required in every laboratory. Swim "
                "goggles are not safety goggles, no matter how tightly they fit.",
            ),
            (
                "Ray Testing Gear",
                "Anyone testing a ray must also wear a mirrored visor, in case the ray "
                "is reflected back by a shiny surface or a smug platypus.",
            ),
        ],
    ),
    (
        "Inator Testing",
        [
            (
                "Test Targets",
                "Inators may be tested only on approved targets, such as watermelons, "
                "mannequins, and the decommissioned photocopier.",
            ),
            (
                "Countdown Rule",
                "Every test must be preceded by a spoken countdown from five. Shouting "
                "'behold' does not replace the countdown.",
            ),
        ],
    ),
    (
        "Spills and Accidents",
        "Spills must be reported to Lab Safety within 15 minutes. Accidents that "
        "shrink, enlarge or turn anyone into a different animal must be reported "
        "immediately.",
    ),
    (
        "Acknowledgment",
        "Entering a laboratory constitutes acknowledgment of this policy and a promise "
        "never to lick anything glowing.",
    ),
]

SELF_DESTRUCT_V1 = [
    (
        "Purpose",
        "Every inator built at Doofenshmirtz Evil Incorporated has a self-destruct "
        "button. This policy makes that tradition official, because nobody remembers "
        "why we started doing it and nobody dares stop.",
    ),
    (
        "Scope",
        "This policy applies to every inator, gadget, robot and novelty mug capable of "
        "doing anything evil.",
    ),
    (
        "Button Requirements",
        [
            (
                "Button Size",
                "Each self-destruct button must be at least 3 inches across, bright "
                "red, and labeled 'SELF-DESTRUCT' in capital letters.",
            ),
            (
                "Button Placement",
                "The button must be placed somewhere a person could reach during a "
                "dramatic struggle, ideally at elbow height.",
            ),
        ],
    ),
    (
        "Testing",
        "Self-destruct buttons are tested by pressing them once, after which the "
        "inator must be rebuilt. Legal is still reviewing whether this is efficient.",
    ),
    (
        "Accidental Activation",
        "Employees who lean on a self-destruct button by accident must report it to "
        "Inator R&D and buy the team donuts.",
    ),
    (
        "Acknowledgment",
        "Building any inator constitutes acknowledgment of this policy.",
    ),
]

LIFECYCLE_V1 = [
    (
        "Purpose",
        "This policy describes the stages every inator passes through, from napkin "
        "sketch to spectacular destruction.",
    ),
    (
        "Scope",
        "This policy applies to every inator project, whether funded, unfunded, or "
        "built in the CEO's apartment over a weekend.",
    ),
    (
        "Stages",
        {
            "intro": "Every inator moves through these stages in order.",
            "bullets": [
                "Idea: a backstory explaining why the inator is needed",
                "Sketch: a drawing on a napkin, whiteboard or forearm",
                "Prototype: a version that works at least once",
                "Deployment: aimed at the Tri-State Area",
                "Destruction: usually by a platypus",
            ],
            "after": "Skipping the Sketch stage is prohibited after the Untitled "
            "Blob-inator incident.",
        },
    ),
    (
        "Stage Gates",
        [
            (
                "Prototype Review",
                "A prototype review with Inator R&D is required before deployment. The "
                "review lasts at most 30 minutes and must include a demo on a "
                "watermelon.",
            ),
            (
                "Deployment Approval",
                "Deployment requires sign-off from the CEO and confirmation that the "
                "self-destruct button is installed and labeled.",
            ),
        ],
    ),
    (
        "Post-Destruction Review",
        "After every destroyed inator, the team holds a 15-minute review covering what "
        "went wrong, who pressed the button, and whether a platypus was involved.",
    ),
    (
        "Acknowledgment",
        "Starting any inator project constitutes acknowledgment of this policy.",
    ),
]

FAMILIES = [
    {
        "name": "Laboratory Safety Policy",
        "department": LAB,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-01-29",
                "format": "pdf",
                "sections": LAB_V1,
            },
            {
                "version": "2.0",
                "date": "2025-01-27",
                "format": "docx",
                "base": "1.0",
                "purpose": "Version 2.0 shortens the spill reporting window and adds a "
                "buddy system after an intern spent a full afternoon as a houseplant "
                "before anyone noticed.",
                "replace": {
                    "Spills and Accidents": (
                        "Spills and Accidents",
                        "Spills must now be reported within 5 minutes, down from 15 "
                        "minutes. Transformations into animals, plants or furniture must "
                        "be reported immediately by the nearest buddy.",
                    )
                },
                "add": [
                    (
                        "Buddy System",
                        "Nobody may work alone in a laboratory. Each employee must have a "
                        "lab buddy who checks on them every 20 minutes and confirms they "
                        "are still a person.",
                    )
                ],
            },
            {
                "version": "3.0",
                "date": "2026-01-26",
                "format": "md",
                "base": "2.0",
                "purpose": "Version 3.0 adds rules for portal experiments, which are now "
                "frequent enough to need their own section.",
                "add": [
                    (
                        "Portal Experiments",
                        [
                            (
                                "Portal Limits",
                                "Only one portal may be open in a laboratory at a time. "
                                "Portals to other dimensions must be closed before lunch.",
                            ),
                            (
                                "Alternate Selves",
                                "Employees who meet an alternate version of themselves "
                                "must not ask it to cover their shift.",
                            ),
                        ],
                    )
                ],
            },
        ],
    },
    {
        "name": "Chemical Storage Policy",
        "department": LAB,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-03-18",
                "format": "md",
                "sections": [
                    (
                        "Purpose",
                        "This policy explains where and how chemicals are stored, so that "
                        "nobody confuses the Evil Goo with the coffee creamer again.",
                    ),
                    (
                        "Scope",
                        "This policy covers every chemical, goo, ooze, and unexplained "
                        "glowing liquid on company premises.",
                    ),
                    (
                        "Storage Rules",
                        [
                            (
                                "Labeling",
                                "Every container must be labeled with its contents and the "
                                "date it was made. Labels that only say 'DO NOT' are not "
                                "sufficient.",
                            ),
                            (
                                "Separation",
                                "Flammable chemicals are stored in the red cabinet and "
                                "anything that hums is stored in the blue cabinet.",
                            ),
                        ],
                    ),
                    (
                        "Quantity Limits",
                        "No laboratory may store more than 20 liters of flammable liquid "
                        "outside the red cabinet.",
                    ),
                    (
                        "Disposal",
                        "Chemicals are disposed of through Lab Safety. Pouring goo down the "
                        "drain is prohibited because the drain has filed a complaint.",
                    ),
                    (
                        "Acknowledgment",
                        "Handling any chemical constitutes acknowledgment of this policy.",
                    ),
                ],
            },
            {
                "version": "2.0",
                "date": "2025-04-21",
                "format": "pdf",
                "base": "1.0",
                "purpose": "Version 2.0 lowers the quantity limit and adds a goo inventory "
                "after the basement ooze became self-aware and requested dental "
                "coverage.",
                "replace": {
                    "Quantity Limits": (
                        "Quantity Limits",
                        "No laboratory may store more than 10 liters of flammable liquid "
                        "outside the red cabinet, down from 20 liters.",
                    )
                },
                "add": [
                    (
                        "Goo Inventory",
                        "All goo must be counted every Monday. Goo that has grown since "
                        "the last count is reported to Lab Safety, and goo that has "
                        "learned to speak is reported to HR.",
                    )
                ],
            },
        ],
    },
    {
        "name": "Inator Development Lifecycle Policy",
        "department": RND,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-02-12",
                "format": "docx",
                "sections": LIFECYCLE_V1,
            },
            {
                "version": "2.0",
                "date": "2025-03-17",
                "format": "pdf",
                "base": "1.0",
                "purpose": "Version 2.0 adds a mandatory platypus-resistance review, "
                "because every single inator in Version 1.0 reached the Destruction stage.",
                "add": [
                    (
                        "Platypus Resistance Review",
                        "Before deployment, every inator must survive a 10-minute test "
                        "against a trained intern in a teal costume and a fedora.",
                    )
                ],
            },
            {
                "version": "3.0",
                "date": "2026-04-06",
                "format": "md",
                "base": "2.0",
                "purpose": "Version 3.0 lengthens the prototype review and introduces an "
                "Inator Review Board, so the CEO is no longer the only approver.",
                "replace": {
                    "Stage Gates": (
                        "Stage Gates",
                        [
                            (
                                "Prototype Review",
                                "Prototype reviews may now last up to 60 minutes and "
                                "must include a demo on at least two watermelons.",
                            ),
                            (
                                "Deployment Approval",
                                "Deployment requires approval from the Inator Review "
                                "Board, made up of the CEO, the head of Lab Safety, and "
                                "Norm, who has a tie-breaking vote.",
                            ),
                        ],
                    )
                },
            },
        ],
    },
    {
        "name": "Self-Destruct Button Policy",
        "department": RND,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-01-15",
                "format": "md",
                "sections": SELF_DESTRUCT_V1,
            },
            {
                "version": "2.0",
                "date": "2025-01-20",
                "format": "pdf",
                "base": "1.0",
                "purpose": "Version 2.0 enlarges the button and adds a protective cover, "
                "after an analysis found that 80 percent of inators were destroyed by "
                "their own self-destruct button.",
                "replace": {
                    "Button Requirements": (
                        "Button Requirements",
                        [
                            (
                                "Button Size",
                                "Each self-destruct button must now be at least 6 inches "
                                "across, up from 3 inches, because the CEO kept missing "
                                "the smaller ones during demos.",
                            ),
                            (
                                "Button Placement",
                                "The button must be at elbow height and protected by a "
                                "flip-up cover that a platypus cannot open with one "
                                "flipper.",
                            ),
                        ],
                    )
                },
            },
            {
                "version": "3.0",
                "date": "2026-02-09",
                "format": "docx",
                "base": "2.0",
                "purpose": "Version 3.0 adds a confirmation prompt to every self-destruct "
                "button, which the CEO calls 'the most evil thing we have ever done to "
                "drama'.",
                "add": [
                    (
                        "Confirmation Prompt",
                        [
                            (
                                "Prompt Rule",
                                "Pressing the button now triggers a voice prompt asking "
                                "'Are you sure?' The inator self-destructs only if the "
                                "button is pressed a second time within 5 seconds.",
                            ),
                            (
                                "Prompt Voice",
                                "The prompt must be recorded in the CEO's voice. Norm's "
                                "voice was tested and found to be too reassuring.",
                            ),
                        ],
                    )
                ],
            },
        ],
    },
]
