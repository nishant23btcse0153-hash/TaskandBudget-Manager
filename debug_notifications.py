"""Debug script to check why notifications might not be working
"""
from app import app, db, User, Task, mail
from datetime import datetime, timedelta, timezone
import sys

# Timezone: IST (UTC +5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist_naive():
    """Return IST datetime (naive so it matches DB naive DateTime)."""
    return datetime.now(IST).replace(tzinfo=None)

print("=" * 70)
print("NOTIFICATION DEBUG REPORT")
print("=" * 70)

with app.app_context():
    # Check email configuration
    print("\n1. EMAIL CONFIGURATION")
    print("-" * 70)
    mail_username = app.config.get('MAIL_USERNAME')
    mail_password = app.config.get('MAIL_PASSWORD')
    
    if not mail_username or not mail_password:
        print("❌ EMAIL NOT CONFIGURED!")
        print("   Email credentials are missing.")
        print("   This is why notifications aren't working!")
        sys.exit(1)
    else:
        print(f"✓ MAIL_USERNAME: {mail_username}")
        print(f"✓ MAIL_PASSWORD: {'*' * 16}")
    
    # Check users with notifications enabled
    print("\n2. USERS WITH NOTIFICATIONS ENABLED")
    print("-" * 70)
    users = User.query.filter_by(notifications_enabled=True, email_verified=True).all()
    
    if not users:
        print("❌ NO USERS with notifications enabled AND email verified")
        print("   Possible reasons:")
        print("   - No users in database")
        print("   - Users have notifications_enabled=False")
        print("   - Users have email_verified=False")
    else:
        print(f"✓ Found {len(users)} user(s) with notifications enabled:")
        for u in users:
            print(f"  - {u.email} (notification_hours: {u.notification_hours})")
    
    # Check pending tasks
    print("\n3. PENDING TASKS")
    print("=" * 50)
    
    now = now_ist_naive()
    total_tasks = 0
    notifiable_tasks = 0
    
    for user in users:
        tasks = Task.query.filter(
            Task.user_id == user.id,
            Task.status == 'pending'
        ).all()
        
        total_tasks += len(tasks)
        
        if tasks:
            print(f"\nUser: {user.email}")
            print(f"  Total pending tasks: {len(tasks)}")
            
            notification_window = now + timedelta(hours=user.notification_hours)
            
            for task in tasks:
                time_to_deadline = (task.deadline - now).total_seconds() / 3600
                within_window = task.deadline <= notification_window and task.deadline > now
                
                status = "✓" if within_window else "✗"
                print(f"  {status} '{task.title}':")
                print(f"      Deadline: {task.deadline}")
                print(f"      Time until deadline: {time_to_deadline:.1f} hours")
                print(f"      Within {user.notification_hours}h window: {within_window}")
                
                if task.last_notification_sent:
                    hours_since = (now - task.last_notification_sent).total_seconds() / 3600
                    print(f"      Last notified: {hours_since:.1f} hours ago")
                else:
                    print(f"      Last notified: Never")
                
                if within_window:
                    notifiable_tasks += 1
    
    if total_tasks == 0:
        print("❌ NO PENDING TASKS found")
        print("   Create some tasks with upcoming deadlines to test notifications")
    
    # Summary
    print("\n4. SUMMARY")
    print("-" * 70)
    
    issues = []
    
    if not mail_username or not mail_password:
        issues.append("Email credentials not configured")
    
    if not users:
        issues.append("No users with notifications enabled and email verified")
    
    if total_tasks == 0:
        issues.append("No pending tasks exist")
    
    if notifiable_tasks == 0 and total_tasks > 0:
        issues.append("Tasks exist but none are within notification window")
    
    if issues:
        print("❌ ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\nFIX THESE ISSUES TO ENABLE NOTIFICATIONS")
    else:
        print("✓ Everything looks good!")
        print(f"  - Email configured")
        print(f"  - {len(users)} user(s) with notifications enabled")
        print(f"  - {total_tasks} pending task(s)")
        print(f"  - {notifiable_tasks} task(s) ready for notification")
        print("\n💡 Try running the notification check now!")

print("\n" + "=" * 70)
