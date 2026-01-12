# from semantic_kernel.functions import kernel_function
# from AI_open_negotiation.utils.logger import log_info, log_error


# class EmailSkill:

#     @kernel_function(
#         name="send_emails",
#         description="Send open negotiation emails with attachments"
#     )
#     def send_emails(self, email_config: dict) -> dict:

#         log_info("[EmailSkill] Email sending started")
#         print("[EmailSkill] Email sending started")

#         try:
#             import os
#             import time
#             import pandas as pd
#             import win32com.client as win32
#             import pythoncom

#             DEFAULT_BODY = """
#             <p>To Whom it May Concern,</p>
#             <p>In accordance with the No Surprise Act, we are submitting a written request of the
#             following as it pertains to the attached referenced member claim:</p>
#             <ol style="margin-left:15px;">
#                 <li>Confirmation if the QPA for items/services included contracted rates that were not on a fee-for-service basis,</li>
#                 <li>Confirmation if the QPA for items/services was determined using underlying fee schedule rates or a derived amount,</li>
#                 <li>Confirmation if any related service codes(s) other than those included on the claim were utilized in determining the QPA,</li>
#                 <li>Confirmation if the plan used an eligible database to determine the QPA and if so, which database was used, and</li>
#                 <li>Confirmation if the plan’s contracted rates include risk-sharing, bonus, or other incentive-based payments.</li>
#             </ol>
#             <p>Due to the volume of requests, we've provided an Excel file broken down by date of services.</p>
#             <p>Respectfully,<br>
#             Open Nego Email Team<br>
#             No Surprise Bill c/o CMG<br>
#             <a href="mailto:concordmgNSA@nosurprisebill.com">concordmgNSA@nosurprisebill.com</a></p>
#             """

#             def run_email_pipeline(config: dict):

#                 pythoncom.CoInitialize()

#                 try:
#                     print("[EmailSkill] Reading Excel...")
#                     excel_path = config["excel_path"]
#                     base_folder = config["base_folder"]
#                     signature_image = config["signature_image"]

#                     df = pd.read_excel(excel_path)
#                     df["InsurancePlanName"] = df["InsurancePlanName"].astype(str).str.strip()
#                     df["ProvOrgNPI"] = df["ProvOrgNPI"].astype(str).str.strip()
#                     df["To"] = df["To"].astype(str).str.strip()

#                     if "CC" in df.columns:
#                         df["CC"] = df["CC"].astype(str).str.strip()

#                     print(f"[EmailSkill] Total rows in Excel: {len(df)}")

#                     outlook = win32.Dispatch("Outlook.Application")
#                     namespace = outlook.GetNamespace("MAPI")

#                     # ===============================
#                     # SELECT SENDER ACCOUNT
#                     # ===============================
#                     send_account = None
#                     for acc in namespace.Accounts:
#                         print(f"[EmailSkill] Found Outlook account: {acc.SmtpAddress}")
#                         if "nosurprisebill.com" in acc.SmtpAddress.lower():
#                             send_account = acc

#                     if not send_account:
#                         raise RuntimeError("Correct Outlook account NOT found")

#                     print(f"[EmailSkill] Using sender account: {send_account.SmtpAddress}")

#                     grouped = df.groupby(["ProvOrgNPI", "InsurancePlanName"])
#                     print(f"[EmailSkill] Total email groups to send: {len(grouped)}")

#                     draft_subjects = []

#                     # =====================================================
#                     # PHASE 1 — CREATE & SAVE DRAFTS
#                     # =====================================================
#                     for idx, ((prov_npi, plan), group) in enumerate(grouped, start=1):

#                         print(f"[EmailSkill] Drafting email {idx}: NPI={prov_npi} | PLAN={plan}")

#                         mail = outlook.CreateItem(0)
#                         mail.SendUsingAccount = send_account

#                         mail.To = group.iloc[0]["To"]
#                         mail.CC = group.iloc[0]["CC"] if "CC" in group.columns else ""
#                         mail.Subject = str(group.iloc[0]["Subject"]).strip()

#                         html_body = DEFAULT_BODY

#                         # Attach files
#                         attachment_folder = os.path.join(base_folder, prov_npi, plan)
#                         attached = 0

#                         if os.path.exists(attachment_folder):
#                             for root, _, files in os.walk(attachment_folder):
#                                 for f in files:
#                                     if f.lower().endswith((".pdf", ".xls", ".xlsx")):
#                                         mail.Attachments.Add(os.path.join(root, f))
#                                         attached += 1

