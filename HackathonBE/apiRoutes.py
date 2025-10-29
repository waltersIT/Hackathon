import re
from urllib.parse import urlparse

# Pre-encoded includes strings (kept exactly as provided)
INCLUDES = {
    "properties": (
        "applicationTemplate%2Cimage%2Cunit%2Clease%2Cportfolios%2Clisting%2C"
        "appliances%2CmanagementFeeSetting%2Cassociations%2CpropertyManager%2CpastLeases%2CfutureLeases%2Cowners"
    ),
    "maintenance_work_orders": (
        "vendor%2CvendorTrade%2Cproperty%2Cunit%2Cbills%2Cassignees%2Cportfolio%2C"
        "portfolioBalances%2Cowners%2Clease%2CleaseBalances%2CleaseTenants%2Cinspection%2C"
        "workOrderProject%2Cassociations%2Cinspection%2Creview"
    ),
    "maintenance_inspections": "areas%2Citems%2Cfiles%2Cunit%2Clease%2Cproperty",
    "maintenance_projects": "assignedToUser%2Cproperty%2Cunit%2Crestrictions",
    "screening_applications": (
        "applicants%2Clease%2Creports%2Cgroup%2CcreditReportDocument%2CcriminalReportDocument%2C"
        "evictionReportDocument%2Cprospect%2Canimals"
    ),
    "screening_prospects": "contact%2Cunit%2Cinvitation%2Cstatus",
    "screening_payments": "applicant%2Capplication%2Crefunds",
}

# Route table: each entry defines how to match a web URL and build the API URL(s)
ROUTES = [
    # Maintenance
    {
        "pattern": re.compile(r"^/maintenance/work-orders/(?P<id>\d+)/?$"),
        "api_path": lambda _id: f"/api/manager/maintenance/work-orders/{_id}",
        "includes": INCLUDES["maintenance_work_orders"],
    },
    {
        "pattern": re.compile(r"^/maintenance/inspections/(?P<id>\d+)/?$"),
        "api_path": lambda _id: f"/api/manager/maintenance/inspections/{_id}",
        "includes": INCLUDES["maintenance_inspections"],
    },
    {
        "pattern": re.compile(r"^/maintenance/projects/(?P<id>\d+)/?$"),
        "api_path": lambda _id: f"/api/manager/maintenance/work-orders/projects/{_id}",
        "includes": INCLUDES["maintenance_projects"],
    },

    # Diagnostics (no ID; maps to TWO API endpoints)
    {
        "pattern": re.compile(r"^/accounting/diagnostics/?$"),
        "api_paths": [
            "/api/manager/accounting/accounts",    # GL accounts
            "/api/manager/accounting/diagnostics"  # actual diagnostics
        ],
    },

    # Properties
    {
        "pattern": re.compile(r"^/properties/(?P<id>\d+)/?$"),
        "api_path": lambda _id: f"/api/manager/properties/{_id}",
        "includes": INCLUDES["properties"],
    },

    # Screening
    {
        "pattern": re.compile(r"^/screening/applications/(?P<id>\d+)/?$"),
        "api_path": lambda _id: f"/api/manager/screening/applications/{_id}",
        "includes": INCLUDES["screening_applications"],
    },
    {
        "pattern": re.compile(r"^/screening/prospects/(?P<id>\d+)/?$"),
        "api_path": lambda _id: f"/api/manager/screening/prospects/{_id}",
        "includes": INCLUDES["screening_prospects"],
    },
    {
        "pattern": re.compile(r"^/screening/payments/(?P<id>\d+)/?$"),
        "api_path": lambda _id: f"/api/manager/screening/payments/{_id}",
        "includes": INCLUDES["screening_payments"],
    },
]

def build_api_url(webpage_url: str) -> str:
    """
    Given a Rentvine webpage URL, return the corresponding API URL(s).
    - Extracts the base (scheme+host)
    - Matches path patterns
    - Injects the object ID when present
    - Appends the correct 'includes' querystring when required

    Returns:
        List of API URL strings (Diagnostics maps to two endpoints).
    Raises:
        ValueError if the URL path is unsupported or an ID is missing/invalid.
    """
    parsed = urlparse(webpage_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path.rstrip("/")

    for route in ROUTES:
        match = route["pattern"].match(path)
        if not match:
            continue

        # Special case: routes with multiple API paths (Diagnostics)
        if "api_paths" in route:
            return [base + p for p in route["api_paths"]]

        # Routes with an ID
        _id = match.groupdict().get("id")
        if _id is not None and not _id.isdigit():
            raise ValueError("Found an ID segment, but it is not numeric.")

        api = base + route["api_path"](_id)  # type: ignore
        if "includes" in route and route["includes"]:
            api += f"?includes={route['includes']}"
        return api

    raise ValueError(f"Unsupported or unrecognized path: {path}")


if __name__ == "__main__":
    examples = [
        "https://123pm.rentvine.com/maintenance/work-orders/5424",
        "https://123pm.rentvine.com/maintenance/inspections/814",
        "https://123pm.rentvine.com/maintenance/projects/151",
        "https://123pm.rentvine.com/accounting/diagnostics",
        "https://123pm.rentvine.com/properties/245?page=1&pageSize=15",
        "https://123pm.rentvine.com/screening/applications/1638",
        "https://123pm.rentvine.com/screening/prospects/114",
        "https://123pm.rentvine.com/screening/payments/1",
    ]
    for e in examples:
        print(e, "=>", build_api_url(e))
