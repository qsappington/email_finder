const HUNTER_API_KEY = 'e894b7ce8d4a878f1cfaebe76f8da449b35e9240';

document.getElementById('findEmail').addEventListener('click', async () => {
  const name = document.getElementById('name').value;
  const company = document.getElementById('company').value;

  if (!name || !company) {
    showError('Please fill in all fields');
    return;
  }

  try {
    const companies = await searchCompanies(company);
    if (companies.length === 0) {
      showError('Could not find any matching companies');
      return;
    }

    showCompanyOptions(companies, name);
  } catch (error) {
    showError('An error occurred while searching');
    console.error(error);
  }
});

async function searchCompanies(company) {
  // Create variations of the company name
  const name_clean = company.toLowerCase().replace(' ', '');
  const variations = [
    company,
    name_clean,
    `${name_clean}capital`,
    `${name_clean}cap`,
    `${company} capital`,
    `${company} partners`,
    `${name_clean}-capital`
  ];

  const companies = new Set();

  // Try each variation
  for (const variation of variations) {
    try {
      const response = await fetch(
        `https://api.hunter.io/v2/domain-search?company=${encodeURIComponent(variation)}&api_key=${HUNTER_API_KEY}`
      );
      const data = await response.json();

      if (data.data) {
        // Add main result
        if (data.data.domain) {
          companies.add({
            name: data.data.organization || variation,
            domain: data.data.domain,
            pattern: data.data.pattern
          });
        }

        // Add alternative domains
        if (data.data.alternative_domains) {
          data.data.alternative_domains.forEach(alt => {
            companies.add({
              name: alt.organization || variation,
              domain: alt.domain,
              pattern: alt.pattern
            });
          });
        }
      }
    } catch (error) {
      console.error(`Error searching for variation '${variation}':`, error);
    }
  }

  // Convert Set to Array and sort results
  const results = Array.from(companies);

  // Sort by relevance
  return results.sort((a, b) => {
    // Exact matches first
    const aExact = a.name.toLowerCase().includes(company.toLowerCase());
    const bExact = b.name.toLowerCase().includes(company.toLowerCase());
    if (aExact && !bExact) return -1;
    if (!aExact && bExact) return 1;

    // Then by name length (shorter names first)
    return a.name.length - b.name.length;
  });
}

function showCompanyOptions(companies, fullName) {
  const container = document.getElementById('companyOptions');
  container.innerHTML = '';
  
  companies.forEach((company, index) => {
    const option = document.createElement('div');
    option.className = 'company-option';
    option.innerHTML = `
      <input type="radio" name="selected_company" id="company_${index}" 
             value="${index}" required>
      <label for="company_${index}" class="company-label">
        <span class="company-name">${company.name}</span>
        <span class="company-domain">${company.domain}</span>
      </label>
    `;
    
    option.querySelector('input').addEventListener('change', () => {
      generateEmail(company, fullName);
    });
    
    container.appendChild(option);
  });
  
  document.getElementById('companySelection').style.display = 'block';
  document.getElementById('result').style.display = 'none';
  document.getElementById('error').style.display = 'none';
}

function generateEmail(company, fullName) {
  const [firstName, ...lastParts] = fullName.split(' ');
  const lastName = lastParts.join(' ');

  const pattern = company.pattern || '{first}.{last}';
  const email = pattern
    .replace('{first}', firstName.toLowerCase())
    .replace('{last}', lastName.toLowerCase())
    .replace('{f}', firstName[0].toLowerCase())
    .replace('{l}', lastName[0].toLowerCase());

  const fullEmail = `${email}@${company.domain}`;

  // Hide company selection and show result
  document.getElementById('companySelection').style.display = 'none';

  const resultBox = document.getElementById('result');
  resultBox.style.display = 'block';
  document.getElementById('emailText').textContent = fullEmail;

  // Scroll to result with smooth animation
  resultBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  // Add highlight animation
  resultBox.classList.add('highlight');
  setTimeout(() => {
    resultBox.classList.remove('highlight');
  }, 1000);
}

document.getElementById('copyButton').addEventListener('click', () => {
  const email = document.getElementById('emailText').textContent;
  navigator.clipboard.writeText(email);

  const btn = document.getElementById('copyButton');
  btn.textContent = 'Copied!';
  setTimeout(() => {
    btn.textContent = 'Copy';
  }, 2000);
});

function showError(message) {
  const errorBox = document.getElementById('error');
  document.getElementById('errorText').textContent = message;
  errorBox.style.display = 'block';
  document.getElementById('companySelection').style.display = 'none';
  document.getElementById('result').style.display = 'none';
}

document.getElementById('backButton').addEventListener('click', () => {
  // Hide result and show company selection
  document.getElementById('result').style.display = 'none';
  document.getElementById('companySelection').style.display = 'block';
  
  // Uncheck the selected radio button
  const selectedRadio = document.querySelector('input[name="selected_company"]:checked');
  if (selectedRadio) {
    selectedRadio.checked = false;
  }
}); 