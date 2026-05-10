# TODOs

## TODOs
1. Add pricing calculations tab to understand back end calculations
2. Need to add a promo code note section in Admin
2. Create seeds file for each of the pricing sheets in `management/pricing_sheets`

# Current bugs/fixes
- Make the delete confirmation on the home page more UI clean and not just a Google error message or whatever it is
- FICA should not be subtracted out of Post Cutoff Cost %
- Default turnover rate needs to be fixed or removed
- When Worker Comp carve out is active, still need to display the workers compensation codes page, grey out the workers comp code and section, and get payroll and fees and PEPM
- On the SUTA page WSES W/ TURNOVER and TAXABLE GWS don't update with a refresh, and WSES W/ TURNOVER should be rounded to a whole number
- Need to add REVERSE WIRE and ACH as separate values in config — pricing system needs to check if the user is using reverse wire or ACH and then calculate the price
- Might need to add a button to turn off TLM in calculations

## Questions
1. How should SUTA deal with self-reporting states? More specifically ME and NY — those are the 2 states that provide rates even though they are marked as self-reporting. Right now the system just uses the uploaded file as the final decision: if there is a rate it uses it, if not it carves it out. Is that the correct outcome?

2. How should commission be calculated? Currently it assumes 25% upfront and 20% ongoing. When there is a broker, it assumes the broker gets a portion of WC as noted in the commission section, and a portion of admin (max 40%). The consultant on the deal gets 10% no matter what, but will get more if the admin rate is lower than 30% — specifically the difference between 40% and the current broker admin rate.

3. How is reverse wire and ACH determined — whether it should be added to the deal or not? On the spreadsheet it is very confusing to tell what determines if it is or isn't included. And why is TLM not included most of the time?

## Notes
- Benefits calculation inside the pricing tool is not set up at all — it just collects some questions right now and does not factor in any numbers for the final proposal.
- None of the additional fees in system configuration are being used for anything right now. **Min WC Fee per Week** is not being used at all either.

## Key Differences
- The FICA wage cap is implemented and is used for pre and post cutoff calculation on the proposal (might need to be changed as it may be unrealistic).
- The bottom of the summary is displayed a little differently than it is on the spreadsheet.
- How SUTA non-client-reporting states are calculated differs a little from how the spreadsheet does it. The spreadsheet uses the old client rate as the cost rate for the SUTA non-client-reporting rates with a minimum rate, which makes no sense.

## Next Steps
- Authentication & Multi-User Access
- Task creation, quote submissions, proposal generation
