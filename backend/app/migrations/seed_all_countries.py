"""Seed a comprehensive ISO country list with flag emojis.

Idempotent: existing rows (matched by ISO) are left untouched. Missing rows are added
as enabled=True with the proper flag + dial code so the admin panel & bot dropdowns
show every country with its flag.

Run:
    docker compose exec api python -m app.migrations.seed_all_countries
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from ..db import SessionLocal
from ..models import Country


def _flag(iso: str) -> str:
    iso = iso.upper()
    if len(iso) != 2 or not iso.isalpha():
        return "🌍"
    return chr(0x1F1E6 + ord(iso[0]) - 65) + chr(0x1F1E6 + ord(iso[1]) - 65)


# (name, dial_code, iso2)
COUNTRIES: list[tuple[str, str, str]] = [
    ("Afghanistan", "93", "AF"), ("Albania", "355", "AL"), ("Algeria", "213", "DZ"),
    ("Andorra", "376", "AD"), ("Angola", "244", "AO"), ("Argentina", "54", "AR"),
    ("Armenia", "374", "AM"), ("Australia", "61", "AU"), ("Austria", "43", "AT"),
    ("Azerbaijan", "994", "AZ"), ("Bahrain", "973", "BH"), ("Bangladesh", "880", "BD"),
    ("Belarus", "375", "BY"), ("Belgium", "32", "BE"), ("Belize", "501", "BZ"),
    ("Benin", "229", "BJ"), ("Bhutan", "975", "BT"), ("Bolivia", "591", "BO"),
    ("Bosnia and Herzegovina", "387", "BA"), ("Botswana", "267", "BW"),
    ("Brazil", "55", "BR"), ("Brunei", "673", "BN"), ("Bulgaria", "359", "BG"),
    ("Burkina Faso", "226", "BF"), ("Burundi", "257", "BI"), ("Cambodia", "855", "KH"),
    ("Cameroon", "237", "CM"), ("Canada", "1", "CA"), ("Cape Verde", "238", "CV"),
    ("Central African Republic", "236", "CF"), ("Chad", "235", "TD"),
    ("Chile", "56", "CL"), ("China", "86", "CN"), ("Colombia", "57", "CO"),
    ("Comoros", "269", "KM"), ("Congo", "242", "CG"),
    ("Congo (DRC)", "243", "CD"), ("Costa Rica", "506", "CR"),
    ("Côte d'Ivoire", "225", "CI"), ("Croatia", "385", "HR"), ("Cuba", "53", "CU"),
    ("Cyprus", "357", "CY"), ("Czech Republic", "420", "CZ"),
    ("Denmark", "45", "DK"), ("Djibouti", "253", "DJ"),
    ("Dominican Republic", "1809", "DO"), ("Ecuador", "593", "EC"),
    ("Egypt", "20", "EG"), ("El Salvador", "503", "SV"),
    ("Equatorial Guinea", "240", "GQ"), ("Eritrea", "291", "ER"),
    ("Estonia", "372", "EE"), ("Eswatini", "268", "SZ"), ("Ethiopia", "251", "ET"),
    ("Fiji", "679", "FJ"), ("Finland", "358", "FI"), ("France", "33", "FR"),
    ("Gabon", "241", "GA"), ("Gambia", "220", "GM"), ("Georgia", "995", "GE"),
    ("Germany", "49", "DE"), ("Ghana", "233", "GH"), ("Greece", "30", "GR"),
    ("Guatemala", "502", "GT"), ("Guinea", "224", "GN"), ("Guinea-Bissau", "245", "GW"),
    ("Guyana", "592", "GY"), ("Haiti", "509", "HT"), ("Honduras", "504", "HN"),
    ("Hong Kong", "852", "HK"), ("Hungary", "36", "HU"), ("Iceland", "354", "IS"),
    ("India", "91", "IN"), ("Indonesia", "62", "ID"), ("Iran", "98", "IR"),
    ("Iraq", "964", "IQ"), ("Ireland", "353", "IE"), ("Israel", "972", "IL"),
    ("Italy", "39", "IT"), ("Jamaica", "1876", "JM"), ("Japan", "81", "JP"),
    ("Jordan", "962", "JO"), ("Kazakhstan", "7", "KZ"), ("Kenya", "254", "KE"),
    ("Kuwait", "965", "KW"), ("Kyrgyzstan", "996", "KG"), ("Laos", "856", "LA"),
    ("Latvia", "371", "LV"), ("Lebanon", "961", "LB"), ("Lesotho", "266", "LS"),
    ("Liberia", "231", "LR"), ("Libya", "218", "LY"), ("Liechtenstein", "423", "LI"),
    ("Lithuania", "370", "LT"), ("Luxembourg", "352", "LU"), ("Macau", "853", "MO"),
    ("Madagascar", "261", "MG"), ("Malawi", "265", "MW"), ("Malaysia", "60", "MY"),
    ("Maldives", "960", "MV"), ("Mali", "223", "ML"), ("Malta", "356", "MT"),
    ("Mauritania", "222", "MR"), ("Mauritius", "230", "MU"), ("Mexico", "52", "MX"),
    ("Moldova", "373", "MD"), ("Monaco", "377", "MC"), ("Mongolia", "976", "MN"),
    ("Montenegro", "382", "ME"), ("Morocco", "212", "MA"), ("Mozambique", "258", "MZ"),
    ("Myanmar", "95", "MM"), ("Namibia", "264", "NA"), ("Nepal", "977", "NP"),
    ("Netherlands", "31", "NL"), ("New Zealand", "64", "NZ"),
    ("Nicaragua", "505", "NI"), ("Niger", "227", "NE"), ("Nigeria", "234", "NG"),
    ("North Korea", "850", "KP"), ("North Macedonia", "389", "MK"),
    ("Norway", "47", "NO"), ("Oman", "968", "OM"), ("Pakistan", "92", "PK"),
    ("Palestine", "970", "PS"), ("Panama", "507", "PA"),
    ("Papua New Guinea", "675", "PG"), ("Paraguay", "595", "PY"),
    ("Peru", "51", "PE"), ("Philippines", "63", "PH"), ("Poland", "48", "PL"),
    ("Portugal", "351", "PT"), ("Qatar", "974", "QA"), ("Romania", "40", "RO"),
    ("Russia", "7", "RU"), ("Rwanda", "250", "RW"), ("Saudi Arabia", "966", "SA"),
    ("Senegal", "221", "SN"), ("Serbia", "381", "RS"), ("Seychelles", "248", "SC"),
    ("Sierra Leone", "232", "SL"), ("Singapore", "65", "SG"),
    ("Slovakia", "421", "SK"), ("Slovenia", "386", "SI"), ("Somalia", "252", "SO"),
    ("South Africa", "27", "ZA"), ("South Korea", "82", "KR"),
    ("South Sudan", "211", "SS"), ("Spain", "34", "ES"), ("Sri Lanka", "94", "LK"),
    ("Sudan", "249", "SD"), ("Suriname", "597", "SR"), ("Sweden", "46", "SE"),
    ("Switzerland", "41", "CH"), ("Syria", "963", "SY"), ("Taiwan", "886", "TW"),
    ("Tajikistan", "992", "TJ"), ("Tanzania", "255", "TZ"), ("Thailand", "66", "TH"),
    ("Timor-Leste", "670", "TL"), ("Togo", "228", "TG"), ("Tunisia", "216", "TN"),
    ("Turkey", "90", "TR"), ("Turkmenistan", "993", "TM"), ("Uganda", "256", "UG"),
    ("Ukraine", "380", "UA"), ("United Arab Emirates", "971", "AE"),
    ("United Kingdom", "44", "GB"), ("United States", "1", "US"),
    ("Uruguay", "598", "UY"), ("Uzbekistan", "998", "UZ"), ("Vatican City", "379", "VA"),
    ("Venezuela", "58", "VE"), ("Vietnam", "84", "VN"), ("Yemen", "967", "YE"),
    ("Zambia", "260", "ZM"), ("Zimbabwe", "263", "ZW"),
]


async def _run() -> None:
    added = 0
    flag_fixed = 0
    async with SessionLocal() as s:
        existing = (await s.execute(select(Country))).scalars().all()
        by_iso = {(c.iso or "").upper(): c for c in existing if c.iso}
        for name, code, iso in COUNTRIES:
            iso_u = iso.upper()
            row = by_iso.get(iso_u)
            if row is None:
                s.add(Country(
                    name=name, code=code, iso=iso_u, flag=_flag(iso_u), enabled=True,
                ))
                added += 1
            else:
                # Backfill missing flag emoji on previously-seeded rows
                if not row.flag or row.flag == "🌍":
                    row.flag = _flag(iso_u)
                    flag_fixed += 1
        await s.commit()
    print(f"countries seed: added={added} flags_fixed={flag_fixed}")


if __name__ == "__main__":
    asyncio.run(_run())
