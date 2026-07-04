from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42


def ensure_data(data_dir: Path, force: bool = False) -> dict[str, Path]:
    """Create the local demo datasets when they are missing."""
    data_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "opspilot": data_dir / "opspilot_requests.csv",
        "dogs": data_dir / "rescueops_dogs.csv",
        "inquiries": data_dir / "rescueops_inquiries.csv",
        "volunteers": data_dir / "rescueops_volunteers.csv",
        "medical": data_dir / "rescueops_medical_costs.csv",
    }

    if force or any(not path.exists() for path in paths.values()):
        rng = np.random.default_rng(SEED)
        opspilot = generate_opspilot_requests(rng)
        dogs = generate_rescueops_dogs(rng)
        inquiries = generate_rescueops_inquiries(rng, dogs)
        volunteers = generate_rescueops_volunteers(rng)
        medical = generate_rescueops_medical_costs(rng, dogs)

        opspilot.to_csv(paths["opspilot"], index=False)
        dogs.to_csv(paths["dogs"], index=False)
        inquiries.to_csv(paths["inquiries"], index=False)
        volunteers.to_csv(paths["volunteers"], index=False)
        medical.to_csv(paths["medical"], index=False)

    return paths


def _choice(rng: np.random.Generator, values: list, probabilities: list[float] | None = None):
    return rng.choice(values, p=probabilities)


def _business_name_pool() -> list[str]:
    first = [
        "Avery",
        "Jordan",
        "Taylor",
        "Morgan",
        "Riley",
        "Casey",
        "Jamie",
        "Parker",
        "Quinn",
        "Reese",
        "Cameron",
        "Drew",
        "Hayden",
        "Rowan",
        "Skyler",
        "Emerson",
        "Logan",
        "Harper",
        "Finley",
        "Kendall",
    ]
    last = [
        "Johnson",
        "Patel",
        "Nguyen",
        "Garcia",
        "Smith",
        "Brown",
        "Miller",
        "Wilson",
        "Davis",
        "Clark",
        "Lewis",
        "Allen",
        "Young",
        "King",
        "Scott",
        "Wright",
    ]
    return [f"{f} {l}" for f in first for l in last]


