from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models.user import Role, User, Officer
from backend.app.models.department import Department
from backend.app.models.complaint import ComplaintCategory

def seed_db():
    print("Creating all tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Seed Roles
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
            
        # 2. Seed Departments
        print("Seeding Departments...")
        depts = [
            {"name": "Bruhat Bengaluru Mahanagara Palike", "code": "BBMP"},
            {"name": "Bangalore Water Supply and Sewerage Board", "code": "BWSSB"},
            {"name": "Bangalore Electricity Supply Company", "code": "BESCOM"},
            {"name": "Bengaluru Traffic Police", "code": "Traffic Police"}
        ]
        db_depts = {}
        for d_info in depts:
            dept = db.query(Department).filter(Department.code == d_info["code"]).first()
            if not dept:
                dept = Department(name=d_info["name"], code=d_info["code"])
                db.add(dept)
                db.flush()
            db_depts[d_info["code"]] = dept
            
        # 3. Seed Complaint Categories
        print("Seeding Complaint Categories...")
        categories = [
            {"name": "Garbage", "dept": "BBMP", "priority": "Medium"},
            {"name": "Pothole", "dept": "BBMP", "priority": "Medium"},
            {"name": "Water Leakage", "dept": "BWSSB", "priority": "Medium"},
            {"name": "No Water Supply", "dept": "BWSSB", "priority": "High"},
            {"name": "Streetlight", "dept": "BESCOM", "priority": "Low"},
            {"name": "Sewage Overflow", "dept": "BWSSB", "priority": "High"},
            {"name": "Tree Fall", "dept": "BBMP", "priority": "Medium"},
            {"name": "Road Damage", "dept": "BBMP", "priority": "Low"},
            {"name": "Illegal Dumping", "dept": "BBMP", "priority": "Medium"},
            {"name": "Others", "dept": "BBMP", "priority": "Low"}
        ]
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
                
        # 4. Seed Admin
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
            
        # 5. Seed Citizen
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
            
        # 6. Seed Officers
        print("Seeding Officer Users...")
        officer_accounts = [
            {"name": "Rajesh Kumar (BBMP)", "email": "officer.bbmp@civicai.gov.in", "dept": "BBMP"},
            {"name": "Anil Gowda (BWSSB)", "email": "officer.bwssb@civicai.gov.in", "dept": "BWSSB"},
            {"name": "Manjunath Swamy (BESCOM)", "email": "officer.bescom@civicai.gov.in", "dept": "BESCOM"},
            {"name": "Police Inspector Girish (BTP)", "email": "officer.traffic@civicai.gov.in", "dept": "Traffic Police"}
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
                
        db.commit()
        print("Database seeded successfully!")
    except Exception as e:
        db.rollback()
        print("Failed to seed database:", e)
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
