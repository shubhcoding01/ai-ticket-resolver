# import os
# import smtplib
# import logging
# from email.mime.text        import MIMEText
# from email.mime.multipart   import MIMEMultipart
# from email.mime.base        import MIMEBase
# from email                  import encoders
# from datetime               import datetime
# from dotenv                 import load_dotenv

# load_dotenv()

# log = logging.getLogger(__name__)

# SMTP_HOST     = os.getenv("SMTP_HOST",     "smtp.gmail.com")
# SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
# SMTP_EMAIL    = os.getenv("SMTP_EMAIL",    "")
# SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
# SUPPORT_NAME  = os.getenv("SUPPORT_NAME",  "IT Support Team")
# COMPANY_NAME  = os.getenv("COMPANY_NAME",  "ICICI Bank")
# SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", SMTP_EMAIL)

# NOTIFICATION_TYPES = {
#     "resolved"         : "Your ticket has been resolved",
#     "escalated"        : "Your ticket is being reviewed by an engineer",
#     "kb_guide_sent"    : "Self-help guide for your issue",
#     "in_progress"      : "Your ticket is being processed",
#     "password_reset"   : "Your password has been reset",
#     "general"          : "Update on your support ticket",
# }

# EMAIL_COLORS = {
#     "resolved"         : "#1D9E75",
#     "escalated"        : "#E8A838",
#     "kb_guide_sent"    : "#378ADD",
#     "in_progress"      : "#7F77DD",
#     "password_reset"   : "#D85A30",
#     "general"          : "#5F5E5A",
# }


# def notify_user(
#     email     : str,
#     ticket_id : int,
#     subject   : str,
#     message   : str,
#     notif_type: str = "general",
#     cc        : list = None,
#     attachment_path: str = None,
# ) -> bool:
#     """
#     Main notification function called by orchestrator and escalation modules.
#     Sends a professionally formatted HTML email to the user.

#     Args:
#         email           : Recipient email address
#         ticket_id       : Freshdesk ticket ID
#         subject         : Original ticket subject line
#         message         : Main body message to send
#         notif_type      : Type of notification — controls color and header text
#                           Options: resolved, escalated, kb_guide_sent,
#                                    in_progress, password_reset, general
#         cc              : Optional list of CC email addresses
#         attachment_path : Optional path to a file to attach

#     Returns:
#         True if email sent successfully, False otherwise
#     """
#     if not email or "@" not in email:
#         log.error(f"Invalid email address: '{email}'. Cannot send notification.")
#         return False

#     if not SMTP_EMAIL or not SMTP_PASSWORD:
#         log.error(
#             "SMTP_EMAIL or SMTP_PASSWORD not set in .env. "
#             "Cannot send email notifications."
#         )
#         return False

#     notif_type   = notif_type if notif_type in NOTIFICATION_TYPES else "general"
#     email_subject = f"[Ticket #{ticket_id}] {NOTIFICATION_TYPES[notif_type]} — {subject}"
#     html_body     = _build_html_email(
#         message    = message,
#         ticket_id  = ticket_id,
#         notif_type = notif_type,
#         subject    = subject,
#     )
#     plain_body = _build_plain_text_email(
#         message   = message,
#         ticket_id = ticket_id,
#         subject   = subject,
#     )

#     log.info(f"Sending '{notif_type}' notification to {email} for ticket #{ticket_id}...")

#     success = _send_email(
#         to              = email,
#         subject         = email_subject,
#         html_body       = html_body,
#         plain_body      = plain_body,
#         cc              = cc or [],
#         attachment_path = attachment_path,
#     )

#     if success:
#         log.info(f"Notification sent successfully to {email} for ticket #{ticket_id}.")
#     else:
#         log.error(f"Failed to send notification to {email} for ticket #{ticket_id}.")

#     return success


# def notify_engineer(
#     engineer_email : str,
#     ticket_id      : int,
#     subject        : str,
#     category       : str,
#     priority       : str,
#     ai_summary     : str,
#     requester_name : str,
#     requester_email: str,
#     machine_name   : str,
#     suggested_action: str,
# ) -> bool:
#     """
#     Send a detailed escalation notification to the engineer/agent.
#     Includes full AI analysis summary so engineer knows exactly
#     what the issue is and what was already tried.

#     Args:
#         engineer_email   : Engineer's email address
#         ticket_id        : Freshdesk ticket ID
#         subject          : Ticket subject
#         category         : AI classified category
#         priority         : AI classified priority
#         ai_summary       : Full AI analysis and suggested action
#         requester_name   : Name of user who raised ticket
#         requester_email  : Email of user who raised ticket
#         machine_name     : User's machine/computer name
#         suggested_action : What the AI recommends doing

#     Returns:
#         True if email sent successfully, False otherwise
#     """
#     if not engineer_email or "@" not in engineer_email:
#         log.error(f"Invalid engineer email: '{engineer_email}'")
#         return False

#     email_subject = (
#         f"[ESCALATED #{ticket_id}] [{priority.upper()}] "
#         f"{subject} — {category.replace('_', ' ').title()}"
#     )

#     html_body  = _build_engineer_html_email(
#         ticket_id       = ticket_id,
#         subject         = subject,
#         category        = category,
#         priority        = priority,
#         ai_summary      = ai_summary,
#         requester_name  = requester_name,
#         requester_email = requester_email,
#         machine_name    = machine_name,
#         suggested_action= suggested_action,
#     )

#     plain_body = (
#         f"ESCALATED TICKET #{ticket_id}\n"
#         f"{'='*50}\n"
#         f"Subject          : {subject}\n"
#         f"Category         : {category}\n"
#         f"Priority         : {priority}\n"
#         f"Requester        : {requester_name} ({requester_email})\n"
#         f"Machine          : {machine_name}\n"
#         f"Suggested Action : {suggested_action}\n\n"
#         f"AI Summary:\n{ai_summary}\n"
#     )

#     log.info(f"Sending escalation email to engineer {engineer_email} for ticket #{ticket_id}...")

#     success = _send_email(
#         to         = engineer_email,
#         subject    = email_subject,
#         html_body  = html_body,
#         plain_body = plain_body,
#     )

#     if success:
#         log.info(f"Engineer notification sent to {engineer_email}.")
#     else:
#         log.error(f"Failed to send engineer notification to {engineer_email}.")

#     return success


# def notify_bulk(notifications: list) -> dict:
#     """
#     Send multiple notifications at once.
#     Useful when processing a batch of tickets.

#     Args:
#         notifications : List of dicts, each with keys:
#                         email, ticket_id, subject, message, notif_type

#     Returns:
#         Dict with keys 'success' and 'failed' showing counts
#     """
#     results = {"success": 0, "failed": 0}