def generate_opspilot_requests(rng: np.random.Generator, rows: int = 720) -> pd.DataFrame:
    today = date.today()
    request_types = [
        "Access Request",
        "Purchase Approval",
        "HR Update",
        "Compliance Review",
        "Document Correction",
        "Equipment Request",
        "Vendor Setup",
        "Policy Exception",
        "Customer Escalation",
        "Training Assignment",
    ]
    request_type_prob = [0.14, 0.13, 0.1, 0.11, 0.12, 0.09, 0.1, 0.07, 0.08, 0.06]
    departments = ["HR", "Finance", "Operations", "IT", "Compliance", "Procurement", "Facilities"]
    department_prob = [0.12, 0.16, 0.2, 0.17, 0.11, 0.16, 0.08]
    stages = ["Intake", "Review", "Approval", "Fulfillment", "Waiting on Requester", "Closeout"]
    stage_prob = [0.13, 0.17, 0.25, 0.16, 0.2, 0.09]
    priorities = ["Low", "Medium", "High", "Critical"]
    priority_prob = [0.22, 0.47, 0.24, 0.07]
    names = _business_name_pool()

    assigned_team_map = {
        "Access Request": "IT Access Queue",
        "Purchase Approval": "Finance Approvals",
        "HR Update": "People Ops",
        "Compliance Review": "Compliance Review",
        "Document Correction": "Operations Intake",
        "Equipment Request": "Facilities Support",
        "Vendor Setup": "Procurement Ops",
        "Policy Exception": "Risk Review",
        "Customer Escalation": "Customer Recovery",
        "Training Assignment": "Learning Ops",
    }
    sla_by_priority = {"Low": 15, "Medium": 10, "High": 5, "Critical": 2}
    stage_delay_base = {
        "Intake": (2, 6),
        "Review": (4, 12),
        "Approval": (8, 28),
        "Fulfillment": (4, 14),
        "Waiting on Requester": (9, 32),
        "Closeout": (1, 5),
    }
    manual_minutes_by_type = {
        "Access Request": 24,
        "Purchase Approval": 38,
        "HR Update": 28,
        "Compliance Review": 52,
        "Document Correction": 34,
        "Equipment Request": 31,
        "Vendor Setup": 48,
        "Policy Exception": 55,
        "Customer Escalation": 44,
        "Training Assignment": 22,
    }

    records: list[dict] = []
    for i in range(rows):
        request_type = str(_choice(rng, request_types, request_type_prob))
        department = str(_choice(rng, departments, department_prob))
        process_stage = str(_choice(rng, stages, stage_prob))
        priority = str(_choice(rng, priorities, priority_prob))
        low, high = stage_delay_base[process_stage]
        days_open = int(rng.integers(low, high + 1))

        if process_stage == "Approval" and rng.random() < 0.42:
            days_open += int(rng.integers(7, 22))
        if process_stage == "Waiting on Requester" and rng.random() < 0.35:
            days_open += int(rng.integers(6, 18))
        if department in {"Finance", "Procurement", "Operations"} and rng.random() < 0.24:
            days_open += int(rng.integers(4, 12))

        current_status = str(
            _choice(
                rng,
                ["Open", "In Progress", "Pending", "Escalated", "Closed"],
                [0.25, 0.27, 0.2, 0.08, 0.2],
            )
        )
        if process_stage in {"Approval", "Waiting on Requester"} and current_status == "Closed":
            current_status = "Pending"
        if process_stage == "Closeout":
            current_status = str(_choice(rng, ["Closed", "In Progress"], [0.78, 0.22]))

        approval_required = bool(
            request_type in {"Purchase Approval", "Vendor Setup", "Policy Exception", "Compliance Review"}
            or rng.random() < 0.28
        )
        if not approval_required:
            approval_status = "Not Required"
        elif process_stage == "Approval" or current_status == "Pending":
            approval_status = "Pending"
        else:
            approval_status = str(_choice(rng, ["Approved", "Pending", "Rejected"], [0.65, 0.3, 0.05]))

        missing_prob = 0.12
        if process_stage in {"Intake", "Waiting on Requester"}:
            missing_prob += 0.22
        if request_type in {"Vendor Setup", "Compliance Review", "Document Correction"}:
            missing_prob += 0.16
        required_documents_missing = bool(rng.random() < missing_prob)

        duplicate_flag = bool(rng.random() < (0.06 + (0.06 if request_type in {"Access Request", "HR Update"} else 0)))
        rework_flag = bool(
            rng.random()
            < (
                0.1
                + (0.14 if request_type in {"Document Correction", "Compliance Review"} else 0)
                + (0.08 if required_documents_missing else 0)
            )
        )

        cycle_time_days = days_open if current_status != "Closed" else max(1, int(days_open * rng.uniform(0.45, 0.9)))
        sla_days = sla_by_priority[priority]
        sla_breached = bool(cycle_time_days > sla_days)
        manual_minutes = max(
            8,
            int(
                rng.normal(manual_minutes_by_type[request_type], 9)
                + (14 if rework_flag else 0)
                + (10 if required_documents_missing else 0)
                + (7 if duplicate_flag else 0)
            ),
        )
        touches = int(
            rng.integers(2, 7)
            + (2 if rework_flag else 0)
            + (2 if required_documents_missing else 0)
            + (1 if approval_status == "Pending" else 0)
        )

        if priority == "Critical" or (sla_breached and department in {"Finance", "Compliance", "Operations"}):
            business_impact = "Critical"
        elif priority == "High" or sla_breached or rework_flag:
            business_impact = "High"
        elif required_documents_missing or duplicate_flag:
            business_impact = "Medium"
        else:
            business_impact = "Low"

        if required_documents_missing:
            candidate_type = "Missing Document Follow-Up"
        elif approval_status == "Pending":
            candidate_type = "Approval Reminder Automation"
        elif duplicate_flag:
            candidate_type = "Duplicate Request Detection"
        elif sla_breached:
            candidate_type = "SLA Escalation Alerts"
        elif process_stage == "Intake":
            candidate_type = "Request Intake Validation"
        elif rework_flag:
            candidate_type = "Rework Prevention Checklist"
        elif request_type in {"Access Request", "Training Assignment", "Equipment Request"}:
            candidate_type = "Auto-Routing by Request Type"
        else:
            candidate_type = "Recurring Status Summary"

        submitted_date = today - timedelta(days=days_open + int(rng.integers(0, 12)))
        records.append(
            {
                "request_id": f"REQ-{100000 + i}",
                "request_type": request_type,
                "department": department,
                "requester": str(_choice(rng, names)),
                "assigned_team": assigned_team_map[request_type],
                "submitted_date": submitted_date.isoformat(),
                "current_status": current_status,
                "process_stage": process_stage,
                "priority": priority,
                "required_documents_missing": required_documents_missing,
                "duplicate_flag": duplicate_flag,
                "rework_flag": rework_flag,
                "approval_required": approval_required,
                "approval_status": approval_status,
                "owner": str(_choice(rng, names)),
                "days_open": 0 if current_status == "Closed" else days_open,
                "cycle_time_days": cycle_time_days,
                "touches_count": touches,
                "estimated_manual_minutes": manual_minutes,
                "sla_days": sla_days,
                "sla_breached": sla_breached,
                "business_impact": business_impact,
                "automation_candidate_type": candidate_type,
            }
        )

    return pd.DataFrame(records)


