import asyncio

async def execute_agents(kernel, request):

    results = {}

    # -------------------------------
    # DOCUMENT CREATION AGENT
    # -------------------------------
    if "document_creation" in request["agents"]:
        doc_function = kernel.plugins["document"]["create_documents"]
        results["document_creation"] = await doc_function(
            kernel,
            document_config=request["document_config"]
        )

    # -------------------------------
    # EMAIL SENDING AGENT
    # -------------------------------
    if "email_sending" in request["agents"]:
        email_function = kernel.plugins["email"]["send_emails"]
        results["email_sending"] = await email_function(
            kernel,
            email_config=request["email_config"]
        )

    return results
