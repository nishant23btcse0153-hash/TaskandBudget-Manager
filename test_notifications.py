"""Test task notification system"""
from app import app, db, mail, User, Task
from notification_utils import check_and_send_notifications
from datetime import datetime, timedelta, timezone

# Timezone: IST (UTC +5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist_naive():
    """Return IST datetime (naive so it matches DB naive DateTime)."""
    return datetime.now(IST).replace(tzinfo=None)

print("=" * 70)
print("TESTING TASK NOTIFICATION SYSTEM")
print("=" * 70)

with app.app_context():
    # Get first user with notifications enabled
    user = User.query.filter_by(notifications_enabled=True, email_verified=True).first()
    
    if not user:
        print("\n❌ No users found with notifications enabled and email verified")
        print("Please:")
        print("1. Register and verify an account")
        print("2. Enable notifications at /settings/notifications")
        exit(1)
    
    print(f"\n✅ Testing with user: {user.email}")
    print(f"   Notifications enabled: {user.notifications_enabled}")
    print(f"   Notification window: {user.notification_hours} hours before deadline")
    
    # Check for existing pending tasks
    now = now_ist_naive()
    notification_time = now + timedelta(hours=user.notification_hours)
    
    tasks = Task.query.filter(
        Task.user_id == user.id,
        Task.status == 'pending',
        Task.deadline <= notification_time,
        Task.deadline > now
    ).all()
    
    print(f"\n� Found {len(tasks)} task(s) in notification window:")
    
    if tasks:
        for task in tasks:
            time_until = task.deadline - now
            hours_until = int(time_until.total_seconds() / 3600)
            print(f"   • '{task.title}' - due in {hours_until} hours")
            print(f"     Last notified: {task.last_notification_sent or 'Never'}")
    else:
        print("   No tasks found in notification window")
        print(f"\n   To test, create a task with deadline within {user.notification_hours} hours")
    
    # Run notification check
    print(f"\n🔍 Running notification check...")
    count = check_and_send_notifications(app, db, mail, User, Task)
    
    print(f"\n{'='*70}")
    print(f"✅ Notification check complete!")
    print(f"   {count} reminder(s) sent")
    print(f"{'='*70}")
    
    if count > 0:
        print(f"\n📧 Check your inbox at: {user.email}")
    else:
        print("\nNo notifications sent. This could mean:")
        print("  • Tasks were already notified within last 12 hours")
        print("  • No pending tasks in notification window")
        print("  • All tasks are overdue or completed")
