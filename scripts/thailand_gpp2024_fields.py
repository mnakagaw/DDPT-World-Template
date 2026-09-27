"""Pinned 2024p current-price sector rows in the official NESDC GPP workbook.

Sector measures are overlapping published rows, not a flat set to add together.
The agriculture alias and non-agriculture subtotal are audited but not exposed
as duplicate indicators.
"""

SECTOR_FIELDS = (
    ("AGRI", "Agriculture", "primary"),
    ("INDUSTRIAL", "Industrial", "industry_total"),
    ("MINING", "Mining and quarrying", "industry_detail"),
    ("MANUFACTURING", "Manufacturing", "industry_detail"),
    ("ELECTRICITY_GAS", "Electricity, gas, steam and air conditioning supply", "industry_detail"),
    ("WATER_WASTE", "Water supply; sewerage, waste management and remediation activities", "industry_detail"),
    ("SERVICES", "Services", "services_total"),
    ("CONSTRUCTION", "Construction", "services_detail"),
    ("WHOLESALE_RETAIL", "Wholesale and retail trade and repair of motor vehicles and motorcycle", "services_detail"),
    ("TRANSPORT_STORAGE", "Transportation and storage", "services_detail"),
    ("ACCOMMODATION_FOOD", "Accommodation and food service activities", "services_detail"),
    ("INFO_COMMS", "Information and communication", "services_detail"),
    ("FINANCE_INSURANCE", "Financial and insurance activities", "services_detail"),
    ("REAL_ESTATE", "Real estate activities", "services_detail"),
    ("PROFESSIONAL_TECH", "Professional, scientific and technical activities", "services_detail"),
    ("ADMIN_SUPPORT", "Administrative and support service activities", "services_detail"),
    ("PUBLIC_ADMIN", "Public administration and defence; compulsory social security", "services_detail"),
    ("EDUCATION", "Education", "services_detail"),
    ("HEALTH_SOCIAL", "Human health and social work activities", "services_detail"),
    ("ARTS_RECREATION", "Arts, entertainment and recreation", "services_detail"),
    ("OTHER_SERVICES", "Other service activities", "services_detail"),
)

SECTOR_LABELS = (
    "Agriculture",
    "Agriculture, forestry and fishing",  # same published value as Agriculture
    "Non-Agriculture",  # published subtotal of Industrial plus Services
    *(label for _, label, _ in SECTOR_FIELDS[1:]),
)
SECTOR_IDS = {label: f"THA_NESDC_CP_{key}_MTHB" for key, label, _ in SECTOR_FIELDS}
