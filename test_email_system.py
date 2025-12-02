"""
Comprehensive Email System Test
Tests all email features: verification, password reset, and task notifications
"""

from app import app, db, User, Task, mail
from email_utils import send_verification_email, send_password_reset_email, generate_token
from notification_utils import send_task_reminder
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash

# Timezone: IST (UTC +5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist_naive():
    """Return IST datetime (naive so it matches DB naive DateTime)."""
    return datetime.now(IST).replace(tzinfo=None)
import sys

print("=" * 70)
print("COMPREHENSIVE EMAIL SYSTEM TEST")
print("=" * 70)

with app.app_context():
    # Check email configuration
    print("\n1. CHECKING EMAIL CONFIGURATION")
    print("-" * 70)
    
    mail_user = app.config.get('MAIL_USERNAME')
    mail_pass = app.config.get('MAIL_PASSWORD')
    server_name = app.config.get('SERVER_NAME')
    
    if not mail_user or not mail_pass:
        print("❌ EMAIL NOT CONFIGURED!")
        print("   Please run: . .\\setup_email_env.ps1")
        sys.exit(1)
    
    print(f"✓ MAIL_USERNAME: {mail_user}")
    print(f"✓ MAIL_PASSWORD: {'*' * 16} (set)")
    print(f"✓ SERVER_NAME: {server_name}")
    print(f"✓ MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    print(f"✓ MAIL_PORT: {app.config.get('MAIL_PORT')}")
    
    # Test 1: Email Verification
    print("\n2. TESTING EMAIL VERIFICATION")
    print("-" * 70)
    
    test_email = input("Enter your email address for testing: ").strip()
    
    if not test_email:
        print("❌ No email provided. Exiting.")
        sys.exit(1)
    
    print(f"Sending verification email to {test_email}...")
    token = generate_token(test_email)
    
    try:
        result = send_verification_email(mail, test_email, token)
        if result:
            print("✓ Verification email sent successfully!")
            print(f"  Check your inbox: {test_email}")
        else:
            print("❌ Failed to send verification email")
    except Exception as e:
        print(f"❌ Error sending verification email: {e}")
    
    # Test 2: Password Reset Email
    print("\n3. TESTING PASSWORD RESET EMAIL")
    print("-" * 70)
    
    reset_token = generate_token(test_email, salt="password-reset")
    print(f"Sending password reset email to {test_email}...")
    
    try:
        result = send_password_reset_email(mail, test_email, reset_token)
        if result:
            print("✓ Password reset email sent successfully!")
            print(f"  Check your inbox: {test_email}")
        else:
            print("❌ Failed to send password reset email")
    except Exception as e:
        print(f"❌ Error sending password reset email: {e}")
    
    # Test 3: Task Deadline Notification
    print("\n4. TESTING TASK DEADLINE NOTIFICATION")
    print("-" * 70)
    
    # Check if test user exists
    test_user = User.query.filter_by(email=test_email).first()
    
    if not test_user:
        print("Creating temporary test user...")
        test_user = User(
            email=test_email,
            password=generate_password_hash("test123"),
            email_verified=True,
            notifications_enabled=True,
            notification_hours=24
        )
        db.session.add(test_user)
        db.session.commit()
        print(f"✓ Test user created (ID: {test_user.id})")
        cleanup_user = True
    else:
        print(f"✓ Using existing user (ID: {test_user.id})")
        cleanup_user = False
    
    # Create test task
    deadline = now_ist_naive() + timedelta(hours=12)
    test_task = Task(
        title="Test Task - Email Notification",
        description="This is a test task to verify email notifications work correctly.",
        deadline=deadline,
        priority="High",
        status="pending",
        user_id=test_user.id
    )
    db.session.add(test_task)
    db.session.commit()
    print(f"✓ Test task created (ID: {test_task.id})")
    
    # Send notification
    print(f"Sending task notification email to {test_email}...")
    
    try:
        result = send_task_reminder(
            mail=mail,
            user_email=test_user.email,
            task_title=test_task.title,
            task_deadline=test_task.deadline,
            task_priority=test_task.priority,
            task_description=test_task.description
        )
        
        if result:
            print("✓ Task notification email sent successfully!")
            print(f"  Check your inbox: {test_email}")
            test_task.last_notification_sent = datetime.utcnow()
            db.session.commit()
        else:
            print("❌ Failed to send task notification email")
    except Exception as e:
        print(f"❌ Error sending task notification: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    print("\n5. CLEANUP")
    print("-" * 70)
    
    cleanup = input("Delete test task and user? (y/n): ").lower()
    
    if cleanup == 'y':
        db.session.delete(test_task)
        if cleanup_user:
            db.session.delete(test_user)
        db.session.commit()
        print("✓ Test data cleaned up")
    else:
        print("ℹ️  Test data kept in database")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("\n📧 Check your email inbox for 3 emails:")
    print("   1. Email Verification")
    print("   2. Password Reset")
    print("   3. Task Deadline Notification")
    print("\n✓ All tests completed!")
    print("=" * 70)