def generate_rescueops_dogs(rng: np.random.Generator, rows: int = 96) -> pd.DataFrame:
    today = date.today()
    dog_names = [
        "Rosie",
        "Maple",
        "Buddy",
        "Luna",
        "Milo",
        "Daisy",
        "Scout",
        "Ruby",
        "Finn",
        "Bella",
        "Cooper",
        "Penny",
        "Winnie",
        "Nora",
        "Otis",
        "Sadie",
        "Theo",
        "Hazel",
        "Archie",
        "Ivy",
        "Moose",
        "Pepper",
        "Gus",
        "Maggie",
        "Blue",
        "Millie",
        "Remy",
        "Ellie",
        "Tucker",
        "Zoe",
        "Hank",
        "Cleo",
        "Louie",
        "Honey",
        "Beau",
        "Mabel",
        "Jasper",
        "Poppy",
        "Oakley",
        "Nala",
        "Benny",
        "Olive",
        "Charlie",
        "June",
        "Murphy",
        "Willow",
        "Rex",
        "Maisie",
        "Sam",
        "Pearl",
        "Rory",
        "Sasha",
        "Frankie",
        "Grace",
        "Henry",
        "Mia",
        "Atlas",
        "Bonnie",
        "George",
        "Cookie",
        "Lucky",
        "Birdie",
        "Harley",
        "Lola",
        "Biscuit",
        "Molly",
        "Chase",
        "Annie",
        "Wally",
        "Fiona",
        "Dexter",
        "Tilly",
        "Jack",
        "Minnie",
        "Bruno",
        "Kona",
        "Rocco",
        "Summer",
        "Diesel",
        "Violet",
        "Baxter",
        "Clover",
        "Boomer",
        "Phoebe",
        "Cash",
        "Macy",
        "Ranger",
        "Sophie",
        "Toby",
        "Layla",
        "Comet",
        "Ember",
        "Rudy",
        "Tessa",
        "Ace",
        "Sunny",
        "Marley",
        "Georgia",
        "Knox",
        "Callie",
        "Ollie",
        "Joy",
    ]
    breed_mix = [
        "Labrador mix",
        "Shepherd mix",
        "Terrier mix",
        "Hound mix",
        "Boxer mix",
        "Beagle mix",
        "Pit mix",
        "Husky mix",
        "Chihuahua mix",
        "Great Pyrenees mix",
        "Cattle Dog mix",
        "Retriever mix",
        "Spaniel mix",
        "Mastiff mix",
    ]
    statuses = ["Intake", "In Foster", "Medical Hold", "Adoption Ready", "Pending Adoption", "Adopted", "Foster Needed"]
    status_prob = [0.1, 0.26, 0.13, 0.2, 0.09, 0.12, 0.1]
    medical_statuses = [
        "Clear",
        "Routine Care",
        "Vaccines Needed",
        "Heartworm Treatment",
        "Surgery Needed",
        "Emergency",
        "Dental Needed",
        "Medical Hold",
    ]
    medical_prob = [0.31, 0.16, 0.14, 0.09, 0.08, 0.04, 0.09, 0.09]

    records: list[dict] = []
    chosen_names = list(rng.choice(dog_names, size=rows, replace=False))
    for i, name in enumerate(chosen_names):
        current_status = str(_choice(rng, statuses, status_prob))
        medical_status = str(_choice(rng, medical_statuses, medical_prob))
        if medical_status in {"Surgery Needed", "Emergency", "Medical Hold"} and rng.random() < 0.55:
            current_status = "Medical Hold"
        if current_status == "Adopted":
            adoption_status = "Adopted"
        elif current_status == "Pending Adoption":
            adoption_status = "Application Pending"
        elif current_status == "Adoption Ready":
            adoption_status = "Available"
        else:
            adoption_status = str(_choice(rng, ["Not Ready", "Available Soon", "Needs Review"], [0.55, 0.25, 0.2]))

        days_in_care = int(rng.integers(3, 210))
        age_group = str(_choice(rng, ["Puppy", "Young", "Adult", "Senior"], [0.18, 0.24, 0.42, 0.16]))
        breed = str(_choice(rng, breed_mix))
        special_needs = bool(medical_status in {"Heartworm Treatment", "Surgery Needed", "Emergency", "Medical Hold"} or rng.random() < 0.12)
        adoption_ready = bool(current_status in {"Adoption Ready", "Pending Adoption"} and medical_status not in {"Emergency", "Surgery Needed"})
        foster_status = (
            "Needs Foster"
            if current_status in {"Foster Needed", "Intake"}
            else str(_choice(rng, ["In Foster", "Short-Term Foster", "Boarding", "Needs Backup"], [0.58, 0.17, 0.13, 0.12]))
        )
        cost_base = {
            "Clear": 65,
            "Routine Care": 105,
            "Vaccines Needed": 130,
            "Heartworm Treatment": 260,
            "Surgery Needed": 410,
            "Emergency": 650,
            "Dental Needed": 220,
            "Medical Hold": 340,
        }[medical_status]
        estimated_monthly_cost = int(max(35, rng.normal(cost_base, cost_base * 0.25)))

        if medical_status in {"Emergency", "Surgery Needed"}:
            priority = "Critical"
        elif current_status == "Foster Needed" or special_needs:
            priority = str(_choice(rng, ["High", "Critical"], [0.75, 0.25]))
        elif days_in_care > 120 or medical_status in {"Heartworm Treatment", "Medical Hold"}:
            priority = "High"
        elif adoption_ready:
            priority = "Medium"
        else:
            priority = str(_choice(rng, ["Low", "Medium"], [0.45, 0.55]))

        records.append(
            {
                "dog_id": f"DOG-{1000 + i}",
                "dog_name": str(name),
                "age_group": age_group,
                "breed_mix": breed,
                "intake_date": (today - timedelta(days=days_in_care)).isoformat(),
                "current_status": current_status,
                "foster_status": foster_status,
                "adoption_status": adoption_status,
                "medical_status": medical_status,
                "behavior_notes": str(
                    _choice(
                        rng,
                        [
                            "Friendly and energetic",
                            "Shy at first",
                            "Needs slow introductions",
                            "Crate trained",
                            "Leash work in progress",
                            "Loves quiet routines",
                            "High play drive",
                        ],
                    )
                ),
                "special_needs": special_needs,
                "good_with_dogs": str(_choice(rng, ["Yes", "No", "Unknown"], [0.62, 0.13, 0.25])),
                "good_with_cats": str(_choice(rng, ["Yes", "No", "Unknown"], [0.36, 0.24, 0.4])),
                "good_with_children": str(_choice(rng, ["Yes", "No", "Unknown"], [0.46, 0.18, 0.36])),
                "energy_level": str(_choice(rng, ["Low", "Medium", "High"], [0.22, 0.48, 0.3])),
                "priority_level": priority,
                "days_in_care": days_in_care,
                "estimated_monthly_cost": estimated_monthly_cost,
                "adoption_ready": adoption_ready,
                "bio_needed": bool(adoption_ready and rng.random() < 0.48),
                "social_post_needed": bool((adoption_ready or current_status == "Foster Needed") and rng.random() < 0.62),
            }
        )

    return pd.DataFrame(records)