#     for notif in notifications:
#         ok = notify_user(
#             email      = notif.get("email", ""),
#             ticket_id  = notif.get("ticket_id", 0),
#             subject    = notif.get("subject", ""),
#             message    = notif.get("message", ""),
#             notif_type = notif.get("notif_type", "general"),
#         )
#         if ok:
#             results["success"] += 1
#         else:
#             results["failed"] += 1

#     log.info(
#         f"Bulk notifications: {results['success']} sent, "
#         f"{results['failed']} failed."
#     )
#     return results


# def _send_email(
#     to             : str,
#     subject        : str,
#     html_body      : str,
#     plain_body     : str,
#     cc             : list = None,
#     attachment_path: str = None,
# ) -> bool:
#     """
#     Core function that actually connects to SMTP and sends the email.
#     Called by all public notify functions.

#     Args:
#         to              : Recipient email address
#         subject         : Email subject line
#         html_body       : HTML formatted email body
#         plain_body      : Plain text fallback body
#         cc              : List of CC addresses
#         attachment_path : Optional file to attach

#     Returns:
#         True if sent successfully, False otherwise
#     """
#     try:
#         msg = MIMEMultipart("alternative")
#         msg["Subject"] = subject
#         msg["From"]    = f"{SUPPORT_NAME} <{SMTP_EMAIL}>"
#         msg["To"]      = to

#         if cc:
#             msg["Cc"] = ", ".join(cc)

#         msg.attach(MIMEText(plain_body, "plain"))
#         msg.attach(MIMEText(html_body,  "html"))

#         if attachment_path and os.path.exists(attachment_path):
#             _attach_file(msg, attachment_path)

#         all_recipients = [to] + (cc or [])

#         with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
#             server.ehlo()
#             server.starttls()
#             server.ehlo()
#             server.login(SMTP_EMAIL, SMTP_PASSWORD)
#             server.sendmail(SMTP_EMAIL, all_recipients, msg.as_string())

#         return True

#     except smtplib.SMTPAuthenticationError:
#         log.error(
#             "SMTP Authentication failed. "
#             "Check SMTP_EMAIL and SMTP_PASSWORD in .env. "
#             "For Gmail use an App Password, not your regular password."
#         )
#         return False

#     except smtplib.SMTPConnectError:
#         log.error(
#             f"Cannot connect to SMTP server {SMTP_HOST}:{SMTP_PORT}. "
#             "Check SMTP_HOST and SMTP_PORT in .env"
#         )
#         return False

#     except smtplib.SMTPRecipientsRefused:
#         log.error(f"Email address rejected by SMTP server: {to}")
#         return False

#     except smtplib.SMTPException as e:
#         log.error(f"SMTP error sending email: {e}")
#         return False

#     except Exception as e:
#         log.error(f"Unexpected error sending email: {e}")
#         return False


# def _attach_file(msg: MIMEMultipart, file_path: str) -> None:
#     """
#     Attach a file to the email message object.

#     Args:
#         msg       : MIMEMultipart email message object
#         file_path : Full path to the file to attach
#     """
#     try:
#         filename = os.path.basename(file_path)
#         with open(file_path, "rb") as f:
#             part = MIMEBase("application", "octet-stream")
#             part.set_payload(f.read())

#         encoders.encode_base64(part)
#         part.add_header(
#             "Content-Disposition",
#             f"attachment; filename={filename}"
#         )
#         msg.attach(part)
#         log.info(f"File attached to email: {filename}")

#     except Exception as e:
#         log.error(f"Failed to attach file {file_path}: {e}")


# def _build_html_email(
#     message   : str,
#     ticket_id : int,
#     notif_type: str,
#     subject   : str,
# ) -> str:
#     """
#     Build a professional HTML email for user notifications.
#     Includes color-coded header based on notification type.

#     Args:
#         message    : Main body text
#         ticket_id  : Freshdesk ticket ID
#         notif_type : Notification type for color coding
#         subject    : Original ticket subject

#     Returns:
#         HTML string
#     """
#     color       = EMAIL_COLORS.get(notif_type, "#5F5E5A")
#     header_text = NOTIFICATION_TYPES.get(notif_type, "Update on your ticket")
#     timestamp   = datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC")
#     message_html = message.replace("\n", "<br>")

#     html = f"""
# <!DOCTYPE html>
# <html>
# <head>
#   <meta charset="UTF-8">
#   <meta name="viewport" content="width=device-width, initial-scale=1.0">
# </head>
# <body style="margin:0;padding:0;background-color:#f5f5f5;font-family:Arial,sans-serif;">

#   <table width="100%" cellpadding="0" cellspacing="0"
#          style="background-color:#f5f5f5;padding:30px 0;">
#     <tr>
#       <td align="center">

#         <table width="600" cellpadding="0" cellspacing="0"
#                style="background:#ffffff;border-radius:8px;
#                       overflow:hidden;border:1px solid #e0e0e0;">

#           <tr>
#             <td style="background-color:{color};padding:24px 32px;">
#               <p style="margin:0;color:#ffffff;font-size:13px;
#                          font-weight:normal;letter-spacing:1px;">
#                 {COMPANY_NAME} — IT Support
#               </p>
#               <h1 style="margin:8px 0 0;color:#ffffff;font-size:22px;
#                           font-weight:600;">
#                 {header_text}
#               </h1>
#             </td>
#           </tr>

#           <tr>
#             <td style="padding:28px 32px;">

#               <table width="100%" cellpadding="0" cellspacing="0"
#                      style="background:#f9f9f9;border-radius:6px;
#                             border:1px solid #eeeeee;
#                             margin-bottom:24px;">
#                 <tr>
#                   <td style="padding:12px 16px;">
#                     <p style="margin:0;font-size:12px;color:#888888;">
#                       Ticket ID
#                     </p>
#                     <p style="margin:4px 0 0;font-size:14px;
#                                font-weight:bold;color:#333333;">
#                       #{ticket_id}
#                     </p>
#                   </td>
#                   <td style="padding:12px 16px;border-left:1px solid #eeeeee;">
#                     <p style="margin:0;font-size:12px;color:#888888;">
#                       Subject
#                     </p>
#                     <p style="margin:4px 0 0;font-size:14px;color:#333333;">
#                       {subject}
#                     </p>
#                   </td>
#                   <td style="padding:12px 16px;border-left:1px solid #eeeeee;">
#                     <p style="margin:0;font-size:12px;color:#888888;">
#                       Time
#                     </p>
#                     <p style="margin:4px 0 0;font-size:13px;color:#555555;">
#                       {timestamp}
#                     </p>
#                   </td>
#                 </tr>
#               </table>

#               <div style="font-size:15px;color:#333333;line-height:1.7;">
#                 {message_html}
#               </div>

#             </td>
#           </tr>

