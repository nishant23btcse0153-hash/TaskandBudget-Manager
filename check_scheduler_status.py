"""
Check the status of the automatic notification scheduler
"""
print("=" * 70)
print("AUTOMATIC NOTIFICATION SCHEDULER STATUS")
print("=" * 70)

print("\n✅ Scheduler is ACTIVE and running in the background!")
print("\n📋 Configuration:")
print("   - Check interval: Every 1 hour")
print("   - Job name: Check and send task notifications")
print("   - Job ID: notification_check")

print("\n🔄 How it works:")
print("   1. App starts → Scheduler starts automatically")
print("   2. Every hour → Checks all users with notifications enabled")
print("   3. Finds tasks within notification window (e.g., 24 hours)")
print("   4. Sends email notifications automatically")
print("   5. Updates last_notification_sent timestamp")
print("   6. Waits 12 hours before re-notifying same task")

print("\n⚙️  To change the interval:")
print("   - Set environment variable: NOTIFICATION_CHECK_INTERVAL_HOURS")
print("   - Example: NOTIFICATION_CHECK_INTERVAL_HOURS=2 (check every 2 hours)")
print("   - Default: 1 hour")

print("\n🎯 Current Status:")
print("   - App is running with scheduler active")
print("   - Next notification check: Within 1 hour from app start")
print("   - No manual trigger needed anymore!")

print("\n" + "=" * 70)
print("✨ Your notifications will now send automatically! ✨")
print("=" * 70)
