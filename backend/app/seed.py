from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models.user import Role, User, Officer
from backend.app.models.department import Department
from backend.app.models.complaint import ComplaintCategory, SLAPolicy

def seed_db():
    print("Creating all tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # ─── 1. Seed Roles ──────────────────────────────────────────────────────────
        print("Seeding Roles...")
        roles = ["Citizen", "Officer", "Admin"]
        db_roles = {}
        for r_name in roles:
            role = db.query(Role).filter(Role.name == r_name).first()
            if not role:
                role = Role(name=r_name)
                db.add(role)
                db.flush()
            db_roles[r_name] = role
            
        # ─── 2. Seed Departments (ONLY 4 Karnataka Agencies) ────────────────────────
        print("Seeding Departments (4 Karnataka Authorities)...")
        depts = [
            {
                "name": "Bruhat Bengaluru Mahanagara Palike",
                "code": "BBMP",
            },
            {
                "name": "Bangalore Electricity Supply Company",
                "code": "BESCOM",
            },
            {
                "name": "Bangalore Water Supply and Sewerage Board",
                "code": "BWSSB",
            },
            {
                "name": "Bengaluru Solid Waste Management Limited",
                "code": "BSWML",
            },
        ]
        db_depts = {}
        for d_info in depts:
            dept = db.query(Department).filter(Department.code == d_info["code"]).first()
            if not dept:
                dept = Department(name=d_info["name"], code=d_info["code"])
                db.add(dept)
                db.flush()
            db_depts[d_info["code"]] = dept
            
        # ─── 3. Seed Complaint Categories ───────────────────────────────────────────
        print("Seeding Complaint Categories for 4 Departments...")
        categories = [
            # 1. BBMP – Roads & Civic Infrastructure
            {"name": "Potholes & Damaged Roads",                 "dept": "BBMP",   "priority": "High"},
            {"name": "Broken Footpaths & Walkways",              "dept": "BBMP",   "priority": "Medium"},
            {"name": "Blocked Stormwater Drains & Waterlogging", "dept": "BBMP",   "priority": "High"},
            {"name": "Damaged Streetlights",                     "dept": "BBMP",   "priority": "Medium"},
            {"name": "Park Maintenance & Public Gardens",       "dept": "BBMP",   "priority": "Low"},
            {"name": "Road & Footpath Encroachment",             "dept": "BBMP",   "priority": "Medium"},
            {"name": "Tree Fall & Dangerous Branches",           "dept": "BBMP",   "priority": "High"},
            {"name": "Stray Animal & Dead Animal Removal",       "dept": "BBMP",   "priority": "Medium"},
            {"name": "Construction Debris & Road Cave-in",       "dept": "BBMP",   "priority": "High"},
            {"name": "Public Toilet & Civic Amenities",          "dept": "BBMP",   "priority": "Low"},
            {"name": "Pothole",                                  "dept": "BBMP",   "priority": "High"},
            {"name": "Road Damage",                              "dept": "BBMP",   "priority": "Medium"},
            {"name": "Tree Fall",                                "dept": "BBMP",   "priority": "High"},
            {"name": "Streetlight",                              "dept": "BBMP",   "priority": "Medium"},
            {"name": "Others",                                   "dept": "BBMP",   "priority": "Low"},

            # 2. BESCOM – Electricity Distribution
            {"name": "Power Outage & Blackout",                  "dept": "BESCOM", "priority": "High"},
            {"name": "Frequent Power Cuts",                      "dept": "BESCOM", "priority": "Medium"},
            {"name": "Voltage Fluctuation (Low/High)",           "dept": "BESCOM", "priority": "Medium"},
            {"name": "Transformer Failure & Sparks",             "dept": "BESCOM", "priority": "Critical"},
            {"name": "Damaged Electric Poles & Broken Wires",    "dept": "BESCOM", "priority": "Critical"},
            {"name": "Exposed Wires & Electrical Hazards",       "dept": "BESCOM", "priority": "Critical"},
            {"name": "Distribution Feeder & Cable Fault",        "dept": "BESCOM", "priority": "Medium"},
            {"name": "Electricity Meter & Billing Issues",       "dept": "BESCOM", "priority": "Low"},
            {"name": "Power Outage",                             "dept": "BESCOM", "priority": "High"},
            {"name": "Fallen Electric Wire",                     "dept": "BESCOM", "priority": "Critical"},

            # 3. BWSSB – Water Supply & Underground Drainage
            {"name": "No Water Supply",                          "dept": "BWSSB",  "priority": "High"},
            {"name": "Low Water Pressure",                       "dept": "BWSSB",  "priority": "Medium"},
            {"name": "Water Pipeline Burst & Leakage",           "dept": "BWSSB",  "priority": "High"},
            {"name": "Contaminated Drinking Water",              "dept": "BWSSB",  "priority": "Critical"},
            {"name": "Sewage Overflow & Gutter Water",           "dept": "BWSSB",  "priority": "High"},
            {"name": "Blocked Sewer Line & Manhole Overflow",    "dept": "BWSSB",  "priority": "High"},
            {"name": "Damaged Manhole Cover & Missing Lid",      "dept": "BWSSB",  "priority": "Critical"},
            {"name": "Water Meter & Tanker Issues",              "dept": "BWSSB",  "priority": "Low"},
            {"name": "Water Leakage",                            "dept": "BWSSB",  "priority": "High"},
            {"name": "Sewage Overflow",                          "dept": "BWSSB",  "priority": "High"},

            # 4. BSWML – Solid Waste Management
            {"name": "Garbage Not Collected",                    "dept": "BSWML",  "priority": "High"},
            {"name": "Irregular Garbage Collection",             "dept": "BSWML",  "priority": "Medium"},
            {"name": "Overflowing Garbage Bins & Blackspots",    "dept": "BSWML",  "priority": "High"},
            {"name": "Illegal Roadside Waste Dumping",           "dept": "BSWML",  "priority": "Medium"},
            {"name": "Foul Smell & Waste Health Hazard",         "dept": "BSWML",  "priority": "High"},
            {"name": "Garbage Burning & Air Pollution",          "dept": "BSWML",  "priority": "Critical"},
            {"name": "Wet & Dry Waste Segregation Issues",       "dept": "BSWML",  "priority": "Low"},
            {"name": "Bulk & Construction Waste Dumping",        "dept": "BSWML",  "priority": "Medium"},
            {"name": "Dead Animal Waste on Road",                "dept": "BSWML",  "priority": "High"},
            {"name": "Garbage",                                  "dept": "BSWML",  "priority": "High"},
            {"name": "Illegal Dumping",                          "dept": "BSWML",  "priority": "Medium"},
        ]
        db_cats = {}
        for cat_info in categories:
            cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == cat_info["name"]).first()
            if not cat:
                cat = ComplaintCategory(
                    name=cat_info["name"],
                    department_id=db_depts[cat_info["dept"]].id,
                    default_priority=cat_info["priority"],
                    is_active=True
                )
                db.add(cat)
                db.flush()
            else:
                # Update department mapping to ensure correct routing
                cat.department_id = db_depts[cat_info["dept"]].id
                cat.default_priority = cat_info["priority"]
                cat.is_active = True
                db.flush()
            db_cats[cat_info["name"]] = cat
        
        # Deactivate any deprecated categories belonging to removed departments
        for old_cat in db.query(ComplaintCategory).all():
            if old_cat.name not in db_cats:
                old_cat.is_active = False
            elif old_cat.department and old_cat.department.code not in db_depts:
                old_cat.is_active = False
        db.flush()

        # ─── 4. Seed SLA Policies ────────────────────────────────────────────────────
        print("Seeding SLA Policies...")
        default_sla = {
            "Critical": 12.0,
            "High":     24.0,
            "Medium":   48.0,
            "Low":      72.0,
        }
        for cat_name, cat_obj in db_cats.items():
            for priority, hours in default_sla.items():
                existing = db.query(SLAPolicy).filter(
                    SLAPolicy.category_id == cat_obj.id,
                    SLAPolicy.priority == priority
                ).first()
                if not existing:
                    db.add(SLAPolicy(
                        category_id=cat_obj.id,
                        priority=priority,
                        resolution_hours=hours,
                        warning_threshold_pct=0.75
                    ))
        
        # ─── 5. Seed Admin User ─────────────────────────────────────────────────────
        print("Seeding Admin User...")
        admin_email = "admin@civicai.gov.in"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                name="Karnataka Civic Admin",
                email=admin_email,
                hashed_password=get_password_hash("adminpassword"),
                role_id=db_roles["Admin"].id,
                phone="9876543210",
                status="Active"
            )
            db.add(admin)
            
        # ─── 6. Seed Citizen User ────────────────────────────────────────────────────
        print("Seeding Citizen User...")
        citizen_email = "citizen@gmail.com"
        citizen = db.query(User).filter(User.email == citizen_email).first()
        if not citizen:
            citizen = User(
                name="Siddaramaiah K",
                email=citizen_email,
                hashed_password=get_password_hash("citizenpassword"),
                role_id=db_roles["Citizen"].id,
                phone="9988776655",
                status="Active"
            )
            db.add(citizen)
            
        # ─── 7. Seed Officer Accounts (EXACTLY 4 DEPARTMENTS) ─────────────────────────
        print("Seeding Officer Users for 4 Departments...")
        officer_accounts = [
            {"name": "Rajesh Kumar (BBMP)",         "email": "officer.bbmp@civicai.gov.in",    "dept": "BBMP"},
            {"name": "Manjunath Swamy (BESCOM)",     "email": "officer.bescom@civicai.gov.in",  "dept": "BESCOM"},
            {"name": "Anil Gowda (BWSSB)",          "email": "officer.bwssb@civicai.gov.in",   "dept": "BWSSB"},
            {"name": "Sunitha Murthy (BSWML)",       "email": "officer.bswml@civicai.gov.in",   "dept": "BSWML"},
        ]
        for off_info in officer_accounts:
            user = db.query(User).filter(User.email == off_info["email"]).first()
            if not user:
                user = User(
                    name=off_info["name"],
                    email=off_info["email"],
                    hashed_password=get_password_hash("officerpassword"),
                    role_id=db_roles["Officer"].id,
                    phone="9008007001",
                    status="Active"
                )
                db.add(user)
                db.flush()
                
                officer = Officer(
                    user_id=user.id,
                    department_id=db_depts[off_info["dept"]].id,
                    status="On Duty"
                )
                db.add(officer)
            else:
                user.status = "Active"
                # Update officer department link
                off_profile = db.query(Officer).filter(Officer.user_id == user.id).first()
                if off_profile:
                    off_profile.department_id = db_depts[off_info["dept"]].id
                    off_profile.status = "On Duty"
                else:
                    db.add(Officer(
                        user_id=user.id,
                        department_id=db_depts[off_info["dept"]].id,
                        status="On Duty"
                    ))
        
        # Deactivate any non-4-department officer users if present
        bmtc_user = db.query(User).filter(User.email == "officer.bmtc@civicai.gov.in").first()
        if bmtc_user:
            bmtc_user.status = "Inactive"
            bmtc_off = db.query(Officer).filter(Officer.user_id == bmtc_user.id).first()
            if bmtc_off:
                bmtc_off.status = "Off Duty"

        db.commit()
        print("=" * 60)
        print("Database seeded successfully with 4 Departments!")
        print("=" * 60)
        print("\nTest Accounts:")
        print("  Citizen  : citizen@gmail.com           / citizenpassword")
        print("  BBMP     : officer.bbmp@civicai.gov.in   / officerpassword")
        print("  BESCOM   : officer.bescom@civicai.gov.in / officerpassword")
        print("  BWSSB    : officer.bwssb@civicai.gov.in  / officerpassword")
        print("  BSWML    : officer.bswml@civicai.gov.in  / officerpassword")
        print("  Admin    : admin@civicai.gov.in          / adminpassword")
    except Exception as e:
        db.rollback()
        print("Failed to seed database:", e)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