def generate_rescueops_inquiries(
    rng: np.random.Generator, dogs: pd.DataFrame, rows: int = 420
) -> pd.DataFrame:
    today = date.today()
    inquiry_types = [
        "Adoption Inquiry",
        "Foster Inquiry",
        "Volunteer Inquiry",
        "Donation Question",
        "Surrender Request",
        "Medical Question",
        "General Info",
    ]
    inquiry_prob = [0.38, 0.18, 0.12, 0.09, 0.09, 0.06, 0.08]
    dog_names = dogs["dog_name"].tolist()
    household_types = ["Apartment", "House with Yard", "Townhome", "Rural Property", "Condo"]
    experience_levels = ["First-Time", "Some Experience", "Experienced", "Rescue/Foster Experience"]

    records: list[dict] = []
    for i in range(rows):
        inquiry_type = str(_choice(rng, inquiry_types, inquiry_prob))
        dog_name = str(_choice(rng, dog_names))
        dog = dogs.loc[dogs["dog_name"] == dog_name].iloc[0]
        days_waiting = int(rng.integers(0, 12))
        has_children = bool(rng.random() < 0.34)
        has_other_pets = bool(rng.random() < 0.55)
        experience = str(_choice(rng, experience_levels, [0.21, 0.36, 0.28, 0.15]))
        response_status = str(
            _choice(
                rng,
                ["New", "In Review", "Responded", "Overdue", "Escalated"],
                [0.18, 0.24, 0.38, 0.14, 0.06],
            )
        )
        if days_waiting > 3 and response_status in {"New", "In Review"}:
            response_status = "Overdue"

        if inquiry_type == "Medical Question":
            triage = "Medical/Safety Escalation"
            priority_score = 92
        elif inquiry_type == "Surrender Request":
            triage = "Urgent Human Review" if days_waiting > 1 else "Needs Follow-Up"
            priority_score = 78 + min(days_waiting * 3, 15)
        elif inquiry_type == "Adoption Inquiry":
            incompatible_children = has_children and dog["good_with_children"] == "No"
            incompatible_pets = has_other_pets and dog["good_with_dogs"] == "No"
            if incompatible_children or incompatible_pets:
                triage = "Not Ideal Fit"
                priority_score = 55 + min(days_waiting * 4, 24)
            elif experience == "First-Time" and bool(dog["special_needs"]):
                triage = "Needs Follow-Up"
                priority_score = 66 + min(days_waiting * 4, 24)
            elif dog["adoption_ready"]:
                triage = "Strong Match"
                priority_score = 70 + min(days_waiting * 4, 24)
            else:
                triage = "Missing Information"
                priority_score = 60 + min(days_waiting * 4, 24)
        elif days_waiting > 3:
            triage = "Needs Follow-Up"
            priority_score = 68 + min(days_waiting * 3, 20)
        else:
            triage = str(_choice(rng, ["Strong Match", "Needs Follow-Up", "Missing Information"], [0.25, 0.45, 0.3]))
            priority_score = {"Strong Match": 72, "Needs Follow-Up": 62, "Missing Information": 52}[triage] + days_waiting * 2

        action_map = {
            "Strong Match": "Send application link and schedule screening call.",
            "Needs Follow-Up": "Send targeted follow-up questions within 24 hours.",
            "Missing Information": "Request missing household and pet compatibility details.",
            "Not Ideal Fit": "Route to adoption lead for careful human review.",
            "Urgent Human Review": "Escalate to intake coordinator today.",
            "Medical/Safety Escalation": "Route to rescue leadership and veterinary contact.",
        }

        records.append(
            {
                "inquiry_id": f"INQ-{5000 + i}",
                "inquiry_date": (today - timedelta(days=days_waiting + int(rng.integers(0, 4)))).isoformat(),
                "inquiry_type": inquiry_type,
                "dog_name": dog_name,
                "applicant_name": str(_choice(rng, _business_name_pool())),
                "household_type": str(_choice(rng, household_types)),
                "has_children": has_children,
                "has_other_pets": has_other_pets,
                "experience_level": experience,
                "message": str(
                    _choice(
                        rng,
                        [
                            "Interested in learning more and next steps.",
                            "Can you tell me whether this dog may fit our home?",
                            "We would like to help but need guidance.",
                            "Checking on availability and response timeline.",
                            "Looking for the best way to support the rescue.",
                        ],
                    )
                ),
                "response_status": response_status,
                "days_waiting": days_waiting,
                "triage_category": triage,
                "priority_score": int(min(priority_score, 100)),
                "recommended_action": action_map[triage],
            }
        )

    return pd.DataFrame(records)