#                         print(f"[EmailSkill] Attachments added: {attached}")

#                         # Signature
#                         if os.path.exists(signature_image):
#                             img = mail.Attachments.Add(signature_image)
#                             img.PropertyAccessor.SetProperty(
#                                 "http://schemas.microsoft.com/mapi/proptag/0x3712001F",
#                                 "signature_img"
#                             )
#                             html_body += '<br><img src="cid:signature_img" width="90">'

#                         mail.HTMLBody = html_body

#                         # 🔥 SAVE AS DRAFT
#                         mail.Save()
#                         draft_subjects.append(mail.Subject)

#                         print(f"[EmailSkill] Draft saved: {mail.Subject}")
#                         log_info(f"[EmailSkill] Draft saved: {mail.Subject}")

#                     # =====================================================
#                     # PHASE 2 — WAIT BEFORE SENDING
#                     # =====================================================
#                     print("[EmailSkill] Waiting 60 seconds before sending emails...")
#                     log_info("[EmailSkill] Waiting 60 seconds before sending emails...")
#                     time.sleep(60)

#                     # =====================================================
#                     # PHASE 3 — SEND DRAFTS SAFELY
#                     # =====================================================
#                     print("[EmailSkill] Sending drafted emails...")
#                     sent_count = 0

#                     drafts_folder = namespace.GetDefaultFolder(16)  # Drafts
#                     drafts = drafts_folder.Items

#                     for mail in drafts:
#                         try:
#                             if mail.Subject in draft_subjects:
#                                 mail.Send()
#                                 sent_count += 1
#                                 print(f"[EmailSkill] Sent email: {mail.Subject}")
#                                 log_info(f"[EmailSkill] Sent email: {mail.Subject}")
#                         except Exception as e:
#                             print(f"[EmailSkill] Failed sending draft: {e}")
#                             log_error(f"[EmailSkill] Failed sending draft: {e}")

#                     return sent_count

#                 finally:
#                     pythoncom.CoUninitialize()

#             # ==========================
#             # RUN PIPELINE
#             # ==========================
#             sent_count = run_email_pipeline(email_config)

#             print(f"[EmailSkill] Total emails sent successfully: {sent_count}")
#             log_info(f"[EmailSkill] Total emails sent successfully: {sent_count}")

#             return {
#                 "status": "SUCCESS",
#                 "emails_sent": sent_count
#             }

#         except Exception as e:
#             log_error(f"[EmailSkill] Error: {e}")
#             print(f"[EmailSkill] Error: {e}")
#             return {"status": "FAILED", "error": str(e)}













from semantic_kernel.functions import kernel_function
from AI_open_negotiation.utils.logger import log_info, log_error
import re


