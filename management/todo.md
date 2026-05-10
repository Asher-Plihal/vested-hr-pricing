# TODOs

## TODOs
1. Add pricing calculations tab to understand back end calculations
2. Need to add a promo code note section in Admin
2. Create seeds file for each of the pricing sheets in `management/pricing_sheets`

# Current bugs/fixes
- Make the delete confirmation on the home page more UI clean and not just a Google error message or whatever it is
- When Worker Comp carve out is active, still need to display the workers compensation codes page, grey out the workers comp code and section, and get payroll and fees and PEPM

## Questions
1. How should SUTA deal with self-reporting states? More specifically ME and NY — those are the 2 states that provide rates even though they are marked as self-reporting. Right now the system just uses the uploaded file as the final decision: if there is a rate it uses it, if not it carves it out. Is that the correct outcome?

2. How should commission be calculated? Currently it assumes 25% upfront and 20% ongoing. When there is a broker, it assumes the broker gets a portion of WC as noted in the commission section, and a portion of admin (max 40%). The consultant on the deal gets 10% no matter what, but will get more if the admin rate is lower than 30% — specifically the difference between 40% and the current broker admin rate.

3. How is reverse wire and ACH determined — whether it should be added to the deal or not? And why is TLM not included most of the time, should it be?

4. How should hwne worker comp is carved out be handle? Right now annual payroll, FTES, PTES are collected thruought the worker comp page for all caculations

## Notes
- Benefits calculation inside the pricing tool is not set up at all — it just collects some questions right now and does not factor in any numbers for the final proposal.
- None of the additional fees in system configuration are being used for anything right now. **Min WC Fee per Week** is not being used at all either.
- Payment method on the general tab is not used on the spreadsheete to determine weither to charge ach fee or reverse wire fee the pricing caculator does have that.
- Right now there is a box to put a promtion if there is one on the deal just like the spreadsheet it does not use it at all in the caculations, but if you knew all your types of perotion and set it up the caculator could caculate the value with the promotion. 

## Key Differences
- The FICA wage cap is implemented and is used for pre and post cutoff calculation on the proposal (might need to be changed as it may be unrealistic).
- The bottom of the summary is displayed a little differently than it is on the spreadsheet.
- How SUTA non-client-reporting states are calculated differs a little from how the spreadsheet does it. The spreadsheet uses the old client rate as the cost rate for the SUTA non-client-reporting rates with a minimum rate, which makes no sense.

## Next Steps
- Authentication & Multi-User Access
- Task creation, quote submissions, proposal generation
