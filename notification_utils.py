"""Task notification system for sending deadline reminders.
"""
from flask import render_template
from flask_mail import Message
from datetime import datetime, timedelta, timezone

# Timezone: IST (UTC +5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist_naive():
    """Return IST datetime (naive so it matches DB naive DateTime)."""
    return datetime.now(IST).replace(tzinfo=None)

def send_task_reminder(mail, user_email, task_title, task_deadline, task_priority, task_description=None):
    """Send task deadline reminder email"""
    try:
        from flask import current_app
        
        msg = Message(
            f'Task Reminder: {task_title}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user_email]
        )
        
        # Calculate time remaining
        now = now_ist_naive()
        time_left = task_deadline - now
        hours_left = int(time_left.total_seconds() / 3600)
        
        if hours_left < 0:
            time_left_str = "OVERDUE"
        elif hours_left < 24:
            time_left_str = f"{hours_left} hours"
        else:
            days_left = hours_left // 24
            time_left_str = f"{days_left} day{'s' if days_left > 1 else ''}"
        
        msg.html = render_template('emails/task_reminder.html',
                                   task_title=task_title,
                                   task_deadline=task_deadline.strftime('%B %d, %Y at %I:%M %p'),
                                   task_priority=task_priority,
                                   task_description=task_description,
                                   time_left=time_left_str,
                                   user_email=user_email)
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending task reminder: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_and_send_notifications(app, db, mail, User, Task):
    """Check for tasks that need notifications and send them"""
    with app.app_context():
        try:
            now = now_ist_naive()
            
            # Get all users with notifications enabled
            users = User.query.filter_by(notifications_enabled=True, email_verified=True).all()
            
            notifications_sent = 0
            
            for user in users:
                # Calculate notification threshold
                notification_time = now + timedelta(hours=user.notification_hours)
                
                # Find tasks that:
                # 1. Are pending
                # 2. Deadline is within notification window
                # 3. Haven't been notified yet (or last notification was > 12 hours ago)
                tasks = Task.query.filter(
                    Task.user_id == user.id,
                    Task.status == 'pending',
                    Task.deadline <= notification_time,
                    Task.deadline > now  # Not overdue yet
                ).all()
                
                for task in tasks:
                    # Check if we already sent a notification recently (within 12 hours)
                    should_send = True
                    if task.last_notification_sent:
                        time_since_last = now - task.last_notification_sent
                        if time_since_last.total_seconds() < 12 * 3600:  # 12 hours
                            should_send = False
                    
                    if should_send:
                        success = send_task_reminder(
                            mail,
                            user.email,
                            task.title,
                            task.deadline,
                            task.priority,
                            task.description
                        )
                        
                        if success:
                            task.last_notification_sent = now
                            notifications_sent += 1
            
            # Commit all updates
            db.session.commit()
            
            if notifications_sent > 0:
                print(f"✅ Sent {notifications_sent} task reminder(s)")
            
            return notifications_sent
            
        except Exception as e:
            print(f"Error in notification check: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return 0