class EmailSkill:

    @kernel_function(
        name="send_emails",
        description="Create Outlook email drafts only (no sending)"
    )
    def send_emails(self, email_config: dict) -> dict:
        log_info("[EmailSkill] Draft creation started")
        print("\n========== EMAIL DRAFT PIPELINE STARTED ==========")

        try:
            import os
            import pandas as pd
            import win32com.client as win32
            import pythoncom

            def safe_folder_name(value: str) -> str:
                return re.sub(r'[\\/:*?"<>|]', "_", str(value).strip())

            DEFAULT_BODY = """
            <p>To Whom it May Concern,</p>
            <p>In accordance with the No Surprise Act, we are submitting a written request of the
            following as it pertains to the attached referenced member claim:</p>
            <ol style="margin-left:15px;">
                <li>Confirmation if the QPA for items/services included contracted rates that were not on a fee-for-service basis,</li>
                <li>Confirmation if the QPA was determined using underlying fee schedule rates or a derived amount,</li>
                <li>Confirmation if related service codes were used in determining the QPA,</li>
                <li>Confirmation if an eligible database was used,</li>
                <li>Confirmation if contracted rates include incentive-based payments.</li>
            </ol>
            <p>Due to the volume of requests, we've provided an Excel file broken down by date of services.</p>
            <p>Respectfully,<br>
            Open Nego Email Team<br>
            No Surprise Bill c/o CMG</p>
            """

            pythoncom.CoInitialize()
            try:
                excel_path = email_config["excel_path"]
                base_folder = email_config["base_folder"]
                signature_image = email_config["signature_image"]

                # ================= EXCEL LOAD =================
                print(f"\n[EXCEL] Reading file: {excel_path}")
                df = pd.read_excel(excel_path)
                print(f"[EXCEL] Total rows read: {len(df)}")
                print(f"[EXCEL] Columns found: {list(df.columns)}")

                required_cols = ["ProvOrgNPI", "InsurancePlanName", "To", "Subject"]
                for col in required_cols:
                    if col not in df.columns:
                        raise ValueError(f"Missing required column: {col}")

                df["InsurancePlanName"] = df["InsurancePlanName"].astype(str).str.strip()
                df["ProvOrgNPI"] = df["ProvOrgNPI"].astype(str).str.strip()
                df["To"] = df["To"].astype(str).str.strip()

                print("[EXCEL] Data normalization completed")

                # ================= OUTLOOK =================
                print("\n[OUTLOOK] Initializing Outlook...")
                outlook = win32.Dispatch("Outlook.Application")
                namespace = outlook.GetNamespace("MAPI")

                send_account = None
                for acc in namespace.Accounts:
                    print(f"[OUTLOOK] Found account: {acc.SmtpAddress}")
                    if "nosurprisebill.com" in acc.SmtpAddress.lower():
                        send_account = acc
                        break

                if not send_account:
                    raise RuntimeError("Outlook sender account not found")

                print(f"[OUTLOOK] Using sender: {send_account.SmtpAddress}")

                # ================= GROUPING =================
                grouped = df.groupby(["ProvOrgNPI", "InsurancePlanName"])
                print(f"\n[GROUPING] Total unique groups: {len(grouped)}")

                drafted = 0

                # ================= CREATE DRAFTS =================
                for idx, ((prov_npi, plan), group) in enumerate(grouped, start=1):

                    print("\n------------------------------------------------")
                    print(f"[GROUP {idx}] Processing")
                    print(f"[GROUP {idx}] ProvOrgNPI : {prov_npi}")
                    print(f"[GROUP {idx}] Plan       : {plan}")
                    print(f"[GROUP {idx}] Rows in group: {len(group)}")

                    prov_clean = safe_folder_name(prov_npi)
                    plan_clean = safe_folder_name(plan)

                    mail = outlook.CreateItem(0)
                    mail.SendUsingAccount = send_account
                    mail.To = group.iloc[0]["To"]
                    mail.Subject = str(group.iloc[0]["Subject"]).strip()
                    mail.HTMLBody = DEFAULT_BODY

                    print(f"[EMAIL] To      : {mail.To}")
                    print(f"[EMAIL] Subject : {mail.Subject}")

                    # ================= ATTACHMENTS =================
                    attach_folder = os.path.join(base_folder, prov_clean, plan_clean)
                    print(f"[ATTACHMENT] Looking in: {attach_folder}")

                    attached = 0
                    if os.path.exists(attach_folder):
                        for root, _, files in os.walk(attach_folder):
                            for f in files:
                                if f.lower().endswith((".pdf", ".xls", ".xlsx")):
                                    file_path = os.path.join(root, f)
                                    mail.Attachments.Add(file_path)
                                    attached += 1
                                    print(f"[ATTACHMENT] Added: {file_path}")
                    else:
                        print("[ATTACHMENT] Folder NOT found")

                    print(f"[ATTACHMENT] Total files attached: {attached}")

                    if attached == 0:
                        print("[SKIPPED] No attachments — draft not created")
                        continue

                    # ================= SIGNATURE =================
                    if os.path.exists(signature_image):
                        img = mail.Attachments.Add(signature_image)
                        img.PropertyAccessor.SetProperty(
                            "http://schemas.microsoft.com/mapi/proptag/0x3712001F",
                            "signature_img"
                        )
                        mail.HTMLBody += '<br><img src="cid:signature_img" width="90">'
                        print("[SIGNATURE] Signature image embedded")
                    else:
                        print("[SIGNATURE] Signature image NOT found")

                    # ================= SAVE DRAFT =================
                    mail.Save()
                    drafted += 1
                    print(f"[DRAFT SAVED] Draft #{drafted} created successfully")

                print("\n========== EMAIL DRAFT PIPELINE COMPLETED ==========")
                print(f"[RESULT] Total drafts created: {drafted}")

                return {
                    "status": "SUCCESS",
                    "drafts_created": drafted
                }

            finally:
                pythoncom.CoUninitialize()

        except Exception as e:
            log_error(f"[EmailSkill] Fatal Error: {e}")
            print(f"[FATAL ERROR] {e}")
            return {"status": "FAILED", "error": str(e)}