def generate_rescueops_volunteers(rng: np.random.Generator, rows: int = 86) -> pd.DataFrame:
    roles = [
        "Foster",
        "Transport",
        "Adoption Screener",
        "Medical Coordinator",
        "Fundraising",
        "Social Media",
        "Event Support",
        "Volunteer Coordinator",
    ]
    role_prob = [0.25, 0.17, 0.14, 0.08, 0.1, 0.09, 0.1, 0.07]
    locations = ["North", "South", "East", "West", "Central", "Remote"]
    records: list[dict] = []
    for i in range(rows):
        role = str(_choice(rng, roles, role_prob))
        can_foster = bool(role == "Foster" or rng.random() < 0.18)
        foster_capacity = int(rng.integers(0, 4)) if can_foster else 0
        current_assignments = int(rng.integers(0, foster_capacity + 1)) if foster_capacity else 0
        records.append(
            {
                "volunteer_id": f"VOL-{7000 + i}",
                "volunteer_name": str(_choice(rng, _business_name_pool())),
                "role": role,
                "availability": str(_choice(rng, ["Weekends", "Weeknights", "Flexible", "Limited"], [0.3, 0.24, 0.28, 0.18])),
                "can_foster": can_foster,
                "can_transport": bool(role == "Transport" or rng.random() < 0.36),
                "can_handle_medical": bool(role == "Medical Coordinator" or rng.random() < 0.22),
                "can_handle_seniors": bool(rng.random() < 0.34),
                "can_handle_large_dogs": bool(rng.random() < 0.42),
                "foster_capacity": foster_capacity,
                "current_assignments": current_assignments,
                "location": str(_choice(rng, locations)),
                "reliability_score": int(rng.integers(62, 99)),
            }
        )
    return pd.DataFrame(records)


