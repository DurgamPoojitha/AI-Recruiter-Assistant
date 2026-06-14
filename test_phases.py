import asyncio
from backend.parsers.resume_parser import analyze_employment_history

print("--- Testing Phase 7: Risk Analyzer ---")
resume_text_high_risk = """
Experience
Software Engineer at Tech Corp
2022 - 2023
Developed backend systems.

Backend Dev at Startup
2023 - 2024
Built APIs.

Fullstack Engineer at Agency
2024 - 2025
Client work.

Frontend Dev at WebCo
2025 - Present
UI work.
"""
risk_level, risk_factors = analyze_employment_history(resume_text_high_risk)
print(f"Risk Level: {risk_level}")
print(f"Risk Factors: {risk_factors}")

resume_text_gap = """
Experience
Software Engineer at BigCorp
2018 - 2021
Wrote code.

Senior Engineer at NewCorp
2024 - Present
Wrote more code.
"""
risk_level, risk_factors = analyze_employment_history(resume_text_gap)
print(f"Risk Level: {risk_level}")
print(f"Risk Factors: {risk_factors}")

