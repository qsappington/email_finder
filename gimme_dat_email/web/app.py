from flask import Flask, request, render_template
from email_validator import validate_email, EmailNotValidError
import re
import whois
from dotenv import load_dotenv
import os
from pyhunter import PyHunter
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

# Initialize Hunter
hunter = PyHunter(os.getenv('HUNTER_API_KEY'))

app = Flask(__name__)

def get_hunter_info(company_name):
    """
    Get domain and email pattern from Hunter.io
    Returns (domain, pattern) or (None, None) if not found
    """
    try:
        # Search for company domain and pattern
        result = hunter.domain_search(company=company_name)
        if result:
            domain = result.get('domain')
            # Get the most common pattern
            pattern = result.get('pattern')
            if domain and pattern:
                return domain, pattern
    except Exception as e:
        print(f"Hunter API error: {e}")
    return None, None

def generate_email_from_pattern(first, last, pattern, domain):
    """
    Generate email based on Hunter's pattern
    Common patterns: {first}, {last}, {f}, {l}
    """
    first = first.lower()
    last = last.lower()
    
    # Create mapping for pattern variables
    mapping = {
        '{first}': first,
        '{last}': last,
        '{f}': first[0] if first else '',
        '{l}': last[0] if last else '',
    }
    
    # Replace pattern variables with actual values
    local_part = pattern
    for key, value in mapping.items():
        local_part = local_part.replace(key, value)
    
    return f"{local_part}@{domain}"

def get_smart_variations(company_name):
    """
    Generate smarter variations, starting with most likely matches
    """
    name_clean = company_name.lower().replace(' ', '')
    
    # Primary variations (most likely)
    primary = [
        company_name,
        name_clean,
        f"{name_clean}capital",
        f"{name_clean}cap",
        f"{name_clean}partners",
        f"{name_clean}group",
        f"{name_clean}mgmt",
        f"{name_clean}management",
        f"{name_clean}advisors",
        f"{name_clean}llc",
        # With spaces
        f"{company_name} capital",
        f"{company_name} partners",
        f"{company_name} management",
        # Financial industry specific
        f"{name_clean}vc",
        f"{name_clean}ventures",
        f"{name_clean}invest",
        f"{name_clean}investments",
        f"{name_clean}asset",
        f"{name_clean}assets"
    ]
    
    # Also try each word separately if it's a multi-word company
    if ' ' in company_name:
        words = company_name.split()
        primary.extend(words)
    
    return primary

def search_single_company(variation):
    """
    Search for a single company variation
    """
    try:
        results = hunter.domain_search(company=variation, limit=5)
        companies = set()
        
        if results:
            # Add main result
            companies.add((
                results.get('organization', variation),
                results.get('domain'),
                results.get('pattern')
            ))
            # Add alternative domains
            for domain in results.get('alternative_domains', []):
                companies.add((
                    domain.get('organization', variation),
                    domain.get('domain'),
                    domain.get('pattern')
                ))
        return companies
    except Exception as e:
        print(f"Hunter API error for variation '{variation}': {e}")
        return set()

def search_companies(company_name):
    """
    Search for company domains with optimized searching
    """
    companies = set()
    variations = get_smart_variations(company_name)
    
    # Try all variations concurrently
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(search_single_company, variations)
        for result in results:
            companies.update(result)
    
    # Try domain suggestions API as well
    try:
        suggestions = hunter.domain_suggestion(company_name)
        if suggestions:
            for suggestion in suggestions:
                companies.add((
                    suggestion.get('organization', company_name),
                    suggestion.get('domain'),
                    suggestion.get('pattern', '{first}.{last}')
                ))
    except Exception as e:
        print(f"Hunter API suggestion error: {e}")
    
    # Remove any entries with None values and convert to list
    valid_companies = [
        company for company in companies 
        if all(company) and not any(x is None for x in company)
    ]
    
    # Sort by relevance with priority for financial terms
    financial_terms = {'capital', 'cap', 'partners', 'mgmt', 'management', 'vc', 'ventures', 'invest'}
    name_clean = company_name.lower().replace(' ', '')
    
    def sort_key(x):
        company_lower = x[0].lower()
        domain_lower = x[1].lower()
        has_financial_term = any(term in domain_lower for term in financial_terms)
        exact_match = name_clean in company_lower.replace(' ', '')
        return (
            not exact_match,  # exact matches first
            not has_financial_term,  # financial terms second
            len(x[0])  # shorter names last
        )
    
    return sorted(valid_companies, key=sort_key)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    domain_info = None
    companies = None
    selected_company = None
    
    if request.method == "POST":
        full_name = request.form["name"].strip()
        company = request.form["company"].strip()
        selected_domain = request.form.get("selected_domain")
        selected_pattern = request.form.get("selected_pattern")
        
        if selected_domain and selected_pattern:
            # User has selected a specific company/domain
            name_parts = full_name.split()
            first = name_parts[0]
            last = name_parts[-1] if len(name_parts) > 1 else ""
            
            email = generate_email_from_pattern(first, last, selected_pattern, selected_domain)
            result = [email]
            domain_info = f"Generated email for domain: {selected_domain}"
        else:
            # First search - show company options
            companies = search_companies(company)
            if not companies:
                domain_info = "Could not find any matching companies"
                result = []
    
    return render_template(
        "index.html", 
        result=result, 
        domain_info=domain_info, 
        companies=companies
    )

if __name__ == "__main__":
    app.run(debug=True)