#           <tr>
#             <td style="background:#f9f9f9;padding:16px 32px;
#                         border-top:1px solid #eeeeee;">
#               <p style="margin:0;font-size:12px;color:#aaaaaa;
#                          text-align:center;">
#                 This is an automated message from the {COMPANY_NAME} IT Support system.<br>
#                 Please do not reply to this email. For further assistance,
#                 contact <a href="mailto:{SUPPORT_EMAIL}"
#                 style="color:{color};">{SUPPORT_EMAIL}</a>
#               </p>
#             </td>
#           </tr>

#         </table>

#       </td>
#     </tr>
#   </table>

# </body>
# </html>
# """
#     return html


# def _build_engineer_html_email(
#     ticket_id       : int,
#     subject         : str,
#     category        : str,
#     priority        : str,
#     ai_summary      : str,
#     requester_name  : str,
#     requester_email : str,
#     machine_name    : str,
#     suggested_action: str,
# ) -> str:
#     """
#     Build a detailed HTML email for engineer escalation notifications.
#     Shows full AI analysis in a structured format.

#     Args:
#         ticket_id        : Freshdesk ticket ID
#         subject          : Ticket subject
#         category         : AI classified category
#         priority         : AI classified priority
#         ai_summary       : Full AI analysis text
#         requester_name   : User's full name
#         requester_email  : User's email
#         machine_name     : User's machine name
#         suggested_action : AI recommended action

#     Returns:
#         HTML string
#     """
#     priority_colors = {
#         "low"    : "#1D9E75",
#         "medium" : "#E8A838",
#         "high"   : "#D85A30",
#         "urgent" : "#E24B4A",
#     }

#     priority_color  = priority_colors.get(priority, "#888888")
#     timestamp       = datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC")
#     ai_summary_html = ai_summary.replace("\n", "<br>")
#     category_label  = category.replace("_", " ").title()

#     html = f"""
# <!DOCTYPE html>
# <html>
# <head>
#   <meta charset="UTF-8">
# </head>
# <body style="margin:0;padding:0;background-color:#f5f5f5;font-family:Arial,sans-serif;">

#   <table width="100%" cellpadding="0" cellspacing="0"
#          style="background-color:#f5f5f5;padding:30px 0;">
#     <tr>
#       <td align="center">

#         <table width="640" cellpadding="0" cellspacing="0"
#                style="background:#ffffff;border-radius:8px;
#                       overflow:hidden;border:1px solid #e0e0e0;">

#           <tr>
#             <td style="background-color:#2C2C2A;padding:20px 32px;">
#               <p style="margin:0;color:#aaaaaa;font-size:12px;">
#                 {COMPANY_NAME} — IT Support Escalation
#               </p>
#               <h1 style="margin:6px 0 0;color:#ffffff;font-size:20px;">
#                 Ticket Escalated — Action Required
#               </h1>
#             </td>
#           </tr>

#           <tr>
#             <td style="padding:24px 32px 12px;">

#               <table width="100%" cellpadding="0" cellspacing="0"
#                      style="border:1px solid #eeeeee;border-radius:6px;
#                             margin-bottom:20px;">
#                 <tr style="background:#f9f9f9;">
#                   <td style="padding:10px 16px;font-size:12px;color:#888888;
#                               border-bottom:1px solid #eeeeee;" colspan="2">
#                     TICKET DETAILS
#                   </td>
#                 </tr>
#                 <tr>
#                   <td style="padding:10px 16px;font-size:13px;
#                               color:#555555;width:140px;
#                               border-bottom:1px solid #f0f0f0;">
#                     Ticket ID
#                   </td>
#                   <td style="padding:10px 16px;font-size:13px;
#                               font-weight:bold;color:#222222;
#                               border-bottom:1px solid #f0f0f0;">
#                     #{ticket_id}
#                   </td>
#                 </tr>
#                 <tr style="background:#fafafa;">
#                   <td style="padding:10px 16px;font-size:13px;
#                               color:#555555;border-bottom:1px solid #f0f0f0;">
#                     Subject
#                   </td>
#                   <td style="padding:10px 16px;font-size:13px;
#                               color:#222222;border-bottom:1px solid #f0f0f0;">
#                     {subject}
#                   </td>
#                 </tr>
#                 <tr>
#                   <td style="padding:10px 16px;font-size:13px;
#                               color:#555555;border-bottom:1px solid #f0f0f0;">
#                     Category
#                   </td>
#                   <td style="padding:10px 16px;font-size:13px;
#                               color:#222222;border-bottom:1px solid #f0f0f0;">
#                     {category_label}
#                   </td>
#                 </tr>
#                 <tr style="background:#fafafa;">
#                   <td style="padding:10px 16px;font-size:13px;
#                               color:#555555;border-bottom:1px solid #f0f0f0;">
#                     Priority
#                   </td>
#                   <td style="padding:10px 16px;border-bottom:1px solid #f0f0f0;">
#                     <span style="background:{priority_color};color:#ffffff;
#                                   font-size:12px;font-weight:bold;
#                                   padding:3px 10px;border-radius:20px;">
#                       {priority.upper()}
#                     </span>
#                   </td>
#                 </tr>
#                 <tr>
#                   <td style="padding:10px 16px;font-size:13px;
#                               color:#555555;border-bottom:1px solid #f0f0f0;">
#                     Requester
#                   </td>
#                   <td style="padding:10px 16px;font-size:13px;
#                               color:#222222;border-bottom:1px solid #f0f0f0;">
#                     {requester_name}
#                     (<a href="mailto:{requester_email}"
#                     style="color:#378ADD;">{requester_email}</a>)
#                   </td>
#                 </tr>
#                 <tr style="background:#fafafa;">
#                   <td style="padding:10px 16px;font-size:13px;
#                               color:#555555;border-bottom:1px solid #f0f0f0;">
#                     Machine
#                   </td>
#                   <td style="padding:10px 16px;font-size:13px;
#                               font-family:monospace;color:#222222;
#                               border-bottom:1px solid #f0f0f0;">
#                     {machine_name}
#                   </td>
#                 </tr>
#                 <tr>
#                   <td style="padding:10px 16px;font-size:13px;color:#555555;">
#                     Escalated At
#                   </td>
#                   <td style="padding:10px 16px;font-size:13px;color:#555555;">
#                     {timestamp}
#                   </td>
#                 </tr>
#               </table>

#               <table width="100%" cellpadding="0" cellspacing="0"
#                      style="border:1px solid #fff3cd;border-radius:6px;
#                             background:#fffdf0;margin-bottom:20px;">
#                 <tr>
#                   <td style="padding:12px 16px;border-bottom:1px solid #fff3cd;">
#                     <p style="margin:0;font-size:12px;color:#888888;
#                                text-transform:uppercase;letter-spacing:1px;">
#                       AI Suggested Action
#                     </p>
#                   </td>
#                 </tr>
#                 <tr>
#                   <td style="padding:12px 16px;font-size:14px;
#                               color:#333333;line-height:1.6;">
#                     {suggested_action}
#                   </td>
#                 </tr>
#               </table>