def generate_rescueops_medical_costs(
    rng: np.random.Generator, dogs: pd.DataFrame, rows: int = 180
) -> pd.DataFrame:
    today = date.today()
    expense_types = [
        "Surgery",
        "Medication",
        "Vaccines",
        "Spay/Neuter",
        "Emergency Vet",
        "Heartworm Treatment",
        "Dental",
        "Diagnostic Testing",
        "Routine Visit",
    ]
    amount_ranges = {
        "Surgery": (850, 3200),
        "Medication": (35, 260),
        "Vaccines": (55, 180),
        "Spay/Neuter": (160, 420),
        "Emergency Vet": (450, 2200),
        "Heartworm Treatment": (700, 1800),
        "Dental": (350, 1450),
        "Diagnostic Testing": (120, 850),
        "Routine Visit": (75, 210),
    }
    urgency_map = {
        "Surgery": "High",
        "Medication": "Medium",
        "Vaccines": "Medium",
        "Spay/Neuter": "Medium",
        "Emergency Vet": "Critical",
        "Heartworm Treatment": "High",
        "Dental": "High",
        "Diagnostic Testing": "Medium",
        "Routine Visit": "Low",
    }

    dog_names = dogs["dog_name"].tolist()
    records: list[dict] = []
    for i in range(rows):
        dog_name = str(_choice(rng, dog_names))
        dog = dogs.loc[dogs["dog_name"] == dog_name].iloc[0]
        if dog["medical_status"] == "Surgery Needed":
            expense_type = str(_choice(rng, ["Surgery", "Diagnostic Testing", "Medication"], [0.58, 0.24, 0.18]))
        elif dog["medical_status"] == "Emergency":
            expense_type = str(_choice(rng, ["Emergency Vet", "Diagnostic Testing", "Medication"], [0.66, 0.22, 0.12]))
        elif dog["medical_status"] == "Heartworm Treatment":
            expense_type = "Heartworm Treatment"
        elif dog["medical_status"] == "Dental Needed":
            expense_type = "Dental"
        else:
            expense_type = str(_choice(rng, expense_types))

        low, high = amount_ranges[expense_type]
        amount = round(float(rng.uniform(low, high)), 2)
        funded_status = str(_choice(rng, ["Funded", "Partially Funded", "Unfunded"], [0.38, 0.31, 0.31]))
        urgency = urgency_map[expense_type]
        if funded_status == "Unfunded" and urgency == "Medium" and rng.random() < 0.25:
            urgency = "High"
        records.append(
            {
                "expense_id": f"MED-{9000 + i}",
                "dog_name": dog_name,
                "expense_date": (today - timedelta(days=int(rng.integers(0, 120)))).isoformat(),
                "expense_type": expense_type,
                "amount": amount,
                "funded_status": funded_status,
                "urgency": urgency,
                "notes": str(
                    _choice(
                        rng,
                        [
                            "Needs funding visibility.",
                            "Track before adoption readiness review.",
                            "Coordinate with volunteer medical lead.",
                            "Candidate for donor update.",
                            "Add to weekly founder review.",
                        ],
                    )
                ),
            }
        )
    return pd.DataFrame(records)
