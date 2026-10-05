"""Minion Operations and Incident Response."""

MIN = "Minion Operations"
IR = "Incident Response"

SCHEDULE_V1 = [
    (
        "Purpose",
        "This policy sets shift schedules for minions, henchpeople and robot staff, "
        "so that someone is always available to guard the inator and someone else is "
        "always available to fetch snacks.",
    ),
    (
        "Scope",
        "This policy applies to all minions, henchpeople, Norm-bots and temporary "
        "goons hired for large schemes.",
    ),
    (
        "Shifts",
        [
            (
                "Shift Length",
                "Minion shifts are 8 hours long, with a 30-minute lunch and two 10-minute "
                "breaks for menacing glances.",
            ),
            (
                "Night Shift",
                "At least two minions must guard the lair overnight. Night-shift minions "
                "receive a 15 percent pay bonus and a nightlight.",
            ),
        ],
    ),
    (
        "Shift Swaps",
        [
            (
                "Swap Requests",
                "Minions may swap shifts with each other if both agree and the swap is "
                "posted on the scheduling board at least 48 hours in advance.",
            ),
            (
                "Robot Swaps",
                "Robots may not swap shifts with humans, because Norm keeps volunteering "
                "for every shift.",
            ),
        ],
    ),
    (
        "Scheme Days",
        "On days when a major scheme is active, all minions are scheduled for a full "
        "shift and paid overtime for any hour spent being chased.",
    ),
    (
        "Acknowledgment",
        "Clocking in for any shift constitutes acknowledgment of this policy.",
    ),
]

UNIFORM_V1 = [
    (
        "Purpose",
        "This policy defines the official henchperson uniform, so that the company's "
        "goons look menacing, consistent, and easy to tell apart from the enemy.",
    ),
    (
        "Scope",
        "This policy applies to all henchpeople and minions working on scheme days.",
    ),
    (
        "Uniform Items",
        [
            (
                "Standard Uniform",
                "The standard uniform is a purple jumpsuit with the company logo on the "
                "back and a matching purple helmet.",
            ),
            (
                "Footwear",
                "Henchpeople must wear black boots with soft soles, so they can sneak "
                "up on a nemesis without squeaking.",
            ),
        ],
    ),
    (
        "Laundry",
        "Uniforms are laundered weekly by Facilities. Uniforms that come back a "
        "different color must be worn anyway until replacements arrive.",
    ),
    (
        "Acknowledgment",
        "Putting on the uniform constitutes acknowledgment of this policy.",
    ),
]

INCIDENT_V1 = [
    (
        "Purpose",
        "This policy describes how the company responds to incidents, which at this "
        "company happen roughly every afternoon around 3 p.m.",
    ),
    (
        "Scope",
        "This policy covers security breaches, inator malfunctions, nemesis "
        "intrusions, and any explosion larger than a popcorn bag.",
    ),
    (
        "Severity Levels",
        {
            "intro": "Every incident is assigned a severity level.",
            "table": [
                ["Level", "Example", "Response Time"],
                ["Sev 1", "Inator aimed at the Tri-State Area by mistake", "Immediate"],
                ["Sev 2", "Nemesis intrusion in progress", "15 minutes"],
                ["Sev 3", "Minor explosion in a lab", "1 hour"],
                ["Sev 4", "Someone took the last donut", "Next business day"],
            ],
            "after": "When in doubt, an incident is classified one level more severe.",
        },
    ),
    (
        "Response Steps",
        [
            (
                "Declare",
                "Any employee may declare an incident by pressing the red alarm button "
                "and shouting the severity level.",
            ),
            (
                "Command",
                "The Incident Commander is the most senior person present who is not "
                "currently trapped.",
            ),
        ],
    ),
    (
        "Post-Incident Report",
        "An incident report must be written within 3 business days for every Sev 1 or "
        "Sev 2 incident.",
    ),
    (
        "Acknowledgment",
        "Surviving any incident constitutes acknowledgment of this policy.",
    ),
]

