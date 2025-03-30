from applications.task import send_email_reminder


result = send_email_reminder.apply_async(args=[5])
print("Task ID:", result.id)