#               <table width="100%" cellpadding="0" cellspacing="0"
#                      style="border:1px solid #eeeeee;border-radius:6px;
#                             margin-bottom:20px;">
#                 <tr style="background:#f9f9f9;">
#                   <td style="padding:10px 16px;font-size:12px;
#                               color:#888888;text-transform:uppercase;
#                               letter-spacing:1px;
#                               border-bottom:1px solid #eeeeee;">
#                     AI Analysis Summary
#                   </td>
#                 </tr>
#                 <tr>
#                   <td style="padding:14px 16px;font-size:13px;
#                               color:#444444;line-height:1.7;">
#                     {ai_summary_html}
#                   </td>
#                 </tr>
#               </table>

#             </td>
#           </tr>

#           <tr>
#             <td style="background:#f9f9f9;padding:14px 32px;
#                         border-top:1px solid #eeeeee;">
#               <p style="margin:0;font-size:12px;color:#aaaaaa;
#                          text-align:center;">
#                 This escalation was generated automatically by the AI Ticket Resolver system.<br>
#                 {COMPANY_NAME} IT Support — {timestamp}
#               </p>
#             </td>
#           </tr>

#         </table>
#       </td>
#     </tr>
#   </table>

# </body>
# </html>
# """
#     return html


# def _build_plain_text_email(
#     message  : str,
#     ticket_id: int,
#     subject  : str,
# ) -> str:
#     """
#     Build a plain text fallback email body.
#     Shown in email clients that do not support HTML.

#     Args:
#         message   : Main body text
#         ticket_id : Freshdesk ticket ID
#         subject   : Original ticket subject

#     Returns:
#         Plain text string
#     """
#     timestamp = datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC")

#     plain = (
#         f"{COMPANY_NAME} — IT Support\n"
#         f"{'='*50}\n\n"
#         f"Ticket ID : #{ticket_id}\n"
#         f"Subject   : {subject}\n"
#         f"Time      : {timestamp}\n\n"
#         f"{'─'*50}\n\n"
#         f"{message}\n\n"
#         f"{'─'*50}\n"
#         f"This is an automated message. Do not reply to this email.\n"
#         f"For further help contact: {SUPPORT_EMAIL}\n"
#     )
#     return plain


# if __name__ == "__main__":
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s [%(levelname)s] %(message)s"
#     )

#     print("\n" + "=" * 60)
#     print("NOTIFIER TEST RUN")
#     print("=" * 60 + "\n")

#     if not SMTP_EMAIL or not SMTP_PASSWORD:
#         print("ERROR: SMTP_EMAIL and SMTP_PASSWORD not set in .env")
#         print("Add these to config/.env and try again:\n")
#         print("  SMTP_HOST=smtp.gmail.com")
#         print("  SMTP_PORT=587")
#         print("  SMTP_EMAIL=youremail@gmail.com")
#         print("  SMTP_PASSWORD=your_gmail_app_password")
#         print("  SUPPORT_NAME=IT Support Team")
#         print("  COMPANY_NAME=ICICI Bank")
#         print("  SUPPORT_EMAIL=support@icici.com")
#         exit(1)

#     TEST_EMAIL = input("\nEnter your email address to receive test emails: ").strip()

#     if not TEST_EMAIL or "@" not in TEST_EMAIL:
#         print("Invalid email. Exiting.")
#         exit(1)

#     print("\n--- Test 1: Resolved notification ---")
#     ok = notify_user(
#         email      = TEST_EMAIL,
#         ticket_id  = 1001,
#         subject    = "Install Zoom on my laptop",
#         message    = (
#             "Dear Rahul,\n\n"
#             "Your ticket has been automatically resolved.\n\n"
#             "Action taken: Zoom has been installed on PC-ICICI-0042.\n\n"
#             "Please restart your computer and verify Zoom is working.\n\n"
#             "Thank you,\nIT Support Team"
#         ),
#         notif_type = "resolved",
#     )
#     print(f"Result: {'SENT' if ok else 'FAILED'}")

#     print("\n--- Test 2: KB guide notification ---")
#     ok = notify_user(
#         email      = TEST_EMAIL,
#         ticket_id  = 1002,
#         subject    = "Cannot connect to VPN",
#         message    = (
#             "Dear Priya,\n\n"
#             "Here is a self-help guide for your VPN issue:\n\n"
#             "1. Open Cisco AnyConnect from your taskbar\n"
#             "2. Enter VPN address: vpn.icici.com\n"
#             "3. Click Connect and enter your AD credentials\n"
#             "4. If it fails, restart your network adapter:\n"
#             "   Settings > Network > Disable > Enable\n\n"
#             "An engineer will also follow up if this does not help."
#         ),
#         notif_type = "kb_guide_sent",
#     )
#     print(f"Result: {'SENT' if ok else 'FAILED'}")

#     print("\n--- Test 3: Engineer escalation email ---")
#     ok = notify_engineer(
#         engineer_email   = TEST_EMAIL,
#         ticket_id        = 1003,
#         subject          = "Laptop screen flickering",
#         category         = "hardware",
#         priority         = "high",
#         ai_summary       = (
#             "User reports laptop screen has been flickering continuously "
#             "since this morning. Issue appears to be hardware-related. "
#             "Auto-resolution was not attempted as hardware issues require "
#             "physical inspection. No KB guide was found for this specific issue."
#         ),
#         requester_name   = "Amit Patel",
#         requester_email  = "amit.patel@icici.com",
#         machine_name     = "LAPTOP-ICICI-115",
#         suggested_action = "Schedule on-site hardware inspection with engineer.",
#     )
#     print(f"Result: {'SENT' if ok else 'FAILED'}")

#     print("\nAll tests complete. Check your inbox.")


import os
import smtplib
import logging
from email.mime.text      import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base      import MIMEBase
from email                import encoders
from datetime             import datetime, timezone
from dotenv               import load_dotenv

load_dotenv("config/.env")

log = logging.getLogger(__name__)

DEMO_MODE     = os.getenv("DEMO_MODE",     "false").strip().lower() == "true"
DRY_RUN_MODE  = os.getenv("DRY_RUN_MODE",  "false").strip().lower() == "true"
SMTP_HOST     = os.getenv("SMTP_HOST",     "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL    = os.getenv("SMTP_EMAIL",    "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS  = os.getenv("SMTP_USE_TLS",  "true").strip().lower() == "true"
SMTP_TIMEOUT  = int(os.getenv("SMTP_TIMEOUT", 15))
SUPPORT_NAME  = os.getenv("SUPPORT_NAME",  "IT Support Team")
COMPANY_NAME  = os.getenv("COMPANY_NAME",  "ICICI Bank")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", SMTP_EMAIL)
SUPPORT_PHONE = os.getenv("SUPPORT_PHONE", "1800-XXX-XXXX")

EMAIL_NOTIFICATIONS_ENABLED = (
    os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "true")
    .strip().lower() == "true"
)