FAMILIES = [
    {
        "name": "Minion Scheduling Policy",
        "department": MIN,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-02-05",
                "format": "md",
                "sections": SCHEDULE_V1,
            },
            {
                "version": "2.0",
                "date": "2025-02-10",
                "format": "pdf",
                "base": "1.0",
                "purpose": "Version 2.0 shortens minion shifts and raises the night "
                "bonus after the minion union pointed out that being chased by a "
                "platypus is cardio and cardio is tiring.",
                "replace": {
                    "Shifts": (
                        "Shifts",
                        [
                            (
                                "Shift Length",
                                "Minion shifts are now 7 hours long, down from 8 hours, "
                                "with a 30-minute lunch and two breaks for menacing "
                                "glances.",
                            ),
                            (
                                "Night Shift",
                                "At least two minions must guard the lair overnight. The "
                                "night-shift bonus rises to 20 percent, and the nightlight "
                                "is now shaped like the company logo.",
                            ),
                        ],
                    )
                },
            },
            {
                "version": "3.0",
                "date": "2026-02-23",
                "format": "docx",
                "base": "2.0",
                "purpose": "Version 3.0 introduces the four-day scheme week, because "
                "schemes on Fridays have a 100 percent failure rate.",
                "add": [
                    (
                        "Four-Day Scheme Week",
                        [
                            (
                                "Schedule",
                                "Minions work four days per week, Monday to Thursday. "
                                "Fridays are reserved for repairs and naps.",
                            ),
                            (
                                "Friday Emergencies",
                                "Minions called in on a Friday receive double pay and a "
                                "written apology from the CEO.",
                            ),
                        ],
                    )
                ],
            },
        ],
    },
    {
        "name": "Henchperson Uniform Policy",
        "department": MIN,
        "status": "retired",
        "versions": [
            {
                "version": "1.0",
                "date": "2024-01-15",
                "format": "docx",
                "sections": UNIFORM_V1,
            },
            {
                "version": "2.0",
                "date": "2024-11-04",
                "format": "md",
                "base": "1.0",
                "purpose": "Version 2.0 switched the uniform to bright orange for "
                "visibility. This version was retired after henchpeople were mistaken "
                "for traffic cones across the Tri-State Area, and the whole policy is "
                "kept only for the audit trail.",
                "replace": {
                    "Uniform Items": (
                        "Uniform Items",
                        [
                            (
                                "Standard Uniform",
                                "The standard uniform became a bright orange jumpsuit "
                                "with reflective stripes and an orange helmet.",
                            ),
                            (
                                "Footwear",
                                "Henchpeople wear orange boots with soft soles.",
                            ),
                        ],
                    )
                },
            },
        ],
    },
    {
        "name": "Incident Response Policy",
        "department": IR,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-01-22",
                "format": "pdf",
                "sections": INCIDENT_V1,
            },
            {
                "version": "2.0",
                "date": "2025-01-06",
                "format": "md",
                "base": "1.0",
                "purpose": "Version 2.0 speeds up nemesis response and shortens the "
                "reporting window, after a Sev 2 intrusion turned into a Sev 1 while "
                "everyone was looking for the alarm button.",
                "replace": {
                    "Severity Levels": (
                        "Severity Levels",
                        {
                            "intro": "Every incident is assigned a severity level.",
                            "table": [
                                ["Level", "Example", "Response Time"],
                                [
                                    "Sev 1",
                                    "Inator aimed at the Tri-State Area by mistake",
                                    "Immediate",
                                ],
                                ["Sev 2", "Nemesis intrusion in progress", "5 minutes"],
                                ["Sev 3", "Minor explosion in a lab", "1 hour"],
                                [
                                    "Sev 4",
                                    "Someone took the last donut",
                                    "Next business day",
                                ],
                            ],
                            "after": "Alarm buttons are now installed in every room, "
                            "including the elevators.",
                        },
                    ),
                    "Post-Incident Report": (
                        "Post-Incident Report",
                        "An incident report must now be written within 2 business days "
                        "for every Sev 1 or Sev 2 incident, down from 3 days.",
                    ),
                },
            },
            {
                "version": "3.0",
                "date": "2026-01-19",
                "format": "docx",
                "base": "2.0",
                "purpose": "Version 3.0 adds an on-call rotation and blameless reviews, "
                "because the previous reviews always blamed the platypus.",
                "add": [
                    (
                        "On-Call Rotation",
                        [
                            (
                                "Rotation",
                                "One engineer and one minion are on call each week. "
                                "On-call staff must answer an alarm within 10 minutes.",
                            ),
                            (
                                "Blameless Reviews",
                                "Post-incident reviews focus on systems, not people. "
                                "Blaming a platypus is allowed only if the platypus is "
                                "in the security footage.",
                            ),
                        ],
                    )
                ],
            },
        ],
    },
    {
        "name": "Nemesis Engagement Policy",
        "department": IR,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-05-13",
                "format": "docx",
                "sections": [
                    (
                        "Purpose",
                        "Every respectable evil company has a nemesis. This policy sets "
                        "the general etiquette for engaging with ours, a certain "
                        "semi-aquatic secret agent in a fedora, without revealing "
                        "anything classified.",
                    ),
                    (
                        "Scope",
                        "This policy applies to every employee who may encounter the "
                        "nemesis, which is all of them, usually on Tuesdays.",
                    ),
                    (
                        "Etiquette",
                        [
                            (
                                "Greeting",
                                "When the nemesis arrives, the CEO greets it by full name "
                                "and title. Employees may wave but should not offer a "
                                "handshake, flipper-shake or snack.",
                            ),
                            (
                                "Trapping",
                                "Only the CEO may trap the nemesis, usually right before a "
                                "monologue. Employees who trap the "
                                "nemesis by accident must release it and apologize.",
                            ),
                        ],
                    ),
                    (
                        "Fighting",
                        "Fights with the nemesis must avoid the server room and the "
                        "break room fridge. Furniture broken during a fight is replaced "
                        "by Facilities within one week.",
                    ),
                    (
                        "Aftermath",
                        "After the nemesis escapes, employees should shout a "
                        "company-approved phrase of frustration, then return to work.",
                    ),
                    (
                        "Acknowledgment",
                        "Being in the building on a Tuesday constitutes acknowledgment "
                        "of this policy.",
                    ),
                ],
            },
            {
                "version": "2.0",
                "date": "2025-06-16",
                "format": "pdf",
                "base": "1.0",
                "purpose": "Version 2.0 extends fight rules to the new rooftop garden, "
                "and limits the number of employees who may watch a fight.",
                "replace": {
                    "Fighting": (
                        "Fighting",
                        "Fights with the nemesis must avoid the server room, the break "
                        "room fridge, and the rooftop garden. No more than five "
                        "employees may watch a fight, and none may sell tickets.",
                    )
                },
            },
        ],
    },
]
