import re
import json
import requests
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
    "portfolios": "owners%2Cproperties%2Cposting%2CstatementSetting%2Cledger",
    "ledgers": "balances",
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
    
    # Portfolios (special case: requires two API calls)
    {
        "pattern": re.compile(r"^/portfolios/(?P<id>\d+)/?$"),
        "api_path": lambda _id: f"/api/manager/portfolios/{_id}",
        "includes": INCLUDES["portfolios"],
        "needs_ledger": True,  # Flag to indicate this route needs a second API call
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
    print("WEB PAGE URL", webpage_url)

    print("building api url")
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
        print("HERE IS THE API URL", api)
        return api

    raise ValueError(f"Unsupported or unrecognized path: {path}")


def fetch_api_responses(webpage_url: str, username: str = None, password: str = None) -> str:
    """
    Given a Rentvine webpage URL, fetch the corresponding API response(s) and return as JSON string.
    
    For portfolios, this will:
    1. Call the portfolio endpoint
    2. Extract the ledgerID from the response
    3. Call the ledger endpoint
    4. Combine both responses into a single JSON string
    
    For other routes, it will call the single endpoint and return the response.
    
    Returns:
        JSON string containing the API response(s)
    Raises:
        ValueError if the URL path is unsupported or an ID is missing/invalid.
        requests.RequestException if API calls fail.
    """
    print("FETCHING API RESPONSES FROM API ROUTES")
    print(f"Input webpage_url: {webpage_url}")
    parsed = urlparse(webpage_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path.rstrip("/")
    print(f"Extracted path: {path}")
    print(f"Base URL: {base}")

    for route in ROUTES:
        match = route["pattern"].match(path)
        if not match:
            continue
        print(f"Matched route pattern: {route['pattern'].pattern}")

        # Special case: portfolios (requires two API calls)
        if route.get("needs_ledger"):
            print("Processing portfolio route (needs ledger)")
            _id = match.groupdict().get("id")
            print(f"Portfolio ID: {_id}")
            if _id is None or not _id.isdigit():
                raise ValueError("Portfolio ID is missing or invalid.")
            
            # Build first API URL (portfolio endpoint)
            portfolio_url = base + route["api_path"](_id)
            if "includes" in route and route["includes"]:
                portfolio_url += f"?includes={route['includes']}"
            print(f"Portfolio API URL: {portfolio_url}")
            
            # Make first API call
            if username and password:
                print("Making portfolio API call with username and password")
                portfolio_response = requests.get(portfolio_url, auth=(username, password), verify=False)
            else:
                portfolio_response = requests.get(portfolio_url, verify=False)
            portfolio_response.raise_for_status()
            portfolio_data = portfolio_response.json()
            print("Portfolio API call successful")
            
            # Extract ledgerID from the response
            ledger_id = None
            if "ledger" in portfolio_data and isinstance(portfolio_data["ledger"], dict):
                ledger_id = portfolio_data["ledger"].get("ledgerID")
            print(f"Extracted ledgerID: {ledger_id}")
            
            if not ledger_id:
                raise ValueError("Could not find ledgerID in portfolio response.")
            
            # Build second API URL (ledger endpoint)
            ledger_url = base + f"/api/manager/accounting/ledgers/{ledger_id}"
            if "ledgers" in INCLUDES:
                ledger_url += f"?includes={INCLUDES['ledgers']}"
            print(f"Ledger API URL: {ledger_url}")
            
            # Make second API call
            if username and password:
                ledger_response = requests.get(ledger_url, auth=(username, password), verify=False)
            else:
                ledger_response = requests.get(ledger_url, verify=False)
            ledger_response.raise_for_status()
            ledger_data = ledger_response.json()
            print("Ledger API call successful")
            
            # Combine both responses
            combined_data = {
                "portfolio": portfolio_data,
                "ledger": ledger_data
            }
            print("Combined portfolio and ledger data")
            
            return json.dumps(combined_data, indent=2)

        # Special case: routes with multiple API paths (Diagnostics)
        if "api_paths" in route:
            responses = []
            for api_path in route["api_paths"]:
                api_url = base + api_path
                if username and password:
                    response = requests.get(api_url, auth=(username, password), verify=False)
                else:
                    response = requests.get(api_url, verify=False)
                response.raise_for_status()
                responses.append(response.json())
            
            # Combine multiple responses (for diagnostics)
            if len(responses) == 1:
                return json.dumps(responses[0], indent=2)
            else:
                combined = {
                    "accounts": responses[0],
                    "diagnostics": responses[1]
                }
                return json.dumps(combined, indent=2)

        # Routes with an ID
        _id = match.groupdict().get("id")
        if _id is not None and not _id.isdigit():
            raise ValueError("Found an ID segment, but it is not numeric.")

        api_url = base + route["api_path"](_id)  # type: ignore
        if "includes" in route and route["includes"]:
            api_url += f"?includes={route['includes']}"
        
        # Make API call
        if username and password:
            response = requests.get(api_url, auth=(username, password), verify=False)
        else:
            response = requests.get(api_url, verify=False)
        response.raise_for_status()
        
        return json.dumps(response.json(), indent=2)

    raise ValueError(f"Unsupported or unrecognized path: {path}")


if __name__ == "__main__":
    examples = [
        "https://abchomes.rentvinedev.com/maintenance/work-orders/5424",
        "https://abchomes.rentvinedev.com/maintenance/inspections/814",
        "https://abchomes.rentvinedev.com/maintenance/projects/151",
        "https://abchomes.rentvinedev.com/accounting/diagnostics",
        "https://abchomes.rentvinedev.com/properties/245?page=1&pageSize=15",
        "https://abchomes.rentvinedev.com/screening/applications/1638",
        "https://abchomes.rentvinedev.com/screening/prospects/114",
        "https://abchomes.rentvinedev.com/screening/payments/1",
    ]
    for e in examples:
        print(e, "=>", build_api_url(e))