NOTIFICATION_TYPES = {
    "resolved"       : "Your ticket has been resolved",
    "escalated"      : "Your ticket is being reviewed by an engineer",
    "kb_guide_sent"  : "Self-help guide for your issue",
    "in_progress"    : "Your ticket is being processed",
    "password_reset" : "Your password has been reset",
    "general"        : "Update on your support ticket",
}

EMAIL_COLORS = {
    "resolved"       : "#1D9E75",
    "escalated"      : "#E8A838",
    "kb_guide_sent"  : "#378ADD",
    "in_progress"    : "#534AB7",
    "password_reset" : "#D85A30",
    "general"        : "#5F5E5A",
}


def _now_str(fmt: str = "%d %b %Y, %I:%M %p UTC") -> str:
    """
    Return current UTC time as a formatted string.
    Uses timezone-aware datetime to avoid deprecation warning.

    Args:
        fmt : strftime format string

    Returns:
        Formatted datetime string
    """
    return datetime.now(timezone.utc).strftime(fmt)


def _is_email_enabled() -> bool:
    """
    Check if email notifications should actually be sent.
    Returns False in demo mode, dry run mode, or when SMTP
    credentials are not configured.

    Returns:
        True if emails should be sent, False if simulated only
    """
    if DEMO_MODE:
        return False
    if DRY_RUN_MODE:
        return False
    if not EMAIL_NOTIFICATIONS_ENABLED:
        return False
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return False
    return True


def notify_user(
    email          : str,
    ticket_id      : int,
    subject        : str,
    message        : str,
    notif_type     : str  = "general",
    cc             : list = None,
    attachment_path: str  = None,
) -> bool:
    """
    Main notification function called by orchestrator,
    escalation, and demo_runner.
    In demo mode logs the notification without sending a
    real email. In live mode sends a formatted HTML email.

    Args:
        email           : Recipient email address
        ticket_id       : Freshdesk ticket ID
        subject         : Original ticket subject line
        message         : Main body message text
        notif_type      : Notification type — controls color
                          and header. Options:
                          resolved | escalated | kb_guide_sent |
                          in_progress | password_reset | general
        cc              : Optional list of CC email addresses
        attachment_path : Optional path to a file to attach

    Returns:
        True if sent (or simulated) successfully, False otherwise
    """
    if not email or "@" not in email:
        log.error(
            f"Invalid email address: '{email}'. "
            "Cannot send notification."
        )
        return False

    notif_type = (
        notif_type
        if notif_type in NOTIFICATION_TYPES
        else "general"
    )

    if not _is_email_enabled():
        mode = (
            "DEMO"     if DEMO_MODE      else
            "DRY RUN"  if DRY_RUN_MODE   else
            "DISABLED"
        )
        log.info(
            f"[{mode}] Notification to {email} "
            f"| type: {notif_type} "
            f"| ticket: #{ticket_id} "
            f"| (email not sent)"
        )
        return True

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        log.error(
            "SMTP_EMAIL or SMTP_PASSWORD not set in config/.env. "
            "Cannot send email notifications."
        )
        return False

    email_subject = (
        f"[Ticket #{ticket_id}] "
        f"{NOTIFICATION_TYPES[notif_type]} — {subject}"
    )

    html_body = _build_html_email(
        message    = message,
        ticket_id  = ticket_id,
        notif_type = notif_type,
        subject    = subject,
    )
    plain_body = _build_plain_text_email(
        message   = message,
        ticket_id = ticket_id,
        subject   = subject,
    )

    log.info(
        f"Sending '{notif_type}' notification to "
        f"{email} for ticket #{ticket_id}..."
    )

    success = _send_email(
        to              = email,
        subject         = email_subject,
        html_body       = html_body,
        plain_body      = plain_body,
        cc              = cc or [],
        attachment_path = attachment_path,
    )

    if success:
        log.info(
            f"Notification sent to {email} "
            f"for ticket #{ticket_id}."
        )
    else:
        log.error(
            f"Failed to send notification to {email} "
            f"for ticket #{ticket_id}."
        )

    return success


def notify_engineer(
    engineer_email   : str,
    ticket_id        : int,
    subject          : str,
    category         : str,
    priority         : str,
    ai_summary       : str,
    requester_name   : str,
    requester_email  : str,
    machine_name     : str,
    suggested_action : str,
) -> bool:
    """
    Send a detailed escalation notification to the engineer.
    Includes full AI analysis summary, ticket details, requester
    info, and machine name so the engineer has everything they
    need without opening Freshdesk.
    In demo mode logs the notification without sending real email.

    Args:
        engineer_email   : Engineer's email address
        ticket_id        : Freshdesk ticket ID
        subject          : Ticket subject
        category         : AI classified category
        priority         : AI classified priority
        ai_summary       : Full AI analysis and suggested action
        requester_name   : Name of user who raised ticket
        requester_email  : Email of user who raised ticket
        machine_name     : User's machine/computer name
        suggested_action : What the AI recommends doing

    Returns:
        True if sent (or simulated) successfully, False otherwise
    """
    if not engineer_email or "@" not in engineer_email:
        log.error(
            f"Invalid engineer email: '{engineer_email}'"
        )
        return False

    if not _is_email_enabled():
        mode = (
            "DEMO"    if DEMO_MODE    else
            "DRY RUN" if DRY_RUN_MODE else
            "DISABLED"
        )
        log.info(
            f"[{mode}] Engineer notification to "
            f"{engineer_email} "
            f"| ticket: #{ticket_id} "
            f"| priority: {priority} "
            f"| (email not sent)"
        )
        return True

    email_subject = (
        f"[ESCALATED #{ticket_id}] "
        f"[{priority.upper()}] "
        f"{subject} — "
        f"{category.replace('_', ' ').title()}"
    )

    html_body = _build_engineer_html_email(
        ticket_id        = ticket_id,
        subject          = subject,
        category         = category,
        priority         = priority,
        ai_summary       = ai_summary,
        requester_name   = requester_name,
        requester_email  = requester_email,
        machine_name     = machine_name,
        suggested_action = suggested_action,
    )

    plain_body = (
        f"ESCALATED TICKET #{ticket_id}\n"
        f"{'=' * 50}\n"
        f"Subject          : {subject}\n"
        f"Category         : {category}\n"
        f"Priority         : {priority}\n"
        f"Requester        : "
        f"{requester_name} ({requester_email})\n"
        f"Machine          : {machine_name}\n"
        f"Suggested Action : {suggested_action}\n\n"
        f"AI Summary:\n{ai_summary}\n"
    )

    log.info(
        f"Sending escalation email to {engineer_email} "
        f"for ticket #{ticket_id}..."
    )

    success = _send_email(
        to         = engineer_email,
        subject    = email_subject,
        html_body  = html_body,
        plain_body = plain_body,
    )

    if success:
        log.info(
            f"Engineer notification sent to {engineer_email} "
            f"for ticket #{ticket_id}."
        )
    else:
        log.error(
            f"Failed to send engineer notification to "
            f"{engineer_email} for ticket #{ticket_id}."
        )

    return success


