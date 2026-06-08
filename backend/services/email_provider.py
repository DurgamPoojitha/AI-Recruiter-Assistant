from abc import ABC, abstractmethod
from backend.core.logging import logger

class EmailProvider(ABC):
    @abstractmethod
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        pass

class MockEmailProvider(EmailProvider):
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        logger.info(f"--- MOCK EMAIL DISPATCH ---")
        logger.info(f"To: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body: \n{body}")
        logger.info(f"---------------------------")
        return True

class SendGridProvider(EmailProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Initialize SendGrid client here

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        # Skeleton for SendGrid API call
        logger.info(f"Simulating SendGrid dispatch to {to_email}")
        return True

class MailgunProvider(EmailProvider):
    def __init__(self, api_key: str, domain: str):
        self.api_key = api_key
        self.domain = domain

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        # Skeleton for Mailgun API call
        logger.info(f"Simulating Mailgun dispatch to {to_email}")
        return True

def get_email_provider() -> EmailProvider:
    # In a real app, this would read from settings and instantiate the right provider
    return MockEmailProvider()
