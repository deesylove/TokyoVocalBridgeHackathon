# Knowledge Base Analysis

## Summary Table

| File | Topic | Key Decision Factors | Steps Count | Critical Deadlines |
|-|-|-|-|-|
| `banking/international-transfers.md` | Sending/receiving money internationally from Japan | Transfer method (Wise vs bank vs fintech), transfer amount (reporting thresholds at 1M and 30M yen), direction (sending vs receiving), whether income is taxable | 6 | 20 days to report 30M+ yen transfers; Feb 16-Mar 15 for overseas income tax filing; Wise MyNumber verification before account functional |
| `banking/opening-bank-account.md` | Opening a Japanese bank account as a foreigner | Time in Japan (<6 months vs >6 months), employer requirements, need for English support, cash card vs debit card | 9 | Before first payday (account + 1-2 weeks for card); MyNumber submission; address update after moving |
| `healthcare/finding-doctors.md` | Finding medical care and English-speaking doctors | Severity (clinic vs hospital), language needs, specialty required, insurance type (NHI vs shakai hoken), mental health vs physical vs dental | 9 (visit process) | Annual health checkup (employer-mandated yearly; NHI Jun-Oct); prescription validity 4 days; insurance enrollment 14 days; medical expense deduction by Mar 15 |
| `healthcare/health-insurance-guide.md` | Japan's mandatory health insurance system | Employment type (company employee vs self-employed/freelancer/student), income level, number of dependents | 6 (NHI enrollment) | 14 days to enroll after residency or job loss; 14 days to report household changes; 2 years retroactive claim window; monthly premium due dates |
| `housing/renting-in-japan.md` | Renting a private apartment as a foreigner | Budget, location, apartment size (1R/1K/1LDK/etc.), foreigner-friendliness of landlord, guarantor availability, employment stability | 8 | 14 days to register new address (fine up to 50,000 yen); rent due 25th-27th of prior month; 1-2 months move-out notice; lease renewal at 2-year mark |
| `housing/ur-housing-guide.md` | UR government-backed housing (no key money, no guarantor) | Income level (4x monthly rent), savings (100x monthly rent), willingness to accept older/suburban buildings, availability | 6 | 14 days to register new address; rent due end of prior month; 14 days move-out notice |
| `pension/lump-sum-withdrawal.md` | Claiming pension refund when leaving Japan permanently | Contribution duration (6mo+ required, 5yr cap), pension type (National vs Employees'), home country totalization agreement, contribution length vs 10yr threshold | 13 | Within 2 years of leaving Japan (strict); appoint tax representative before departure; move-out notification before departure; tax refund filing Feb 16-Mar 15 (or up to 5 years for refunds) |
| `pension/pension-system-overview.md` | Japan's mandatory pension system for foreign residents | Employment type (employee vs self-employed), age (20-59), income level (for exemptions), length of stay, home country totalization agreements | 4 (enrollment) | 14 days to enroll after residency/job change; 2 years for retroactive payments; 10 years minimum for pension qualification; 2 years after leaving to claim lump-sum; age 65 for benefits |
| `tax/income-tax-guide.md` | National income tax for foreign professionals | Tax residency status (non-resident <1yr, non-permanent <=5yr, permanent >5yr), employment type (salaried vs self-employed), income level, whether year-end adjustment applies | 6 | Nov-Dec year-end adjustment forms; Jan 31 employer issues gensen choshuhyo; Feb 16-Mar 15 filing period; Mar 15 payment deadline; file before departure if leaving permanently |
| `tax/residence-tax-guide.md` | Local residence tax (juminzei) based on prior-year income | January 1 residency status, employment type (special vs ordinary collection), income level, whether leaving Japan mid-year | 4 (for each payment method) | Jan 1 residency determination; Mar 15 tax return; Jun/Aug/Oct/Jan installment due dates; settle tax or appoint nozei kanrinin before departure |
| `tax/tax-return-filing.md` | How and when to file a tax return (kakutei shinkoku) | Filing requirement triggers (multiple employers, >20M salary, >200K side income, self-employed, leaving Japan), filing method (e-Tax vs paper vs mail), refund eligibility | 10 (e-Tax) + checklist | Jan 1 earliest refund filing; Feb 16 filing period opens; Mar 15 filing AND payment deadline; file before departure; 5 years for refund-only returns; 5 years for correction claims |
| `visa/first-steps-arrival.md` | Critical registrations in first 14 days after arriving in Japan | Visa type (work vs dependent), employer insurance enrollment path, bank account timing (<6mo vs >6mo) | 8 | 14 days to register address (fine 200,000 yen); immediately enroll health insurance + pension after registration; MyNumber to employer ASAP |
| `visa/path-to-permanent-residency.md` | Pathways to permanent residency (eijuken) | Residence duration, HSP points (70+ = 3yr, 80+ = 1yr), marriage to Japanese national, tax/pension compliance, income level, visa duration held | ~7 (application process) | 10yr residence (general), 3yr (70pt HSP), 1yr (80pt HSP); 3yr marriage + 1yr residence (spouse route); renew visa before expiry during PR processing; PR card renewal every 7 years; re-entry permit for >1yr absence |
| `visa/residence-card-guide.md` | Residence Card obligations, updates, renewal, and loss procedures | Type of change (address, employer, visa renewal, loss/theft), visa scope vs new job, digital system updates | 6+ (varies by procedure) | 14 days to update address; 14 days to notify employer change; 14 days to apply for reissuance after loss; 3 months before expiry to start renewal; return card at departure |

## Cross-References Between Files

### Tax Representative (nozei kanrinin) -- Central Hub for Departure

| Source File | Connects To | Reference |
|-|-|-|
| `pension/lump-sum-withdrawal.md` | `tax/tax-return-filing.md`, `tax/residence-tax-guide.md` | Recommends appointing a tax representative before departure to recover the 20.42% withholding tax on the pension lump-sum withdrawal |
| `tax/residence-tax-guide.md` | `pension/lump-sum-withdrawal.md`, `tax/tax-return-filing.md` | Describes nozei kanrinin appointment process for handling residence tax after departure |
| `tax/tax-return-filing.md` | `pension/lump-sum-withdrawal.md`, `tax/residence-tax-guide.md` | Filing before departure or via tax representative; references residence-tax-guide.md explicitly |

### Pension and Tax Filing

| Source File | Connects To | Reference |
|-|-|-|
| `pension/pension-system-overview.md` | `pension/lump-sum-withdrawal.md` | Directly references "separate lump-sum withdrawal guide" for departure options |
| `pension/lump-sum-withdrawal.md` | `tax/tax-return-filing.md` | Tax return (kakutei shinkoku) must be filed to recover withheld 20.42% tax on pension withdrawal |
| `pension/lump-sum-withdrawal.md` | `tax/income-tax-guide.md` | Tax representative concept and filing deadlines (Feb 16 - Mar 15) |
| `tax/income-tax-guide.md` | `tax/tax-return-filing.md` | Explicitly references "tax-return-filing.md" for when/how to file |
| `tax/income-tax-guide.md` | `tax/residence-tax-guide.md` | Explicitly references "residence-tax-guide.md" for local income tax details |

### Health Insurance and Healthcare

| Source File | Connects To | Reference |
|-|-|-|
| `healthcare/health-insurance-guide.md` | `healthcare/finding-doctors.md` | Insurance card (hokensho) required at all doctor visits; 30% co-pay applies to prescriptions at pharmacies |
| `healthcare/finding-doctors.md` | `healthcare/health-insurance-guide.md` | Requires insurance enrollment; references insurance types (NHI vs shakai hoken) |
| `healthcare/finding-doctors.md` | `tax/tax-return-filing.md` | Medical expense deduction >100,000 yen claimed via tax return by March 15 |
| `tax/income-tax-guide.md` | `healthcare/finding-doctors.md` | Medical expense deduction (iryo-hi kojo) references household medical costs |

### First Steps and Downstream Dependencies

| Source File | Connects To | Reference |
|-|-|-|
| `visa/first-steps-arrival.md` | `healthcare/health-insurance-guide.md` | Step 4 covers health insurance enrollment (both shakai hoken and NHI paths) |
| `visa/first-steps-arrival.md` | `pension/pension-system-overview.md` | Step 5 covers pension enrollment; mentions lump-sum withdrawal (dattai ichijikin) |
| `visa/first-steps-arrival.md` | `banking/opening-bank-account.md` | Step 6 covers bank account opening; references Yucho, Shinsei, Wise, and 6-month rule |
| `visa/first-steps-arrival.md` | `visa/residence-card-guide.md` | Step 1 covers Residence Card issuance at airport; address registration updates the card |

### Housing and Address Registration

| Source File | Connects To | Reference |
|-|-|-|
| `housing/renting-in-japan.md` | `visa/residence-card-guide.md` | 14-day address registration requirement at ward office after moving |
| `housing/renting-in-japan.md` | `visa/first-steps-arrival.md` | Utility setup and ward office address change referenced |
| `housing/ur-housing-guide.md` | `housing/renting-in-japan.md` | UR guide references "the renting guide" for utility setup details; acts as alternative to private rentals |
| `housing/ur-housing-guide.md` | `visa/residence-card-guide.md` | 14-day address registration same obligation |

### Banking and International Money

| Source File | Connects To | Reference |
|-|-|-|
| `banking/international-transfers.md` | `banking/opening-bank-account.md` | Requires a Japanese bank account for funding Wise or making wire transfers; references MyNumber requirement |
| `banking/international-transfers.md` | `tax/tax-return-filing.md` | Overseas income received in Japan is taxable and must be declared; Feb 16-Mar 15 filing |
| `banking/opening-bank-account.md` | `visa/first-steps-arrival.md` | Bank account depends on address registration and MyNumber; employer may require specific bank |

### Permanent Residency and Compliance

| Source File | Connects To | Reference |
|-|-|-|
| `visa/path-to-permanent-residency.md` | `tax/income-tax-guide.md`, `tax/residence-tax-guide.md` | Tax compliance (shotokuzei + juuminzei) is a strict requirement; 5 years of tax certificates needed |
| `visa/path-to-permanent-residency.md` | `pension/pension-system-overview.md` | Pension payment compliance strictly enforced; even 1 late payment can cause denial |
| `visa/path-to-permanent-residency.md` | `healthcare/health-insurance-guide.md` | Health insurance enrollment and payment compliance required for PR application |
| `visa/path-to-permanent-residency.md` | `visa/residence-card-guide.md` | Must hold maximum visa duration; PR card renewed every 7 years |

### MyNumber as Universal Dependency

MyNumber is referenced across almost all files as a prerequisite:

- `visa/first-steps-arrival.md` -- assigned after address registration
- `banking/opening-bank-account.md` -- required to open bank account
- `banking/international-transfers.md` -- required for Wise and all financial services
- `tax/income-tax-guide.md` -- required for employer tax withholding
- `tax/tax-return-filing.md` -- required for e-Tax filing
- `healthcare/health-insurance-guide.md` -- required for NHI enrollment
- `pension/pension-system-overview.md` -- required for pension enrollment

### Departure Workflow (Cross-cutting)

When leaving Japan permanently, these files form a connected sequence:

1. `pension/lump-sum-withdrawal.md` -- claim pension refund after departure
2. `tax/tax-return-filing.md` -- file final tax return before departure or via representative
3. `tax/residence-tax-guide.md` -- settle residence tax or appoint nozei kanrinin
4. `tax/income-tax-guide.md` -- file income tax for partial year
5. `visa/residence-card-guide.md` -- return card at airport
6. `banking/international-transfers.md` -- transfer remaining funds out of Japan