def notify_bulk(notifications: list) -> dict:
    """
    Send multiple notifications at once.
    Useful when processing a batch of tickets.
    In demo mode simulates all notifications.

    Args:
        notifications : List of dicts with keys:
                        email, ticket_id, subject,
                        message, notif_type

    Returns:
        Dict with 'success', 'failed', 'total' counts
    """
    results = {
        "success" : 0,
        "failed"  : 0,
        "total"   : len(notifications),
    }

    for notif in notifications:
        ok = notify_user(
            email      = notif.get("email",      ""),
            ticket_id  = notif.get("ticket_id",  0),
            subject    = notif.get("subject",    ""),
            message    = notif.get("message",    ""),
            notif_type = notif.get("notif_type", "general"),
        )
        if ok:
            results["success"] += 1
        else:
            results["failed"] += 1

    log.info(
        f"Bulk notifications: "
        f"{results['success']} sent, "
        f"{results['failed']} failed "
        f"out of {results['total']} total."
    )
    return results


def _send_email(
    to             : str,
    subject        : str,
    html_body      : str,
    plain_body     : str,
    cc             : list = None,
    attachment_path: str  = None,
) -> bool:
    """
    Core function that connects to SMTP and sends the email.
    Called by all public notify functions.
    Handles all SMTP errors gracefully without crashing.

    Args:
        to              : Recipient email address
        subject         : Email subject line
        html_body       : HTML formatted email body
        plain_body      : Plain text fallback body
        cc              : List of CC email addresses
        attachment_path : Optional file path to attach

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        msg            = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{SUPPORT_NAME} <{SMTP_EMAIL}>"
        msg["To"]      = to

        if cc:
            msg["Cc"] = ", ".join(cc)

        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body,  "html"))

        if attachment_path and os.path.exists(attachment_path):
            _attach_file(msg, attachment_path)

        all_recipients = [to] + (cc or [])

        with smtplib.SMTP(
            SMTP_HOST, SMTP_PORT,
            timeout=SMTP_TIMEOUT,
        ) as server:
            server.ehlo()
            if SMTP_USE_TLS:
                server.starttls()
                server.ehlo()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(
                SMTP_EMAIL,
                all_recipients,
                msg.as_string(),
            )

        return True

    except smtplib.SMTPAuthenticationError:
        log.error(
            "SMTP authentication failed. "
            "Check SMTP_EMAIL and SMTP_PASSWORD in config/.env. "
            "For Gmail use an App Password, not your regular password."
        )
        return False

    except smtplib.SMTPConnectError:
        log.error(
            f"Cannot connect to SMTP server "
            f"{SMTP_HOST}:{SMTP_PORT}. "
            "Check SMTP_HOST and SMTP_PORT in config/.env"
        )
        return False

    except smtplib.SMTPRecipientsRefused:
        log.error(
            f"Email address rejected by SMTP server: {to}"
        )
        return False

    except smtplib.SMTPException as e:
        log.error(f"SMTP error sending email: {e}")
        return False

    except OSError as e:
        log.error(
            f"Network error sending email: {e}. "
            "Check internet connection."
        )
        return False

    except Exception as e:
        log.error(f"Unexpected error sending email: {e}")
        return False


def _attach_file(
    msg      : MIMEMultipart,
    file_path: str,
) -> None:
    """
    Attach a file to the email message object.

    Args:
        msg       : MIMEMultipart email message
        file_path : Full path to the file to attach
    """
    try:
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={filename}"
        )
        msg.attach(part)
        log.info(f"File attached to email: {filename}")

    except Exception as e:
        log.error(f"Failed to attach file {file_path}: {e}")


def _build_html_email(
    message   : str,
    ticket_id : int,
    notif_type: str,
    subject   : str,
) -> str:
    """
    Build a professional HTML email for user notifications.
    Color-coded header based on notification type.
    Uses timezone-aware UTC timestamp.

    Args:
        message    : Main body text
        ticket_id  : Freshdesk ticket ID
        notif_type : Notification type for color coding
        subject    : Original ticket subject

    Returns:
        HTML string
    """
    color        = EMAIL_COLORS.get(notif_type, "#5F5E5A")
    header_text  = NOTIFICATION_TYPES.get(
        notif_type, "Update on your ticket"
    )
    timestamp    = _now_str()
    message_html = message.replace("\n", "<br>")

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f5f5f5;
             font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#f5f5f5;padding:30px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:8px;
                    overflow:hidden;border:1px solid #e0e0e0;">

        <tr>
          <td style="background:{color};padding:24px 32px;">
            <p style="margin:0;color:#fff;font-size:12px;
                       letter-spacing:1px;">
              {COMPANY_NAME} — IT Support
            </p>
            <h1 style="margin:8px 0 0;color:#fff;font-size:22px;
                        font-weight:600;">
              {header_text}
            </h1>
          </td>
        </tr>

        <tr>
          <td style="padding:28px 32px;">
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#f9f9f9;border-radius:6px;
                          border:1px solid #eee;margin-bottom:24px;">
              <tr>
                <td style="padding:12px 16px;">
                  <p style="margin:0;font-size:12px;color:#888;">
                    Ticket ID
                  </p>
                  <p style="margin:4px 0 0;font-size:14px;
                             font-weight:bold;color:#333;">
                    #{ticket_id}
                  </p>
                </td>
                <td style="padding:12px 16px;
                            border-left:1px solid #eee;">
                  <p style="margin:0;font-size:12px;color:#888;">
                    Subject
                  </p>
                  <p style="margin:4px 0 0;font-size:14px;
                             color:#333;">
                    {subject}
                  </p>
                </td>
                <td style="padding:12px 16px;
                            border-left:1px solid #eee;">
                  <p style="margin:0;font-size:12px;color:#888;">
                    Time
                  </p>
                  <p style="margin:4px 0 0;font-size:13px;
                             color:#555;">
                    {timestamp}
                  </p>
                </td>
              </tr>
            </table>

            <div style="font-size:15px;color:#333;line-height:1.7;">
              {message_html}
            </div>
          </td>
        </tr>

        <tr>
          <td style="background:#f9f9f9;padding:16px 32px;
                      border-top:1px solid #eee;">
            <p style="margin:0;font-size:12px;color:#aaa;
                       text-align:center;">
              Automated message from {COMPANY_NAME} IT Support.<br>
              Do not reply — contact
              <a href="mailto:{SUPPORT_EMAIL}"
                 style="color:{color};">{SUPPORT_EMAIL}</a>
              or call {SUPPORT_PHONE}
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return html


def _build_engineer_html_email(
    ticket_id       : int,
    subject         : str,
    category        : str,
    priority        : str,
    ai_summary      : str,
    requester_name  : str,
    requester_email : str,
    machine_name    : str,
    suggested_action: str,
) -> str:
    """
    Build a detailed HTML escalation email for engineers.
    Shows full AI analysis in a structured table format.
    Uses timezone-aware UTC timestamp.

    Args:
        ticket_id        : Freshdesk ticket ID
        subject          : Ticket subject
        category         : AI classified category
        priority         : AI classified priority
        ai_summary       : Full AI analysis text
        requester_name   : User's full name
        requester_email  : User's email
        machine_name     : User's machine name
        suggested_action : AI recommended action

    Returns:
        HTML string
    """
    priority_colors = {
        "low"    : "#1D9E75",
        "medium" : "#E8A838",
        "high"   : "#D85A30",
        "urgent" : "#E24B4A",
    }

    priority_color  = priority_colors.get(priority, "#888888")
    timestamp       = _now_str()
    ai_summary_html = ai_summary.replace("\n", "<br>")
    category_label  = category.replace("_", " ").title()

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
</head>
<body style="margin:0;padding:0;background:#f5f5f5;
             font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#f5f5f5;padding:30px 0;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:8px;
                    overflow:hidden;border:1px solid #e0e0e0;">

        <tr>
          <td style="background:#2C2C2A;padding:20px 32px;">
            <p style="margin:0;color:#aaa;font-size:12px;">
              {COMPANY_NAME} — IT Support Escalation
            </p>
            <h1 style="margin:6px 0 0;color:#fff;font-size:20px;">
              Ticket Escalated — Action Required
            </h1>
          </td>
        </tr>

        <tr>
          <td style="padding:24px 32px 12px;">

            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border:1px solid #eee;border-radius:6px;
                          margin-bottom:20px;">
              <tr style="background:#f9f9f9;">
                <td style="padding:10px 16px;font-size:12px;
                            color:#888;letter-spacing:1px;
                            border-bottom:1px solid #eee;"
                    colspan="2">
                  TICKET DETAILS
                </td>
              </tr>
              <tr>
                <td style="padding:10px 16px;font-size:13px;
                            color:#555;width:140px;
                            border-bottom:1px solid #f0f0f0;">
                  Ticket ID
                </td>
                <td style="padding:10px 16px;font-size:13px;
                            font-weight:bold;color:#222;
                            border-bottom:1px solid #f0f0f0;">
                  #{ticket_id}
                </td>
              </tr>
              <tr style="background:#fafafa;">
                <td style="padding:10px 16px;font-size:13px;
                            color:#555;border-bottom:1px solid #f0f0f0;">
                  Subject
                </td>
                <td style="padding:10px 16px;font-size:13px;
                            color:#222;border-bottom:1px solid #f0f0f0;">
                  {subject}
                </td>
              </tr>
              <tr>
                <td style="padding:10px 16px;font-size:13px;
                            color:#555;border-bottom:1px solid #f0f0f0;">
                  Category
                </td>
                <td style="padding:10px 16px;font-size:13px;
                            color:#222;border-bottom:1px solid #f0f0f0;">
                  {category_label}
                </td>
              </tr>
              <tr style="background:#fafafa;">
                <td style="padding:10px 16px;font-size:13px;
                            color:#555;border-bottom:1px solid #f0f0f0;">
                  Priority
                </td>
                <td style="padding:10px 16px;
                            border-bottom:1px solid #f0f0f0;">
                  <span style="background:{priority_color};
                                color:#fff;font-size:12px;
                                font-weight:bold;padding:3px 10px;
                                border-radius:20px;">
                    {priority.upper()}
                  </span>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 16px;font-size:13px;
                            color:#555;border-bottom:1px solid #f0f0f0;">
                  Requester
                </td>
                <td style="padding:10px 16px;font-size:13px;
                            color:#222;border-bottom:1px solid #f0f0f0;">
                  {requester_name}
                  (<a href="mailto:{requester_email}"
                     style="color:#378ADD;">{requester_email}</a>)
                </td>
              </tr>
              <tr style="background:#fafafa;">
                <td style="padding:10px 16px;font-size:13px;
                            color:#555;border-bottom:1px solid #f0f0f0;">
                  Machine
                </td>
                <td style="padding:10px 16px;font-size:13px;
                            font-family:monospace;color:#222;
                            border-bottom:1px solid #f0f0f0;">
                  {machine_name}
                </td>
              </tr>
              <tr>
                <td style="padding:10px 16px;font-size:13px;
                            color:#555;">
                  Escalated At
                </td>
                <td style="padding:10px 16px;font-size:13px;
                            color:#555;">
                  {timestamp}
                </td>
              </tr>
            </table>

            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border:1px solid #fff3cd;border-radius:6px;
                          background:#fffdf0;margin-bottom:20px;">
              <tr>
                <td style="padding:12px 16px;
                            border-bottom:1px solid #fff3cd;">
                  <p style="margin:0;font-size:12px;color:#888;
                             text-transform:uppercase;letter-spacing:1px;">
                    AI Suggested Action
                  </p>
                </td>
              </tr>
              <tr>
                <td style="padding:12px 16px;font-size:14px;
                            color:#333;line-height:1.6;">
                  {suggested_action}
                </td>
              </tr>
            </table>

            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border:1px solid #eee;border-radius:6px;
                          margin-bottom:20px;">
              <tr style="background:#f9f9f9;">
                <td style="padding:10px 16px;font-size:12px;
                            color:#888;text-transform:uppercase;
                            letter-spacing:1px;
                            border-bottom:1px solid #eee;">
                  AI Analysis Summary
                </td>
              </tr>
              <tr>
                <td style="padding:14px 16px;font-size:13px;
                            color:#444;line-height:1.7;">
                  {ai_summary_html}
                </td>
              </tr>
            </table>

          </td>
        </tr>

        <tr>
          <td style="background:#f9f9f9;padding:14px 32px;
                      border-top:1px solid #eee;">
            <p style="margin:0;font-size:12px;color:#aaa;
                       text-align:center;">
              AI Ticket Resolver — {COMPANY_NAME} IT Support
              — {timestamp}
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return html


def _build_plain_text_email(
    message  : str,
    ticket_id: int,
    subject  : str,
) -> str:
    """
    Build a plain text fallback email body.
    Shown in email clients that do not support HTML.
    Uses timezone-aware UTC timestamp.

    Args:
        message   : Main body text
        ticket_id : Freshdesk ticket ID
        subject   : Original ticket subject

    Returns:
        Plain text string
    """
    timestamp = _now_str()

    plain = (
        f"{COMPANY_NAME} — IT Support\n"
        f"{'=' * 50}\n\n"
        f"Ticket ID : #{ticket_id}\n"
        f"Subject   : {subject}\n"
        f"Time      : {timestamp}\n\n"
        f"{'─' * 50}\n\n"
        f"{message}\n\n"
        f"{'─' * 50}\n"
        f"Automated message — do not reply.\n"
        f"Contact: {SUPPORT_EMAIL} | {SUPPORT_PHONE}\n"
    )
    return plain


if __name__ == "__main__":
    import sys
    sys.path.insert(
        0,
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s",
    )

    print("\n" + "=" * 60)
    print("NOTIFIER TEST RUN")
    print("=" * 60)
    print(
        f"  Mode         : "
        f"{'DEMO (no real emails)' if DEMO_MODE else 'LIVE'}"
    )
    print(f"  SMTP email   : {SMTP_EMAIL or 'not set'}")
    print(
        f"  SMTP password: "
        f"{'set ✓' if SMTP_PASSWORD else 'not set'}"
    )
    print(
        f"  Notifications: "
        f"{'ENABLED' if EMAIL_NOTIFICATIONS_ENABLED else 'DISABLED'}"
    )
    print(f"  TLS          : {SMTP_USE_TLS}")
    print(f"  Timeout      : {SMTP_TIMEOUT}s")
    print()

    if not DEMO_MODE and (not SMTP_EMAIL or not SMTP_PASSWORD):
        print(
            "ERROR: SMTP credentials not set in config/.env\n"
            "Add these to config/.env:\n"
            "  SMTP_HOST=smtp.gmail.com\n"
            "  SMTP_PORT=587\n"
            "  SMTP_EMAIL=youremail@gmail.com\n"
            "  SMTP_PASSWORD=your_gmail_app_password\n\n"
            "Or run in demo mode:\n"
            "  DEMO_MODE=true"
        )
        if not DEMO_MODE:
            sys.exit(1)

    if DEMO_MODE:
        TEST_EMAIL = "demo.user@icici.com"
        print(f"Running in DEMO MODE — using test address: {TEST_EMAIL}\n")
    else:
        TEST_EMAIL = input(
            "Enter your email to receive test emails: "
        ).strip()
        if not TEST_EMAIL or "@" not in TEST_EMAIL:
            print("Invalid email. Exiting.")
            sys.exit(1)

    print("--- Test 1: Resolved notification ---")
    ok = notify_user(
        email      = TEST_EMAIL,
        ticket_id  = 1001,
        subject    = "Install Zoom on my laptop",
        message    = (
            "Dear Rahul,\n\n"
            "Your ticket has been automatically resolved.\n\n"
            "Action taken: Zoom installed on PC-ICICI-0042.\n\n"
            "Please restart your computer and verify Zoom is working.\n\n"
            "Thank you,\nIT Support Team"
        ),
        notif_type = "resolved",
    )
    print(f"  Result: {'SENT ✓' if ok else 'FAILED ✗'}\n")

    print("--- Test 2: KB guide notification ---")
    ok = notify_user(
        email      = TEST_EMAIL,
        ticket_id  = 1002,
        subject    = "Cannot connect to VPN",
        message    = (
            "Dear Priya,\n\n"
            "Here is a self-help guide for your VPN issue:\n\n"
            "1. Open Cisco AnyConnect from your taskbar\n"
            "2. Enter VPN address: vpn.icici.com\n"
            "3. Click Connect and enter your AD credentials\n"
            "4. If it fails, restart your network adapter\n\n"
            "An engineer will follow up if this does not help."
        ),
        notif_type = "kb_guide_sent",
    )
    print(f"  Result: {'SENT ✓' if ok else 'FAILED ✗'}\n")

    print("--- Test 3: Escalated notification ---")
    ok = notify_user(
        email      = TEST_EMAIL,
        ticket_id  = 1003,
        subject    = "Laptop screen flickering",
        message    = (
            "Dear Amit,\n\n"
            "Your ticket has been escalated to an engineer.\n\n"
            "An engineer will review and follow up within 4 hours.\n\n"
            "Thank you for your patience."
        ),
        notif_type = "escalated",
    )
    print(f"  Result: {'SENT ✓' if ok else 'FAILED ✗'}\n")

    print("--- Test 4: Engineer escalation email ---")
    ok = notify_engineer(
        engineer_email   = TEST_EMAIL,
        ticket_id        = 1004,
        subject          = "Laptop screen flickering badly",
        category         = "hardware",
        priority         = "high",
        ai_summary       = (
            "User reports laptop screen has been flickering "
            "continuously since morning. Appears to be physical "
            "hardware damage. Auto-resolution was not attempted. "
            "No KB guide was found for this issue."
        ),
        requester_name   = "Amit Patel",
        requester_email  = "amit.patel@icici.com",
        machine_name     = "LAPTOP-ICICI-115",
        suggested_action = (
            "Schedule on-site hardware inspection with engineer."
        ),
    )
    print(f"  Result: {'SENT ✓' if ok else 'FAILED ✗'}\n")

    print("--- Test 5: Bulk notifications ---")
    bulk_results = notify_bulk([
        {
            "email"      : TEST_EMAIL,
            "ticket_id"  : 2001,
            "subject"    : "Bulk test ticket 1",
            "message"    : "Bulk notification test 1.",
            "notif_type" : "general",
        },
        {
            "email"      : TEST_EMAIL,
            "ticket_id"  : 2002,
            "subject"    : "Bulk test ticket 2",
            "message"    : "Bulk notification test 2.",
            "notif_type" : "resolved",
        },
    ])
    print(
        f"  Success: {bulk_results['success']} "
        f"| Failed: {bulk_results['failed']} "
        f"| Total: {bulk_results['total']}\n"
    )

    print("--- Test 6: Invalid email handled ---")
    ok = notify_user(
        email      = "not-a-valid-email",
        ticket_id  = 9999,
        subject    = "Test",
        message    = "This should fail gracefully.",
    )
    print(f"  Result: {'FAILED as expected ✓' if not ok else 'Should have failed ✗'}\n")

    print("=" * 60)
    print("All notifier tests complete.")
    if not DEMO_MODE:
        print("Check your inbox for test emails.")
    print("=" * 60 + "\n")